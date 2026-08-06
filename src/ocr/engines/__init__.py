"""Letter OCR engine registry."""

from __future__ import annotations

from ocr.engines.easyocr import EasyLetterEngine
from ocr.engines.paddle import PaddleLetterEngine
from ocr.engines.tesseract import TesseractLetterEngine
from ocr.provider import LetterOCREngine

_ENGINE_NAMES = ("paddle", "easyocr", "tesseract")


def available_engine_names() -> tuple[str, ...]:
    """Return engines that can run in this environment."""
    names: list[str] = []
    if _try_import("paddleocr"):
        names.append("paddle")
    if _try_import("easyocr"):
        names.append("easyocr")
    if TesseractLetterEngine.is_available():
        names.append("tesseract")
    return tuple(names)


def create_engine(name: str, *, use_gpu: bool = False, lang: str = "en") -> LetterOCREngine:
    """
    Construct a letter OCR engine by name.

    Raises:
        ValueError: Unknown engine name.
        RuntimeError: Engine dependencies or binaries missing.
    """
    normalized = name.strip().lower()
    if normalized == "paddle":
        if not _try_import("paddleocr"):
            raise RuntimeError("paddleocr is not installed")
        return PaddleLetterEngine(use_gpu=use_gpu, lang=lang)
    if normalized == "easyocr":
        if not _try_import("easyocr"):
            raise RuntimeError("easyocr is not installed")
        return EasyLetterEngine(use_gpu=use_gpu)
    if normalized == "tesseract":
        if not TesseractLetterEngine.is_available():
            raise RuntimeError("tesseract binary is not installed")
        return TesseractLetterEngine()
    raise ValueError(f"Unknown OCR engine {name!r}; expected one of {_ENGINE_NAMES}")


def _try_import(module: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(module) is not None
