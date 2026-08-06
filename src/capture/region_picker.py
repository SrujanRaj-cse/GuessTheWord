"""Draggable screen region selection (one-time setup)."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from capture.mss_provider import monitor_geometry
from capture.types import CaptureRegion

logger = logging.getLogger(__name__)

_MIN_REGION_SIZE = 40
_INSTRUCTION = "Drag to select the game area · Enter to confirm · Esc to cancel"


class _RegionOverlay(QWidget):
    """Fullscreen overlay on one monitor for rectangle selection."""

    def __init__(self, monitor_index: int) -> None:
        super().__init__()
        self._monitor_index = monitor_index
        self._origin = None
        self._selection = QRect()
        self._confirmed: CaptureRegion | None = None

        left, top, width, height = monitor_geometry(monitor_index)
        self.setGeometry(left, top, width, height)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def confirmed_region(self) -> CaptureRegion | None:
        return self._confirmed

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        if not self._selection.isNull():
            painter.setPen(QPen(QColor(0, 200, 120), 2, Qt.PenStyle.SolidLine))
            painter.fillRect(self._selection, QColor(0, 200, 120, 40))
            painter.drawRect(self._selection)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(20, 30, _INSTRUCTION)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._selection = QRect(self._origin, self._origin)
            self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._origin is not None:
            self._selection = QRect(self._origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = None

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()
            self.close()

    def _confirm_selection(self) -> None:
        if self._selection.width() < _MIN_REGION_SIZE or self._selection.height() < _MIN_REGION_SIZE:
            logger.warning("Selection too small; draw a larger rectangle.")
            return
        geo = self.geometry()
        self._confirmed = CaptureRegion(
            left=geo.left() + self._selection.left(),
            top=geo.top() + self._selection.top(),
            width=self._selection.width(),
            height=self._selection.height(),
            monitor_index=self._monitor_index,
        )


def pick_capture_region(monitor_index: int = 1) -> CaptureRegion | None:
    """
    Block until the user confirms or cancels region selection.

    Returns:
        Selected region in absolute screen coordinates, or ``None`` if cancelled.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    overlay = _RegionOverlay(monitor_index)
    overlay.show()
    app.exec()
    return overlay.confirmed_region()
