"""Convert OpenCV arrays to Qt images for debug preview."""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QImage


def array_to_qimage(frame: np.ndarray) -> QImage:
    """Build a ``QImage`` from BGR or single-channel uint8 arrays."""
    if frame.ndim == 2:
        height, width = frame.shape
        bytes_per_line = width
        return QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8,
        ).copy()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    return QImage(
        rgb.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    ).copy()
