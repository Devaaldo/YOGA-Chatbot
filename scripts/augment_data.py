"""
Data augmentation for YOGA Chatbot intent patterns.

Reads an intents JSON file and produces an augmented version by applying
text augmentation techniques per intent class:

  - Greeting intents: greeting_augmentation + random_insertion
  - Location intents: location_augmentation + synonym_replacement
  - General intents:  synonym_replacement + random_insertion + random_deletion

Usage
-----
    python scripts/augment_data.py \\
        --input  data/raw/intents_diy_full.json \\
        --output data/processed/intents_augmented.json \\
        --target 60 \\
        --seed   42

Source: adapted from YOGA-Chatbot-alpha/scripts/augment_data.py
"""

from __future__ import annotations

import argparse
import json
import random
from copy import deepcopy
from pathlib import Path

# ---------------------------------------------------------------------------
# Vocabulary resources
# ---------------------------------------------------------------------------

SYNONYMS: dict[str, list[str]] = {
    "wisata":      ["tempat wisata", "destinasi", "objek wisata", "lokasi wisata", "tujuan wisata"],
    "rekomendasi": ["saran", "usulan", "referensi", "info", "informasi"],
    "dimana":      ["di mana", "lokasinya", "tempatnya", "ada di"],
    "bagus":       ["menarik", "keren", "oke", "recommended", "top"],
    "info":        ["informasi", "data", "keterangan", "penjelasan"],
    "ada":         ["punya", "tersedia", "terdapat"],
    "bisa":        ["dapat", "boleh", "bisa gak", "bisa ga"],
    "mau":         ["ingin", "pengen", "minta"],
    "cari":        ["mencari", "nyari", "butuh", "perlu"],
    "bantu":       ["membantu", "bantuin", "tolong"],
}

GREETING_TEMPLATES: dict[str, list[str]] = {
    "selamat": ["selamat", "met", "slmt", "slamat"],
    "halo":    ["halo", "hai", "hello", "hi", "hey"],
    "suffix":  ["yoga", "bot", "chatbot", "kak", "gan", "min", "mas", "mba"],
}

FILLERS: list[str] = [
    "dong", "deh", "sih", "nih", "ya", "yuk",
    "coba", "tolong", "please", "bro", "sis",
]

LOCATION_PREFIXES: list[str] = [
    "wisata", "tempat wisata", "destinasi",
    "rekomendasi", "info", "wisata di",
]


# ---------------------------------------------------------------------------
# Augmentation functions
# ---------------------------------------------------------------------------


def synonym_replacement(text: str, n: int = 2) -> str:
    words = text.split()
    indices = [i for i, w in enumerate(words) if w in SYNONYMS]
    random.shuffle(indices)
    for idx in indices[:n]:
        words[idx] = random.choice(SYNONYMS[words[idx]])
    return " ".join(words)


def random_insertion(text: str, n: int = 1) -> str:
    words = text.split()
    for _ in range(n):
        words.insert(random.randint(0, len(words)), random.choice(FILLERS))
    return " ".join(words)


def random_deletion(text: str, p: float = 0.1) -> str:
    words = text.split()
    if len(words) == 1:
        return text
    new_words = [w for w in words if random.random() > p]
    return " ".join(new_words) if new_words else random.choice(words)


def greeting_augmentation(text: str) -> list[str]:
    variations: list[str] = []
    lower = text.lower()

    for selamat_var in GREETING_TEMPLATES["selamat"]:
        if "selamat" in lower:
            variations.append(lower.replace("selamat", selamat_var))

    if any(h in lower for h in GREETING_TEMPLATES["halo"]):
        for hello_var in GREETING_TEMPLATES["halo"]:
            for suffix_var in GREETING_TEMPLATES["suffix"]:
                variations.append(f"{hello_var} {suffix_var}")
                variations.append(hello_var)

    return variations


def location_augmentation(text: str, keywords: list[str]) -> list[str]:
    variations: list[str] = []
    lower = text.lower()
    for loc in keywords:
        if loc in lower:
            for prefix in LOCATION_PREFIXES:
                variations.append(f"{prefix} {loc}")
                variations.append(f"{loc} {random.choice(FILLERS)}")
    return variations


def augment_pattern(pattern: str, intent_tag: str) -> list[str]:
    """Return augmented variants for a single pattern."""
    augmented: list[str] = [pattern]

    is_greeting = any(
        x in intent_tag
        for x in ["pagi", "siang", "sore", "malam", "greeting", "goodbye"]
    )
    is_location = "kecamatan_" in intent_tag or "kabupaten_" in intent_tag

    if is_greeting:
        augmented.extend(greeting_augmentation(pattern))
        augmented.append(random_insertion(pattern, 1))

    elif is_location:
        location = intent_tag.split("_")[-1]
        augmented.extend(location_augmentation(pattern, [location]))
        augmented.append(synonym_replacement(pattern, 1))

    else:
        has_synonym = any(w in pattern.lower() for w in SYNONYMS)
        if has_synonym:
            augmented.append(synonym_replacement(pattern, 1))
            augmented.append(synonym_replacement(pattern, 2))
        augmented.append(random_insertion(pattern, 1))
        if len(pattern.split()) > 3:
            augmented.append(random_deletion(pattern, 0.1))

    # Deduplicate, drop empty strings
    seen: set[str] = set()
    result: list[str] = []
    for p in augmented:
        cleaned = p.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def augment_intents(
    input_path: Path,
    output_path: Path,
    target_per_class: int = 60,
    seed: int = 42,
) -> None:
    random.seed(seed)

    with input_path.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    augmented_data = deepcopy(data)
    total_original = 0
    total_final = 0

    for intent in augmented_data["intents"]:
        tag: str = intent["tag"]
        original_patterns: list[str] = intent["patterns"]
        total_original += len(original_patterns)

        all_augmented: list[str] = []
        for pattern in original_patterns:
            all_augmented.extend(augment_pattern(pattern, tag))

        # Deduplicate while preserving originals
        seen: set[str] = set()
        unique: list[str] = []
        for p in all_augmented:
            if p not in seen:
                seen.add(p)
                unique.append(p)

        if len(unique) > target_per_class:
            # Keep all originals; sample from extras
            extras = [p for p in unique if p not in original_patterns]
            random.shuffle(extras)
            final = original_patterns + extras[: target_per_class - len(original_patterns)]
        else:
            final = unique

        intent["patterns"] = final
        total_final += len(final)
        print(f"  {tag}: {len(original_patterns)} → {len(final)} patterns")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=2)

    print(
        f"\nDone. {total_original} original → {total_final} augmented patterns.\n"
        f"Output: {output_path}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Augment intent patterns for YOGA Chatbot training."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/intents_diy_full.json"),
        help="Path to input intents JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/intents_augmented.json"),
        help="Path to output augmented intents JSON file.",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=60,
        help="Target number of patterns per intent class (default: 60).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    augment_intents(
        input_path=args.input,
        output_path=args.output,
        target_per_class=args.target,
        seed=args.seed,
    )
