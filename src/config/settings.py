"""Application configuration loaded from defaults, TOML file, and environment."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, fields, replace
from enum import Enum
from functools import lru_cache
from pathlib import Path
from types import UnionType
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints

ENV_PREFIX = "GUESSWORD_"

# Default path for optional user config (project root / config / default.toml).
_DEFAULT_CONFIG_RELATIVE = Path("config") / "default.toml"


class LogLevel(str, Enum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class CaptureSettings:
    """Screen capture region and timing."""

    monitor_index: int = 1
    left: int = 0
    top: int = 0
    width: int = 800
    height: int = 200
    region_selected: bool = False
    preferred_fps: int = 60
    fallback_fps: int = 30
    frame_change_threshold: float = 0.02
    backend: str = "mss"


@dataclass(frozen=True)
class DebugSettings:
    """Debug preview and verbose pipeline output."""

    enabled: bool = False
    show_capture_preview: bool = True


@dataclass(frozen=True)
class VisionSettings:
    """Image preprocessing parameters (used from Phase 3 onward)."""

    crop_margin_px: int = 0
    threshold_block_size: int = 11
    threshold_c: int = 2


@dataclass(frozen=True)
class OCRSettings:
    """OCR engine options (used from Phase 4 onward)."""

    min_confidence: float = 0.5
    use_gpu: bool = False
    lang: str = "en"


@dataclass(frozen=True)
class SolverSettings:
    """Dictionary and ranking options (used from Phase 5 onward)."""

    dictionary_path: Path | None = None
    max_candidates: int = 20
    min_word_length: int = 3
    max_word_length: int = 15


@dataclass(frozen=True)
class OverlaySettings:
    """Floating overlay UI (used from Phase 6 onward)."""

    width: int = 320
    height: int = 180
    opacity: float = 0.92
    font_size_pt: int = 14


@dataclass(frozen=True)
class LoggingSettings:
    """Logging destination and verbosity."""

    level: LogLevel = LogLevel.INFO
    log_to_console: bool = True
    log_file: Path | None = None


@dataclass(frozen=True)
class AppSettings:
    """Root settings aggregate passed into application modules."""

    capture: CaptureSettings = CaptureSettings()
    vision: VisionSettings = VisionSettings()
    ocr: OCRSettings = OCRSettings()
    solver: SolverSettings = SolverSettings()
    overlay: OverlaySettings = OverlaySettings()
    logging: LoggingSettings = LoggingSettings()
    debug: DebugSettings = DebugSettings()


T = TypeVar("T")


def _field_value_type(field_type: type) -> type:
    """Resolve ``Path | None`` and similar unions to the non-optional type."""
    origin = get_origin(field_type)
    if origin is Union or origin is UnionType:
        candidates = [arg for arg in get_args(field_type) if arg is not type(None)]
        if len(candidates) == 1:
            return candidates[0]
    return field_type


def _coerce_value(field_name: str, target_type: type, raw: str) -> Any:
    """Convert an environment string to the type expected by a dataclass field."""
    target_type = _field_value_type(target_type)
    if target_type is LogLevel:
        return LogLevel(raw.upper())
    if target_type is Path:
        return Path(raw)
    if target_type is bool:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if target_type is int:
        return int(raw)
    if target_type is float:
        return float(raw)
    if target_type is str:
        return raw
    raise TypeError(f"Unsupported settings type for {field_name}: {target_type}")


def _apply_env_overrides(settings: AppSettings) -> AppSettings:
    """Apply GUESSWORD_* environment variables to nested dataclass fields."""
    updates: dict[str, Any] = {}

    for section in fields(AppSettings):
        section_obj = getattr(settings, section.name)
        section_updates: dict[str, Any] = {}
        type_hints = get_type_hints(type(section_obj))

        for field in fields(section_obj):
            env_key = f"{ENV_PREFIX}{section.name.upper()}_{field.name.upper()}"
            if env_key not in os.environ:
                continue
            section_updates[field.name] = _coerce_value(
                field.name, type_hints[field.name], os.environ[env_key]
            )

        if section_updates:
            updates[section.name] = replace(section_obj, **section_updates)

    result = settings
    for name, value in updates.items():
        result = replace(result, **{name: value})
    return result


def _nested_from_mapping(
    cls: type[T],
    data: dict[str, Any],
) -> T:
    """Build a frozen dataclass instance from a TOML section dict."""
    kwargs: dict[str, Any] = {}
    type_hints = get_type_hints(cls)
    for field in fields(cls):
        if field.name not in data:
            continue
        value = data[field.name]
        resolved = _field_value_type(type_hints[field.name])
        if resolved is LogLevel and isinstance(value, str):
            value = LogLevel(value.upper())
        elif resolved is Path:
            if value is not None and value != "":
                value = Path(str(value))
            else:
                value = None
        kwargs[field.name] = value
    return cls(**kwargs)  # type: ignore[arg-type,misc]


def _settings_from_toml(data: dict[str, Any]) -> AppSettings:
    """Map a parsed TOML document onto AppSettings."""
    return AppSettings(
        capture=_nested_from_mapping(CaptureSettings, data.get("capture", {})),
        vision=_nested_from_mapping(VisionSettings, data.get("vision", {})),
        ocr=_nested_from_mapping(OCRSettings, data.get("ocr", {})),
        solver=_nested_from_mapping(SolverSettings, data.get("solver", {})),
        overlay=_nested_from_mapping(OverlaySettings, data.get("overlay", {})),
        logging=_nested_from_mapping(LoggingSettings, data.get("logging", {})),
        debug=_nested_from_mapping(DebugSettings, data.get("debug", {})),
    )


def load_settings(
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> AppSettings:
    """
    Load settings: defaults, optional TOML file, then environment overrides.

    Args:
        config_path: Explicit TOML path. When None, uses ``project_root/config/default.toml``
            if that file exists.
        project_root: Root directory of the project. Defaults to the parent of ``src/config``.

    Returns:
        Immutable ``AppSettings`` instance.
    """
    root = project_root or Path(__file__).resolve().parents[2]
    path = config_path
    if path is None:
        candidate = root / _DEFAULT_CONFIG_RELATIVE
        path = candidate if candidate.is_file() else None

    settings = AppSettings()
    if path is not None and path.is_file():
        with path.open("rb") as handle:
            document = tomllib.load(handle)
        settings = _settings_from_toml(document)

    return _apply_env_overrides(settings)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Cached settings loader for application entry points.

    Prefer ``load_settings()`` in tests with explicit paths.
    """
    return load_settings()


def clear_settings_cache() -> None:
    """Clear the cached settings (for tests)."""
    get_settings.cache_clear()
