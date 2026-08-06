"""Shared value types for the capture module."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CaptureRegion:
    """
    Screen rectangle in absolute desktop coordinates.

    Multi-monitor support later: change ``monitor_index`` and backend mapping only.
    """

    left: int
    top: int
    width: int
    height: int
    monitor_index: int = 1

    def as_mss_dict(self) -> dict[str, int]:
        """Format expected by MSS ``grab``."""
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class CaptureResult:
    """Single frame from a capture backend."""

    frame: np.ndarray
    capture_ms: float
    region: CaptureRegion
