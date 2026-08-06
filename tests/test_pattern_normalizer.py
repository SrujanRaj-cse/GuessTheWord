"""Tests for pattern merge logic."""

from __future__ import annotations

import pytest

from ocr.pattern_normalizer import PatternNormalizer


@pytest.fixture
def normalizer() -> PatternNormalizer:
    return PatternNormalizer()


def test_merge_letters_and_blanks(normalizer: PatternNormalizer) -> None:
    assert normalizer.merge("to", "_____") == "to_____"


def test_normalize_letters_strips_noise(normalizer: PatternNormalizer) -> None:
    assert normalizer.normalize_letters(" To! ") == "to"
    assert normalizer.normalize_letters("A.B-C") == "abc"


def test_normalize_blanks_underscores_only(normalizer: PatternNormalizer) -> None:
    assert normalizer.normalize_blanks("___") == "___"


def test_normalize_blanks_rejects_invalid(normalizer: PatternNormalizer) -> None:
    with pytest.raises(ValueError):
        normalizer.normalize_blanks("_a_")


def test_merge_empty_blanks(normalizer: PatternNormalizer) -> None:
    assert normalizer.merge("hello", "") == "hello"
