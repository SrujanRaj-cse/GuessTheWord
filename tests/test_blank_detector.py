"""Tests for underscore blank detection on binary images."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from config.settings import VisionSettings
from ocr.blank_detector import BlankDetector
from vision.image_processor import ImageProcessor

_FIXTURE = __import__("pathlib").Path(__file__).resolve().parent / "fixtures" / "sample_word_strip.png"


def _synthetic_underscores(count: int, width: int = 20, gap: int = 5) -> np.ndarray:
    """White background with ``count`` horizontal underscore strokes."""
    canvas = np.full((40, count * (width + gap) + 10), 255, dtype=np.uint8)
    x = 5
    for _ in range(count):
        cv2.rectangle(canvas, (x, 28), (x + width, 32), 0, thickness=-1)
        x += width + gap
    return canvas


def test_detect_synthetic_five_underscores() -> None:
    detector = BlankDetector()
    result = detector.detect(_synthetic_underscores(5))
    assert result.blanks == "_____"
    assert result.component_count == 5
    assert result.confidence > 0


def test_detect_synthetic_three_underscores() -> None:
    detector = BlankDetector()
    result = detector.detect(_synthetic_underscores(3))
    assert result.blanks == "___"


def test_detect_fixture_finds_multiple_blanks() -> None:
    frame = cv2.imread(str(_FIXTURE))
    assert frame is not None
    processed = ImageProcessor(VisionSettings()).process(frame).processed
    result = BlankDetector().detect(processed)
    assert len(result.blanks) >= 4
    assert all(ch == "_" for ch in result.blanks)


def test_rejects_non_binary_channel() -> None:
    detector = BlankDetector()
    color = np.zeros((10, 10, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        detector.detect(color)
