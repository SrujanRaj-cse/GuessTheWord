"""Tests for capture config persistence."""

from __future__ import annotations

from config.persist import save_capture_settings
from config.settings import CaptureSettings, load_settings


def test_save_capture_merges_into_toml(tmp_path) -> None:
    config_path = tmp_path / "config" / "default.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("[logging]\nlevel = \"INFO\"\n", encoding="utf-8")

    capture = CaptureSettings(
        left=100,
        top=200,
        width=640,
        height=120,
        region_selected=True,
        preferred_fps=60,
        fallback_fps=30,
    )
    save_capture_settings(tmp_path, capture, config_path)

    text = config_path.read_text(encoding="utf-8")
    normalized = text.replace(" ", "").replace("\n", "")
    assert "region_selected=true" in normalized
    settings = load_settings(config_path=config_path, project_root=tmp_path)
    assert settings.capture.left == 100
    assert settings.capture.region_selected is True
    assert settings.logging.level.value == "INFO"
