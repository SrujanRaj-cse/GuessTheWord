"""Create capture backends from settings."""

from __future__ import annotations

from capture.mss_provider import MssCaptureProvider
from capture.provider import CaptureProvider
from capture.types import CaptureRegion
from config.settings import CaptureSettings


def region_from_settings(settings: CaptureSettings) -> CaptureRegion:
    """Map frozen settings to a ``CaptureRegion``."""
    return CaptureRegion(
        left=settings.left,
        top=settings.top,
        width=settings.width,
        height=settings.height,
        monitor_index=settings.monitor_index,
    )


def create_capture_provider(settings: CaptureSettings) -> CaptureProvider:
    """
    Factory for ``CaptureProvider`` implementations.

    Multi-monitor: add backend selection and monitor mapping here.
    """
    region = region_from_settings(settings)
    backend = settings.backend.lower()
    if backend == "mss":
        return MssCaptureProvider(region)
    raise ValueError(f"Unsupported capture backend: {settings.backend}")
