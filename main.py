"""GuessWord AI — capture and vision pipeline entry (Phase 3)."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from capture.factory import create_capture_provider, region_from_settings  # noqa: E402
from capture.qt_screen_provider import QtScreenCaptureProvider  # noqa: E402
from capture.region_picker import (  # noqa: E402
    pick_capture_region,
    pick_capture_region_from_frame,
)
from config.persist import (  # noqa: E402
    capture_settings_from_region,
    default_config_path,
    save_capture_settings,
)
from config.settings import (  # noqa: E402
    AppSettings,
    clear_settings_cache,
    get_settings,
    load_settings,
)
from core.events import EventBus  # noqa: E402
from core.pipeline import CapturePipeline  # noqa: E402
from debug.preview import CaptureDebugWindow  # noqa: E402
from ocr.stage import OCRStage  # noqa: E402
from overlay import PredictionOverlay  # noqa: E402
from solver.stage import SolverStage  # noqa: E402
from utils.logging_config import configure_logging  # noqa: E402
from vision.stage import VisionStage  # noqa: E402

logger = logging.getLogger(__name__)

_TIMER_MS = 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GuessWord AI")
    parser.add_argument(
        "--pick-region",
        action="store_true",
        help="Reopen the region picker (selection already happens every launch)",
    )
    return parser.parse_args()


def _ensure_region(args: argparse.Namespace) -> None:
    settings = load_settings(project_root=_PROJECT_ROOT)
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


def _ensure_wayland_region(
    args: argparse.Namespace,
    settings: AppSettings,
    provider: QtScreenCaptureProvider,
) -> AppSettings:
    """Request portal screen access first, then pick from its actual video frame."""
    logger.info("Approve screen sharing and select the monitor containing the game")
    frame = provider.grab_screen()
    logger.info("Select the game rectangle from the shared screen preview")
    region = pick_capture_region_from_frame(frame, settings.capture.monitor_index)
    if region is None:
        provider.close()
        raise SystemExit(1)

    capture = capture_settings_from_region(
        region,
        preferred_fps=settings.capture.preferred_fps,
        fallback_fps=settings.capture.fallback_fps,
        frame_change_threshold=settings.capture.frame_change_threshold,
        backend="qt",
    )
    save_capture_settings(_PROJECT_ROOT, capture, default_config_path(_PROJECT_ROOT))
    clear_settings_cache()
    settings = load_settings(project_root=_PROJECT_ROOT)
    provider.set_region(region_from_settings(settings.capture))
    return settings


def _install_interrupt_handler(app: QApplication) -> QTimer:
    """Let SIGINT reach Qt while its event loop is running."""
    signal.signal(signal.SIGINT, lambda *_args: app.quit())
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    return timer


def main() -> int:
    args = _parse_args()
    settings = get_settings()
    configure_logging(settings.logging)
    logger.info("GuessWord AI starting")

    app = QApplication(sys.argv)
    interrupt_timer = _install_interrupt_handler(app)
    is_wayland = sys.platform.startswith("linux") and os.environ.get(
        "XDG_SESSION_TYPE", ""
    ).lower() == "wayland"
    if is_wayland:
        provider = create_capture_provider(settings.capture)
        try:
            settings = _ensure_wayland_region(args, settings, provider)
        except RuntimeError as error:
            provider.close()
            QMessageBox.critical(None, "Screen sharing failed", str(error))
            return 1
    else:
        _ensure_region(args)
        settings = load_settings(project_root=_PROJECT_ROOT)
        provider = create_capture_provider(settings.capture)

    bus = EventBus()
    pipeline = CapturePipeline(provider, settings.capture, bus)
    VisionStage(bus, settings.vision)
    ocr_stage = OCRStage(bus, settings.ocr)
    SolverStage(bus, settings.solver)
    overlay = PredictionOverlay(bus, settings.overlay)
    overlay.show()
    app.aboutToQuit.connect(ocr_stage.close)
    app.aboutToQuit.connect(provider.close)

    debug_window: CaptureDebugWindow | None = None
    if settings.debug.enabled and settings.debug.show_capture_preview:
        debug_window = CaptureDebugWindow(bus)
        debug_window.show()

    def _on_tick() -> None:
        try:
            pipeline.process_one_frame()
        except Exception as error:
            timer.stop()
            logger.exception("Screen capture stopped")
            QMessageBox.critical(None, "Screen capture stopped", str(error))
            app.quit()

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
    exit_code = app.exec()
    interrupt_timer.stop()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
