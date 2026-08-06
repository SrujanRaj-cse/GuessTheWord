"""Debug preview for live capture (Phase 2)."""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.events import EventBus, FrameCapturedEvent, FrameChangedEvent


class CaptureDebugWindow(QWidget):
    """Show captured frame, FPS, and capture timing."""

    def __init__(self, bus: EventBus) -> None:
        super().__init__()
        self.setWindowTitle("GuessWord AI — Capture Debug")
        self._image_label = QLabel("Waiting for frames…")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label = QLabel("")
        self._change_label = QLabel("Frame changed: —")
        layout = QVBoxLayout(self)
        layout.addWidget(self._image_label)
        layout.addWidget(self._stats_label)
        layout.addWidget(self._change_label)
        self.resize(640, 480)

        bus.subscribe(FrameCapturedEvent, self._on_frame)
        bus.subscribe(FrameChangedEvent, self._on_changed)

    def _on_frame(self, event: FrameCapturedEvent) -> None:
        pixmap = QPixmap.fromImage(_bgr_to_qimage(event.frame))
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._stats_label.setText(
            f"Target FPS: {event.target_fps}  ·  "
            f"Avg FPS: {event.achieved_fps:.1f}  ·  "
            f"Capture: {event.capture_ms:.2f} ms"
        )

    def _on_changed(self, _event: FrameChangedEvent) -> None:
        self._change_label.setText("Frame changed: yes (OCR would run)")


def _bgr_to_qimage(frame_bgr: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    return QImage(
        rgb.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    ).copy()
