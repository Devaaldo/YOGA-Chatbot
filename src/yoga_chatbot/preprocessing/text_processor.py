"""
Text preprocessing pipeline for YOGA Chatbot.

Applies a fixed sequence of normalisation steps used consistently by both
the NLU intent classifier and the entity extractor:
    lowercase → strip URLs/mentions → remove punctuation → normalise
    whitespace → Sastrawi stemming
"""

from __future__ import annotations

import re
import string

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


class TextProcessor:
    """Stateful text preprocessor backed by a Sastrawi stemmer.

    The stemmer is expensive to initialise, so instantiate this class once
    and reuse it throughout the application lifetime.
    """

    def __init__(self) -> None:
        factory = StemmerFactory()
        self._stemmer = factory.create_stemmer()
        self._punctuation_table = str.maketrans("", "", string.punctuation)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess(self, text: str) -> str:
        """Return a cleaned, stemmed version of *text*.

        Steps
        -----
        1. Lowercase
        2. Remove URLs (http/https)
        3. Remove @mentions and #hashtags
        4. Strip punctuation
        5. Collapse whitespace
        6. Sastrawi stem each token
        """
        if not text or not text.strip():
            return ""

        text = text.lower()
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[@#]\S+", "", text)
        text = text.translate(self._punctuation_table)
        text = re.sub(r"\s+", " ", text).strip()
        tokens = [self._stemmer.stem(token) for token in text.split()]
        return " ".join(tokens)

    def tokenize(self, text: str) -> list[str]:
        """Preprocess *text* and return a list of tokens."""
        return self.preprocess(text).split()
