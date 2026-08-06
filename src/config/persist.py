"""Persist configuration updates to TOML."""

from __future__ import annotations

import logging
from pathlib import Path

import tomlkit

from capture.types import CaptureRegion
from config.settings import CaptureSettings, _DEFAULT_CONFIG_RELATIVE

logger = logging.getLogger(__name__)


def default_config_path(project_root: Path) -> Path:
    """Path to ``config/default.toml`` under the project root."""
    return project_root / _DEFAULT_CONFIG_RELATIVE


def save_capture_settings(
    project_root: Path,
    capture: CaptureSettings,
    config_path: Path | None = None,
) -> Path:
    """
    Write capture fields into the project TOML config (creates file if missing).

    Args:
        project_root: Repository / app root directory.
        capture: Capture section to persist.
        config_path: Override config file path.

    Returns:
        Path to the written config file.
    """
    path = config_path or default_config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file():
        document = tomlkit.parse(path.read_text(encoding="utf-8"))
    else:
        document = tomlkit.document()

    section = document.get("capture")
    if section is None:
        section = tomlkit.table()
        document["capture"] = section

    section["monitor_index"] = capture.monitor_index
    section["left"] = capture.left
    section["top"] = capture.top
    section["width"] = capture.width
    section["height"] = capture.height
    section["region_selected"] = capture.region_selected
    section["preferred_fps"] = capture.preferred_fps
    section["fallback_fps"] = capture.fallback_fps
    section["frame_change_threshold"] = capture.frame_change_threshold
    section["backend"] = capture.backend

    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    logger.info("Saved capture region to %s", path)
    return path


def capture_settings_from_region(
    region: CaptureRegion,
    preferred_fps: int,
    fallback_fps: int,
    frame_change_threshold: float,
) -> CaptureSettings:
    """Build ``CaptureSettings`` after region picker confirmation."""
    return CaptureSettings(
        monitor_index=region.monitor_index,
        left=region.left,
        top=region.top,
        width=region.width,
        height=region.height,
        region_selected=True,
        preferred_fps=preferred_fps,
        fallback_fps=fallback_fps,
        frame_change_threshold=frame_change_threshold,
        backend="mss",
    )
