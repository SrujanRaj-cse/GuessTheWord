# Changelog

All notable changes to GuessWord AI are documented here.

## [Unreleased]

### Added

- Phase 4 foundation: two-path pattern pipeline (`BlankDetector`, `PatternNormalizer`, `PatternRecognizer`), letter-only OCR engines (PaddleOCR, EasyOCR, Tesseract), seed benchmark dataset (`benchmarks/ocr_dataset/`), standalone `tools/ocr_validate` CLI with metrics and reports, `LetterOCREngine` protocol refactor, and `docs/OCR_PHASE4_DESIGN.md`. `HANDOFF.md` added for cross-session continuity.
- Phase 3: `ImageProcessor`, `VisionStage`, `VisionProcessedEvent`, debug preview stage toggle, fixture tests.
- Phase 2: region picker, MSS capture provider, adaptive FPS loop, frame-change events, debug preview, config persistence, OCR/WordSource protocol stubs.
- Phase 1: project skeleton, TOML/env configuration, logging bootstrap, settings tests, and documentation (`ARCHITECTURE.md`, `TASKS.md`, `PROJECT.md`).
