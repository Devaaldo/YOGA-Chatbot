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
    "greeting": [
        "halo", "hai", "hi", "hello", "hey", "haii", "halo kak", "hai kak",
        "halo yoga", "hai yoga", "halo bot", "hi min", "hello admin",
        "permisi", "assalamualaikum", "woi", "oi", "halo min", "hai bot",
        "hai admin", "halo gan", "hallo", "haloo", "hola", "halo yoga bot",
    ],
    "pagi": [
        "selamat pagi", "pagi", "met pagi", "pagi kak", "morning",
        "good morning", "selamat pagi yoga", "pagi bot", "pagi min",
        "pagi gan", "slamat pagi", "pagi semua", "selamat pagi kak",
        "met pagi yoga", "pagiii",
    ],
    "siang": [
        "selamat siang", "siang", "met siang", "siang kak", "good afternoon",
        "selamat siang yoga", "siang bot", "siang min", "slamat siang",
        "siang semua", "selamat siang kak", "met siang yoga", "siangg",
    ],
    "sore": [
        "selamat sore", "sore", "met sore", "sore kak", "selamat sore yoga",
        "sore bot", "sore min", "slamat sore", "sore semua",
        "selamat sore kak", "met sore yoga", "soree",
    ],
    "malam": [
        "selamat malam", "malam", "met malam", "malam kak", "good evening",
        "good night", "selamat malam yoga", "malam bot", "malam min",
        "met malem", "malem", "slamat malam", "malam semua", "malemm",
    ],
    "goodbye": [
        "dadah", "bye", "sampai jumpa", "makasih ya", "terima kasih",
        "thanks", "sampai nanti", "see you", "selamat tinggal", "babai",
        "bye bye", "makasih bot", "sampai jumpa lagi", "oke makasih",
        "thank you", "sip makasih", "udahan dulu", "makasih yoga",
        "da da", "terima kasih banyak",
    ],
    "cari_by_harga": [
        "wisata murah di jogja", "tempat wisata tiket murah",
        "rekomendasi wisata hemat", "wisata budget 20rb",
        "tiket masuk murah", "wisata gratis di yogyakarta",
        "tempat wisata terjangkau", "wisata di bawah 50 ribu",
        "harga tiket masuk berapa", "wisata murah meriah",
        "cari wisata hemat di sleman", "tempat wisata tiket di bawah 30rb",
        "wisata gratis tanpa tiket", "rekomendasi wisata harga terjangkau",
        "tempat wisata murah buat keluarga", "wisata tiket 10rb",
        "ada wisata gratis ga", "wisata yang murah dong",
        "tempat wisata budget mahasiswa", "wisata hemat di bantul",
        "rekomendasi wisata murah meriah di jogja", "tiket masuk paling murah",
        "wisata dengan tiket terjangkau", "wisata gratisan",
        "berapa harga tiket masuknya", "wisata murah buat anak kos",
        "wisata di bawah 25 ribu", "tempat wisata gak bayar",
        "wisata yang tiketnya murah", "rekomendasi wisata low budget",
        "wisata murah di gunungkidul", "wisata gratis di kota jogja",
        "tempat wisata tiket 5000", "wisata murah deket sini",
        "ada tempat wisata yang gratis", "wisata hemat buat liburan",
        "tiket masuk dibawah 20rb", "wisata paling murah di jogja",
        "tempat wisata yang terjangkau", "wisata murah tapi bagus",
        "rekomendasi wisata gratis", "wisata budget minim",
        "tempat wisata harga miring", "mau wisata yang murah",
        "wisata 15 ribuan",
    ],
    "cari_by_type": [
        "rekomendasi pantai", "wisata candi di jogja", "tempat wisata alam",
        "cari museum di yogyakarta", "wisata kuliner jogja",
        "tempat wisata bukit", "wisata air terjun", "rekomendasi goa",
        "wisata taman", "tempat wisata budaya dan sejarah",
        "wisata pantai di jogja", "rekomendasi candi", "tempat kuliner enak",
        "wisata gunung", "cari air terjun", "tempat wisata danau",
        "wisata hutan pinus", "spot foto bukit", "wisata edukasi museum",
        "tempat wisata religi", "wisata pantai yang bagus",
        "rekomendasi tempat kuliner", "wisata alam terbuka",
        "cari wisata goa di gunungkidul", "tempat wisata sejarah di jogja",
        "wisata taman bermain", "wisata embung", "tempat wisata tebing",
        "wisata sawah", "wisata budaya jawa", "pantai buat berenang",
        "candi peninggalan sejarah", "tempat makan khas jogja",
        "wisata kebun teh", "rekomendasi air terjun di kulonprogo",
        "wisata pemandian", "tempat wisata outbound", "wisata desa wisata",
        "spot sunrise di bukit", "wisata pantai pasir putih",
        "museum di kota jogja", "tempat wisata keluarga alam",
        "wisata gua pindul", "rekomendasi wisata gunung merapi",
        "tempat wisata air",
    ],
    "cari_by_rating": [
        "rekomendasi wisata rating tertinggi", "wisata paling populer di jogja",
        "tempat wisata terbaik", "wisata rating bagus",
        "wisata yang paling banyak dikunjungi", "tempat wisata favorit",
        "wisata hits di jogja", "destinasi paling recommended",
        "rating terbaik", "wisata viral di jogja", "tempat wisata terpopuler",
        "wisata dengan rating tinggi", "rekomendasi wisata kekinian",
        "wisata terfavorit di sleman", "tempat wisata paling bagus",
        "wisata yang lagi hits", "destinasi wisata terkenal",
        "wisata rating 5 bintang", "tempat wisata yang banyak ulasannya",
        "wisata paling top di jogja", "rekomendasi tempat wisata terbaik",
        "wisata instagramable terpopuler", "tempat wisata yang ramai dikunjungi",
        "wisata terbaik di bantul", "wisata paling recommended di gunungkidul",
        "destinasi favorit wisatawan", "wisata rating tertinggi di jogja",
        "tempat wisata bintang lima", "wisata yang reviewnya bagus",
        "rekomendasi destinasi populer", "wisata paling diminati",
        "tempat wisata kekinian dan hits", "wisata terbaik buat liburan",
        "wisata yang ratingnya tinggi", "destinasi wisata terbaik di jogja",
        "tempat paling banyak direview", "wisata top rating",
        "rekomendasi wisata paling bagus", "wisata terpopuler 2024",
        "tempat wisata yang paling oke",
    ],
    "info_detail": [
        "info candi prambanan", "ceritakan tentang keraton yogyakarta",
        "apa itu taman sari", "jelaskan tentang malioboro",
        "info detail pantai parangtritis", "deskripsi tebing breksi",
        "sejarah candi ratu boko", "info tentang gunung merapi",
        "ceritakan soal goa pindul", "info hutan pinus mangunan",
        "apa itu tugu jogja", "info museum affandi",
        "detail tentang pantai indrayanti", "info kalibiru",
        "jelaskan candi borobudur", "info embung nglanggeran",
        "tentang air terjun sri gethuk", "info alun alun kidul",
        "deskripsi tempat ini", "info lengkap candi prambanan",
        "ceritakan tentang pantai timang", "info tamansari",
        "apa keunikan tebing breksi", "info wisata heha sky view",
        "detail obelix hills", "info pantai depok",
        "jelaskan tentang merapi", "info spot riyadi",
        "tentang museum ullen sentalu", "info bukit bintang",
        "ceritakan tentang taman pelangi", "info gembira loka zoo",
        "detail tentang pinus pengger", "info jurang tembelan",
        "apa itu studio gamplong", "info seribu batu songgo langit",
        "jelaskan tentang pantai glagah", "info wisata di tempat ini",
        "ceritakan lebih detail", "info candi ijo",
    ],
    "info_lokasi": [
        "lokasi wisata terdekat", "alamat tempat wisata",
        "lokasi candi prambanan", "alamat pantai parangtritis dimana",
        "dimana lokasi tebing breksi", "lokasi keraton yogyakarta",
        "alamat malioboro", "arah ke gunung merapi",
        "lokasi goa pindul dimana", "alamat museum affandi",
        "dimana pantai indrayanti", "lokasi hutan pinus mangunan",
        "peta menuju candi ratu boko", "alamat tugu jogja",
        "lokasi taman sari", "dimana letak air terjun sri gethuk",
        "alamat embung nglanggeran", "lokasi kalibiru",
        "arah menuju pantai timang", "dimana lokasi heha sky view",
        "lokasi obelix hills dimana", "alamat pantai depok",
        "peta ke tebing breksi", "lokasi bukit bintang",
        "dimana alamat museum ullen sentalu", "lokasi pinus pengger",
        "arah ke pantai glagah", "alamat gembira loka zoo",
        "dimana studio gamplong", "lokasi candi ijo",
        "letak alun alun kidul", "lokasi spot riyadi dimana",
        "alamat taman pelangi", "dimana lokasi jurang tembelan",
        "arah menuju merapi", "lokasi wisata ini dimana",
        "alamat lengkap tempat ini", "dimana saya bisa menemukan tempat ini",
        "lokasi pantai glagah dimana", "peta lokasi candi prambanan",
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
