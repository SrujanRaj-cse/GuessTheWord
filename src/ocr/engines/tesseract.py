"""Tesseract letter-only adapter."""

from __future__ import annotations

import shutil

import cv2
import numpy as np

from ocr.engines.base import mean_confidence, sanitize_letters
from ocr.provider import LetterOCRResult


class TesseractLetterEngine:
    """Letter recognition via system Tesseract and pytesseract."""

    name = "tesseract"

    def __init__(self, tesseract_cmd: str | None = None) -> None:
        self._tesseract_cmd = tesseract_cmd

    @staticmethod
    def is_available(tesseract_cmd: str | None = None) -> bool:
        if tesseract_cmd:
            return shutil.which(tesseract_cmd) is not None
        return shutil.which("tesseract") is not None

    def recognize_letters(self, image_bgr: np.ndarray) -> LetterOCRResult:
        import pytesseract

        if self._tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
        if not self.is_available(self._tesseract_cmd):
            raise RuntimeError("tesseract binary is not installed or not on PATH")

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY) if image_bgr.ndim == 3 else image_bgr
        config = "--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        data = pytesseract.image_to_data(
            gray,
            config=config,
            output_type=pytesseract.Output.DICT,
        )
        texts: list[str] = []
        confidences: list[float] = []
        for text, conf in zip(data["text"], data["conf"], strict=True):
            cleaned = text.strip()
            if not cleaned:
                continue
            texts.append(cleaned)
            if int(conf) >= 0:
                confidences.append(int(conf) / 100.0)
        return sanitize_letters("".join(texts), mean_confidence(confidences))
