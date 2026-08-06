"""GuessWord AI — capture pipeline entry (Phase 2)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from capture.factory import create_capture_provider  # noqa: E402
from capture.region_picker import pick_capture_region  # noqa: E402
from config.persist import (  # noqa: E402
    capture_settings_from_region,
    default_config_path,
    save_capture_settings,
)
from config.settings import clear_settings_cache, get_settings, load_settings  # noqa: E402
from core.events import EventBus, FrameChangedEvent  # noqa: E402
from core.pipeline import CapturePipeline  # noqa: E402
from debug.preview import CaptureDebugWindow  # noqa: E402
from utils.logging_config import configure_logging  # noqa: E402

logger = logging.getLogger(__name__)

_TIMER_MS = 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GuessWord AI")
    parser.add_argument(
        "--pick-region",
        action="store_true",
        help="Force the draggable region picker and save to config/default.toml",
    )
    return parser.parse_args()


def _ensure_region(args: argparse.Namespace) -> None:
    settings = load_settings(project_root=_PROJECT_ROOT)
    if settings.capture.region_selected and not args.pick_region:
        return

    logger.info("Open the region picker: drag a rectangle, Enter to save, Esc to cancel")
    region = pick_capture_region(settings.capture.monitor_index)
    if region is None:
        logger.error("Region selection cancelled")
        raise SystemExit(1)

    capture = capture_settings_from_region(
        region,
        preferred_fps=settings.capture.preferred_fps,
        fallback_fps=settings.capture.fallback_fps,
        frame_change_threshold=settings.capture.frame_change_threshold,
    )
    save_capture_settings(_PROJECT_ROOT, capture, default_config_path(_PROJECT_ROOT))
    clear_settings_cache()


def main() -> int:
    args = _parse_args()
    settings = get_settings()
    configure_logging(settings.logging)
    logger.info("GuessWord AI starting (Phase 2 — capture)")

    app = QApplication(sys.argv)
    _ensure_region(args)
    settings = load_settings(project_root=_PROJECT_ROOT)

    bus = EventBus()
    provider = create_capture_provider(settings.capture)
    pipeline = CapturePipeline(provider, settings.capture, bus)

    debug_window: CaptureDebugWindow | None = None
    if settings.debug.enabled and settings.debug.show_capture_preview:
        debug_window = CaptureDebugWindow(bus)
        debug_window.show()

    change_count = {"n": 0}

    def _count_changes(event: FrameChangedEvent) -> None:
        change_count["n"] += 1

    bus.subscribe(FrameChangedEvent, _count_changes)

    def _on_tick() -> None:
        pipeline.process_one_frame()

    timer = QTimer()
    timer.timeout.connect(_on_tick)
    timer.start(_TIMER_MS)

    logger.info(
        "Capture region %sx%s at (%s, %s); debug=%s",
        settings.capture.width,
        settings.capture.height,
        settings.capture.left,
        settings.capture.top,
        settings.debug.enabled,
    )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
