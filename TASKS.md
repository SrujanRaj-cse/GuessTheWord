# Development tasks

## Phase 1 — Project setup

- [x] Folder structure under `src/` and `tests/`
- [x] `PROJECT.md`, `ARCHITECTURE.md`, `README.md`, `CHANGELOG.md`
- [x] `requirements.txt`
- [x] Configuration system (`config/settings.py`)
- [x] Logging setup (`utils/logging_config.py`)
- [x] `main.py` entry point
- [x] Unit tests for settings loading

## Phase 2 — Screen capture

- [x] `CaptureProvider` + `MssCaptureProvider`
- [x] Draggable region picker → `config/default.toml`
- [x] Adaptive 60 / 30 FPS capture loop
- [x] Frame change detection + `FrameChangedEvent` (no OCR)
- [x] Capture timing metrics + debug preview window
- [x] Event bus + capture pipeline stub for later OCR/solver
- [x] Tests (frame change, persist, pipeline)

## Phase 3 — Image preprocessing

- [x] `vision/image_processor.py`
- [x] Grayscale, threshold, noise removal
- [x] `VisionProcessedEvent` + `VisionStage` on `FrameChangedEvent`
- [x] Debug preview stage toggle (original / gray / threshold / processed)
- [x] Fixture-based unit tests

## Phase 4 — OCR

- [ ] `ocr/ocr_engine.py` (PaddleOCR)
- [ ] Pattern extraction (`to____`)
- [ ] Confidence in result dict

## Phase 5 — Solver

- [ ] `solver/dictionary.py`
- [ ] `solver/matcher.py`
- [ ] `solver/ranking.py` (wordfreq / RapidFuzz)

## Phase 6 — Overlay

- [ ] `overlay/overlay.py` (PySide6, transparent, always on top)

## Phase 7 — Performance

- [ ] OCR throttling / caching
- [ ] Threading model
- [ ] Profiling toward &lt;200 ms

Note: basic frame change detection ships in Phase 2 (`capture/frame_change.py`).
