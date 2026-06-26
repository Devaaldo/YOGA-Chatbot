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
import random
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


def _augment(patterns: list[str], labels: list[str]) -> tuple[list[str], list[str]]:
    """Expand a (patterns, labels) set with intent-aware augmentation."""
    out_p: list[str] = []
    out_y: list[str] = []
    for pattern, label in zip(patterns, labels):
        for variant in augment_pattern(pattern, label):
            out_p.append(variant)
            out_y.append(label)
    return out_p, out_y


def cross_validate(
    patterns: list[str],
    labels: list[str],
    extractor: EntityExtractor,
    processor: TextProcessor,
    n_splits: int = 5,
) -> dict[str, float]:
    """Stratified k-fold CV with augmentation applied INSIDE each fold.

    A single 80/20 split leaves only 3-5 test samples in the minority intents,
    so its per-class metrics are noise. CV over the raw patterns — augmenting
    only the training fold each iteration — gives a trustworthy mean ± std and
    keeps augmented variants out of the validation fold.
    """
    from sklearn.model_selection import StratifiedKFold

    patterns_arr = np.array(patterns, dtype=object)
    labels_arr = np.array(labels)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    accs: list[float] = []
    f1s: list[float] = []
    for fold, (tr, te) in enumerate(skf.split(patterns_arr, labels_arr), 1):
        ap, ay = _augment(list(patterns_arr[tr]), list(labels_arr[tr]))
        X_tr_text = [_preprocess(p, extractor, processor) for p in ap]
        X_te_text = [_preprocess(p, extractor, processor) for p in patterns_arr[te]]

        vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=2,
                              max_df=0.9, token_pattern=r"\b\w+\b")
        X_tr = vec.fit_transform(X_tr_text)
        X_te = vec.transform(X_te_text)

        svm = SVC(kernel="linear", C=1.0, class_weight="balanced",
                  random_state=RANDOM_STATE)
        svm.fit(X_tr, ay)
        pred = svm.predict(X_te)
        y_te = list(labels_arr[te])
        accs.append(accuracy_score(y_te, pred))
        f1s.append(f1_score(y_te, pred, average="macro", zero_division=0))
        print(f"  fold {fold}: acc={accs[-1]*100:.2f}%  macroF1={f1s[-1]*100:.2f}%")

    print(f"\n  {n_splits}-fold CV accuracy : {np.mean(accs)*100:.2f}% "
          f"+/- {np.std(accs)*100:.2f}%")
    print(f"  {n_splits}-fold CV macro F1 : {np.mean(f1s)*100:.2f}% "
          f"+/- {np.std(f1s)*100:.2f}%")
    return {
        "cv_accuracy_mean": round(float(np.mean(accs)), 4),
        "cv_accuracy_std": round(float(np.std(accs)), 4),
        "cv_macro_f1_mean": round(float(np.mean(f1s)), 4),
        "cv_macro_f1_std": round(float(np.std(f1s)), 4),
    }


def train(input_path: Path, model_dir: Path, kecamatan_path: Path) -> None:
    # Seed every RNG the pipeline touches. augment_pattern uses the stdlib
    # `random` module, so without this the augmented set — and therefore the
    # trained model — would differ on every run.
    random.seed(RANDOM_STATE)
    np.random.seed(RANDOM_STATE)

    print(f"Loading {input_path} ...")
    patterns, labels = _load_patterns(input_path)
    print(f"  {len(patterns)} patterns across {len(set(labels))} classes")

    extractor = EntityExtractor(kecamatan_path)
    processor = TextProcessor()

    # --- 0. Cross-validation for a trustworthy, split-independent estimate ---
    print("\nStratified 5-fold cross-validation (augmentation inside each fold):")
    cv_metrics = cross_validate(patterns, labels, extractor, processor, n_splits=5)

    # --- 1. Split FIRST, on raw patterns, to prevent augmentation leakage ---
    print("\nFinal model — single 80/20 hold-out:")
    p_train, p_test, y_train_lbl, y_test_lbl = train_test_split(
        patterns, labels,
        test_size=0.2, random_state=RANDOM_STATE, stratify=labels,
    )
    print(f"  train={len(p_train)}  test={len(p_test)} (pre-augmentation)")

    # --- 2. Augment TRAIN split only ---
    aug_patterns, aug_labels = _augment(p_train, y_train_lbl)
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

    root = Path(__file__).resolve().parent.parent
    try:
        dataset_label = str(input_path.resolve().relative_to(root))
    except ValueError:
        dataset_label = input_path.name
    metadata = {
        "trained_on": str(date.today()),
        "input_dataset": dataset_label,
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "classes": list(label_encoder.classes_),
        "n_classes": len(label_encoder.classes_),
        "train_samples_pre_aug": len(p_train),
        "train_samples_post_aug": len(aug_patterns),
        "test_samples": len(p_test),
        "test_accuracy": round(float(acc), 4),
        "test_macro_f1": round(float(macro_f1), 4),
        **cv_metrics,
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
