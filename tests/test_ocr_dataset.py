"""Tests for OCR benchmark dataset loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ocr.dataset import load_benchmark_dataset

_ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "ocr_dataset"


def test_load_seed_dataset() -> None:
    dataset = load_benchmark_dataset(_ROOT)
    assert len(dataset.samples) >= 1
    sample = dataset.samples[0]
    assert sample.expected_pattern == sample.expected_letters + sample.expected_blanks
    assert sample.image_path.is_file()


def test_rejects_pattern_mismatch(tmp_path: Path) -> None:
    image = tmp_path / "img.png"
    image.write_bytes(b"placeholder")
    manifest = {
        "version": 1,
        "samples": [
            {
                "id": "bad",
                "image": "img.png",
                "expected_letters": "a",
                "expected_blanks": "__",
                "expected_pattern": "a_",
            }
        ],
    }
    (tmp_path / "dataset.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        load_benchmark_dataset(tmp_path)
