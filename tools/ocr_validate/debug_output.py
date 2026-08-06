"""Optional debug artifacts for OCR validation."""

from __future__ import annotations

from pathlib import Path

import cv2

from ocr.pattern_recognizer import RecognizeOutput


def save_debug_artifacts(
    output_dir: Path,
    sample_id: str,
    engine: str,
    recognize_output: RecognizeOutput,
) -> None:
    """Write processed binary and a text summary for one recognition pass."""
    folder = output_dir / sample_id / engine
    folder.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(folder / "processed.png"), recognize_output.vision.processed)
    summary = (
        f"letters={recognize_output.result.letters}\n"
        f"blanks={recognize_output.result.blanks}\n"
        f"pattern={recognize_output.result.pattern}\n"
        f"confidence={recognize_output.result.confidence:.4f}\n"
        f"recognition_score={recognize_output.result.recognition_score:.4f}\n"
        f"vision_ms={recognize_output.timing.vision_ms:.2f}\n"
        f"blank_ms={recognize_output.timing.blank_ms:.2f}\n"
        f"ocr_ms={recognize_output.timing.ocr_ms:.2f}\n"
        f"total_ms={recognize_output.timing.total_ms:.2f}\n"
    )
    (folder / "result.txt").write_text(summary, encoding="utf-8")
