"""
Regression tests for the API layer.

These cover the bugs found in the audit: a number in prose being read as a
budget, a regency filter silently falling back to the whole island, and the
duplicate POIs that used to inflate every "top rated" list.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from api import server  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(server.app)


def chat(client: TestClient, message: str, lang: str = "id") -> dict:
    response = client.post("/api/chat", json={"message": message, "lang": lang})
    assert response.status_code == 200, response.text
    return response.json()


class TestCatalogue:
    def test_health_reports_deduplicated_total(self, client: TestClient) -> None:
        body = client.get("/api/health").json()
        assert body["status"] == "ok"
        assert body["places"] == len(server.ALL_PLACES)
        assert 2_000 < body["places"] < 3_399, body["places"]

    def test_meta_totals_match_place_count(self, client: TestClient) -> None:
        meta = client.get("/api/meta").json()
        assert sum(c["count"] for c in meta["categories"]) == meta["total"]
        assert sum(r["count"] for r in meta["regencies"]) == meta["total"]
        assert meta["total"] == len(server.ALL_PLACES)

    def test_places_endpoint_returns_full_catalogue(self, client: TestClient) -> None:
        body = client.get("/api/places", params={"limit": 4000}).json()
        assert body["total"] == len(server.ALL_PLACES)
        assert len(body["items"]) == body["total"]

    def test_no_place_appears_twice_at_the_same_spot(self) -> None:
        seen = set()
        for place in server.ALL_PLACES:
            key = (place["name"].lower(), place["lat"], place["lng"])
            assert key not in seen, f"duplicate place: {place['name']}"
            seen.add(key)


class TestBudgetParsing:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("tiket 30rb", 30_000),
            ("budget 1.500.000", 1_500_000),
            ("di bawah 10 ribu", 10_000),
            ("maksimal 50000", 50_000),
            ("harga 2,5 juta", 2_500_000),
        ],
    )
    def test_parses_money(self, text: str, expected: int) -> None:
        assert server._extract_budget(text) == expected

    @pytest.mark.parametrize(
        "text",
        ["rating 4.5", "buatkan itinerary 2 hari", "pantai di gunungkidul", "halo"],
    )
    def test_ignores_numbers_that_are_not_money(self, text: str) -> None:
        assert server._extract_budget(text) is None

    def test_rating_query_still_returns_places(self, client: TestClient) -> None:
        body = chat(client, "wisata rating 4.5")
        assert body["intent"] == "cari_by_rating"
        assert body["places"], "a rating query must not be turned into a Rp45 budget"


class TestSearchHonesty:
    def test_impossible_combination_says_so(self, client: TestClient) -> None:
        body = chat(client, "pantai di sleman")
        assert body["places"] == []
        assert "Sleman" in body["reply"]
        assert "pantai" in body["reply"].lower()

    def test_kecamatan_beats_its_own_regency(self, client: TestClient) -> None:
        body = chat(client, "wisata di pakem sleman")
        assert body["entity"]["value"] == "pakem"
        assert "Pakem" in body["reply"]

    def test_budget_filter_is_respected(self, client: TestClient) -> None:
        body = chat(client, "tempat wisata tiket murah 10rb")
        assert body["places"]
        assert all(
            p["priceWeekday"] is not None and p["priceWeekday"] <= 10_000
            for p in body["places"]
        )

    def test_english_reply(self, client: TestClient) -> None:
        body = chat(client, "beaches in gunungkidul", lang="en")
        assert body["places"]
        assert "Top beaches" in body["reply"]


class TestValidation:
    def test_empty_message_is_rejected(self, client: TestClient) -> None:
        assert client.post("/api/chat", json={"message": ""}).status_code == 422

    def test_unknown_language_is_rejected(self, client: TestClient) -> None:
        assert (
            client.post("/api/chat", json={"message": "halo", "lang": "fr"}).status_code
            == 422
        )

    def test_unknown_place_returns_404(self, client: TestClient) -> None:
        assert client.get("/api/places/9999999").status_code == 404
