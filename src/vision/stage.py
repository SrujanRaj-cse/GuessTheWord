"""Subscribe to capture events and run the vision pipeline."""

from __future__ import annotations

import logging
import time

from config.settings import VisionSettings
from core.events import EventBus, FrameChangedEvent
from vision.events import VisionProcessedEvent
from vision.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class VisionStage:
    """
    Run ``ImageProcessor`` on ``FrameChangedEvent`` and publish results.

    OCR (Phase 4) should subscribe to ``VisionProcessedEvent``, not raw frames.
    """

    def __init__(self, bus: EventBus, settings: VisionSettings) -> None:
        self._bus = bus
        self._processor = ImageProcessor(settings)
        bus.subscribe(FrameChangedEvent, self._on_frame_changed)

    def _on_frame_changed(self, event: FrameChangedEvent) -> None:
        start = time.perf_counter()
        result = self._processor.process(event.frame)
        process_ms = (time.perf_counter() - start) * 1000.0
        logger.debug("Vision processed frame in %.2f ms", process_ms)
        self._bus.publish(
            VisionProcessedEvent(
                result=result,
                capture_ms=event.capture_ms,
                region=event.region,
                process_ms=process_ms,
            )
        )
