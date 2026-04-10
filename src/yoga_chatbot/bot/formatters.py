"""
Text formatters for Telegram messages.

All output is plain Markdown (Telegram MarkdownV2 where needed) with no
emoji unless the content itself comes from the data source.

Functions
---------
format_place_summary   — one-liner used in list views
format_place_detail    — full info card for a single place
format_place_list      — numbered list of summaries
format_no_results      — fallback message when search returns nothing
"""

from __future__ import annotations

from yoga_chatbot.knowledge.knowledge_base import Place


def format_price(place: Place) -> str:
    """Return a human-readable price string."""
    if not place.has_price:
        return "Tidak tersedia"
    weekday = place.harga.weekday
    if weekday == 0:
        return "Gratis"
    if weekday is not None:
        return f"Rp {weekday:,}".replace(",", ".")
    return "Tidak tersedia"


def format_rating(place: Place) -> str:
    """Return a star-rating string with vote count."""
    if not place.has_rating or place.rating == 0:
        return "Belum ada rating"
    stars = round(place.rating * 2) / 2  # round to nearest 0.5
    return f"{stars}/5 ({place.vote_count:,} ulasan)".replace(",", ".")


def format_place_summary(place: Place, index: int | None = None) -> str:
    """Return a compact one-line summary of *place*.

    Example
    -------
    ``1. Candi Prambanan — Candi | Rating: 4.6/5 | Tiket: Rp 40.000``
    """
    prefix = f"{index}. " if index is not None else ""
    return (
        f"{prefix}*{place.nama}*\n"
        f"   Kategori: {place.type}\n"
        f"   Rating: {format_rating(place)}\n"
        f"   Tiket: {format_price(place)}"
    )


def format_place_detail(place: Place) -> str:
    """Return a full information card for *place*."""
    lines: list[str] = [
        f"*{place.nama}*",
        f"Kategori: {place.type}",
        f"Rating: {format_rating(place)}",
        f"Tiket: {format_price(place)}",
    ]

    if place.has_description and place.description:
        lines.append(f"\n{place.description[:300]}{'...' if len(place.description) > 300 else ''}")

    if place.has_address and place.address:
        lines.append(f"\nAlamat: {place.address}")

    if place.has_contact and place.phone:
        lines.append(f"Telepon: {place.phone}")

    if place.website:
        lines.append(f"Website: {place.website}")

    maps_url = place.lokasi.maps_url()
    if maps_url:
        lines.append(f"\n[Lihat di Google Maps]({maps_url})")

    return "\n".join(lines)


def format_place_lokasi(place: Place) -> str:
    """Return a location-focused card with coordinates and a Maps link."""
    lines: list[str] = [f"*{place.nama}*"]

    if place.has_address and place.address:
        lines.append(f"Alamat: {place.address}")

    lat = place.lokasi.latitude
    lng = place.lokasi.longitude
    if lat is not None and lng is not None:
        lines.append(f"Koordinat: {lat:.6f}, {lng:.6f}")

    maps_url = place.lokasi.maps_url()
    if maps_url:
        lines.append(f"\n[Buka di Google Maps]({maps_url})")

    if place.phone:
        lines.append(f"Telepon: {place.phone}")

    return "\n".join(lines)


def format_place_list(places: list[Place], header: str = "Rekomendasi wisata:") -> str:
    """Return a numbered list of place summaries with a header."""
    if not places:
        return format_no_results()
    parts = [header, ""]
    for i, place in enumerate(places, start=1):
        parts.append(format_place_summary(place, index=i))
        parts.append("")
    parts.append("Ketuk nama tempat untuk info lengkap.")
    return "\n".join(parts)


def format_no_results(context: str = "") -> str:
    suffix = f" di {context}" if context else ""
    return (
        f"Maaf, saya tidak menemukan tempat wisata{suffix} yang sesuai.\n"
        "Coba gunakan kata kunci lain atau tanyakan rekomendasi umum."
    )
