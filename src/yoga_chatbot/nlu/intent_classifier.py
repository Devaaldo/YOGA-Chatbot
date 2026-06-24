"""
Three-stage hybrid intent classifier for YOGA Chatbot.

Pipeline
--------
Stage 0  Rule-based gate
         If word_count > WORD_COUNT_THRESHOLD, skip straight to Stage 2.
         Short texts are more likely to be greetings; long texts are almost
         never greetings and sending them through the binary detector wastes
         time and introduces confusion.

Stage 1  Binary GreetingDetector (SVM)
         Classifies text as greeting vs. non-greeting.
         If P(greeting) >= GREETING_CONFIDENCE_THRESHOLD → Stage 1b.

Stage 1b Greeting sub-classifier
         Uses the main SVM's decision function but restricts the label space
         to the six greeting intents so that the most likely greeting variant
         is returned (e.g. "pagi" vs "siang").

Stage 2  Main SVM classifier
         88-class SVM covering all location and thematic intents.

Source: adapted from YOGA-Chatbot-alpha/src/telegram_bot_v3.py
        predict_intent_hybrid() — refactored into a loadable class.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# The six greeting intent labels the main SVM was trained on
GREETING_INTENTS: frozenset[str] = frozenset(
    ["goodbye", "greeting", "pagi", "siang", "sore", "malam"]
)


class HybridIntentClassifier:
    """Load and run the three-stage SVM hybrid intent pipeline.

    Parameters
    ----------
    model_dir:
        Directory containing all ``.pkl`` / ``.pickle`` model artifacts.
    greeting_confidence_threshold:
        Minimum ``predict_proba`` score for the binary greeting detector to
        classify a text as a greeting (default 0.7).
    word_count_threshold:
        Texts with more tokens than this skip the greeting detector entirely
        (default 3).
    intent_confidence_threshold:
        Minimum ``predict_proba`` score for the main 88-class SVM to commit to
        a label. Below this the classifier returns ``"fallback"`` instead of
        forcing one of the 88 classes onto out-of-domain or ambiguous input
        (default 0.15). Kept low because probabilities are spread thin across
        88 classes; tune against real user input.
    """

    def __init__(
        self,
        model_dir: Path,
        greeting_confidence_threshold: float = 0.7,
        word_count_threshold: int = 3,
        intent_confidence_threshold: float = 0.15,
    ) -> None:
        self._greeting_confidence_threshold = greeting_confidence_threshold
        self._word_count_threshold = word_count_threshold
        self._intent_confidence_threshold = intent_confidence_threshold
        self._load_models(model_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, preprocessed_text: str) -> tuple[str, float]:
        """Predict intent label and confidence for *preprocessed_text*.

        Parameters
        ----------
        preprocessed_text:
            Text that has already been run through :class:`TextProcessor`.

        Returns
        -------
        tuple[str, float]
            ``(intent_label, confidence)``
        """
        if not preprocessed_text.strip():
            return "fallback", 0.0

        word_count = len(preprocessed_text.split())

        # Stage 0: long-text bypass
        if word_count > self._word_count_threshold:
            return self._predict_main(preprocessed_text)

        # Stage 1: binary greeting detection
        greeting_vec = self._tfidf_greeting.transform([preprocessed_text])
        greeting_proba = self._greeting_detector.predict_proba(greeting_vec)[0]
        greeting_confidence = float(np.max(greeting_proba))
        is_greeting = (
            greeting_confidence >= self._greeting_confidence_threshold
            and self._greeting_detector.classes_[np.argmax(greeting_proba)] == "greeting"
        )

        if is_greeting:
            return self._predict_greeting_subclass(preprocessed_text, greeting_confidence)

        # Stage 2: main classifier
        return self._predict_main(preprocessed_text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _predict_main(self, text: str) -> tuple[str, float]:
        vec = self._tfidf_vectorizer.transform([text])
        proba = self._svm_model.predict_proba(vec)[0]
        idx = int(np.argmax(proba))
        confidence = float(proba[idx])
        if confidence < self._intent_confidence_threshold:
            return "fallback", confidence
        label = self._label_encoder.inverse_transform([idx])[0]
        return str(label), confidence

    def _predict_greeting_subclass(
        self, text: str, base_confidence: float
    ) -> tuple[str, float]:
        """Pick the best greeting sub-label via decision function scoring."""
        vec = self._tfidf_vectorizer.transform([text])
        decision_scores: np.ndarray = self._svm_model.decision_function(vec)[0]
        all_classes: list[str] = list(
            self._label_encoder.inverse_transform(range(len(decision_scores)))
        )

        best_label: str = "greeting"
        best_score: float = float("-inf")
        for label, score in zip(all_classes, decision_scores):
            if label in GREETING_INTENTS and float(score) > best_score:
                best_label = label
                best_score = float(score)

        return best_label, base_confidence

    def _load_models(self, model_dir: Path) -> None:
        """Load all required model artifacts from *model_dir*."""
        logger.info("Loading intent classifier models from %s", model_dir)

        self._greeting_detector: Any = self._load_pickle(
            model_dir / "greeting_detector.pkl"
        )
        self._svm_model: Any = self._load_pickle(model_dir / "svm_model.pkl")
        self._tfidf_greeting: Any = self._load_pickle(
            model_dir / "tfidf_greeting.pickle"
        )
        self._tfidf_vectorizer: Any = self._load_pickle(
            model_dir / "tfidf_vectorizer.pickle"
        )
        self._label_encoder: Any = self._load_pickle(
            model_dir / "label_encoder.pickle"
        )

        logger.info(
            "Intent classifier ready — %d classes",
            len(self._label_encoder.classes_),
        )

    @staticmethod
    def _load_pickle(path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        with path.open("rb") as f:
            return pickle.load(f)
