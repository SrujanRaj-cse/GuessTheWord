"""Adaptive-FPS capture loop with timing metrics."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from capture.provider import CaptureProvider
from capture.types import CaptureResult
from utils.metrics import RollingAverage

logger = logging.getLogger(__name__)

_FPS_WINDOW = 30
_UNDERPERFORM_WINDOWS_BEFORE_FALLBACK = 3
_RECOVER_WINDOWS_BEFORE_BOOST = 5
_FPS_TOLERANCE = 0.9


@dataclass
class CaptureLoopStats:
    """Latest capture-loop measurements (debug / tuning)."""

    target_fps: int
    achieved_fps: float
    last_capture_ms: float
    avg_capture_ms: float


class AdaptiveCaptureLoop:
    """
    Grab frames at ``preferred_fps``, falling back to ``fallback_fps`` if needed.

    Does not perform OCR or image processing beyond calling the provider.
    """

    def __init__(
        self,
        provider: CaptureProvider,
        preferred_fps: int = 60,
        fallback_fps: int = 30,
    ) -> None:
        self._provider = provider
        self._preferred_fps = preferred_fps
        self._fallback_fps = fallback_fps
        self._target_fps = preferred_fps
        self._capture_times = RollingAverage(_FPS_WINDOW)
        self._loop_times = RollingAverage(_FPS_WINDOW)
        self._underperform_streak = 0
        self._recover_streak = 0
        self._last_result: CaptureResult | None = None

    @property
    def stats(self) -> CaptureLoopStats:
        avg_loop = self._loop_times.mean_seconds()
        achieved = 1.0 / avg_loop if avg_loop > 0 else 0.0
        return CaptureLoopStats(
            target_fps=self._target_fps,
            achieved_fps=achieved,
            last_capture_ms=self._last_result.capture_ms if self._last_result else 0.0,
            avg_capture_ms=self._capture_times.mean_ms(),
        )

    def tick(self) -> CaptureResult:
        """Capture one frame and sleep to match the current FPS target."""
        loop_start = time.perf_counter()
        result = self._provider.grab()
        self._last_result = result
        self._capture_times.add_ms(result.capture_ms)

        elapsed = time.perf_counter() - loop_start
        self._loop_times.add_seconds(elapsed)
        self._adjust_fps_target()
        self._sleep_for_fps(elapsed)
        return result

    def _adjust_fps_target(self) -> None:
        avg_loop = self._loop_times.mean_seconds()
        if avg_loop <= 0:
            return
        achieved = 1.0 / avg_loop
        target = self._target_fps

        if self._target_fps == self._preferred_fps:
            if achieved < target * _FPS_TOLERANCE:
                self._underperform_streak += 1
            else:
                self._underperform_streak = 0
            if self._underperform_streak >= _UNDERPERFORM_WINDOWS_BEFORE_FALLBACK:
                logger.warning(
                    "Capture below %s FPS (%.1f); falling back to %s FPS",
                    self._preferred_fps,
                    achieved,
                    self._fallback_fps,
                )
                self._target_fps = self._fallback_fps
                self._underperform_streak = 0
                self._recover_streak = 0
        elif achieved >= self._preferred_fps * _FPS_TOLERANCE:
            self._recover_streak += 1
            if self._recover_streak >= _RECOVER_WINDOWS_BEFORE_BOOST:
                logger.info("Capture recovered; targeting %s FPS again", self._preferred_fps)
                self._target_fps = self._preferred_fps
                self._recover_streak = 0

    def _sleep_for_fps(self, elapsed_seconds: float) -> None:
        frame_budget = 1.0 / self._target_fps
        remaining = frame_budget - elapsed_seconds
        if remaining > 0:
            time.sleep(remaining)
