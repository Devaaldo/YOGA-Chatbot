"""
Black-box end-to-end pipeline tests.

Tests the full NLU pipeline (TextProcessor → EntityExtractor →
HybridIntentClassifier) from raw user input to intent label, mirroring
real-world chatbot interactions.

Test categories (adapted from YOGA-Chatbot-alpha/tests/test_blackbox.py):
  - Greeting intents
  - Location-based intents
  - Category/filter intents
  - Fallback / edge cases
"""

from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import Settings
from yoga_chatbot.nlu.pipeline import NLUPipeline

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pipeline() -> NLUPipeline:
    """Load the full NLU pipeline using real models."""
    settings = Settings()
    return NLUPipeline.from_settings(settings)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def assert_intent(pipeline: NLUPipeline, text: str, expected: str | set[str]) -> None:
    """Assert that NLU classifies *text* as *expected* intent (or one of a set)."""
    result = pipeline.understand(text)
    if isinstance(expected, str):
        assert result.intent == expected, (
            f"Input: {text!r}\n"
            f"Expected: {expected}\n"
            f"Got: {result.intent} (confidence={result.confidence:.2f})"
        )
    else:
        assert result.intent in expected, (
            f"Input: {text!r}\n"
            f"Expected one of: {expected}\n"
            f"Got: {result.intent} (confidence={result.confidence:.2f})"
        )


# ---------------------------------------------------------------------------
# Greeting tests
# ---------------------------------------------------------------------------


class TestGreetings:
    def test_halo(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "halo", "greeting")

    def test_hai(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "hai", "greeting")

    def test_selamat_pagi(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "selamat pagi", "pagi")

    def test_selamat_siang(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "selamat siang", "siang")

    def test_selamat_sore(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "selamat sore", "sore")

    def test_selamat_malam(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "selamat malam", "malam")

    def test_goodbye(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "sampai jumpa", "goodbye")

    def test_goodbye_dadah(self, pipeline: NLUPipeline) -> None:
        assert_intent(pipeline, "dadah", "goodbye")


# ---------------------------------------------------------------------------
# Location / recommendation tests
# ---------------------------------------------------------------------------


class TestLocationRecommendations:
    def test_bantul_location_entity(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("wisata di bantul")
        assert result.entity["type"] in ("kecamatan", "kabupaten")
        assert result.entity["kabupaten"] == "bantul"

    def test_kasihan_kecamatan_entity(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("rekomendasi tempat wisata di kasihan")
        assert result.entity["type"] == "kecamatan"
        assert result.entity["value"] == "kasihan"

    def test_sleman_entity(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("tempat wisata sleman yang bagus")
        assert result.entity["kabupaten"] == "sleman"

    def test_gunungkidul_entity(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("pantai bagus di gunung kidul")
        assert result.entity["type"] == "kabupaten"

    def test_jogja_province(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("wisata terbaik di jogja")
        assert result.entity["type"] == "provinsi"


# ---------------------------------------------------------------------------
# Filter intents
# ---------------------------------------------------------------------------


class TestFilterIntents:
    def test_cari_by_rating_long_text(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("tempat wisata dengan rating paling tinggi")
        # Not expected to be a greeting — should pass to main classifier
        assert result.intent != "greeting"

    def test_general_rekomendasi(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("rekomendasikan tempat wisata")
        assert result.intent not in ("greeting", "pagi", "siang", "sore", "malam")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string_fallback(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("")
        assert result.intent == "fallback"
        assert result.confidence == 0.0

    def test_whitespace_only_fallback(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("   ")
        assert result.intent == "fallback"

    def test_long_text_bypasses_greeting_detector(self, pipeline: NLUPipeline) -> None:
        # More than 3 words — should skip binary greeting detector
        result = pipeline.understand("saya ingin mencari tempat wisata yang indah")
        assert result.intent not in ("greeting", "pagi", "siang", "sore", "malam")

    def test_returns_nlu_result_fields(self, pipeline: NLUPipeline) -> None:
        result = pipeline.understand("halo")
        assert hasattr(result, "intent")
        assert hasattr(result, "confidence")
        assert hasattr(result, "entity")
        assert hasattr(result, "raw_text")
        assert hasattr(result, "preprocessed_text")
        assert 0.0 <= result.confidence <= 1.0
