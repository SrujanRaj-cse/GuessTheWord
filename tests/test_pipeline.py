"""Tests for capture event pipeline."""

from __future__ import annotations

import numpy as np

from capture.mock_provider import MockCaptureProvider
from capture.types import CaptureRegion
from config.settings import CaptureSettings
from core.events import EventBus, FrameCapturedEvent, FrameChangedEvent
from core.pipeline import CapturePipeline


def _region() -> CaptureRegion:
    return CaptureRegion(left=0, top=0, width=32, height=16, monitor_index=1)


def test_pipeline_emits_captured_every_tick() -> None:
    bus = EventBus()
    captured: list[FrameCapturedEvent] = []
    bus.subscribe(FrameCapturedEvent, captured.append)

    frames = [np.zeros((16, 32, 3), dtype=np.uint8)]
    provider = MockCaptureProvider(_region(), frames=frames, capture_ms=2.0)
    settings = CaptureSettings(frame_change_threshold=0.02)
    pipeline = CapturePipeline(provider, settings, bus)

    pipeline.process_one_frame()
    pipeline.process_one_frame()
    assert len(captured) == 2


def test_pipeline_skips_unchanged_frame_events() -> None:
    bus = EventBus()
    changed: list[FrameChangedEvent] = []
    bus.subscribe(FrameChangedEvent, changed.append)

    frame = np.zeros((16, 32, 3), dtype=np.uint8)
    provider = MockCaptureProvider(_region(), frames=[frame], capture_ms=1.0)
    settings = CaptureSettings(frame_change_threshold=0.02)
    pipeline = CapturePipeline(provider, settings, bus)

    pipeline.process_one_frame()
    pipeline.process_one_frame()
    assert len(changed) == 1
