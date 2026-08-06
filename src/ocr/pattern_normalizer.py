"""Merge letter OCR output with CV-detected blank runs into a solver pattern."""

from __future__ import annotations

import re

_LETTERS_RE = re.compile(r"^[a-z]*$")


class PatternNormalizer:
    """
    Combine alphabetic OCR text and underscore blank runs.

    Layout policy: single-line left-to-right concatenation ``letters + blanks``.
    OCR noise (spaces, punctuation) is stripped before lowercase normalization.
    """

    def merge(self, letters: str, blanks: str) -> str:
        """
        Build the final pattern string.

        Args:
            letters: Alphabetic characters only (may include spaces/punctuation to strip).
            blanks: Underscore characters representing blank slots.

        Returns:
            Lowercase pattern such as ``to_____``.

        Raises:
            ValueError: If normalized blanks contain non-underscore characters.
        """
        normalized_letters = self.normalize_letters(letters)
        normalized_blanks = self.normalize_blanks(blanks)
        return f"{normalized_letters}{normalized_blanks}"

    def normalize_letters(self, raw: str) -> str:
        """Strip non-letters and lowercase."""
        cleaned = "".join(ch for ch in raw.lower() if ch.isalpha())
        return cleaned

    def normalize_blanks(self, raw: str) -> str:
        """Keep underscores only."""
        if any(ch != "_" for ch in raw):
            raise ValueError(f"Blanks must contain only '_', got {raw!r}")
        return raw

    def validate_letters(self, letters: str) -> bool:
        """Return True if ``letters`` is already normalized alphabetic text."""
        return bool(_LETTERS_RE.fullmatch(letters))
