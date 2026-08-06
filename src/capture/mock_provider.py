"""In-memory capture provider for tests."""

from __future__ import annotations

import time

import numpy as np

from capture.types import CaptureRegion, CaptureResult


class MockCaptureProvider:
    """Return a fixed or scripted sequence of frames."""

    def __init__(
        self,
        region: CaptureRegion,
        frames: list[np.ndarray] | None = None,
        capture_ms: float = 1.0,
    ) -> None:
        self._region = region
        self._frames = frames or [_blank_frame(region)]
        self._index = 0
        self._capture_ms = capture_ms

    def grab(self) -> CaptureResult:
        frame = self._frames[self._index % len(self._frames)]
        self._index += 1
        time.sleep(0)
        return CaptureResult(frame=frame.copy(), capture_ms=self._capture_ms, region=self._region)


def _blank_frame(region: CaptureRegion) -> np.ndarray:
    return np.zeros((max(region.height, 1), max(region.width, 1), 3), dtype=np.uint8)
