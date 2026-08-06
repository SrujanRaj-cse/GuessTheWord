"""Shared helpers for letter-only OCR engines."""

from __future__ import annotations

import re

from ocr.provider import LetterOCRResult

_NON_LETTER = re.compile(r"[^a-zA-Z]+")


def sanitize_letters(raw: str, confidence: float) -> LetterOCRResult:
    """Lowercase alphabetic characters only."""
    letters = _NON_LETTER.sub("", raw).lower()
    return LetterOCRResult(letters=letters, confidence=max(0.0, min(1.0, confidence)))


def mean_confidence(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
