"""Markdown and JSON benchmark reports."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from tools.ocr_validate.metrics import SampleMetrics


def write_reports(
    metrics: list[SampleMetrics],
    *,
    markdown_path: Path | None,
    json_path: Path | None,
    dataset_name: str,
) -> str:
    """Write optional report files and return Markdown body."""
    body = render_markdown(metrics, dataset_name=dataset_name)
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(body, encoding="utf-8")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"dataset": dataset_name, "samples": [asdict(row) for row in metrics]}
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return body


def render_markdown(metrics: list[SampleMetrics], *, dataset_name: str) -> str:
    lines = [
        f"# OCR validation report — {dataset_name}",
        "",
        "## Per-engine summary",
        "",
        "| Engine | Samples | Letter acc (mean) | Pattern acc (mean) | Recognition (mean) | Latency ms (mean) | CPU s (mean) |",
        "|--------|---------|-------------------|--------------------|--------------------|-------------------|--------------|",
    ]
    by_engine: dict[str, list[SampleMetrics]] = defaultdict(list)
    for row in metrics:
        by_engine[row.engine].append(row)

    for engine, rows in sorted(by_engine.items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    engine,
                    str(len(rows)),
                    f"{_mean(r.letter_accuracy for r in rows):.3f}",
                    f"{_mean(r.pattern_accuracy for r in rows):.3f}",
                    f"{_mean(r.recognition_score for r in rows):.3f}",
                    f"{_mean(r.latency_ms for r in rows):.1f}",
                    f"{_mean(r.cpu_seconds for r in rows):.3f}",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Per-sample detail", ""])
    for row in metrics:
        lines.append(
            f"- **{row.sample_id}** / {row.engine}: "
            f"letters `{row.actual_letters}` (expected `{row.expected_letters}`), "
            f"pattern `{row.actual_pattern}` (expected `{row.expected_pattern}`), "
            f"latency {row.latency_ms:.1f} ms, score {row.recognition_score:.3f}"
        )
    lines.append("")
    return "\n".join(lines)


def _mean(values: object) -> float:
    items = list(values)  # type: ignore[arg-type]
    if not items:
        return 0.0
    return sum(items) / len(items)  # type: ignore[return-value]
