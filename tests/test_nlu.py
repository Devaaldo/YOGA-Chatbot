"""
Unit tests for EntityExtractor and NLU pipeline integration.

Tests follow equivalence partitioning:
  - kecamatan entities
  - kabupaten entities
  - provinsi entities
  - no entity (None)
  - placeholder replacement
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yoga_chatbot.nlu.entity_extractor import EntityExtractor

# ---------------------------------------------------------------------------
# Fixture: EntityExtractor backed by real kecamatan_diy.json
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def extractor() -> EntityExtractor:
    kec_path = Path(__file__).parent.parent / "data" / "knowledge" / "kecamatan_diy.json"
    return EntityExtractor(kecamatan_path=kec_path)


# ---------------------------------------------------------------------------
# EntityExtractor tests
# ---------------------------------------------------------------------------


class TestKecamatanDetection:
    def test_bantul_kecamatan(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("wisata di kasihan bantul")
        assert result["type"] == "kecamatan"
        assert result["value"] == "kasihan"
        assert result["kabupaten"] == "bantul"

    def test_sleman_kecamatan(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("cari tempat wisata di pakem sleman")
        assert result["type"] == "kecamatan"
        assert result["value"] == "pakem"

    def test_gunungkidul_kecamatan(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("pantai di tepus gunungkidul")
        assert result["type"] == "kecamatan"
        assert result["value"] == "tepus"

    def test_case_insensitive(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("Wisata di PRAMBANAN")
        assert result["type"] == "kecamatan"
        assert result["value"] == "prambanan"


class TestKabupatenDetection:
    def test_bantul_kabupaten(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("rekomendasi wisata di bantul")
        # Should detect kabupaten since no kecamatan name is present
        assert result["type"] in ("kecamatan", "kabupaten")
        assert result["kabupaten"] == "bantul"

    def test_sleman_kabupaten(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("wisata alam di kabupaten sleman")
        assert result["type"] in ("kecamatan", "kabupaten")

    def test_gunungkidul_alias(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("pantai gunung kidul")
        assert result["type"] == "kabupaten"
        assert result["value"] == "gunungkidul"

    def test_kulonprogo_alias(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("kulon progo itu dimana")
        assert result["type"] == "kabupaten"
        assert result["value"] == "kulonprogo"


class TestProvincialDetection:
    def test_jogja_keyword(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("wisata di jogja apa aja")
        assert result["type"] == "provinsi"

    def test_diy_keyword(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("rekomendasi wisata DIY")
        assert result["type"] == "provinsi"


class TestNoEntity:
    def test_no_entity(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("halo selamat pagi")
        assert result["type"] is None
        assert result["value"] is None

    def test_empty_string(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("")
        assert result["type"] is None

    def test_general_question(self, extractor: EntityExtractor) -> None:
        result = extractor.extract("wisata pantai yang bagus")
        assert result["type"] is None


class TestPlaceholderReplacement:
    def test_replaces_kecamatan(self, extractor: EntityExtractor) -> None:
        text = "wisata di kasihan bantul"
        result = extractor.replace_with_placeholder(text)
        assert "[LOKASI]" in result
        assert "kasihan" not in result

    def test_no_replacement_when_no_entity(self, extractor: EntityExtractor) -> None:
        text = "rekomendasi wisata pantai"
        result = extractor.replace_with_placeholder(text)
        assert result == text.lower() or result == text
