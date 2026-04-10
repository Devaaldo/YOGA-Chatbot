"""
Action handlers — one method per intent.

Each handler receives the :class:`NLUResult` and the :class:`KnowledgeBase`
and returns either a plain string (for simple text replies) or a list of
:class:`Place` objects (for recommendation replies rendered with inline
keyboards by the bot layer).

Intent routing
--------------
greeting / pagi / siang / sore / malam / goodbye
    → handle_greeting(intent) -> str

rekomendasi_wisata  (with optional location entity)
    → handle_rekomendasi(result, kb) -> list[Place]

cari_by_type        (extract type keyword from raw text)
    → handle_cari_by_type(result, kb) -> list[Place]

cari_by_rating
    → handle_cari_by_rating(kb) -> list[Place]

info_detail         (fuzzy-search place name)
    → handle_info_detail(result, kb) -> Place | None

info_lokasi         (fuzzy-search + maps link)
    → handle_info_lokasi(result, kb) -> Place | None

fallback / unknown
    → handle_fallback() -> str
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase, Place
    from yoga_chatbot.nlu.pipeline import NLUResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static response pools (small, no JSON dependency for greetings)
# ---------------------------------------------------------------------------

_GREETING_RESPONSES: dict[str, list[str]] = {
    "greeting": [
        "Halo! Saya YOGA, asisten wisata Yogyakarta. Ada yang bisa saya bantu?",
        "Hai! Selamat datang di YOGA Chatbot. Mau cari wisata apa hari ini?",
        "Halo, saya siap membantu kamu menemukan tempat wisata terbaik di Yogyakarta!",
    ],
    "pagi": [
        "Selamat pagi! Semoga harimu menyenangkan. Mau wisata ke mana hari ini?",
        "Pagi! Udara segar pagi ini cocok untuk mulai merencanakan perjalanan wisata.",
    ],
    "siang": [
        "Selamat siang! Ada rencana wisata sore ini?",
        "Siang! Mau cari rekomendasi tempat wisata untuk dikunjungi?",
    ],
    "sore": [
        "Selamat sore! Masih ada waktu untuk menikmati sore di Yogyakarta.",
        "Sore! Ingin tahu rekomendasi wisata sore yang menarik?",
    ],
    "malam": [
        "Selamat malam! Yogyakarta malam hari juga punya banyak tempat menarik.",
        "Malam! Sedang merencanakan wisata malam di Jogja?",
    ],
    "goodbye": [
        "Sampai jumpa! Semoga perjalanan wisatamu menyenangkan.",
        "Dadah! Jangan lupa kunjungi tempat-tempat wisata indah di Yogyakarta ya.",
        "Selamat jalan! Terima kasih sudah menggunakan YOGA Chatbot.",
    ],
}

_FALLBACK_RESPONSES: list[str] = [
    "Maaf, saya kurang memahami maksud kamu. Coba tanyakan seputar wisata Yogyakarta ya.",
    "Hmm, saya tidak yakin dengan pertanyaan itu. Coba ketik /help untuk melihat contoh pertanyaan.",
    "Pertanyaan kamu di luar jangkauan saya. Saya spesialis wisata Yogyakarta.",
]

# Mapping dari keyword user ke type di knowledge base
_TYPE_MAPPING: dict[str, str] = {
    "pantai": "pantai",
    "beach": "pantai",
    "candi": "candi",
    "temple": "candi",
    "gunung": "gunung",
    "bukit": "bukit",
    "hill": "bukit",
    "museum": "museum",
    "budaya": "budaya",
    "culture": "budaya",
    "sejarah": "sejarah",
    "history": "sejarah",
    "alam": "alam",
    "nature": "alam",
    "kuliner": "kuliner",
    "food": "kuliner",
    "waterfall": "air terjun",
    "air terjun": "air terjun",
    "taman": "taman",
    "park": "taman",
    "goa": "goa",
    "cave": "goa",
    "sawah": "sawah",
    "danau": "danau",
    "lake": "danau",
}

# Regex for extracting budget amounts from natural language
_BUDGET_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(rb|ribu|k|jt|juta|m)?", re.IGNORECASE
)


class ActionHandler:
    """Stateless action dispatcher.  All methods are pure functions of their inputs."""

    # ------------------------------------------------------------------
    # Greeting / conversational
    # ------------------------------------------------------------------

    @staticmethod
    def handle_greeting(intent: str) -> str:
        import random
        responses = _GREETING_RESPONSES.get(intent, _GREETING_RESPONSES["greeting"])
        return random.choice(responses)

    @staticmethod
    def handle_fallback() -> str:
        import random
        return random.choice(_FALLBACK_RESPONSES)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    @staticmethod
    def handle_rekomendasi(result: "NLUResult", kb: "KnowledgeBase") -> "list[Place]":
        """Return top-rated places, optionally filtered to a detected location."""
        entity = result.entity
        if entity["type"] in ("kecamatan", "kabupaten") and entity["value"]:
            places = kb.search_by_location(entity["value"])
            if places:
                return places
        return kb.top_rated(limit=5)

    @staticmethod
    def handle_cari_by_type(result: "NLUResult", kb: "KnowledgeBase") -> "list[Place]":
        """Detect a type keyword in the raw text and search by type."""
        raw = result.raw_text.lower()
        for keyword, mapped_type in _TYPE_MAPPING.items():
            if keyword in raw:
                logger.debug("cari_by_type: matched keyword=%r → type=%r", keyword, mapped_type)
                places = kb.search_by_type(mapped_type)
                if places:
                    return places
        # No type keyword detected, fall back to top-rated
        return kb.top_rated(limit=5)

    @staticmethod
    def handle_cari_by_rating(kb: "KnowledgeBase") -> "list[Place]":
        return kb.search_by_rating(min_rating=4.0, limit=5)

    @staticmethod
    def handle_cari_by_harga(result: "NLUResult", kb: "KnowledgeBase") -> "list[Place]":
        """Extract a budget amount from the raw text and search by price."""
        raw = result.raw_text.lower()

        # Handle "gratis" / "free"
        if "gratis" in raw or "free" in raw or "murah" in raw and "0" in raw:
            return kb.search_by_budget(0, limit=5)

        budget = ActionHandler._extract_budget(raw)
        if budget is None:
            logger.debug("cari_by_harga: no budget detected, returning top-rated")
            return kb.top_rated(limit=5)

        logger.debug("cari_by_harga: extracted budget=%d IDR", budget)
        return kb.search_by_budget(budget, limit=5)

    # ------------------------------------------------------------------
    # Place info
    # ------------------------------------------------------------------

    @staticmethod
    def handle_info_detail(result: "NLUResult", kb: "KnowledgeBase") -> "Place | None":
        """Fuzzy-search for a place name in the raw text."""
        places = kb.fuzzy_search(result.raw_text, limit=1)
        return places[0] if places else None

    @staticmethod
    def handle_info_lokasi(result: "NLUResult", kb: "KnowledgeBase") -> "Place | None":
        """Same as info_detail — caller renders with a Google Maps link."""
        return ActionHandler.handle_info_detail(result, kb)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_budget(text: str) -> int | None:
        """Parse a budget amount (IDR) from natural-language text.

        Handles multipliers: rb/ribu/k → ×1 000, jt/juta/m → ×1 000 000.
        Returns ``None`` if no numeric value is found.
        """
        for match in _BUDGET_PATTERN.finditer(text):
            amount_str = match.group(1).replace(",", "").replace(".", "")
            multiplier_str = (match.group(2) or "").lower()
            try:
                amount = int(amount_str)
            except ValueError:
                continue

            if multiplier_str in ("rb", "ribu", "k"):
                amount *= 1_000
            elif multiplier_str in ("jt", "juta", "m"):
                amount *= 1_000_000

            return amount
        return None
