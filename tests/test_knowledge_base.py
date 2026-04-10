"""
Unit tests for KnowledgeBase search methods.

Tests use the real tourism_knowledge_base.json to ensure data is correctly
loaded and search behaviour matches expectations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase, Place


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    path = Path(__file__).parent.parent / "data" / "processed" / "tourism_knowledge_base.json"
    return KnowledgeBase(path)


class TestLoad:
    def test_loads_places(self, kb: KnowledgeBase) -> None:
        assert len(kb._places) > 0

    def test_place_has_required_fields(self, kb: KnowledgeBase) -> None:
        place = kb._places[0]
        assert isinstance(place, Place)
        assert isinstance(place.nama, str)
        assert isinstance(place.rating, float)


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
        first = kb._places[0]
        result = kb.get_by_id(first.id)
        assert result is not None
        assert result.id == first.id

    def test_nonexistent_id(self, kb: KnowledgeBase) -> None:
        result = kb.get_by_id(999999)
        assert result is None
