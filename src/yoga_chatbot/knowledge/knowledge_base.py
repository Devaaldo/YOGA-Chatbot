"""
Tourism knowledge base for Yogyakarta.

Loads ``tourism_knowledge_base.json`` (enriched with Geoapify + Kaggle data)
into typed ``Place`` dataclasses and exposes search methods used by action
handlers.

Schema reference (per record in the JSON)
------------------------------------------
{
    "id":            int,
    "source":        str,
    "nama":          str,
    "nama_clean":    str,
    "type":          str,
    "type_clean":    str,
    "rating":        float,
    "vote_count":    int,
    "harga": {
        "weekday":   int | null,
        "weekend":   int | null
    },
    "lokasi": {
        "latitude":  float | null,
        "longitude": float | null
    },
    "description":   str,
    "address":       str,
    "phone":         str,
    "website":       str,
    "flags": {
        "has_price":       bool,
        "has_rating":      bool,
        "has_description": bool,
        "has_address":     bool,
        "has_contact":     bool
    }
}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class HargaInfo:
    weekday: int | None
    weekend: int | None


@dataclass
class LokasiInfo:
    latitude: float | None
    longitude: float | None

    def maps_url(self) -> str | None:
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None


@dataclass
class Place:
    id: int
    source: str
    nama: str
    nama_clean: str
    type: str
    type_clean: str
    rating: float
    vote_count: int
    harga: HargaInfo
    lokasi: LokasiInfo
    description: str
    address: str
    phone: str
    website: str
    has_price: bool
    has_rating: bool
    has_description: bool
    has_address: bool
    has_contact: bool


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------


class KnowledgeBase:
    """In-memory tourism knowledge base backed by a JSON file.

    Parameters
    ----------
    path:
        Path to ``tourism_knowledge_base.json``.
    """

    def __init__(self, path: Path) -> None:
        self._places: list[Place] = self._load(path)
        logger.info("KnowledgeBase loaded %d places from %s", len(self._places), path)

    # ------------------------------------------------------------------
    # Search API
    # ------------------------------------------------------------------

    def search_by_type(self, place_type: str, limit: int = 5) -> list[Place]:
        """Return the top-rated places matching *place_type* (partial, case-insensitive)."""
        query = place_type.lower()
        matches = [
            p for p in self._places if query in p.type_clean
        ]
        return self._top_rated(matches, limit)

    def search_by_budget(self, max_budget: int, limit: int = 5) -> list[Place]:
        """Return places whose weekday price is <= *max_budget*.

        Places without price data are excluded unless *max_budget* == 0,
        in which case only free (0 IDR) places are returned.
        """
        if max_budget == 0:
            matches = [
                p for p in self._places
                if p.has_price and p.harga.weekday == 0
            ]
        else:
            matches = [
                p for p in self._places
                if p.has_price
                and p.harga.weekday is not None
                and p.harga.weekday <= max_budget
            ]
        return self._top_rated(matches, limit)

    def search_by_rating(self, min_rating: float = 4.0, limit: int = 5) -> list[Place]:
        """Return places with rating >= *min_rating*, sorted descending."""
        matches = [p for p in self._places if p.has_rating and p.rating >= min_rating]
        return self._top_rated(matches, limit)

    def search_by_location(self, location_name: str, limit: int = 5) -> list[Place]:
        """Return places located in *location_name*, sorted by rating.

        The query is matched against each place's ``address`` (which carries
        the administrative region, e.g. "Bantul Regency"), as well as its
        ``nama_clean`` and ``description``. Matching is whitespace-insensitive
        so canonical entity values such as ``"gunungkidul"`` match address
        spellings like ``"Gunung Kidul"``.

        Returns an empty list when no place matches; callers decide whether to
        fall back to a generic recommendation.
        """
        query = self._normalise(location_name)
        if not query:
            return []
        matches = [
            p for p in self._places
            if query in self._normalise(p.address)
            or query in self._normalise(p.nama_clean)
            or query in self._normalise(p.description)
        ]
        return self._top_rated(matches, limit)

    def fuzzy_search(self, query: str, limit: int = 5) -> list[Place]:
        """Return places ranked by word-overlap score against *query*.

        Each token in *query* that appears in the place's ``nama_clean``
        increments the score.  Falls back to top-rated overall when the
        best score is zero.
        """
        tokens = set(query.lower().split())
        scored: list[tuple[int, Place]] = []
        for place in self._places:
            name_tokens = set(place.nama_clean.split())
            score = len(tokens & name_tokens)
            if score > 0:
                scored.append((score, place))

        if not scored:
            return self._top_rated(self._places, limit)

        scored.sort(key=lambda x: (-x[0], -x[1].rating))
        return [p for _, p in scored[:limit]]

    def get_by_id(self, place_id: int) -> Place | None:
        """Return a single place by its integer *place_id*, or ``None``."""
        for place in self._places:
            if place.id == place_id:
                return place
        return None

    def top_rated(self, limit: int = 5) -> list[Place]:
        """Return the globally top-rated places."""
        return self._top_rated(self._places, limit)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _top_rated(places: list[Place], limit: int) -> list[Place]:
        return sorted(places, key=lambda p: (-p.rating, -p.vote_count))[:limit]

    @staticmethod
    def _normalise(text: str) -> str:
        """Lowercase and strip whitespace so 'Gunung Kidul' == 'gunungkidul'."""
        return "".join((text or "").lower().split())

    @staticmethod
    def _load(path: Path) -> list[Place]:
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {path}")

        with path.open(encoding="utf-8") as f:
            records: list[dict[str, Any]] = json.load(f)

        places: list[Place] = []
        for rec in records:
            harga_raw = rec.get("harga") or {}
            lokasi_raw = rec.get("lokasi") or {}
            flags_raw = rec.get("flags") or {}

            place = Place(
                id=rec.get("id", 0),
                source=rec.get("source", ""),
                nama=rec.get("nama", ""),
                nama_clean=rec.get("nama_clean", ""),
                type=rec.get("type", ""),
                type_clean=rec.get("type_clean", ""),
                rating=float(rec.get("rating") or 0.0),
                vote_count=int(rec.get("vote_count") or 0),
                harga=HargaInfo(
                    weekday=harga_raw.get("weekday"),
                    weekend=harga_raw.get("weekend"),
                ),
                lokasi=LokasiInfo(
                    latitude=lokasi_raw.get("latitude"),
                    longitude=lokasi_raw.get("longitude"),
                ),
                description=rec.get("description", ""),
                address=rec.get("address", ""),
                phone=rec.get("phone", ""),
                website=rec.get("website", ""),
                has_price=bool(flags_raw.get("has_price", False)),
                has_rating=bool(flags_raw.get("has_rating", False)),
                has_description=bool(flags_raw.get("has_description", False)),
                has_address=bool(flags_raw.get("has_address", False)),
                has_contact=bool(flags_raw.get("has_contact", False)),
            )
            places.append(place)

        return places
