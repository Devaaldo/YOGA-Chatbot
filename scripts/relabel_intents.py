"""
Relabel the location-centric intent dataset into a *semantic* taxonomy.

Background
----------
``intents_diy_full.json`` labels patterns by location (``kabupaten_bantul``,
``kecamatan_pakem``, ...) — 80 location classes plus a few greetings. But the
bot's action layer (``bot/handlers.py``) and the inference pipeline (which
replaces location names with ``[LOKASI]`` before classification) are built
around *semantic* intents. The two taxonomies never matched, so every location
query fell through to the fallback handler.

This script maps each pattern to one of the semantic intents the bot actually
routes on, using keyword heuristics, and merges greeting responses. Location is
intentionally dropped from the label space — it is handled by the
``EntityExtractor`` at runtime.

Output classes
--------------
greeting, pagi, siang, sore, malam, goodbye,
rekomendasi_wisata, cari_by_type, cari_by_harga, cari_by_rating,
info_detail, info_lokasi

Usage
-----
    PYTHONPATH=src python scripts/relabel_intents.py \\
        --input  data/raw/intents_diy_full.json \\
        --output data/raw/intents_semantic.json

The heuristic is best-effort: review the printed distribution and a sample of
relabelled patterns, then hand-correct ``intents_semantic.json`` as needed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# Greeting tags are carried through unchanged.
GREETING_TAGS: frozenset[str] = frozenset(
    {"greeting", "pagi", "siang", "sore", "malam", "goodbye"}
)

# Tourism category keywords that signal a "search by type" query.
TYPE_KEYWORDS: list[str] = [
    "pantai", "candi", "gunung", "bukit", "museum", "budaya", "sejarah",
    "alam", "kuliner", "air terjun", "waterfall", "taman", "goa", "gua",
    "danau", "sawah", "hutan", "embung", "tebing", "jurang",
]

# Ordered, most-specific-first heuristic rules. First match wins.
_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("cari_by_harga", re.compile(
        r"\b(harga|murah|mahal|tiket|biaya|budget|gratis|hemat|terjangkau"
        r"|\d+\s*(rb|ribu|k|jt|juta))\b")),
    ("cari_by_rating", re.compile(
        r"\b(rating|terbaik|populer|favorit|recommended|hits|kekinian"
        r"|viral|bagus|terkenal|paling)\b")),
    ("info_lokasi", re.compile(
        r"\b(lokasi|alamat|dimana|di mana|arah|maps|peta|menuju|jalan ke)\b")),
    ("info_detail", re.compile(
        r"\b(info|tentang|jelaskan|detail|deskripsi|ceritakan|apa itu|sejarah)\b")),
]

_TYPE_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in TYPE_KEYWORDS) + r")")

# Hand-authored seed patterns for intents the source data under-represents.
# Expand these freely; they are merged into the relabelled dataset.
SEED_PATTERNS: dict[str, list[str]] = {
    "cari_by_harga": [
        "wisata murah di jogja", "tempat wisata tiket murah",
        "rekomendasi wisata hemat", "wisata budget 20rb",
        "tiket masuk murah", "wisata gratis di yogyakarta",
        "tempat wisata terjangkau", "wisata di bawah 50 ribu",
        "harga tiket masuk berapa", "wisata murah meriah",
        "cari wisata hemat di sleman", "tempat wisata tiket di bawah 30rb",
        "wisata gratis tanpa tiket", "rekomendasi wisata harga terjangkau",
        "tempat wisata murah buat keluarga",
    ],
    "cari_by_type": [
        "rekomendasi pantai", "wisata candi di jogja", "tempat wisata alam",
        "cari museum di yogyakarta", "wisata kuliner jogja",
        "tempat wisata bukit", "wisata air terjun", "rekomendasi goa",
        "wisata taman", "tempat wisata budaya dan sejarah",
    ],
    "info_lokasi": [
        "lokasi wisata terdekat", "alamat tempat wisata",
    ],
}


def classify(pattern: str) -> str:
    """Map a single raw pattern to a semantic intent tag."""
    text = pattern.lower()
    for tag, rule in _RULES:
        if rule.search(text):
            return tag
    if _TYPE_RE.search(text):
        return "cari_by_type"
    return "rekomendasi_wisata"


def relabel(input_path: Path, output_path: Path) -> None:
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    patterns_by_tag: dict[str, list[str]] = defaultdict(list)
    responses_by_tag: dict[str, list[str]] = defaultdict(list)

    for intent in data["intents"]:
        src_tag = intent["tag"]
        responses = intent.get("responses", [])
        if src_tag in GREETING_TAGS:
            patterns_by_tag[src_tag].extend(intent["patterns"])
            responses_by_tag[src_tag].extend(responses)
            continue
        for pattern in intent["patterns"]:
            target = classify(pattern)
            patterns_by_tag[target].append(pattern)
            responses_by_tag[target].extend(responses)

    # Merge in hand-authored seed patterns.
    for tag, seeds in SEED_PATTERNS.items():
        patterns_by_tag[tag].extend(seeds)

    # Build output, de-duplicating patterns and responses per tag.
    intents_out = []
    for tag, patterns in patterns_by_tag.items():
        intents_out.append({
            "tag": tag,
            "patterns": _dedup(patterns),
            "responses": _dedup(responses_by_tag[tag]),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"intents": intents_out}, f, ensure_ascii=False, indent=2)

    print("Relabelled intent distribution:")
    for intent in sorted(intents_out, key=lambda i: -len(i["patterns"])):
        print(f"  {intent['tag']:20} {len(intent['patterns'])}")
    print(f"\nOutput: {output_path}")


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(key)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=Path("data/raw/intents_diy_full.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/raw/intents_semantic.json"))
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    relabel(args.input, args.output)
