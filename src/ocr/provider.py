"""OCR providers and visible-letter pattern extraction."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

import cv2
import numpy as np


@dataclass(frozen=True)
class OCRResult:
    """Recognized letter pattern from a processed image."""

    pattern: str
    confidence: float


class OCRProvider(Protocol):
    """Swap PaddleOCR, EasyOCR, or mocks without changing the pipeline."""

    def recognize(self, image: np.ndarray) -> OCRResult:
        """Extract visible letters and blanks as a pattern string."""
        ...


_WORD_PATTERN = re.compile(r"^[a-z_?]+$", re.IGNORECASE)
_IGNORED_LINES = {
    "guesstheword",
    "completethemissingletters",
    "possibleanswers",
    "bestguess",
    "confidence",
    "hintitsaname",
}


def _count_underline_marks(image: np.ndarray) -> int:
    """Count separated horizontal blank marks in the processed game image.

    PaddleOCR often merges adjacent answer slots into one underscore. The
    slots remain separate components in the thresholded image, so recover
    their count from the row of short, wide components.
    """
    if image.size == 0:
        return 0
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, ink = cv2.threshold(grayscale, 127, 255, cv2.THRESH_BINARY_INV)
    count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    image_height, image_width = grayscale.shape[:2]
    marks: list[int] = []
    for index in range(1, count):
        x, y, width, height, _ = stats[index]
        if (
            width >= 6
            and width <= image_width * 0.25
            and width / max(height, 1) >= 2.5
            and y > image_height * 0.25
            and y + height < image_height * 0.95
        ):
            marks.append(y + height // 2)
    if not marks:
        return 0

    tolerance = max(3, round(image_height * 0.04))
    rows: list[list[int]] = []
    for center_y in sorted(marks):
        row = next(
            (values for values in rows if abs(sum(values) / len(values) - center_y) <= tolerance),
            None,
        )
        if row is None:
            rows.append([center_y])
        else:
            row.append(center_y)
    return max(map(len, rows), default=0)


def extract_pattern(text: str) -> str | None:
    """Normalize OCR text into a letter/blank pattern, or return None."""
    for line in text.splitlines():
        tokens = re.findall(r"[a-z]+", line.lower())
        has_blanks = bool(re.search(r"[_?]", line))
        if not has_blanks and len(tokens) > 1 and not all(len(token) == 1 for token in tokens):
            continue
        normalized = re.sub(r"[^a-zA-Z_?]", "", line).lower()
        if len(normalized) < 2 or normalized in _IGNORED_LINES:
            continue
        if _WORD_PATTERN.fullmatch(normalized) and any(char.isalpha() for char in normalized):
            return normalized.replace("?", "_")
    return None


class PaddleOCRProvider:
    """PaddleOCR-backed provider, initialized on first recognition request."""

    def __init__(self, lang: str = "en", use_gpu: bool = False) -> None:
        self._lang = lang
        self._use_gpu = use_gpu
        self._engine: Any | None = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as error:
                raise RuntimeError(
                    "PaddleOCR is not installed. Install the OCR dependencies from requirements.txt."
                ) from error
            self._engine = PaddleOCR(
                use_angle_cls=False,
                lang=self._lang,
                use_gpu=self._use_gpu,
                show_log=False,
            )
        return self._engine

    def recognize(self, image: np.ndarray) -> OCRResult:
        """Recognize text and return the most likely word-shaped pattern."""
        if image.size == 0:
            return OCRResult(pattern="", confidence=0.0)
        result = self._get_engine().ocr(image, cls=False)
        lines = result[0] if result and result[0] else []
        candidates: list[tuple[str, float]] = []
        for item in lines:
            text, confidence = item[1]
            pattern = extract_pattern(str(text))
            if pattern:
                candidates.append((pattern, float(confidence)))
        if not candidates:
            return OCRResult(pattern="", confidence=0.0)
        pattern, confidence = max(
            candidates,
            key=lambda item: (
                item[0].count("_") > 0,
                item[0].count("_"),
                len(item[0]),
                item[1],
            ),
        )
        underline_count = _count_underline_marks(image)
        if underline_count > pattern.count("_"):
            pattern += "_" * (underline_count - pattern.count("_"))
        return OCRResult(pattern=pattern, confidence=confidence)
