"""MSS-based capture for a single monitor region."""

from __future__ import annotations

import logging
import time

import mss
import numpy as np

from capture.provider import CaptureProvider
from capture.types import CaptureRegion, CaptureResult

logger = logging.getLogger(__name__)

_BGR_CHANNELS = 3


class MssCaptureProvider:
    """Capture a fixed region using python-mss."""

    def __init__(self, region: CaptureRegion) -> None:
        self._region = region
        self._sct = mss.mss()

    @property
    def region(self) -> CaptureRegion:
        return self._region

    def close(self) -> None:
        """Release MSS resources."""
        self._sct.close()

    def grab(self) -> CaptureResult:
        start = time.perf_counter()
        shot = self._sct.grab(self._region.as_mss_dict())
        frame = np.asarray(shot, dtype=np.uint8)
        frame = frame[:, :, :_BGR_CHANNELS].copy()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return CaptureResult(frame=frame, capture_ms=elapsed_ms, region=self._region)


def monitor_geometry(monitor_index: int) -> tuple[int, int, int, int]:
    """
    Return ``(left, top, width, height)`` for an MSS monitor index.

    Index ``0`` is the virtual full desktop; ``1+`` are physical monitors.
    """
    with mss.mss() as sct:
        if monitor_index < 0 or monitor_index >= len(sct.monitors):
            raise ValueError(f"Invalid monitor_index: {monitor_index}")
        mon = sct.monitors[monitor_index]
        return mon["left"], mon["top"], mon["width"], mon["height"]
