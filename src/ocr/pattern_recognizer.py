"""Orchestrate blank detection, letter OCR, and pattern normalization."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from config.settings import OCRSettings, VisionSettings
from ocr.blank_detector import BlankDetector
from ocr.engines import LetterOCREngine
from ocr.pattern_normalizer import PatternNormalizer
from ocr.provider import LetterOCRResult, PatternResult
from vision.image_processor import ImageProcessor
from vision.types import VisionProcessResult


@dataclass(frozen=True)
class RecognizeTiming:
    """Milliseconds spent in each stage of one recognition pass."""

    vision_ms: float
    blank_ms: float
    ocr_ms: float
    total_ms: float


@dataclass(frozen=True)
class RecognizeOutput:
    """Pattern recognition result plus timing breakdown."""

    result: PatternResult
    vision: VisionProcessResult
    timing: RecognizeTiming


class PatternRecognizer:
    """
    Full offline pattern pipeline: vision preprocess → blanks → letters → merge.

    Used by the validation tool and (later) ``OCRStage`` on the event bus.
    """

    def __init__(
        self,
        engine: LetterOCREngine,
        vision_settings: VisionSettings | None = None,
        ocr_settings: OCRSettings | None = None,
    ) -> None:
        self._engine = engine
        self._vision_settings = vision_settings or VisionSettings()
        self._ocr_settings = ocr_settings or OCRSettings()
        self._processor = ImageProcessor(self._vision_settings)
        self._blank_detector = BlankDetector()
        self._normalizer = PatternNormalizer()

    @property
    def engine_name(self) -> str:
        return self._engine.name

    def recognize_frame(self, frame_bgr: np.ndarray) -> RecognizeOutput:
        """Run vision preprocessing and pattern extraction on a BGR capture."""
        start_total = time.perf_counter()
        start_vision = time.perf_counter()
        vision = self._processor.process(frame_bgr)
        vision_ms = (time.perf_counter() - start_vision) * 1000.0

        start_blank = time.perf_counter()
        blanks_result = self._blank_detector.detect(vision.processed)
        blank_ms = (time.perf_counter() - start_blank) * 1000.0

        ocr_image = self._letter_image(vision)
        start_ocr = time.perf_counter()
        letters_result = self._engine.recognize_letters(ocr_image)
        ocr_ms = (time.perf_counter() - start_ocr) * 1000.0

        pattern = self._normalizer.merge(letters_result.letters, blanks_result.blanks)
        confidence = letters_result.confidence
        recognition_score = confidence * blanks_result.confidence
        total_ms = (time.perf_counter() - start_total) * 1000.0

        result = PatternResult(
            pattern=pattern,
            letters=letters_result.letters,
            blanks=blanks_result.blanks,
            confidence=confidence,
            recognition_score=recognition_score,
        )
        timing = RecognizeTiming(
            vision_ms=vision_ms,
            blank_ms=blank_ms,
            ocr_ms=ocr_ms,
            total_ms=total_ms,
        )
        return RecognizeOutput(result=result, vision=vision, timing=timing)

    def _letter_image(self, vision: VisionProcessResult) -> np.ndarray:
        source = self._ocr_settings.letter_image_source.lower()
        if source == "grayscale":
            return vision.grayscale
        if source == "original":
            return vision.original_bgr
        raise ValueError(f"Unsupported letter_image_source {source!r}")
