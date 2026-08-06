"""Tests for vision event wiring."""

from __future__ import annotations

import numpy as np

from capture.types import CaptureRegion
from config.settings import VisionSettings
from core.events import EventBus, FrameChangedEvent
from vision.events import VisionProcessedEvent
from vision.stage import VisionStage


def test_vision_stage_publishes_on_frame_changed() -> None:
    bus = EventBus()
    VisionStage(bus, VisionSettings())
    processed: list[VisionProcessedEvent] = []
    bus.subscribe(VisionProcessedEvent, processed.append)

    frame = np.zeros((24, 48, 3), dtype=np.uint8)
    frame[8:16, 12:36] = 255
    region = CaptureRegion(left=0, top=0, width=48, height=24)
    bus.publish(
        FrameChangedEvent(frame=frame, capture_ms=1.5, region=region),
    )

    assert len(processed) == 1
    assert processed[0].process_ms >= 0
    assert processed[0].result.processed.shape[0] > 0
