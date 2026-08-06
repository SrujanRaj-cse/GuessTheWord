"""OCR types and engine protocols (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class LetterOCRResult:
    """Alphabetic characters recognized by an OCR backend."""

    letters: str
    confidence: float


@dataclass(frozen=True)
class PatternResult:
    """Full pattern after blank detection, letter OCR, and normalization."""

    pattern: str
    letters: str
    blanks: str
    confidence: float
    recognition_score: float


class LetterOCREngine(Protocol):
    """Swap PaddleOCR, EasyOCR, Tesseract, or mocks without changing the pipeline."""

    @property
    def name(self) -> str:
        """Short engine identifier for reports."""
        ...

    def recognize_letters(self, image_bgr: np.ndarray) -> LetterOCRResult:
        """Extract visible alphabetic characters only (no underscores)."""
        ...


@dataclass(frozen=True)
class OCRResult:
    """Legacy shape for event bus; populated from ``PatternResult`` in OCRStage."""

    pattern: str
    confidence: float
