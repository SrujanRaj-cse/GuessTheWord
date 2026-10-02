"""Draggable screen region selection (one-time setup)."""

from __future__ import annotations

import logging
import sys

import numpy as np
from PySide6.QtCore import QEventLoop, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from capture.mss_provider import monitor_geometry
from capture.types import CaptureRegion
from debug.qimage_utils import array_to_qimage

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


class _FrameRegionPicker(QWidget):
    """Select a game rectangle on a still preview of a portal-shared screen."""

    def __init__(self, frame_bgr: np.ndarray, monitor_index: int) -> None:
        super().__init__(None, Qt.WindowType.WindowStaysOnTopHint)
        self._frame_height, self._frame_width = frame_bgr.shape[:2]
        self._pixmap = QPixmap.fromImage(array_to_qimage(frame_bgr))
        self._monitor_index = monitor_index
        self._selection = QRect()
        self._origin = None
        self._confirmed: CaptureRegion | None = None
        self._message = "Drag over the game area · Enter to confirm · Esc to cancel"
        self._loop = QEventLoop(self)
        self.setWindowTitle("Select the game area from the shared screen")
        self.resize(min(self._frame_width, 1200), min(self._frame_height, 800))

    def choose(self) -> CaptureRegion | None:
        """Show the preview picker and return a stream-relative rectangle."""
        self.showMaximized()
        self._loop.exec()
        return self._confirmed

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(24, 27, 32))
        image_rect = self._image_rect()
        scaled = self._pixmap.scaled(
            image_rect.size().toSize(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(image_rect.topLeft(), scaled)
        if not self._selection.isNull():
            painter.setPen(QPen(QColor(0, 220, 130), 3))
            painter.fillRect(self._selection, QColor(0, 220, 130, 50))
            painter.drawRect(self._selection)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(20, 30, self._message)

    def _image_rect(self) -> QRectF:
        scaled = self._pixmap.size().scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio
        )
        left = (self.width() - scaled.width()) / 2
        top = (self.height() - scaled.height()) / 2
        return QRectF(left, top, scaled.width(), scaled.height())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            if self._image_rect().contains(point):
                self._origin = point
                self._selection = QRect(point, point)
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
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._loop.quit()
        event.accept()

    def _confirm_selection(self) -> None:
        selection = self._selection.intersected(self._image_rect().toAlignedRect())
        if selection.width() < _MIN_REGION_SIZE or selection.height() < _MIN_REGION_SIZE:
            self._message = "Selection too small; drag a larger rectangle. · Esc to cancel"
            self.update()
            return
        image_rect = self._image_rect()
        scale_x = self._frame_width / image_rect.width()
        scale_y = self._frame_height / image_rect.height()
        left = round((selection.left() - image_rect.left()) * scale_x)
        top = round((selection.top() - image_rect.top()) * scale_y)
        right = round((selection.right() + 1 - image_rect.left()) * scale_x)
        bottom = round((selection.bottom() + 1 - image_rect.top()) * scale_y)
        self._confirmed = CaptureRegion(
            left=left,
            top=top,
            width=right - left,
            height=bottom - top,
            monitor_index=self._monitor_index,
        )
        self.close()


def pick_capture_region_from_frame(
    frame_bgr: np.ndarray,
    monitor_index: int = 1,
) -> CaptureRegion | None:
    """Select a region on a preview after the Wayland portal shares a screen."""
    picker = _FrameRegionPicker(frame_bgr, monitor_index)
    return picker.choose()
