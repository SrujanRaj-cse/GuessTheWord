"""Vision-stage events (kept separate from ``core.events`` to avoid import cycles)."""

from __future__ import annotations

from dataclasses import dataclass

from capture.types import CaptureRegion
from vision.types import VisionProcessResult


@dataclass(frozen=True)
class VisionProcessedEvent:
    """Published after preprocessing when the capture frame changed."""

    result: VisionProcessResult
    capture_ms: float
    region: CaptureRegion
    process_ms: float
