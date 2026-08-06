"""Tests for validation metrics math."""

from __future__ import annotations

from tools.ocr_validate.metrics import (
    build_sample_metrics,
    char_accuracy,
    recognition_score,
)


def test_char_accuracy_partial() -> None:
    assert char_accuracy("to", "tx") == 0.5


def test_recognition_score_product() -> None:
    assert recognition_score(1.0, 0.5, 0.8) == 0.4


def test_build_sample_metrics() -> None:
    row = build_sample_metrics(
        sample_id="1",
        engine="stub",
        expected_letters="ab",
        expected_pattern="ab__",
        actual_letters="ab",
        actual_pattern="ab_",
        confidence=0.9,
        latency_ms=10.0,
        cpu_seconds=0.01,
    )
    assert row.pattern_accuracy == 0.75
    assert row.recognition_score == row.letter_accuracy * row.pattern_accuracy * 0.9
