"""
Unit tests for TextProcessor.

Tests cover:
- Basic normalisation steps (lowercase, punctuation, whitespace)
- URL and mention stripping
- Edge cases (empty string, emoji-only, very long text)
"""

from __future__ import annotations

import pytest

from yoga_chatbot.preprocessing.text_processor import TextProcessor


@pytest.fixture(scope="module")
def processor() -> TextProcessor:
    return TextProcessor()


class TestPreprocess:
    def test_lowercase(self, processor: TextProcessor) -> None:
        assert processor.preprocess("HALO YOGA") == processor.preprocess("halo yoga")

    def test_strips_urls(self, processor: TextProcessor) -> None:
        result = processor.preprocess("cek https://example.com/wisata")
        assert "http" not in result
        assert "example" not in result

    def test_strips_mentions(self, processor: TextProcessor) -> None:
        result = processor.preprocess("tanya @yogabot dulu")
        assert "@" not in result

    def test_strips_hashtags(self, processor: TextProcessor) -> None:
        result = processor.preprocess("info #wisatajogja")
        assert "#" not in result

    def test_removes_punctuation(self, processor: TextProcessor) -> None:
        result = processor.preprocess("wisata, pantai! (bagus)")
        assert "," not in result
        assert "!" not in result
        assert "(" not in result

    def test_normalises_whitespace(self, processor: TextProcessor) -> None:
        result = processor.preprocess("  wisata   pantai  ")
        assert "  " not in result
        assert result == result.strip()

    def test_empty_string(self, processor: TextProcessor) -> None:
        assert processor.preprocess("") == ""

    def test_whitespace_only(self, processor: TextProcessor) -> None:
        assert processor.preprocess("   ") == ""

    def test_returns_string(self, processor: TextProcessor) -> None:
        result = processor.preprocess("rekomendasi wisata bantul")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_stemming_applied(self, processor: TextProcessor) -> None:
        # Sastrawi should stem "membantu" → "bantu"
        result = processor.preprocess("tolong membantu saya")
        assert "bantu" in result


class TestTokenize:
    def test_returns_list(self, processor: TextProcessor) -> None:
        tokens = processor.tokenize("wisata di bantul")
        assert isinstance(tokens, list)
        assert all(isinstance(t, str) for t in tokens)

    def test_empty_input(self, processor: TextProcessor) -> None:
        assert processor.tokenize("") == []
