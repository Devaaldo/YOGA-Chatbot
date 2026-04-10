"""
Main entry point for the YOGA Telegram chatbot.

Usage
-----
    python -m yoga_chatbot.bot.bot

Or via Makefile:
    make run
"""

from __future__ import annotations

import logging
from functools import partial

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config.settings import Settings, settings as default_settings
from yoga_chatbot.bot.handlers import (
    cmd_about,
    cmd_help,
    cmd_reset,
    cmd_start,
    handle_callback,
    handle_message,
)
from yoga_chatbot.knowledge.knowledge_base import KnowledgeBase
from yoga_chatbot.nlu.pipeline import NLUPipeline

logger = logging.getLogger(__name__)


class YogaChatbot:
    """Assembles and runs the YOGA Telegram bot.

    All heavy objects (NLU models, knowledge base) are loaded once during
    ``__init__`` and shared across all incoming updates via ``partial``
    wrappers — avoiding global state while keeping handler signatures clean.

    Parameters
    ----------
    settings:
        Configuration object. Defaults to the module-level singleton.
    """

    def __init__(self, settings: Settings = default_settings) -> None:
        settings.validate()
        self._settings = settings
        self._nlu = NLUPipeline.from_settings(settings)
        self._kb = KnowledgeBase(settings.knowledge_base_path)

    def run(self) -> None:
        """Build the Telegram Application and start polling."""
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            level=getattr(logging, self._settings.log_level, logging.INFO),
        )
        logger.info("Starting YOGA Chatbot…")

        app = (
            Application.builder()
            .token(self._settings.telegram_bot_token)
            .build()
        )

        # Commands
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("about", cmd_about))
        app.add_handler(CommandHandler("reset", cmd_reset))

        # Free-text messages (bind NLU and KB via partial)
        message_handler = partial(handle_message, nlu=self._nlu, kb=self._kb)
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        # Inline keyboard callbacks
        callback_handler = partial(handle_callback, kb=self._kb)
        app.add_handler(CallbackQueryHandler(callback_handler))

        logger.info("Bot is running. Press Ctrl+C to stop.")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main() -> None:
    YogaChatbot().run()


if __name__ == "__main__":
    main()
