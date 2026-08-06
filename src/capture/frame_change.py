"""Detect meaningful changes between consecutive frames."""

from __future__ import annotations

import cv2
import numpy as np

_COMPARE_WIDTH = 160
_MIN_CHANGE = 1e-6


class FrameChangeDetector:
    """
    Compare downscaled grayscale frames.

    Emits a change when mean absolute pixel difference exceeds ``threshold``.
    """

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold
        self._previous: np.ndarray | None = None

    def reset(self) -> None:
        """Clear stored frame (e.g. after region change)."""
        self._previous = None

    def has_changed(self, frame_bgr: np.ndarray) -> bool:
        """Return True if ``frame_bgr`` differs enough from the previous frame."""
        current = self._to_compare_gray(frame_bgr)
        if self._previous is None:
            self._previous = current
            return True

        diff = cv2.absdiff(current, self._previous)
        mean_diff = float(np.mean(diff)) / 255.0
        self._previous = current
        return mean_diff >= max(self._threshold, _MIN_CHANGE)

    def _to_compare_gray(self, frame_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        scale = _COMPARE_WIDTH / max(width, 1)
        new_size = (_COMPARE_WIDTH, max(int(height * scale), 1))
        return cv2.resize(gray, new_size, interpolation=cv2.INTER_AREA)
