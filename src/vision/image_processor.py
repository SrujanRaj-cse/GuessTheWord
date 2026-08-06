"""Grayscale conversion, adaptive threshold, and noise removal for OCR."""

from __future__ import annotations

import cv2
import numpy as np

from config.settings import VisionSettings
from vision.types import VisionProcessResult

_MIN_BLOCK_SIZE = 3
_MORPH_KERNEL_SIZE = 2


class ImageProcessor:
    """Pure OpenCV preprocessing; no OCR or screen I/O."""

    def __init__(self, settings: VisionSettings) -> None:
        self._settings = settings

    def process(self, frame_bgr: np.ndarray) -> VisionProcessResult:
        """
        Run the vision pipeline on one BGR capture frame.

        Args:
            frame_bgr: Raw capture in BGR channel order.

        Returns:
            Stage images including final ``processed`` binary output.
        """
        original = self._apply_crop(frame_bgr)
        grayscale = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        thresholded = self._adaptive_threshold(grayscale)
        processed = self._remove_noise(thresholded)
        return VisionProcessResult(
            original_bgr=original.copy(),
            grayscale=grayscale.copy(),
            thresholded=thresholded.copy(),
            processed=processed.copy(),
        )

    def _apply_crop(self, frame_bgr: np.ndarray) -> np.ndarray:
        margin = self._settings.crop_margin_px
        if margin <= 0:
            return frame_bgr.copy()
        height, width = frame_bgr.shape[:2]
        if height <= 2 * margin or width <= 2 * margin:
            return frame_bgr.copy()
        return frame_bgr[margin : height - margin, margin : width - margin].copy()

    def _adaptive_threshold(self, grayscale: np.ndarray) -> np.ndarray:
        block_size = self._settings.threshold_block_size
        if block_size < _MIN_BLOCK_SIZE:
            block_size = _MIN_BLOCK_SIZE
        if block_size % 2 == 0:
            block_size += 1
        return cv2.adaptiveThreshold(
            grayscale,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=block_size,
            C=self._settings.threshold_c,
        )

    def _remove_noise(self, binary: np.ndarray) -> np.ndarray:
        kernel = np.ones((_MORPH_KERNEL_SIZE, _MORPH_KERNEL_SIZE), dtype=np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
