"""
Centralized configuration for YOGA Chatbot.

All runtime settings are loaded from environment variables (via .env file).
Import the singleton `settings` object rather than instantiating Settings directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    # --- Telegram ---
    telegram_bot_token: str = field(
        default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", "")
    )

    # --- Paths ---
    model_dir: Path = field(default_factory=lambda: ROOT_DIR / "models")
    data_dir: Path = field(default_factory=lambda: ROOT_DIR / "data")

    @property
    def knowledge_base_path(self) -> Path:
        return self.data_dir / "processed" / "tourism_knowledge_base.json"

    @property
    def kecamatan_path(self) -> Path:
        return self.data_dir / "knowledge" / "kecamatan_diy.json"

    # --- NLU thresholds ---
    greeting_confidence_threshold: float = float(
        os.environ.get("GREETING_CONFIDENCE_THRESHOLD", "0.7")
    )
    word_count_threshold: int = int(
        os.environ.get("WORD_COUNT_THRESHOLD", "3")
    )

    # --- Logging ---
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")

    # --- Model file names ---
    greeting_detector_filename: str = "greeting_detector.pkl"
    svm_model_filename: str = "svm_model.pkl"
    tfidf_greeting_filename: str = "tfidf_greeting.pickle"
    tfidf_vectorizer_filename: str = "tfidf_vectorizer.pickle"
    label_encoder_filename: str = "label_encoder.pickle"

    def validate(self) -> None:
        """Raise ValueError for any missing critical configuration."""
        if not self.telegram_bot_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set. "
                "Add it to your .env file or environment variables."
            )
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.knowledge_base_path}"
            )


# Singleton instance used across the entire application
settings = Settings()
