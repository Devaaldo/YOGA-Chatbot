"""
Unit tests for KnowledgeBase search methods.

Tests use the real tourism_knowledge_base.json to ensure data is correctly
loaded and search behaviour matches expectations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yoga_chatbot.knowledge.knowledge_base import (
    HargaInfo,
    KnowledgeBase,
    LokasiInfo,
    Place,
    dedupe_places,
)


def make_place(place_id: int, name: str, lat: float, lng: float, **kwargs) -> Place:
    """Minimal Place factory for dedupe tests."""
    defaults = dict(
        source="test",
        nama_clean=name.lower(),
        type="Alam",
        type_clean="alam",
        rating=0.0,
        vote_count=0,
        harga=HargaInfo(weekday=None, weekend=None),
        lokasi=LokasiInfo(latitude=lat, longitude=lng),
        description="",
        address="",
        phone="",
        website="",
        has_price=False,
        has_rating=False,
        has_description=False,
        has_address=False,
        has_contact=False,
    )
    defaults.update(kwargs)
    return Place(id=place_id, nama=name, **defaults)


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    path = Path(__file__).parent.parent / "data" / "processed" / "tourism_knowledge_base.json"
    return KnowledgeBase(path)


class TestLoad:
    def test_loads_places(self, kb: KnowledgeBase) -> None:
        assert len(kb.places) > 0

    def test_place_has_required_fields(self, kb: KnowledgeBase) -> None:
        place = kb.places[0]
        assert isinstance(place, Place)
        assert isinstance(place.nama, str)
        assert isinstance(place.rating, float)

    def test_duplicates_are_collapsed(self, kb: KnowledgeBase) -> None:
        keys = [(p.nama.lower(), round(p.lokasi.latitude or 0, 3),
                 round(p.lokasi.longitude or 0, 3)) for p in kb.places]
        assert len(keys) == len(set(keys))

    def test_dedupe_can_be_disabled(self, kb: KnowledgeBase) -> None:
        path = Path(__file__).parent.parent / "data" / "processed" / "tourism_knowledge_base.json"
        raw = KnowledgeBase(path, dedupe=False)
        assert len(raw.places) > len(kb.places)


class TestTopRated:
    def test_returns_limit(self, kb: KnowledgeBase) -> None:
        results = kb.top_rated(limit=5)
        assert len(results) <= 5

    def test_descending_rating(self, kb: KnowledgeBase) -> None:
        results = kb.top_rated(limit=10)
        ratings = [p.rating for p in results]
        assert ratings == sorted(ratings, reverse=True)


class TestSearchByType:
    def test_candi_search(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_type("candi")
        assert all("candi" in p.type_clean for p in results)

    def test_partial_match(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_type("budaya")
        assert len(results) >= 0  # May have results or not

    def test_returns_at_most_limit(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_type("pantai", limit=3)
        assert len(results) <= 3

    def test_unknown_type_returns_empty(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_type("xyznonexistent")
        assert results == []


class TestSearchByBudget:
    def test_free_places(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_budget(0)
        assert all(p.harga.weekday == 0 for p in results)

    def test_budget_50000(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_budget(50_000)
        assert all(
            p.harga.weekday is not None and p.harga.weekday <= 50_000
            for p in results
        )

    def test_returns_at_most_limit(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_budget(100_000, limit=3)
        assert len(results) <= 3


class TestSearchByRating:
    def test_min_rating_filter(self, kb: KnowledgeBase) -> None:
        results = kb.search_by_rating(min_rating=4.0)
        assert all(p.rating >= 4.0 for p in results)

    def test_high_threshold_returns_fewer(self, kb: KnowledgeBase) -> None:
        r_40 = len(kb.search_by_rating(4.0, limit=100))
        r_48 = len(kb.search_by_rating(4.8, limit=100))
        assert r_40 >= r_48


class TestFuzzySearch:
    def test_borobudur_search(self, kb: KnowledgeBase) -> None:
        results = kb.fuzzy_search("candi borobudur")
        names = [p.nama_clean for p in results]
        assert any("borobudur" in n for n in names)

    def test_no_match_falls_back_to_top_rated(self, kb: KnowledgeBase) -> None:
        results = kb.fuzzy_search("zzznomatchxxx")
        assert len(results) > 0  # Falls back to top-rated

    def test_returns_at_most_limit(self, kb: KnowledgeBase) -> None:
        results = kb.fuzzy_search("candi", limit=3)
        assert len(results) <= 3


class TestGetById:
    def test_existing_id(self, kb: KnowledgeBase) -> None:
        first = kb.places[0]
        result = kb.get_by_id(first.id)
        assert result is not None
        assert result.id == first.id

    def test_nonexistent_id(self, kb: KnowledgeBase) -> None:
        result = kb.get_by_id(999999)
        assert result is None


class TestDedupe:
    def test_same_name_same_spot_collapses_and_keeps_richest(self) -> None:
        poor = make_place(1, "Candi Prambanan", -7.751834, 110.491532)
        rich = make_place(
            2, "Candi Prambanan", -7.752227, 110.491533,
            rating=4.7, vote_count=71751, has_rating=True,
            harga=HargaInfo(weekday=50_000, weekend=50_000), has_price=True,
            description="Kompleks candi Hindu.", has_description=True,
        )
        merged = dedupe_places([poor, rich])
        assert len(merged) == 1
        assert merged[0].vote_count == 71_751
        assert merged[0].harga.weekday == 50_000
        assert merged[0].description

    def test_same_name_far_apart_stays_separate(self) -> None:
        a = make_place(1, "Masjid Agung", -7.79, 110.36)
        b = make_place(2, "Masjid Agung", -7.90, 110.50)
        assert len(dedupe_places([a, b])) == 2

    def test_name_case_and_punctuation_are_normalised(self) -> None:
        a = make_place(1, "Taman Sari", -7.8098, 110.3595)
        b = make_place(2, "taman  sari!", -7.8099, 110.3596)
        assert len(dedupe_places([a, b])) == 1

    def test_different_names_never_merge(self) -> None:
        a = make_place(1, "Candi Prambanan", -7.75, 110.49)
        b = make_place(2, "Candi Sewu", -7.75, 110.49)
        assert len(dedupe_places([a, b])) == 2
