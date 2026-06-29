from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase, Place 
from yoga_chatbot.nlu.entity_extractor import EntityExtractor
from yoga_chatbot.nlu.pipeline import NLUPipeline

# Load models + data once at startup (same artifacts as the bot)
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

# Backend Place -> frontend place mapping
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
    # Rough lat/lng buckets for the 5 DIY regencies (fallback only)
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
    # Derive kabupaten/kota from the address (kecamatan map), then coordinates
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

# Precompute the mapped catalogue once (also reused by /api/places).
ALL_PLACES: list[dict[str, Any]] = [map_place(p) for p in kb._places]

# Fine-grained type keywords (user text -> place tag).
_FINE_TYPES: dict[str, str] = {
    "pantai": "Pantai", "beach": "Pantai",
    "candi": "Candi", "temple": "Candi",
    "gunung": "Gunung", "merapi": "Gunung",
    "bukit": "Bukit", "puncak": "Bukit",
    "tebing": "Tebing",
    "air terjun": "Air Terjun", "curug": "Air Terjun", "grojogan": "Air Terjun",
    "goa": "Goa", "gua": "Goa",
    "museum": "Museum",
    "hutan": "Hutan", "pinus": "Hutan",
    "embung": "Embung", "telaga": "Embung", "waduk": "Embung",
    "taman": "Taman",
    "kuliner": "Kuliner", "kebun binatang": "Kebun Binatang", "zoo": "Kebun Binatang",
    "desa wisata": "Desa Wisata",
}

_BUDGET_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(rb|ribu|k|jt|juta)?", re.IGNORECASE)


def _popular(items: list[dict[str, Any]], n: int = 5) -> list[dict[str, Any]]:
    """Top places preferring well-known ones (vote floor) so obscure 5.0-rated
    outliers with a handful of votes don't dominate."""
    known = [p for p in items if (p.get("votes") or 0) >= 100]
    pool = known if len(known) >= n else items
    return sorted(pool, key=lambda p: ((p.get("rating") or 0), (p.get("votes") or 0)),
                reverse=True)[:n]

def _detect_type(text: str) -> Optional[str]:
    t = text.lower()
    for kw, tag in _FINE_TYPES.items():
        if kw in t:
            return tag
    return None

def _extract_budget(text: str) -> Optional[int]:
    m = _BUDGET_RE.search(text.lower())
    if not m:
        return None
    try:
        amount = int(m.group(1).replace(".", "").replace(",", ""))
    except ValueError:
        return None
    unit = (m.group(2) or "").lower()
    if unit in ("rb", "ribu", "k"):
        amount *= 1_000
    elif unit in ("jt", "juta"):
        amount *= 1_000_000
    return amount

def _by_regency(items: list[dict[str, Any]], regency: Optional[str]) -> list[dict[str, Any]]:
    if not regency:
        return items
    sub = [p for p in items if p["regency"].lower() == regency.lower()]
    return sub if sub else items

def _fuzzy_place(text: str) -> Optional[dict[str, Any]]:
    t = text.lower()
    best, best_score = None, 0
    for p in ALL_PLACES:
        name = p["name"].lower()
        if name in t:
            return p
        score = sum(1 for w in name.split() if len(w) > 3 and w in t)
        if score > best_score:
            best, best_score = p, score
    return best if best_score > 0 else None


_CHEAP_WORDS = ("murah", "hemat", "budget", "termurah", "ramah kantong", "cheap")
_RATING_WORDS = ("rating", "terbaik", "bagus", "populer", "favorit", "top",
                 "best", "recommended", "hits", "terkenal")
_ITINERARY_WORDS = ("itinerary", "itinerari", "rencana", "jadwal", "plan")


def _rupiah(n: int) -> str:
    return "Rp" + f"{n:,}".replace(",", ".")


def resolve_search(text, regency, lang):
    """Compositional search: combine type + regency + budget + rating from a
    single message (e.g. 'pantai murah di gunungkidul')."""
    t = text.lower()
    tag = _detect_type(text)
    wants_free = "gratis" in t or "free" in t
    budget = _extract_budget(t)
    wants_cheap = wants_free or budget is not None or any(w in t for w in _CHEAP_WORDS)
    wants_rating = any(w in t for w in _RATING_WORDS)

    items = ALL_PLACES
    if tag:
        items = [p for p in items if p["tag"] == tag]
    items = _by_regency(items, regency)

    if wants_free:
        free = [p for p in items if p["priceWeekday"] == 0]
        items = free or [p for p in items if p["priceWeekday"] not in (None, 0)]
    elif budget:
        items = [p for p in items if p["priceWeekday"] is not None and p["priceWeekday"] <= budget]

    if wants_cheap and not wants_free:
        cand = [p for p in items if p["priceWeekday"] not in (None, 0)]
        cand.sort(key=lambda p: (p["priceWeekday"], -(p["votes"] or 0)))
        places = cand[:6]
    else:
        places = _popular(items, 6)

    label = tag.lower() if tag else _L(lang, "wisata", "places")
    where = (_L(lang, " di ", " in ") + regency) if regency else ""
    if wants_free:
        mod = _L(lang, " gratis/termurah", " (free/cheapest)")
    elif wants_cheap:
        mod = _L(lang, " termurah", " (cheapest)")
    elif wants_rating:
        mod = _L(lang, " rating terbaik", " (top-rated)")
    else:
        mod = ""
    reply = _L(lang, f"Rekomendasi {label}{where}{mod}:", f"Top {label}{where}{mod}:")
    return places, reply


def build_itinerary(text, regency, lang):
    """Turn 'buatkan itinerary 2 hari' into a day-by-day plan + budget."""
    m = re.search(r"(\d+)\s*(hari|day)", text.lower())
    days = max(1, min(int(m.group(1)) if m else 2, 5))
    pool = _by_regency(ALL_PLACES, regency)
    picks = _popular(pool, days * 3)
    if len(picks) < days * 3:
        picks = _popular(ALL_PLACES, days * 3)

    segments, total = [], 0
    for i in range(days):
        group = picks[i * 3:(i + 1) * 3]
        if not group:
            break
        total += sum((p["priceWeekday"] or 0) for p in group)
        names = ", ".join(p["name"] for p in group)
        segments.append(_L(lang, f"Hari {i + 1}: ", f"Day {i + 1}: ") + names)

    head = _L(lang,
              f"Rencana {days} hari di {regency or 'Yogyakarta'}",
              f"A {days}-day plan in {regency or 'Yogyakarta'}")
    budget = _L(lang, f"Perkiraan tiket {_rupiah(total)}", f"Estimated tickets {_rupiah(total)}")
    reply = head + " — " + " · ".join(segments) + ". " + budget + "."
    return picks, reply


# FastAPI app
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
    return {"status": "ok", "places": len(kb._places)} 

@app.get("/api/meta")
def meta() -> dict[str, Any]:
    cats: dict[str, int] = {}
    regs: dict[str, int] = {}
    for p in kb._places:
        m = map_place(p)
        cats[m["category"]] = cats.get(m["category"], 0) + 1
        regs[m["regency"]] = regs.get(m["regency"], 0) + 1
    return {
        "categories": [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])],
        "regencies": [{"name": k, "count": v} for k, v in sorted(regs.items(), key=lambda x: -x[1])],
        "total": len(kb._places),
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
    items = [map_place(p) for p in kb._places]

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
    """Run the NLU model, then pick places from the mapped catalogue using
    fine-grained tags + a popularity floor (better than the coarse KB search)."""
    result = nlu.understand(req.message)
    intent = result.intent
    lang = req.lang
    text = req.message

    kab = result.entity.get("kabupaten")
    if kab is None and result.entity.get("type") == "kabupaten":
        kab = result.entity.get("value")
    regency = _KAB_DISPLAY.get(kab)

    places: list[dict[str, Any]] = []
    t = text.lower()
    is_itinerary = bool(any(w in t for w in _ITINERARY_WORDS)
                        or re.search(r"\d+\s*(hari|day)", t))

    if is_itinerary:
        places, reply = build_itinerary(text, regency, lang)
    elif intent in GREETING_INTENTS:
        reply = _greeting_reply(intent, lang)
    elif intent == "info_detail":
        p = _fuzzy_place(text)
        if p:
            places = [p]
            reply = _L(lang, f"Ini {p['name']}:", f"Here's {p['name']}:")
        else:
            reply = _fallback_reply(lang)
    elif intent == "info_lokasi":
        p = _fuzzy_place(text)
        if p:
            places = [p]
            reply = _L(lang, f"{p['name']} ada di {p['regency']}. Ketuk untuk peta:",
                       f"{p['name']} is in {p['regency']}. Tap for the map:")
        else:
            reply = _fallback_reply(lang)
    elif intent in ("cari_by_type", "cari_by_harga", "cari_by_rating", "rekomendasi_wisata"):
        places, reply = resolve_search(text, regency, lang)
    else:
        reply = _fallback_reply(lang)

    return {
        "reply": reply,
        "intent": intent,
        "confidence": round(result.confidence, 3),
        "entity": result.entity,
        "places": places,
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
