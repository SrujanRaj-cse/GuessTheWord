"""Detect underscore blank slots on binary vision output."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

_MIN_COMPONENT_AREA = 16
_MAX_BACKGROUND_AREA_RATIO = 0.35
_UNDERSCORE_MAX_HEIGHT = 10
_UNDERSCORE_MIN_WIDTH = 8
_UNDERSCORE_MIN_ASPECT = 2.5


@dataclass(frozen=True)
class BlankDetectionResult:
    """Underscore run detected left-to-right on the binary image."""

    blanks: str
    confidence: float
    component_count: int


class BlankDetector:
    """
    Find horizontal underscore-like components on ``processed`` binary images.

    Expects uint8 single-channel data with ink at 0 and background at 255, or the inverse.
    """

    def detect(self, processed_binary: np.ndarray) -> BlankDetectionResult:
        """
        Count blank indicators in reading order.

        Args:
            processed_binary: Grayscale/binary image from ``VisionProcessResult.processed``.

        Returns:
            Blank string of ``_`` characters and a heuristic confidence score.
        """
        if processed_binary.ndim != 2:
            raise ValueError("BlankDetector expects a single-channel binary image")
        ink_mask = self._ink_mask(processed_binary)
        components = self._underscore_components(ink_mask, processed_binary.shape)
        blanks = "_" * len(components)
        confidence = self._confidence(components, ink_mask)
        return BlankDetectionResult(
            blanks=blanks,
            confidence=confidence,
            component_count=len(components),
        )

    def _ink_mask(self, binary: np.ndarray) -> np.ndarray:
        """Return uint8 mask where ink pixels are 255."""
        if binary.dtype != np.uint8:
            raise TypeError("Expected uint8 binary image")
        mean_value = float(np.mean(binary))
        if mean_value > 127:
            return (255 - binary).astype(np.uint8)
        return binary.copy()

    def _underscore_components(
        self,
        ink_mask: np.ndarray,
        shape: tuple[int, ...],
    ) -> list[tuple[int, int, int, int]]:
        """Return bounding boxes (x, y, w, h) for underscore-shaped ink, sorted by x."""
        height, width = shape[:2]
        max_background_area = int(height * width * _MAX_BACKGROUND_AREA_RATIO)
        binary = (ink_mask > 127).astype(np.uint8)
        count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )
        boxes: list[tuple[int, int, int, int]] = []
        for index in range(1, count):
            x, y, box_width, box_height, area = stats[index]
            if area < _MIN_COMPONENT_AREA:
                continue
            if area > max_background_area:
                continue
            if box_height > _UNDERSCORE_MAX_HEIGHT:
                continue
            if box_width < _UNDERSCORE_MIN_WIDTH:
                continue
            aspect = box_width / max(box_height, 1)
            if aspect < _UNDERSCORE_MIN_ASPECT:
                continue
            boxes.append((int(x), int(y), int(box_width), int(box_height)))
        boxes.sort(key=lambda item: item[0])
        return boxes

    def _confidence(
        self,
        components: list[tuple[int, int, int, int]],
        ink_mask: np.ndarray,
    ) -> float:
        if not components:
            return 0.0
        total_ink = float(np.count_nonzero(ink_mask))
        if total_ink <= 0:
            return 0.0
        underscore_ink = 0.0
        for x, y, box_width, box_height in components:
            region = ink_mask[y : y + box_height, x : x + box_width]
            underscore_ink += float(np.count_nonzero(region))
        ratio = underscore_ink / total_ink
        return min(1.0, max(0.1, ratio * 2.0))
