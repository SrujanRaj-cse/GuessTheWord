"""OCR providers and visible-letter pattern extraction."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

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
_IGNORED_LINES = {"guesstheword", "possibleanswers", "bestguess", "confidence"}


def extract_pattern(text: str) -> str | None:
    """Normalize OCR text into a letter/blank pattern, or return None."""
    for line in text.splitlines():
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
        pattern, confidence = max(candidates, key=lambda item: (len(item[0]), item[1]))
        return OCRResult(pattern=pattern, confidence=confidence)
