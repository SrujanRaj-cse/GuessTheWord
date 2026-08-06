"""PaddleOCR letter-only adapter."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from ocr.engines.base import mean_confidence, sanitize_letters
from ocr.provider import LetterOCRResult


class PaddleLetterEngine:
    """Letter recognition via PaddleOCR detection + recognition."""

    name = "paddle"

    def __init__(self, use_gpu: bool = False, lang: str = "en") -> None:
        self._use_gpu = use_gpu
        self._lang = lang
        self._ocr: Any | None = None

    def _ensure_loaded(self) -> None:
        if self._ocr is not None:
            return
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(
            use_angle_cls=False,
            lang=self._lang,
            show_log=False,
            use_gpu=self._use_gpu,
        )

    def recognize_letters(self, image_bgr: np.ndarray) -> LetterOCRResult:
        self._ensure_loaded()
        assert self._ocr is not None
        if image_bgr.ndim == 2:
            image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_GRAY2BGR)
        raw = self._ocr.ocr(image_bgr, cls=False)
        texts: list[str] = []
        confidences: list[float] = []
        if raw and raw[0]:
            for line in raw[0]:
                if line and len(line) >= 2:
                    texts.append(str(line[1][0]))
                    confidences.append(float(line[1][1]))
        combined = "".join(texts)
        return sanitize_letters(combined, mean_confidence(confidences))
