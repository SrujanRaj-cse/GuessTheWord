"""Benchmark dataset loading for OCR validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_DATASET_FILENAME = "dataset.json"
_CURRENT_VERSION = 1


@dataclass(frozen=True)
class BenchmarkSample:
    """One labeled image in the OCR benchmark corpus."""

    id: str
    image_path: Path
    expected_letters: str
    expected_blanks: str
    expected_pattern: str
    tags: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class BenchmarkDataset:
    """Loaded manifest plus root directory for resolving image paths."""

    name: str
    description: str
    root: Path
    samples: tuple[BenchmarkSample, ...]


def load_benchmark_dataset(root: Path) -> BenchmarkDataset:
    """
    Load ``dataset.json`` from ``root`` and validate sample entries.

    Args:
        root: Directory containing ``dataset.json`` and image files.

    Raises:
        FileNotFoundError: Missing manifest.
        ValueError: Schema or consistency validation failed.
    """
    manifest_path = root / _DATASET_FILENAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing {_DATASET_FILENAME} under {root}")

    with manifest_path.open(encoding="utf-8") as handle:
        document = json.load(handle)

    version = document.get("version")
    if version != _CURRENT_VERSION:
        raise ValueError(f"Unsupported dataset version {version!r}, expected {_CURRENT_VERSION}")

    raw_samples = document.get("samples")
    if not isinstance(raw_samples, list) or not raw_samples:
        raise ValueError("Dataset must contain a non-empty samples list")

    samples: list[BenchmarkSample] = []
    seen_ids: set[str] = set()
    for entry in raw_samples:
        sample = _parse_sample(root, entry)
        if sample.id in seen_ids:
            raise ValueError(f"Duplicate sample id {sample.id!r}")
        seen_ids.add(sample.id)
        samples.append(sample)

    return BenchmarkDataset(
        name=str(document.get("name", root.name)),
        description=str(document.get("description", "")),
        root=root.resolve(),
        samples=tuple(samples),
    )


def _parse_sample(root: Path, entry: object) -> BenchmarkSample:
    if not isinstance(entry, dict):
        raise ValueError("Each sample must be a JSON object")

    sample_id = _require_str(entry, "id")
    image_rel = _require_str(entry, "image")
    expected_letters = _require_str(entry, "expected_letters")
    expected_blanks = _require_str(entry, "expected_blanks")
    expected_pattern = _require_str(entry, "expected_pattern")

    if expected_pattern != expected_letters + expected_blanks:
        raise ValueError(
            f"Sample {sample_id}: expected_pattern must equal letters + blanks, "
            f"got {expected_pattern!r} vs {expected_letters + expected_blanks!r}"
        )
    if expected_blanks and not all(ch == "_" for ch in expected_blanks):
        raise ValueError(f"Sample {sample_id}: expected_blanks must be underscores only")

    image_path = (root / image_rel).resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Sample {sample_id}: missing image {image_path}")

    tags_raw = entry.get("tags", [])
    if not isinstance(tags_raw, list):
        raise ValueError(f"Sample {sample_id}: tags must be a list")
    tags = tuple(str(tag) for tag in tags_raw)

    notes = str(entry.get("notes", ""))
    return BenchmarkSample(
        id=sample_id,
        image_path=image_path,
        expected_letters=expected_letters,
        expected_blanks=expected_blanks,
        expected_pattern=expected_pattern,
        tags=tags,
        notes=notes,
    )


def _require_str(entry: dict[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Sample field {key!r} must be a non-empty string")
    return value
