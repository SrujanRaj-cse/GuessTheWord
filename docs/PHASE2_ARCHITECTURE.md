# Phase 2 — Capture architecture

## Goals

- One-time draggable region picker; persist to `config/default.toml` (no manual coordinates).
- Pluggable capture backend behind `CaptureProvider` (MSS today).
- Single monitor for MVP; `CaptureRegion` uses absolute screen coordinates so multi-monitor is a backend concern later.
- Target 60 FPS with automatic fallback to 30 FPS when the loop cannot keep pace.
- Frame change detection only — **no OCR** in this phase; emit events so OCR runs only on `FrameChanged` later.
- Capture timing metrics and debug preview (live frame + FPS + capture ms).

## Why an event pipeline (not a linear script)

A linear `capture → ocr → solve` loop couples modules and makes threading, skipping OCR, and testing hard. Instead:

```
CaptureProvider.grab()
    → FrameCapturedEvent   (every frame; debug preview, metrics)
    → FrameChangeDetector
    → FrameChangedEvent    (only if pixels changed enough; future OCR trigger)
```

Later phases add `PatternChangedEvent` and `ResultChangedEvent` without rewriting capture.

## Interfaces

| Interface | Role | Phase 2 implementation |
|-----------|------|------------------------|
| `CaptureProvider` | Return BGR `numpy` frames + timing | `MssCaptureProvider` |
| `OCRProvider` | (stub) Recognize pattern from image | Not wired |
| `WordSource` | (stub) Dictionary lookup | Not wired |

Downstream code depends on protocols, not MSS or PaddleOCR.

## Adaptive FPS

The loop sleeps to hit `preferred_fps` (60). A rolling window measures achieved FPS. If it stays below ~90% of target for several windows, switch to `fallback_fps` (30). If performance recovers on fallback, promote back to 60.

## Frame change detection

Downscale to a small grayscale image, compute mean absolute difference vs the previous frame. If below `frame_change_threshold`, skip `FrameChangedEvent`. This is the same gate OCR will use — never every frame.

## Region picker

PySide6 fullscreen overlay on the configured monitor (MVP: one monitor). Drag rectangle → Enter confirms → `config/persist.py` writes `[capture]` via `tomlkit` (preserves other sections and comments).

## Module layout

```
src/capture/     provider, mss_provider, frame_change, region_picker, loop
src/core/        events, pipeline
src/config/      persist.py
src/debug/       preview.py
src/utils/       metrics.py
```
