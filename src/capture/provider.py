"""Capture backend abstraction."""

from __future__ import annotations

from typing import Protocol

from capture.types import CaptureResult


class CaptureProvider(Protocol):
    """Pluggable screen capture (MSS today; other backends later)."""

    def grab(self) -> CaptureResult:
        """Capture one frame from the configured region."""
        ...
