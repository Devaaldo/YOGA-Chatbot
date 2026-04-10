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

        Returns an :class:`EntityResult` with all fields set to ``None``
        when no entity is detected.
        """
        normalised = text.lower().strip()

        # Priority 1: kecamatan
        for kec in self._all_kecamatan:
            if re.search(r"\b" + re.escape(kec) + r"\b", normalised):
                return EntityResult(
                    type="kecamatan",
                    value=kec,
                    kabupaten=self._kec_to_kab[kec],
                )

        # Priority 2: kabupaten / kota
        for kab_canonical, aliases in _KABUPATEN_ALIASES.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if re.search(r"\b" + re.escape(alias) + r"\b", normalised):
                    return EntityResult(
                        type="kabupaten",
                        value=kab_canonical,
                        kabupaten=kab_canonical,
                    )

        # Priority 3: provinsi
        for keyword in sorted(_PROVINCE_KEYWORDS, key=len, reverse=True):
            if re.search(r"\b" + re.escape(keyword) + r"\b", normalised):
                return EntityResult(
                    type="provinsi",
                    value="yogyakarta",
                    kabupaten=None,
                )

        return EntityResult(type=None, value=None, kabupaten=None)

    def replace_with_placeholder(
        self, text: str, placeholder: str = "[LOKASI]"
    ) -> str:
        """Return *text* with any detected location name replaced by *placeholder*.

        This lets the intent classifier see a location-neutral sentence, which
        improves generalisation across the 78 kecamatan.
        """
        entity = self.extract(text)
        if entity["value"] is None:
            return text

        normalised = text.lower()
        pattern = r"\b" + re.escape(entity["value"]) + r"\b"
        replaced = re.sub(pattern, placeholder, normalised, flags=re.IGNORECASE)
        return replaced

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load(path: Path) -> dict[str, list[str]]:
        if not path.exists():
            raise FileNotFoundError(f"kecamatan data not found: {path}")
        with path.open(encoding="utf-8") as f:
            data: dict[str, list[str]] = json.load(f)
        return data
