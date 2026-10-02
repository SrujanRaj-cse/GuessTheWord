"""Run OCR asynchronously after vision preprocessing."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock

import numpy as np

from config.settings import OCRSettings
from core.events import EventBus, PatternChangedEvent
from ocr.provider import OCRProvider, OCRResult, PaddleOCRProvider
from vision.events import VisionProcessedEvent

logger = logging.getLogger(__name__)


class OCRStage:
    """Convert processed images to patterns without blocking the Qt event loop."""

    def __init__(
        self,
        bus: EventBus,
        settings: OCRSettings,
        provider: OCRProvider | None = None,
    ) -> None:
        self._bus = bus
        self._settings = settings
        self._provider = provider or PaddleOCRProvider(settings.lang, settings.use_gpu)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="guessword-ocr")
        self._pending = False
        self._failed = False
        self._closed = False
        self._latest_image: np.ndarray | None = None
        self._lock = Lock()
        bus.subscribe(VisionProcessedEvent, self._on_vision)

    def _on_vision(self, event: VisionProcessedEvent) -> None:
        image = event.result.processed.copy()
        with self._lock:
            if self._failed or self._closed:
                return
            if self._pending:
                self._latest_image = image
                return
            self._pending = True
        self._submit(image)

    def _submit(self, image: np.ndarray) -> None:
        with self._lock:
            if self._closed:
                self._pending = False
                return
            future = self._executor.submit(self._provider.recognize, image)
        future.add_done_callback(self._on_recognized)

    def _on_recognized(self, future: Future[OCRResult]) -> None:
        try:
            result = future.result()
        except Exception:
            with self._lock:
                if self._closed:
                    self._pending = False
                    return
                self._failed = True
                self._pending = False
                self._latest_image = None
            logger.exception("OCR recognition failed")
            self._bus.publish(PatternChangedEvent(pattern="", confidence=0.0))
            return
        with self._lock:
            if self._closed:
                self._pending = False
                return
            latest_image = self._latest_image
            self._latest_image = None
            if latest_image is None:
                self._pending = False
        if latest_image is not None:
            self._submit(latest_image)
            return
        pattern = result.pattern if result.confidence >= self._settings.min_confidence else ""
        logger.debug("OCR pattern=%r confidence=%.3f", pattern, result.confidence)
        self._bus.publish(PatternChangedEvent(pattern=pattern, confidence=result.confidence))

    def close(self) -> None:
        """Stop accepting images and cancel recognition jobs not yet started."""
        with self._lock:
            self._closed = True
            self._latest_image = None
        self._executor.shutdown(wait=False, cancel_futures=True)
