"""Qt ScreenCast provider for Wayland and XDG Desktop Portal sessions."""

from __future__ import annotations

import logging
import time

import cv2
import numpy as np
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaCaptureSession, QScreenCapture, QVideoFrame, QVideoSink

from capture.types import CaptureRegion, CaptureResult

logger = logging.getLogger(__name__)
_FRAME_WAIT_MS = 30_000


class QtScreenCaptureProvider:
    """Read portal-approved screen frames and crop to the saved game region."""

    def __init__(self, region: CaptureRegion | None = None) -> None:
        self._region = region
        self._session = QMediaCaptureSession()
        self._screen_capture = QScreenCapture()
        self._video_sink = QVideoSink()
        self._session.setScreenCapture(self._screen_capture)
        self._session.setVideoSink(self._video_sink)
        self._screen_capture.errorOccurred.connect(self._on_capture_error)
        self._video_sink.videoFrameChanged.connect(self._on_video_frame)
        self._latest_frame: np.ndarray | None = None
        self._capture_error: str | None = None
        self._wait_loop: QEventLoop | None = None
        logger.info("Requesting screen sharing permission from the desktop portal")
        self._screen_capture.start()

    def _on_capture_error(self, _error: QScreenCapture.Error, message: str) -> None:
        self._capture_error = message or "Screen capture failed"
        if self._wait_loop is not None:
            self._wait_loop.quit()

    def _on_video_frame(self, frame: QVideoFrame) -> None:
        image = frame.toImage()
        if image.isNull():
            return
        image = image.convertToFormat(QImage.Format.Format_RGB888)
        height, width = image.height(), image.width()
        raw = np.frombuffer(image.bits(), dtype=np.uint8, count=image.sizeInBytes())
        rgb = raw.reshape(height, image.bytesPerLine())[:, : width * 3]
        rgb = rgb.reshape(height, width, 3).copy()
        self._latest_frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        if self._wait_loop is not None:
            self._wait_loop.quit()

    def grab(self) -> CaptureResult:
        """Return the newest approved screen frame cropped to the saved region."""
        start = time.perf_counter()
        frame = self.grab_screen()
        if self._region is None:
            raise RuntimeError("Select a game region before starting capture.")
        frame = self._crop_region(frame)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return CaptureResult(frame=frame, capture_ms=elapsed_ms, region=self._region)

    def grab_screen(self) -> np.ndarray:
        """Return a copy of the entire screen stream selected in the portal."""
        if self._latest_frame is None:
            if self._capture_error is not None:
                raise RuntimeError(
                    f"Wayland screen capture failed: {self._capture_error}. Check that the "
                    "desktop ScreenCast portal and PipeWire are available."
                )
            self._wait_for_first_frame()
        if self._latest_frame is None:
            detail = self._capture_error or "No screen frame arrived from the portal"
            raise RuntimeError(
                f"Wayland screen capture failed: {detail}. Accept the screen-share prompt and "
                "select the monitor containing the game."
            )
        return self._latest_frame.copy()

    def set_region(self, region: CaptureRegion) -> None:
        """Set a rectangle whose coordinates are relative to the shared stream."""
        self._region = region

    def _wait_for_first_frame(self) -> None:
        self._wait_loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(self._wait_loop.quit)
        timeout.start(_FRAME_WAIT_MS)
        self._wait_loop.exec()
        timeout.stop()
        self._wait_loop = None

    def _crop_region(self, frame: np.ndarray) -> np.ndarray:
        if self._region is None:
            raise RuntimeError("No game region has been selected.")
        frame_height, frame_width = frame.shape[:2]
        left, top = self._region.left, self._region.top
        width, height = self._region.width, self._region.height
        cropped = frame[top : top + height, left : left + width]
        if cropped.size == 0 or cropped.shape[:2] != (height, width):
            raise RuntimeError(
                "The shared screen does not contain the saved region. Choose the same monitor "
                "in the screen-sharing prompt, then run `python main.py --pick-region`."
            )
        return cropped.copy()

    def close(self) -> None:
        """Stop the portal stream and release Qt Multimedia objects."""
        self._screen_capture.stop()
