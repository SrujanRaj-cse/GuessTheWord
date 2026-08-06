"""Tests for the pattern recognition facade."""

from __future__ import annotations

import cv2
import numpy as np

from ocr.pattern_recognizer import PatternRecognizer
from ocr.provider import LetterOCRResult

_FIXTURE = __import__("pathlib").Path(__file__).resolve().parent / "fixtures" / "sample_word_strip.png"


class _StubEngine:
    name = "stub"

    def __init__(self, letters: str, confidence: float) -> None:
        self._letters = letters
        self._confidence = confidence

    def recognize_letters(self, image_bgr: np.ndarray) -> LetterOCRResult:
        return LetterOCRResult(letters=self._letters, confidence=self._confidence)


def test_recognize_frame_merges_stub_letters_with_detected_blanks() -> None:
    frame = cv2.imread(str(_FIXTURE))
    assert frame is not None
    recognizer = PatternRecognizer(_StubEngine("to", 0.95))
    output = recognizer.recognize_frame(frame)
    assert output.result.letters == "to"
    assert output.result.pattern.startswith("to")
    assert "_" in output.result.pattern
    assert output.timing.total_ms >= 0
