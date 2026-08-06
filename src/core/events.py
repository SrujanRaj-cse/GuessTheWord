"""Application events for the capture → OCR → solver pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TypeVar

import numpy as np

from capture.types import CaptureRegion

T = TypeVar("T")


@dataclass(frozen=True)
class FrameCapturedEvent:
    """Emitted every capture tick (debug preview, FPS)."""

    frame: np.ndarray
    capture_ms: float
    region: CaptureRegion
    target_fps: int
    achieved_fps: float


@dataclass(frozen=True)
class FrameChangedEvent:
    """Emitted when the frame differs enough from the previous one (OCR trigger)."""

    frame: np.ndarray
    capture_ms: float
    region: CaptureRegion


@dataclass(frozen=True)
class PatternChangedEvent:
    """Future: OCR produced a new letter pattern."""

    pattern: str
    confidence: float


@dataclass(frozen=True)
class ResultChangedEvent:
    """Future: solver produced new ranked guesses."""

    candidates: list[dict[str, float]] = field(default_factory=list)


Handler = Callable[[T], None]


class EventBus:
    """Simple synchronous pub/sub for pipeline stages."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = {}

    def subscribe(self, event_type: type[T], handler: Handler[T]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: T) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)
