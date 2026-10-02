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
- [x] Wayland screen capture through Qt ScreenCast / PipeWire portal
- [x] Draggable region picker → `config/default.toml`
- [x] Wayland region picker uses a preview of the portal-approved screen stream
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

- [x] `ocr/provider.py` (`PaddleOCRProvider`, lazy model initialization)
- [x] Pattern extraction (`to____`)
- [x] Confidence filtering and `PatternChangedEvent`

## Phase 5 — Solver

- [x] `solver/dictionary.py` (custom word list or cached wordfreq source)
- [x] Pattern matching (`_` / `?` wildcards)
- [x] `solver/ranking.py` (word frequency and pattern similarity)
- [x] Solver stage publishes `ResultChangedEvent`

## Phase 6 — Overlay

- [x] `overlay` prediction window (translucent, always on top, draggable)
- [x] Thread-safe event updates from OCR worker

## Phase 7 — Performance

- [x] OCR throttling (single in-flight job)
- [x] OCR worker thread and cached dictionary
- [ ] Profiling toward &lt;200 ms

Note: basic frame change detection ships in Phase 2 (`capture/frame_change.py`).
