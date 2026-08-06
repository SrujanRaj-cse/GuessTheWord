"""Capture-stage pipeline: frames and change events only (no OCR)."""

from __future__ import annotations

import logging

from capture.frame_change import FrameChangeDetector
from capture.loop import AdaptiveCaptureLoop
from capture.provider import CaptureProvider
from config.settings import CaptureSettings
from core.events import EventBus, FrameCapturedEvent, FrameChangedEvent

logger = logging.getLogger(__name__)


class CapturePipeline:
    """
    Run capture loop and publish events.

    OCR and solver subscribe to ``FrameChangedEvent`` / ``VisionProcessedEvent`` in later phases.
    """

    def __init__(
        self,
        provider: CaptureProvider,
        settings: CaptureSettings,
        bus: EventBus,
    ) -> None:
        self._loop = AdaptiveCaptureLoop(
            provider,
            preferred_fps=settings.preferred_fps,
            fallback_fps=settings.fallback_fps,
        )
        self._change = FrameChangeDetector(settings.frame_change_threshold)
        self._bus = bus

    def process_one_frame(self) -> None:
        """Capture one frame, publish events, skip OCR when unchanged."""
        result = self._loop.tick()
        stats = self._loop.stats
        self._bus.publish(
            FrameCapturedEvent(
                frame=result.frame,
                capture_ms=result.capture_ms,
                region=result.region,
                target_fps=stats.target_fps,
                achieved_fps=stats.achieved_fps,
            )
        )
        if self._change.has_changed(result.frame):
            logger.debug("Frame changed (capture_ms=%.2f)", result.capture_ms)
            self._bus.publish(
                FrameChangedEvent(
                    frame=result.frame,
                    capture_ms=result.capture_ms,
                    region=result.region,
                )
            )
