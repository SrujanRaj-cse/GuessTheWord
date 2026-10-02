"""Floating prediction overlay."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from config.settings import OverlaySettings
from core.events import EventBus, PatternChangedEvent, ResultChangedEvent


class _OverlayEvents(QObject):
    """Qt signal bridge so worker-thread events update widgets safely."""

    pattern = Signal(object)
    results = Signal(object)


class PredictionOverlay(QWidget):
    """Small translucent, always-on-top, draggable prediction window."""

    def __init__(self, bus: EventBus, settings: OverlaySettings) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self._drag_offset: QPoint | None = None
        self._events = _OverlayEvents(self)
        self._events.pattern.connect(self._show_pattern)
        self._events.results.connect(self._show_results)
        self._pattern_label = QLabel("Waiting for a word…")
        self._pattern_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pattern_label.setStyleSheet("font-weight: 700")
        self._confidence_label = QLabel("")
        self._confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._results_label = QLabel("Predictions will appear here")
        self._results_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._results_label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._pattern_label)
        layout.addWidget(self._confidence_label)
        layout.addWidget(self._results_label)
        self.resize(settings.width, settings.height)
        self.setWindowOpacity(max(0.2, min(settings.opacity, 1.0)))
        self.setStyleSheet(
            "QWidget { background: #20242b; color: #f4f6f8; border: 1px solid #59616d; "
            f"border-radius: 8px; font-size: {max(8, settings.font_size_pt)}pt; }} "
            "QLabel { padding: 4px; }"
        )
        bus.subscribe(PatternChangedEvent, lambda event: self._events.pattern.emit(event))
        bus.subscribe(ResultChangedEvent, lambda event: self._events.results.emit(event))

    def _show_pattern(self, event: PatternChangedEvent) -> None:
        self._pattern_label.setText(event.pattern or "No word detected")
        self._confidence_label.setText(
            f"OCR confidence: {event.confidence:.0%}" if event.pattern else ""
        )

    def _show_results(self, event: ResultChangedEvent) -> None:
        if not event.candidates:
            self._results_label.setText("No matching words yet")
            return
        lines = [f"{item['word']}   {item['score']:.0%}" for item in event.candidates[:5]]
        self._results_label.setText("\n".join(lines))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        event.accept()
