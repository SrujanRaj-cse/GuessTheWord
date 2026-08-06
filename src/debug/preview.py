"""Debug preview for live capture and vision preprocessing (Phases 2–3)."""

from __future__ import annotations

from enum import Enum

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from core.events import EventBus, FrameCapturedEvent, FrameChangedEvent
from debug.qimage_utils import array_to_qimage
from vision.events import VisionProcessedEvent
from vision.types import VisionProcessResult


class PreviewMode(str, Enum):
    """Which pipeline stage to show in the debug image pane."""

    ORIGINAL = "Original frame"
    GRAYSCALE = "Grayscale"
    THRESHOLD = "Thresholded"
    PROCESSED = "Final processed"


class CaptureDebugWindow(QWidget):
    """Show captured frames, vision stages, FPS, and change detection."""

    def __init__(self, bus: EventBus) -> None:
        super().__init__()
        self.setWindowTitle("GuessWord AI — Capture & Vision Debug")
        self._mode = PreviewMode.ORIGINAL
        self._latest_capture: np.ndarray | None = None
        self._latest_vision: VisionProcessResult | None = None
        self._vision_process_ms: float | None = None

        self._image_label = QLabel("Waiting for frames…")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label = QLabel("")
        self._change_label = QLabel("Frame changed: —")
        self._vision_label = QLabel("Vision: —")

        self._mode_selector = QComboBox()
        for mode in PreviewMode:
            self._mode_selector.addItem(mode.value, mode)
        self._mode_selector.currentIndexChanged.connect(self._on_mode_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self._mode_selector)
        layout.addWidget(self._image_label)
        layout.addWidget(self._stats_label)
        layout.addWidget(self._change_label)
        layout.addWidget(self._vision_label)
        self.resize(640, 520)

        bus.subscribe(FrameCapturedEvent, self._on_frame)
        bus.subscribe(FrameChangedEvent, self._on_changed)
        bus.subscribe(VisionProcessedEvent, self._on_vision)

    def _on_mode_changed(self, _index: int) -> None:
        mode = self._mode_selector.currentData()
        if isinstance(mode, PreviewMode):
            self._mode = mode
        self._refresh_image()

    def _on_frame(self, event: FrameCapturedEvent) -> None:
        self._latest_capture = event.frame
        self._stats_label.setText(
            f"Target FPS: {event.target_fps}  ·  "
            f"Avg FPS: {event.achieved_fps:.1f}  ·  "
            f"Capture: {event.capture_ms:.2f} ms"
        )
        if self._mode == PreviewMode.ORIGINAL:
            self._show_array(event.frame)

    def _on_changed(self, _event: FrameChangedEvent) -> None:
        self._change_label.setText("Frame changed: yes (vision runs)")

    def _on_vision(self, event: VisionProcessedEvent) -> None:
        self._latest_vision = event.result
        self._vision_process_ms = event.process_ms
        self._vision_label.setText(f"Vision: {event.process_ms:.2f} ms")
        if self._mode != PreviewMode.ORIGINAL:
            self._refresh_image()

    def _refresh_image(self) -> None:
        array = self._array_for_mode(self._mode)
        if array is not None:
            self._show_array(array)

    def _array_for_mode(self, mode: PreviewMode) -> np.ndarray | None:
        if mode == PreviewMode.ORIGINAL:
            return self._latest_capture
        if self._latest_vision is None:
            return self._latest_capture
        if mode == PreviewMode.GRAYSCALE:
            return self._latest_vision.grayscale
        if mode == PreviewMode.THRESHOLD:
            return self._latest_vision.thresholded
        return self._latest_vision.processed

    def _show_array(self, array: np.ndarray) -> None:
        pixmap = QPixmap.fromImage(array_to_qimage(array))
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
