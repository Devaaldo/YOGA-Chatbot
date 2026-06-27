"""
HTTP API for the Jelajah Jogja web frontend.

Wraps the existing YOGA NLU pipeline + knowledge base (the same code the
Telegram bot uses) behind a small FastAPI service so the React frontend can:

  GET  /api/health            liveness probe
  GET  /api/places            list places (filter/sort) for the Explore page
  GET  /api/places/{id}       single place
  GET  /api/meta              categories + regencies (counts)
  POST /api/chat              run the real NLU model -> reply + place cards

Run:
    PYTHONPATH=src python -m uvicorn api.server:app --reload --port 8000
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make `yoga_chatbot` (under src/) and `config` importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from yoga_chatbot.actions.handlers import ActionHandler  # noqa: E402
from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase, Place  # noqa: E402
from yoga_chatbot.nlu.entity_extractor import EntityExtractor  # noqa: E402
from yoga_chatbot.nlu.pipeline import NLUPipeline  # noqa: E402

# ---------------------------------------------------------------------------
# Load models + data once at startup (same artifacts as the bot)
# ---------------------------------------------------------------------------

KB_PATH = ROOT / "data" / "processed" / "tourism_knowledge_base.json"
KECAMATAN_PATH = ROOT / "data" / "knowledge" / "kecamatan_diy.json"
MODEL_DIR = ROOT / "models"


class _Settings:
    model_dir = MODEL_DIR
    kecamatan_path = KECAMATAN_PATH
    greeting_confidence_threshold = 0.7
    word_count_threshold = 3
    intent_confidence_threshold = 0.15


kb = KnowledgeBase(KB_PATH)
nlu = NLUPipeline.from_settings(_Settings)
extractor = EntityExtractor(KECAMATAN_PATH)

GREETING_INTENTS = {"greeting", "pagi", "siang", "sore", "malam", "goodbye"}

# ---------------------------------------------------------------------------
# Backend Place -> frontend place mapping
# ---------------------------------------------------------------------------

_MAIN_CATEGORIES = {"Alam", "Kuliner", "Budaya & Sejarah", "Buatan", "Wisata Air", "Wisata Umum"}
_CATEGORY_BUCKET = {
    "Budaya dan Sejarah": "Budaya & Sejarah",
    "Pantai": "Alam",
    "Agrowisata": "Alam",
    "Petualangan": "Alam",
    "Museum": "Budaya & Sejarah",
    "Desa Wisata": "Wisata Umum",
    "Minat Khusus": "Wisata Umum",
    "Lainnya": "Wisata Umum",
}

# Canonical kabupaten value (from EntityExtractor) -> display label
_KAB_DISPLAY = {
    "bantul": "Bantul",
    "sleman": "Sleman",
    "gunungkidul": "Gunungkidul",
    "kulonprogo": "Kulon Progo",
    "yogyakarta": "Kota Yogyakarta",
}

_TAG_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Pantai", ("pantai",)),
    ("Candi", ("candi",)),
    ("Goa", ("goa", "gua")),
    ("Air Terjun", ("air terjun", "curug", "grojogan")),
    ("Tebing", ("tebing",)),
    ("Bukit", ("bukit", "puncak")),
    ("Gunung", ("gunung", "merapi")),
    ("Museum", ("museum",)),
    ("Embung", ("embung", "waduk", "telaga")),
    ("Hutan", ("hutan", "pinus")),
    ("Desa Wisata", ("desa wisata",)),
    ("Kebun Binatang", ("kebun binatang", "zoo", "gembira loka")),
    ("Keraton", ("keraton", "kraton", "taman sari", "tamansari")),
    ("Taman", ("taman",)),
]

_SCENE_BY_CATEGORY = {
    "Budaya & Sejarah": "dusk",
    "Alam": "nature",
    "Kuliner": "recreation",
    "Buatan": "recreation",
    "Wisata Air": "water",
    "Wisata Umum": "culture",
}


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "tempat"


def _normalize_category(type_str: str) -> str:
    first = (type_str or "").split(",")[0].strip()
    first = _CATEGORY_BUCKET.get(first, first)
    return first if first in _MAIN_CATEGORIES else _CATEGORY_BUCKET.get(first, "Wisata Umum")


def _regency_by_coord(lat: Optional[float], lng: Optional[float]) -> Optional[str]:
    """Rough lat/lng buckets for the 5 DIY regencies (fallback only)."""
    if lat is None or lng is None:
        return None
    if lng < 110.27:
        return "Kulon Progo"
    if lng > 110.50:
        return "Gunungkidul"
    if lat > -7.74:
        return "Sleman"
    if -7.83 <= lat <= -7.76 and 110.34 <= lng <= 110.42:
        return "Kota Yogyakarta"
    if lat < -7.83:
        return "Bantul"
    return "Sleman"


def _regency_of(place: Place) -> str:
    """Derive kabupaten/kota from the address (kecamatan map), then coordinates."""
    entity = extractor.extract(place.address)
    kab = entity.get("kabupaten")
    if kab is None and entity.get("type") == "kabupaten":
        kab = entity.get("value")
    if kab in _KAB_DISPLAY:
        return _KAB_DISPLAY[kab]
    return _regency_by_coord(place.lokasi.latitude, place.lokasi.longitude) or "Yogyakarta"


def _tag_of(place: Place, category: str) -> str:
    hay = f"{place.nama} {place.type_clean}".lower()
    for tag, keys in _TAG_RULES:
        if any(k in hay for k in keys):
            return tag
    return category


def map_place(place: Place) -> dict[str, Any]:
    category = _normalize_category(place.type)
    tag = _tag_of(place, category)
    scene = "beach" if tag == "Pantai" else _SCENE_BY_CATEGORY.get(category, "culture")
    return {
        "id": place.id,
        "name": place.nama,
        "slug": _slugify(place.nama),
        "category": category,
        "tag": tag,
        "regency": _regency_of(place),
        "rating": place.rating if place.has_rating else None,
        "votes": place.vote_count,
        "priceWeekday": place.harga.weekday if place.has_price else None,
        "priceWeekend": place.harga.weekend if place.has_price else None,
        "lat": place.lokasi.latitude,
        "lng": place.lokasi.longitude,
        "scene": scene,
        "address": place.address,
        "phone": place.phone,
        "website": place.website,
        "description": place.description,
        "hasRating": place.has_rating,
        "hasPrice": place.has_price,
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Jelajah Jogja API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    lang: str = "id"


def _L(lang: str, id_text: str, en_text: str) -> str:
    return en_text if lang == "en" else id_text


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "places": len(kb._places)}  # noqa: SLF001


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    cats: dict[str, int] = {}
    regs: dict[str, int] = {}
    for p in kb._places:  # noqa: SLF001
        m = map_place(p)
        cats[m["category"]] = cats.get(m["category"], 0) + 1
        regs[m["regency"]] = regs.get(m["regency"], 0) + 1
    return {
        "categories": [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])],
        "regencies": [{"name": k, "count": v} for k, v in sorted(regs.items(), key=lambda x: -x[1])],
        "total": len(kb._places),  # noqa: SLF001
    }


@app.get("/api/places")
def list_places(
    q: Optional[str] = None,
    category: Optional[str] = None,
    regency: Optional[str] = None,
    max_price: Optional[int] = None,
    min_rating: Optional[float] = None,
    sort: str = "rating",
    limit: int = Query(default=500, le=4000),
) -> dict[str, Any]:
    items = [map_place(p) for p in kb._places]  # noqa: SLF001

    if q:
        ql = q.lower()
        items = [m for m in items if ql in m["name"].lower() or ql in (m["description"] or "").lower()]
    if category:
        items = [m for m in items if m["category"] == category]
    if regency:
        items = [m for m in items if m["regency"] == regency]
    if max_price is not None:
        items = [m for m in items if m["priceWeekday"] is not None and m["priceWeekday"] <= max_price]
    if min_rating is not None:
        items = [m for m in items if (m["rating"] or 0) >= min_rating]

    if sort == "price":
        items.sort(key=lambda m: (m["priceWeekday"] is None, m["priceWeekday"] or 0))
    elif sort == "name":
        items.sort(key=lambda m: m["name"].lower())
    else:  # rating (default) — rated first, then by rating & votes
        items.sort(key=lambda m: (m["rating"] or 0, m["votes"] or 0), reverse=True)

    total = len(items)
    return {"total": total, "items": items[:limit]}


@app.get("/api/places/{place_id}")
def get_place(place_id: int) -> dict[str, Any]:
    place = kb.get_by_id(place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return map_place(place)


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    """Run the real NLU model and route to the same actions the bot uses."""
    result = nlu.understand(req.message)
    intent = result.intent
    lang = req.lang
    places: list[Place] = []
    reply: str

    if intent in GREETING_INTENTS:
        reply = _greeting_reply(intent, lang)
    elif intent == "rekomendasi_wisata":
        places = ActionHandler.handle_rekomendasi(result, kb)
        loc = result.entity.get("value")
        reply = _L(lang,
                   f"Rekomendasi wisata{' di ' + loc.title() if loc else ' terbaik'}:",
                   f"Recommended places{' in ' + loc.title() if loc else ''}:")
    elif intent == "cari_by_type":
        places = ActionHandler.handle_cari_by_type(result, kb)
        reply = _L(lang, "Hasil pencarian berdasarkan kategori:", "Results by category:")
    elif intent == "cari_by_harga":
        places = ActionHandler.handle_cari_by_harga(result, kb)
        reply = _L(lang, "Wisata sesuai anggaranmu:", "Places within your budget:")
    elif intent == "cari_by_rating":
        places = ActionHandler.handle_cari_by_rating(kb)
        reply = _L(lang, "Wisata dengan rating terbaik:", "Top-rated places:")
    elif intent == "info_detail":
        place = ActionHandler.handle_info_detail(result, kb)
        if place:
            places = [place]
            reply = _L(lang, f"Ini {place.nama}:", f"Here's {place.nama}:")
        else:
            reply = _fallback_reply(lang)
    elif intent == "info_lokasi":
        place = ActionHandler.handle_info_lokasi(result, kb)
        if place:
            places = [place]
            reply = _L(lang, f"{place.nama} ada di {_regency_of(place)}. Ketuk untuk peta:",
                       f"{place.nama} is in {_regency_of(place)}. Tap for the map:")
        else:
            reply = _fallback_reply(lang)
    else:
        reply = _fallback_reply(lang)

    return {
        "reply": reply,
        "intent": intent,
        "confidence": round(result.confidence, 3),
        "entity": result.entity,
        "places": [map_place(p) for p in places],
    }


def _greeting_reply(intent: str, lang: str) -> str:
    base = {
        "greeting": ("Halo! Saya YOGA, asisten wisata Yogyakarta. Mau cari wisata apa?",
                     "Hi! I'm YOGA, your Yogyakarta travel assistant. What are you looking for?"),
        "pagi": ("Selamat pagi! Mau wisata ke mana hari ini?", "Good morning! Where would you like to go today?"),
        "siang": ("Selamat siang! Ada rencana wisata?", "Good afternoon! Any travel plans?"),
        "sore": ("Selamat sore! Cari rekomendasi wisata?", "Good evening! Looking for recommendations?"),
        "malam": ("Selamat malam! Merencanakan wisata di Jogja?", "Good evening! Planning a trip in Jogja?"),
        "goodbye": ("Sampai jumpa! Semoga perjalananmu menyenangkan.", "See you! Have a great trip."),
    }
    id_text, en_text = base.get(intent, base["greeting"])
    return _L(lang, id_text, en_text)


def _fallback_reply(lang: str) -> str:
    return _L(lang,
              "Maaf, saya kurang paham. Coba tanya rekomendasi wisata, kategori, harga, atau rating.",
              "Sorry, I didn't catch that. Try asking for recommendations, a category, price, or rating.")
