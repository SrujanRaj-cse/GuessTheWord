"""Tests for OCR engine helpers."""

from __future__ import annotations

from ocr.engines.base import sanitize_letters


def test_sanitize_letters_strips_non_alpha() -> None:
    result = sanitize_letters("To! 123", 1.2)
    assert result.letters == "to"
    assert result.confidence == 1.0
