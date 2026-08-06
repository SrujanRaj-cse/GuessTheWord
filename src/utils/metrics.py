"""Rolling timing averages for debug metrics."""

from __future__ import annotations

from collections import deque


class RollingAverage:
    """Fixed-size window mean for milliseconds or seconds."""

    def __init__(self, window_size: int) -> None:
        self._values: deque[float] = deque(maxlen=window_size)

    def add_ms(self, value_ms: float) -> None:
        self._values.append(value_ms)

    def add_seconds(self, value_seconds: float) -> None:
        self._values.append(value_seconds * 1000.0)

    def mean_ms(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def mean_seconds(self) -> float:
        return self.mean_ms() / 1000.0
