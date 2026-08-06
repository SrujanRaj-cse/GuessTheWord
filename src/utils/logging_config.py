"""Central logging configuration for GuessWord AI."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from config.settings import LoggingSettings, LogLevel

_BYTES_PER_MIB = 1024 * 1024
_DEFAULT_MAX_LOG_BYTES = 5 * _BYTES_PER_MIB
_DEFAULT_BACKUP_COUNT = 3

_LEVEL_MAP: dict[LogLevel, int] = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}


def configure_logging(settings: LoggingSettings) -> None:
    """
    Configure the root logger once at application startup.

    Args:
        settings: Logging section from ``AppSettings``.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(_LEVEL_MAP[settings.level])

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if settings.log_to_console:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        root.addHandler(console)

    if settings.log_file is not None:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_file,
            maxBytes=_DEFAULT_MAX_LOG_BYTES,
            backupCount=_DEFAULT_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
