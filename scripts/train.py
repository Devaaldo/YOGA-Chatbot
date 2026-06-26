"""
Reproducible training pipeline for the YOGA Chatbot intent classifier.

Produces the five artifacts loaded by :class:`HybridIntentClassifier`:
    tfidf_vectorizer.pickle   main 88->semantic TF-IDF (fitted on TRAIN only)
    tfidf_greeting.pickle     binary-detector TF-IDF   (fitted on TRAIN only)
    svm_model.pkl             main multi-class SVM (probability=True)
    greeting_detector.pkl     binary greeting-vs-rest SVM
    label_encoder.pickle      semantic-intent LabelEncoder
plus ``models/metadata.json`` recording data, versions and metrics.

Why this script exists
----------------------
The original notebook (a) fit the TF-IDF on the *full* corpus before the
train/test split — leaking test vocabulary/IDF and inflating accuracy, (b)
trained on text containing location names while the runtime pipeline replaces
locations with ``[LOKASI]``, and (c) never actually saved fitted artifacts.
This script fixes all three:

  1. Split FIRST (stratified), then augment the TRAIN split only.
  2. Apply the *exact* runtime preprocessing — ``EntityExtractor`` location
     placeholder + ``TextProcessor`` stemming — so training matches inference.
  3. Fit every vectorizer on TRAIN only; report metrics on the untouched test
     split; persist fully fitted artifacts.

Usage
-----
    PYTHONPATH=src python scripts/train.py \\
        --input data/raw/intents_semantic.json
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from datetime import date
from pathlib import Path

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

# Allow `PYTHONPATH=src` imports and direct `python scripts/train.py` runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yoga_chatbot.nlu.entity_extractor import EntityExtractor  # noqa: E402
from yoga_chatbot.nlu.intent_classifier import GREETING_INTENTS  # noqa: E402
from yoga_chatbot.preprocessing.text_processor import TextProcessor  # noqa: E402

# augment_pattern lives next to this script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from augment_data import augment_pattern  # noqa: E402

RANDOM_STATE = 42


def _load_patterns(path: Path) -> tuple[list[str], list[str]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    patterns: list[str] = []
    labels: list[str] = []
    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            patterns.append(pattern)
            labels.append(intent["tag"])
    return patterns, labels


def _preprocess(
    raw: str, extractor: EntityExtractor, processor: TextProcessor
) -> str:
    """Apply the exact runtime transform: location placeholder + stemming."""
    neutral = extractor.replace_with_placeholder(raw)
    return processor.preprocess(neutral)


def train(input_path: Path, model_dir: Path, kecamatan_path: Path) -> None:
    print(f"Loading {input_path} ...")
    patterns, labels = _load_patterns(input_path)
    print(f"  {len(patterns)} patterns across {len(set(labels))} classes")

    extractor = EntityExtractor(kecamatan_path)
    processor = TextProcessor()

    # --- 1. Split FIRST, on raw patterns, to prevent augmentation leakage ---
    p_train, p_test, y_train_lbl, y_test_lbl = train_test_split(
        patterns, labels,
        test_size=0.2, random_state=RANDOM_STATE, stratify=labels,
    )
    print(f"  train={len(p_train)}  test={len(p_test)} (pre-augmentation)")

    # --- 2. Augment TRAIN split only ---
    aug_patterns: list[str] = []
    aug_labels: list[str] = []
    for pattern, label in zip(p_train, y_train_lbl):
        for variant in augment_pattern(pattern, label):
            aug_patterns.append(variant)
            aug_labels.append(label)
    print(f"  train after augmentation: {len(aug_patterns)}")

    # --- 3. Runtime-parity preprocessing ---
    X_train_text = [_preprocess(p, extractor, processor) for p in aug_patterns]
    X_test_text = [_preprocess(p, extractor, processor) for p in p_test]

    label_encoder = LabelEncoder()
    label_encoder.fit(aug_labels + y_test_lbl)
    y_train = label_encoder.transform(aug_labels)
    y_test = label_encoder.transform(y_test_lbl)

    # --- 4. Fit vectorizers on TRAIN only ---
    tfidf_main = TfidfVectorizer(
        max_features=2000, ngram_range=(1, 2), min_df=2, max_df=0.9,
        token_pattern=r"\b\w+\b",
    )
    X_train_main = tfidf_main.fit_transform(X_train_text)
    X_test_main = tfidf_main.transform(X_test_text)

    tfidf_greeting = TfidfVectorizer(
        max_features=500, ngram_range=(1, 2), min_df=1, max_df=0.9,
        token_pattern=r"\b\w+\b",
    )
    X_train_greet = tfidf_greeting.fit_transform(X_train_text)

    # --- 5. Train models ---
    print("Training main SVM ...")
    main_svm = SVC(kernel="linear", C=1.0, probability=True,
                   class_weight="balanced", random_state=RANDOM_STATE)
    main_svm.fit(X_train_main, y_train)

    print("Training binary greeting detector ...")
    greeting_codes = set(label_encoder.transform(sorted(GREETING_INTENTS)))
    y_train_bin = np.array([1 if c in greeting_codes else 0 for c in y_train])
    greeting_detector = SVC(kernel="linear", C=1.0, probability=True,
                            class_weight="balanced", random_state=RANDOM_STATE)
    greeting_detector.fit(X_train_greet, y_train_bin)

    # --- 6. Evaluate on the untouched test split ---
    y_pred = main_svm.predict(X_test_main)
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    print("\n" + "=" * 60)
    print(f"Main SVM test accuracy : {acc * 100:.2f}%")
    print(f"Main SVM macro F1       : {macro_f1 * 100:.2f}%")
    print("=" * 60)
    print(classification_report(
        y_test, y_pred, target_names=label_encoder.classes_, zero_division=0))

    # --- 7. Persist fully fitted artifacts ---
    model_dir.mkdir(parents=True, exist_ok=True)
    _dump(tfidf_main, model_dir / "tfidf_vectorizer.pickle")
    _dump(tfidf_greeting, model_dir / "tfidf_greeting.pickle")
    _dump(main_svm, model_dir / "svm_model.pkl")
    _dump(greeting_detector, model_dir / "greeting_detector.pkl")
    _dump(label_encoder, model_dir / "label_encoder.pickle")

    metadata = {
        "trained_on": str(date.today()),
        "input_dataset": str(input_path),
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "classes": list(label_encoder.classes_),
        "n_classes": len(label_encoder.classes_),
        "train_samples_pre_aug": len(p_train),
        "train_samples_post_aug": len(aug_patterns),
        "test_samples": len(p_test),
        "test_accuracy": round(float(acc), 4),
        "test_macro_f1": round(float(macro_f1), 4),
        "random_state": RANDOM_STATE,
    }
    with (model_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"\nArtifacts written to {model_dir}")


def _dump(obj: object, path: Path) -> None:
    with path.open("wb") as f:
        pickle.dump(obj, f)


def _parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=root / "data/raw/intents_semantic.json")
    parser.add_argument("--model-dir", type=Path, default=root / "models")
    parser.add_argument("--kecamatan", type=Path,
                        default=root / "data/knowledge/kecamatan_diy.json")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train(args.input, args.model_dir, args.kecamatan)
