"""
Named-entity extraction for Yogyakarta geographical regions.

Recognises three levels of administrative granularity:
  - kecamatan  (sub-district)  — 78 kecamatan across all 5 kabupaten/kota
  - kabupaten  (regency/city)  — bantul, sleman, gunungkidul, kulonprogo, yogyakarta
  - provinsi   (province)      — DIY keywords

Priority order: kecamatan > kabupaten > provinsi.

The extractor also exposes ``replace_with_placeholder`` which substitutes
the matched region name with the token ``[LOKASI]`` so the intent classifier
sees a location-neutral sentence.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------


class EntityResult(TypedDict):
    type: str | None       # "kecamatan" | "kabupaten" | "provinsi" | None
    value: str | None      # normalised name (lowercase, no leading/trailing space)
    kabupaten: str | None  # parent kabupaten for kecamatan entities


_PROVINCE_KEYWORDS = frozenset({
    "yogyakarta", "jogja", "jogjakarta", "diy",
    "daerah istimewa yogyakarta", "daerah istimewa",
})

_KABUPATEN_ALIASES: dict[str, list[str]] = {
    "bantul":       ["bantul", "kab bantul", "kabupaten bantul"],
    "sleman":       ["sleman", "kab sleman", "kabupaten sleman"],
    "gunungkidul":  ["gunungkidul", "gunung kidul", "kab gunungkidul", "kabupaten gunungkidul"],
    "kulonprogo":   ["kulonprogo", "kulon progo", "kab kulonprogo", "kabupaten kulonprogo"],
    "yogyakarta":   ["kota yogyakarta", "kota jogja", "kotamadya yogyakarta"],
}


class EntityExtractor:
    """Extract geographical entities from raw Indonesian user input.

    Parameters
    ----------
    kecamatan_path:
        Path to ``kecamatan_diy.json`` — a mapping of kabupaten name to list
        of lowercase kecamatan names.
    """

    def __init__(self, kecamatan_path: Path) -> None:
        self._kecamatan_map: dict[str, list[str]] = self._load(kecamatan_path)
        # flat lookup: kecamatan_name → parent_kabupaten
        self._kec_to_kab: dict[str, str] = {
            kec: kab
            for kab, kec_list in self._kecamatan_map.items()
            for kec in kec_list
        }
        # sorted longest-first so multi-word names are matched before substrings
        self._all_kecamatan: list[str] = sorted(
            self._kec_to_kab.keys(), key=len, reverse=True
        )
        logger.debug(
            "EntityExtractor loaded %d kecamatan across %d kabupaten",
            len(self._all_kecamatan),
            len(self._kecamatan_map),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, text: str) -> EntityResult:
        """Return the most specific geographical entity found in *text*.

        When several names of the same level appear (e.g. ``"pakem sleman"``),
        the one mentioned first wins; ties go to the longer name. Ordering by
        position matters because the location the user says first is the one
        they are asking about — ``"pakem sleman"`` means Pakem, not Sleman.

        Returns an :class:`EntityResult` with all fields set to ``None``
        when no entity is detected.
        """
        found = self._find(text)
        if found is None:
            return EntityResult(type=None, value=None, kabupaten=None)
        kind, value, parent, _surface = found
        return EntityResult(type=kind, value=value, kabupaten=parent)

    def replace_with_placeholder(
        self, text: str, placeholder: str = "[LOKASI]"
    ) -> str:
        """Return *text* with the detected location replaced by *placeholder*.

        The replacement uses the surface form that actually occurs in the text
        (``"gunung kidul"``), not the canonical value (``"gunungkidul"``) —
        otherwise aliases silently survive and the classifier still sees a
        location token.
        """
        found = self._find(text)
        if found is None:
            return text
        _kind, _value, _parent, surface = found
        pattern = r"\b" + re.escape(surface) + r"\b"
        return re.sub(pattern, placeholder, text, flags=re.IGNORECASE)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find(self, text: str) -> tuple[str, str, str | None, str] | None:
        """Return ``(kind, canonical, parent, surface)`` for the best match.

        Levels are tried in priority order (kecamatan → kabupaten → provinsi).
        Inside a level the earliest mention wins, so a sub-district named the
        same as its regency can no longer hijack the query.
        """
        normalised = text.lower()
        if not normalised.strip():
            return None

        # Priority 1: kecamatan
        best: tuple[int, int, str, str, str | None] | None = None
        for kec in self._all_kecamatan:
            match = re.search(r"\b" + re.escape(kec) + r"\b", normalised)
            if match is None:
                continue
            candidate = (match.start(), -len(kec), kec, kec, self._kec_to_kab[kec])
            if best is None or candidate[:2] < best[:2]:
                best = candidate
        if best is not None:
            return ("kecamatan", best[2], best[4], text[best[0]:best[0] + len(best[2])])

        # Priority 2: kabupaten / kota
        best = None
        for kab_canonical, aliases in _KABUPATEN_ALIASES.items():
            for alias in aliases:
                match = re.search(r"\b" + re.escape(alias) + r"\b", normalised)
                if match is None:
                    continue
                candidate = (match.start(), -len(alias), kab_canonical, alias, kab_canonical)
                if best is None or candidate[:2] < best[:2]:
                    best = candidate
        if best is not None:
            return ("kabupaten", best[2], best[4], text[best[0]:best[0] + len(best[3])])

        # Priority 3: provinsi
        for keyword in sorted(_PROVINCE_KEYWORDS, key=len, reverse=True):
            match = re.search(r"\b" + re.escape(keyword) + r"\b", normalised)
            if match is not None:
                return ("provinsi", "yogyakarta", None, text[match.start():match.end()])

        return None

    @staticmethod
    def _load(path: Path) -> dict[str, list[str]]:
        if not path.exists():
            raise FileNotFoundError(f"kecamatan data not found: {path}")
        with path.open(encoding="utf-8") as f:
            data: dict[str, list[str]] = json.load(f)
        return data
