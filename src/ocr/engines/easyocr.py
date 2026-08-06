"""EasyOCR letter-only adapter."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from ocr.engines.base import mean_confidence, sanitize_letters
from ocr.provider import LetterOCRResult


class EasyLetterEngine:
    """Letter recognition via EasyOCR."""

    name = "easyocr"

    def __init__(self, use_gpu: bool = False, model_storage_directory: str | None = None) -> None:
        self._use_gpu = use_gpu
        self._model_dir = model_storage_directory
        self._reader: Any | None = None

    def _ensure_loaded(self) -> None:
        if self._reader is not None:
            return
        import easyocr

        kwargs: dict[str, object] = {"gpu": self._use_gpu, "verbose": False}
        if self._model_dir:
            kwargs["model_storage_directory"] = self._model_dir
        self._reader = easyocr.Reader(["en"], **kwargs)

    def recognize_letters(self, image_bgr: np.ndarray) -> LetterOCRResult:
        self._ensure_loaded()
        assert self._reader is not None
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        detections = self._reader.readtext(rgb, detail=1)
        texts = [str(item[1]) for item in detections]
        confidences = [float(item[2]) for item in detections]
        return sanitize_letters("".join(texts), mean_confidence(confidences))
