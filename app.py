"""
Hugging Face Spaces entry point for the YOGA Telegram chatbot.

HF Spaces (Docker SDK) require the container to listen on a port (7860). A
Telegram *polling* bot has no inbound HTTP, so we run a tiny health server on
that port in a background thread purely to satisfy the platform and to give an
external uptime pinger (e.g. UptimeRobot) something to hit — keeping the free
Space from sleeping. The bot itself runs in the main thread because
python-telegram-bot installs asyncio signal handlers there.

Locally you do not need this file — use `python -m yoga_chatbot.bot.bot`.
"""

from __future__ import annotations

import http.server
import os
import threading

PORT = int(os.environ.get("PORT", "7860"))


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"YOGA Chatbot is alive")

    def log_message(self, *args: object) -> None:  # silence access logs
        pass


def _serve_health() -> None:
    http.server.HTTPServer(("0.0.0.0", PORT), _HealthHandler).serve_forever()


def main() -> None:
    threading.Thread(target=_serve_health, daemon=True).start()
    # Imported lazily so the health endpoint is up even if model loading is slow.
    from yoga_chatbot.bot.bot import main as run_bot
    run_bot()


if __name__ == "__main__":
    main()
