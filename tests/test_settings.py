"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config.settings import AppSettings, LogLevel, clear_settings_cache, load_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_default_settings_when_no_config_file(tmp_path: Path) -> None:
    empty_root = tmp_path / "noroot"
    empty_root.mkdir()
    settings = load_settings(config_path=tmp_path / "missing.toml", project_root=empty_root)
    assert isinstance(settings, AppSettings)
    assert settings.capture.preferred_fps == 60
    assert settings.logging.level == LogLevel.INFO


def test_loads_from_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text(
        """
[capture]
width = 640
height = 120
preferred_fps = 60

[logging]
level = "DEBUG"
""",
        encoding="utf-8",
    )
    settings = load_settings(config_path=config_file, project_root=tmp_path)
    assert settings.capture.width == 640
    assert settings.capture.height == 120
    assert settings.capture.preferred_fps == 60
    assert settings.logging.level == LogLevel.DEBUG


def test_env_overrides_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / "app.toml"
    config_file.write_text("[capture]\nwidth = 640\n", encoding="utf-8")
    monkeypatch.setenv("GUESSWORD_CAPTURE_WIDTH", "900")
    settings = load_settings(config_path=config_file, project_root=tmp_path)
    assert settings.capture.width == 900


def test_env_boolean_and_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUESSWORD_OCR_USE_GPU", "true")
    monkeypatch.setenv("GUESSWORD_LOGGING_LEVEL", "warning")
    settings = load_settings(config_path=Path("/nonexistent/config.toml"))
    assert settings.ocr.use_gpu is True
    assert settings.logging.level == LogLevel.WARNING


def test_default_toml_from_project_root() -> None:
    project_root = Path(__file__).resolve().parents[1]
    settings = load_settings(project_root=project_root)
    assert settings.capture.width == 800
