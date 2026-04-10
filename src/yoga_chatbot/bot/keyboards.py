"""
Inline keyboard builders for Telegram.

Callback data format
--------------------
``"place:<id>"``   — user selected a specific place from a list
``"type:<name>"``  — user tapped a category filter button
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from yoga_chatbot.knowledge.knowledge_base import Place

# Predefined category buttons shown when no specific type is mentioned
_PLACE_CATEGORIES: list[tuple[str, str]] = [
    ("Pantai", "pantai"),
    ("Candi", "candi"),
    ("Gunung / Bukit", "gunung"),
    ("Museum", "museum"),
    ("Alam", "alam"),
    ("Kuliner", "kuliner"),
]


def build_places_keyboard(places: list[Place]) -> InlineKeyboardMarkup:
    """Build a keyboard with one button per place for detail lookup.

    Each button callback carries the place ID so the callback handler can
    retrieve the full record from the knowledge base.
    """
    buttons = [
        [InlineKeyboardButton(text=place.nama, callback_data=f"place:{place.id}")]
        for place in places
    ]
    return InlineKeyboardMarkup(buttons)


def build_type_keyboard() -> InlineKeyboardMarkup:
    """Build a 2-column keyboard for browsing by place category."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for label, type_key in _PLACE_CATEGORIES:
        row.append(InlineKeyboardButton(text=label, callback_data=f"type:{type_key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)
