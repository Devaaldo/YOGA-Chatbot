"""
NLU Pipeline — orchestrates preprocessing, entity extraction, and intent classification.

Usage
-----
    pipeline = NLUPipeline.from_settings(settings)
    result   = pipeline.understand("rekomendasi wisata di bantul dong")
    print(result.intent)   # e.g. "rekomendasi_wisata"
    print(result.entity)   # e.g. {"type": "kabupaten", "value": "bantul", ...}
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from yoga_chatbot.nlu.entity_extractor import EntityExtractor, EntityResult
from yoga_chatbot.nlu.intent_classifier import HybridIntentClassifier
from yoga_chatbot.preprocessing.text_processor import TextProcessor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NLUResult:
    """Immutable result returned by :meth:`NLUPipeline.understand`."""

    intent: str
    confidence: float
    entity: EntityResult
    raw_text: str
    preprocessed_text: str

    @property
    def has_location(self) -> bool:
        return self.entity["type"] is not None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class NLUPipeline:
    """End-to-end NLU pipeline.

    Execution order
    ---------------
    1. :class:`TextProcessor` — clean and stem the raw text.
    2. :class:`EntityExtractor` — detect kecamatan / kabupaten / provinsi.
    3. :class:`HybridIntentClassifier` — classify intent on location-neutral text.

    Parameters
    ----------
    text_processor:
        Shared :class:`TextProcessor` instance.
    entity_extractor:
        Loaded :class:`EntityExtractor` instance.
    intent_classifier:
        Loaded :class:`HybridIntentClassifier` instance.
    """

    def __init__(
        self,
        text_processor: TextProcessor,
        entity_extractor: EntityExtractor,
        intent_classifier: HybridIntentClassifier,
    ) -> None:
        self._processor = text_processor
        self._extractor = entity_extractor
        self._classifier = intent_classifier

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_settings(cls, settings: object) -> "NLUPipeline":
        """Convenience factory that reads paths from a ``Settings`` object."""
        processor = TextProcessor()
        extractor = EntityExtractor(kecamatan_path=settings.kecamatan_path)  # type: ignore[attr-defined]
        classifier = HybridIntentClassifier(
            model_dir=settings.model_dir,  # type: ignore[attr-defined]
            greeting_confidence_threshold=settings.greeting_confidence_threshold,  # type: ignore[attr-defined]
            word_count_threshold=settings.word_count_threshold,  # type: ignore[attr-defined]
            intent_confidence_threshold=settings.intent_confidence_threshold,  # type: ignore[attr-defined]
        )
        return cls(processor, extractor, classifier)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def understand(self, raw_text: str) -> NLUResult:
        """Analyse *raw_text* and return a structured :class:`NLUResult`.

        The entity extractor runs on the *original* lowercased text so that
        proper-noun matching is reliable. The intent classifier runs on a
        location-neutral version (``[LOKASI]`` placeholder) so that a single
        "rekomendasi_wisata" intent covers all 78 kecamatan instead of needing
        one intent class per location.
        """
        if not raw_text or not raw_text.strip():
            return NLUResult(
                intent="fallback",
                confidence=0.0,
                entity=EntityResult(type=None, value=None, kabupaten=None),
                raw_text=raw_text,
                preprocessed_text="",
            )

        # Step 1: entity extraction (on raw text)
        entity = self._extractor.extract(raw_text)

        # Step 2: replace location with placeholder, then preprocess
        neutral_text = self._extractor.replace_with_placeholder(raw_text)
        preprocessed = self._processor.preprocess(neutral_text)

        # Step 3: intent classification
        intent, confidence = self._classifier.predict(preprocessed)

        logger.debug(
            "NLU | raw=%r entity=%s intent=%s (%.2f)",
            raw_text,
            entity,
            intent,
            confidence,
        )

        return NLUResult(
            intent=intent,
            confidence=confidence,
            entity=entity,
            raw_text=raw_text,
            preprocessed_text=preprocessed,
        )
