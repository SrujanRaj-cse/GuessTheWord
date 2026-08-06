"""OCR engine plug-in interface (Phase 4+)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
