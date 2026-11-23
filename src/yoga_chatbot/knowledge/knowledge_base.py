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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Two POIs closer than this are treated as the same place when their names
# also match. ~0.0015° is roughly 165 m of latitude in Yogyakarta.
_DUPLICATE_RADIUS_DEG = 0.0015


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

    def __init__(self, path: Path, dedupe: bool = True) -> None:
        raw = self._load(path)
        self._places: list[Place] = dedupe_places(raw) if dedupe else raw
        if len(self._places) != len(raw):
            logger.info(
                "KnowledgeBase deduplicated %d -> %d places",
                len(raw),
                len(self._places),
            )
        logger.info("KnowledgeBase loaded %d places from %s", len(self._places), path)

    @property
    def places(self) -> list[Place]:
        """All places, read-only view (duplicates already collapsed)."""
        return self._places

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


# ---------------------------------------------------------------------------
# Duplicate collapsing
# ---------------------------------------------------------------------------


def _name_key(name: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace for name matching."""
    return re.sub(r"[^a-z0-9]+", " ", (name or "").casefold()).strip()


def _completeness(place: Place) -> tuple:
    """Sort key: prefer records that actually carry community data."""
    return (
        place.vote_count > 0,
        place.vote_count,
        place.has_rating,
        place.has_price,
        len(place.description or ""),
    )


def _same_place(a: Place, b: Place) -> bool:
    """Same normalised name already established; check they are co-located.

    Records without coordinates fall back to name-only matching, which is the
    best available signal.
    """
    lat_a, lng_a = a.lokasi.latitude, a.lokasi.longitude
    lat_b, lng_b = b.lokasi.latitude, b.lokasi.longitude
    if None in (lat_a, lng_a, lat_b, lng_b):
        return True
    return (
        abs(lat_a - lat_b) <= _DUPLICATE_RADIUS_DEG
        and abs(lng_a - lng_b) <= _DUPLICATE_RADIUS_DEG
    )


def _merge_into(target: Place, donor: Place) -> None:
    """Fill gaps in *target* from *donor* without overwriting better data."""
    if not target.has_rating and donor.has_rating:
        target.rating = donor.rating
        target.vote_count = donor.vote_count
        target.has_rating = True
    if not target.has_price and donor.has_price:
        target.harga = donor.harga
        target.has_price = True
    if target.lokasi.latitude is None and donor.lokasi.latitude is not None:
        target.lokasi = donor.lokasi
    for attr in ("description", "address", "phone", "website"):
        if not getattr(target, attr) and getattr(donor, attr):
            setattr(target, attr, getattr(donor, attr))
    target.has_description = bool(target.description)
    target.has_address = bool(target.address)
    target.has_contact = bool(target.phone or target.website)


def dedupe_places(places: Iterable[Place]) -> list[Place]:
    """Collapse the same POI ingested twice (Kaggle seed + Geoapify enrichment).

    The knowledge base was built by matching a curated Kaggle list against
    Geoapify results, so 41% of rows are the same destination twice: one with
    ratings/votes, one with only a name and coordinates. Left in, duplicates
    dominate "top rated" lists and inflate the catalogue count.

    Matching is name + proximity, never name alone, so two genuinely different
    places that share a name (different regencies) stay separate. The richest
    record of each cluster survives and absorbs the missing fields of the rest.
    """
    buckets: dict[str, list[Place]] = {}
    for place in places:
        buckets.setdefault(_name_key(place.nama), []).append(place)

    collapsed: list[Place] = []
    for group in buckets.values():
        clusters: list[list[Place]] = []
        for place in sorted(group, key=_completeness, reverse=True):
            for cluster in clusters:
                if _same_place(cluster[0], place):
                    cluster.append(place)
                    break
            else:
                clusters.append([place])

        for cluster in clusters:
            keeper = cluster[0]
            for extra in cluster[1:]:
                _merge_into(keeper, extra)
            collapsed.append(keeper)

    collapsed.sort(key=lambda p: p.id)
    return collapsed
