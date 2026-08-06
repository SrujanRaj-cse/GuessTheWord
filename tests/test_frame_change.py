"""Tests for frame change detection."""

from __future__ import annotations

import numpy as np

from capture.frame_change import FrameChangeDetector


def test_first_frame_always_changed() -> None:
    detector = FrameChangeDetector(threshold=0.02)
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    assert detector.has_changed(frame) is True


def test_identical_frames_not_changed() -> None:
    detector = FrameChangeDetector(threshold=0.02)
    frame = np.zeros((40, 80, 3), dtype=np.uint8)
    detector.has_changed(frame)
    assert detector.has_changed(frame.copy()) is False


def test_large_diff_triggers_change() -> None:
    detector = FrameChangeDetector(threshold=0.02)
    a = np.zeros((40, 80, 3), dtype=np.uint8)
    b = a.copy()
    detector.has_changed(a)
    b[10:30, 20:60] = 255
    assert detector.has_changed(b) is True
