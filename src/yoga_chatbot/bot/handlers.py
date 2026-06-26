"""
Telegram update handlers for YOGA Chatbot.

Registers
---------
/start   — welcome message
/help    — usage guide with example queries
/about   — model and project information
/reset   — clear conversation context (stateless bot — just sends a note)

MessageHandler    — routes free-text through NLU pipeline → action handler
CallbackQueryHandler — processes inline button taps
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from yoga_chatbot.actions.handlers import ActionHandler
from yoga_chatbot.bot.formatters import (
    format_no_results,
    format_place_detail,
    format_place_list,
    format_place_lokasi,
)
from yoga_chatbot.bot.keyboards import build_places_keyboard, build_type_keyboard
from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase
from yoga_chatbot.nlu.pipeline import NLUPipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent → handler routing table
# ---------------------------------------------------------------------------

_GREETING_INTENTS = frozenset(["greeting", "pagi", "siang", "sore", "malam", "goodbye"])

_HELP_TEXT = """
*YOGA Chatbot — Panduan Penggunaan*

Saya bisa membantu kamu menemukan tempat wisata di Yogyakarta.

*Contoh pertanyaan:*
- Rekomendasi wisata di Bantul
- Wisata pantai di Gunungkidul
- Tempat wisata dengan tiket murah
- Tempat wisata dengan rating bagus
- Info tentang Candi Prambanan
- Lokasi Pantai Parangtritis

*Perintah:*
/start  — Mulai ulang percakapan
/help   — Tampilkan panduan ini
/about  — Informasi tentang bot ini
/reset  — Reset percakapan
""".strip()

_ABOUT_TEXT = """
*YOGA Chatbot*
Asisten wisata Daerah Istimewa Yogyakarta

*Arsitektur NLU:*
- Preprocessing: Sastrawi stemmer + TF-IDF
- Entity extractor: 78 kecamatan, 5 kabupaten/kota
- Intent classifier: Hybrid 3-stage SVM pipeline
- Accuracy: 94.73% (held-out test set)

*Knowledge base:*
- 3.000+ tempat wisata di Yogyakarta
- Data: Kaggle + Geoapify Places API

*Versi:* 1.0.0
""".strip()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user else "Wisatawan"
    text = (
        f"Halo, {name}! Saya *YOGA*, asisten wisata Yogyakarta.\n\n"
        "Saya bisa membantu kamu menemukan rekomendasi tempat wisata, "
        "mencari wisata berdasarkan kategori, harga, atau rating, "
        "dan memberikan info lengkap beserta lokasi.\n\n"
        "Ketik /help untuk melihat contoh pertanyaan."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_HELP_TEXT, parse_mode="Markdown")


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_ABOUT_TEXT, parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Percakapan direset. Silakan ajukan pertanyaan baru.",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    nlu: NLUPipeline,
    kb: KnowledgeBase,
) -> None:
    """Route an incoming message through the full NLU → action → response pipeline."""
    raw_text = update.message.text or ""
    if not raw_text.strip():
        return

    logger.info("Message from user %s: %r", update.effective_user.id, raw_text)

    result = nlu.understand(raw_text)
    intent = result.intent

    logger.info("Intent: %s (%.2f) | Entity: %s", intent, result.confidence, result.entity)

    # --- Greeting / conversational ---
    if intent in _GREETING_INTENTS:
        reply = ActionHandler.handle_greeting(intent)
        await update.message.reply_text(reply, parse_mode="Markdown")
        return

    # --- Recommendations ---
    if intent in ("rekomendasi_wisata", "rekomendasi_wisata_kecamatan",
                  "rekomendasi_wisata_kabupaten", "rekomendasi_wisata_provinsi"):
        places = ActionHandler.handle_rekomendasi(result, kb)
        if not places:
            await update.message.reply_text(format_no_results())
            return
        header = (
            f"Rekomendasi wisata di {result.entity['value'].title()}:"
            if result.has_location
            else "Rekomendasi wisata terbaik di Yogyakarta:"
        )
        text = format_place_list(places, header=header)
        keyboard = build_places_keyboard(places)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    # --- Category search ---
    if intent == "cari_by_type":
        places = ActionHandler.handle_cari_by_type(result, kb)
        if not places:
            await update.message.reply_text(
                "Tidak ada tempat wisata dengan kategori tersebut.\n"
                "Pilih kategori:",
                reply_markup=build_type_keyboard(),
            )
            return
        text = format_place_list(places, header="Hasil pencarian berdasarkan kategori:")
        keyboard = build_places_keyboard(places)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    # --- Price search ---
    if intent == "cari_by_harga":
        places = ActionHandler.handle_cari_by_harga(result, kb)
        text = format_place_list(places, header="Wisata sesuai anggaran kamu:")
        keyboard = build_places_keyboard(places)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    # --- Rating search ---
    if intent == "cari_by_rating":
        places = ActionHandler.handle_cari_by_rating(kb)
        text = format_place_list(places, header="Wisata dengan rating terbaik:")
        keyboard = build_places_keyboard(places)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    # --- Place detail ---
    if intent == "info_detail":
        place = ActionHandler.handle_info_detail(result, kb)
        if place is None:
            await update.message.reply_text(format_no_results())
            return
        await update.message.reply_text(
            format_place_detail(place), parse_mode="Markdown"
        )
        return

    # --- Location info ---
    if intent == "info_lokasi":
        place = ActionHandler.handle_info_lokasi(result, kb)
        if place is None:
            await update.message.reply_text(format_no_results())
            return
        await update.message.reply_text(
            format_place_lokasi(place), parse_mode="Markdown"
        )
        return

    # --- Fallback ---
    await update.message.reply_text(ActionHandler.handle_fallback())


# ---------------------------------------------------------------------------
# Callback query handler (inline keyboard button presses)
# ---------------------------------------------------------------------------


async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    kb: KnowledgeBase,
) -> None:
    """Process inline button taps from place lists or category keyboards."""
    query = update.callback_query
    await query.answer()

    data: str = query.data or ""

    if data.startswith("place:"):
        place_id = int(data.split(":", 1)[1])
        place = kb.get_by_id(place_id)
        if place is None:
            await query.edit_message_text("Informasi tempat tidak ditemukan.")
            return
        await query.edit_message_text(
            format_place_detail(place), parse_mode="Markdown"
        )
        return

    if data.startswith("type:"):
        place_type = data.split(":", 1)[1]
        places = kb.search_by_type(place_type)
        if not places:
            await query.edit_message_text(
                f"Tidak ada tempat wisata dengan kategori '{place_type}'."
            )
            return
        text = format_place_list(places, header=f"Wisata {place_type.title()}:")
        keyboard = build_places_keyboard(places)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    logger.warning("Unhandled callback data: %r", data)
    await query.edit_message_text("Tindakan tidak dikenali.")
