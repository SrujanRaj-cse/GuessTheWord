"""Accuracy and timing helpers for OCR validation."""

from __future__ import annotations

from dataclasses import dataclass


def char_accuracy(expected: str, actual: str) -> float:
    """Character-level accuracy on aligned prefix of equal-length comparison."""
    if not expected and not actual:
        return 1.0
    if not expected or not actual:
        return 0.0
    limit = max(len(expected), len(actual))
    matches = sum(
        1 for index in range(min(len(expected), len(actual))) if expected[index] == actual[index]
    )
    return matches / limit


def exact_match_accuracy(expected: str, actual: str) -> float:
    return 1.0 if expected == actual else 0.0


@dataclass(frozen=True)
class SampleMetrics:
    """Benchmark metrics for one sample and engine."""

    sample_id: str
    engine: str
    expected_letters: str
    expected_pattern: str
    actual_letters: str
    actual_pattern: str
    letter_accuracy: float
    pattern_accuracy: float
    confidence: float
    recognition_score: float
    latency_ms: float
    cpu_seconds: float


def recognition_score(letter_accuracy: float, pattern_accuracy: float, confidence: float) -> float:
    return letter_accuracy * pattern_accuracy * confidence


def build_sample_metrics(
    *,
    sample_id: str,
    engine: str,
    expected_letters: str,
    expected_pattern: str,
    actual_letters: str,
    actual_pattern: str,
    confidence: float,
    latency_ms: float,
    cpu_seconds: float,
) -> SampleMetrics:
    letter_acc = char_accuracy(expected_letters, actual_letters)
    pattern_acc = char_accuracy(expected_pattern, actual_pattern)
    score = recognition_score(letter_acc, pattern_acc, confidence)
    return SampleMetrics(
        sample_id=sample_id,
        engine=engine,
        expected_letters=expected_letters,
        expected_pattern=expected_pattern,
        actual_letters=actual_letters,
        actual_pattern=actual_pattern,
        letter_accuracy=letter_acc,
        pattern_accuracy=pattern_acc,
        confidence=confidence,
        recognition_score=score,
        latency_ms=latency_ms,
        cpu_seconds=cpu_seconds,
    )
