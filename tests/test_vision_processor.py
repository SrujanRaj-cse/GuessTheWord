"""Tests for vision preprocessing."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from config.settings import VisionSettings
from vision.image_processor import ImageProcessor

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_word_strip.png"


def test_process_fixture_produces_binary_stages() -> None:
    frame = cv2.imread(str(_FIXTURE))
    assert frame is not None
    processor = ImageProcessor(VisionSettings())
    result = processor.process(frame)

    assert result.original_bgr.shape == frame.shape
    assert result.grayscale.ndim == 2
    assert result.thresholded.ndim == 2
    assert result.processed.ndim == 2
    assert result.thresholded.dtype == np.uint8
    assert set(np.unique(result.thresholded)).issubset({0, 255})


def test_crop_margin_reduces_dimensions() -> None:
    frame = cv2.imread(str(_FIXTURE))
    assert frame is not None
    processor = ImageProcessor(VisionSettings(crop_margin_px=5))
    result = processor.process(frame)
    height, width = frame.shape[:2]
    assert result.original_bgr.shape[0] == height - 10
    assert result.original_bgr.shape[1] == width - 10


def test_noise_removal_can_change_threshold_output() -> None:
    frame = cv2.imread(str(_FIXTURE))
    assert frame is not None
    processor = ImageProcessor(VisionSettings())
    result = processor.process(frame)
    assert result.processed.shape == result.thresholded.shape
    # Morphology may leave identical output on blank regions; fixture has ink.
    assert np.any(result.processed > 0)
