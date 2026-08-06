# GuessWord AI — Session Handoff

> **Single source of truth** for any Cursor session or agent picking up this repo.
> Update this file at the end of every session (commit hash, phase status, next task).

---

## Snapshot (2026-08-06)

| Field | Value |
|-------|--------|
| **Last verified commit** | `f182960` — *Add Phase 3 image preprocessing pipeline* |
| **Working tree** | Large **uncommitted** Phase 4 OCR work (see below) |
| **Current phase** | **Phase 4 — OCR & pattern recognition** (in progress) |
| **Tests** | 31 passed (`pytest -q`, venv) |
| **Build** | `main.py` imports OK; app still Phase 3 (capture + vision only) |
| **Next task** | Commit Phase 4 foundation, then expand benchmark dataset toward 50–100 samples |

---

## Phase checklist

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Setup | ✅ Done | Committed |
| 2 — Capture | ✅ Done | Committed |
| 3 — Vision | ✅ Done | Committed at `f182960` |
| 4 — OCR | 🟡 In progress | Core pipeline written, **not committed**; dataset seed-only; no engine decision; no `OCRStage` |
| 5 — Solver | ⬜ Not started | `WordSource` protocol stub only |
| 6 — Overlay | ⬜ Not started | Empty `overlay/` package |
| 7 — Performance | ⬜ Not started | Frame change detection exists from Phase 2 |

---

## Phase 4 — what exists (uncommitted unless noted)

### Completed in working tree

| Component | Path | Notes |
|-----------|------|-------|
| Blank detector | `src/ocr/blank_detector.py` | CV on `VisionProcessResult.processed` |
| Pattern normalizer | `src/ocr/pattern_normalizer.py` | Pure merge `letters + blanks` |
| Pattern recognizer | `src/ocr/pattern_recognizer.py` | Facade: vision → blanks → OCR → normalize |
| Letter OCR protocol | `src/ocr/provider.py` | `LetterOCREngine`, `LetterOCRResult`, `PatternResult` |
| Engines | `src/ocr/engines/{paddle,easyocr,tesseract}.py` | Letter-only, shared `sanitize_letters` in `base.py` |
| Engine registry | `src/ocr/engines/__init__.py` | `create_engine`, `available_engine_names` |
| Dataset loader | `src/ocr/dataset.py` | Validates `dataset.json` schema v1 |
| Benchmark seed | `benchmarks/ocr_dataset/` | **1 sample** (`0001.png`, `to_____`) |
| Validation CLI | `tools/ocr_validate/` | CLI, runner, metrics, report, debug output |
| Design doc | `docs/OCR_PHASE4_DESIGN.md` | Approved architecture reference |
| Unit tests | `tests/test_{blank_detector,pattern_normalizer,pattern_recognizer,ocr_dataset,ocr_engines_base,ocr_validate_metrics}.py` | All pass |
| Settings | `src/config/settings.py` | `letter_image_source`, `engine` fields added |
| Docs delta | `ARCHITECTURE.md`, `TASKS.md`, `.gitignore` | Updated for Phase 4 |

### Partially done

| Component | Gap |
|-----------|-----|
| Benchmark dataset | Seed only (1/50–100 target). No synthetic augmentation script. |
| `tools/ocr_validate/report.py` | Missing **p95 latency**, **exact-match rates**, **tag breakdown** per design doc |
| `tools/ocr_validate/metrics.py` | `exact_match_accuracy` defined but unused in reports |
| `CHANGELOG.md` | Phase 4 not documented |
| `TASKS.md` checkboxes | Still all `[ ]` for Phase 4 despite implementation |
| Engine benchmark | EasyOCR runs (~391 ms, poor accuracy on seed); Tesseract not installed in env |

### Not started (Phase 4)

| Component | Blocked by |
|-----------|------------|
| `docs/OCR_ENGINE_DECISION.md` | Dataset ≥ 50 samples + benchmark run |
| `OCRStage` (`VisionProcessedEvent` → `PatternChangedEvent`) | Engine validation sign-off |
| `@pytest.mark.ocr` integration tests | Optional; not required for sign-off |

---

## Architecture compliance

| Rule | Status |
|------|--------|
| OCR logic only in `src/ocr/` | ✅ |
| `tools/ocr_validate` imports `src/ocr`, no duplicate engines | ✅ |
| Vision does not OCR | ✅ |
| Capture does not OCR | ✅ |
| `main.py` not wired to OCR yet | ✅ (by design until validation) |
| Blank detector does not call OCR | ✅ |
| Pattern normalizer has no OpenCV/ML | ✅ |

**Minor deviation:** `dataset.py` lives in `src/ocr/` instead of `tools/ocr_validate/dataset.py` as sketched in the design doc. Acceptable — shared by tests and CLI; no duplicated logic.

**No architecture conflicts** requiring redesign.

---

## Key commands

```bash
cd GuessTheWord
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Fast CI-style tests
pytest -q

# Run app (Phase 3: capture + vision preview)
python main.py

# OCR benchmark (needs OCR deps; tesseract optional)
PYTHONPATH=src python -m tools.ocr_validate \
  --dataset benchmarks/ocr_dataset \
  --engines easyocr \
  --report reports/ocr_benchmark.md \
  --runs 3
```

---

## Remaining work (implementation order)

1. **Commit** existing Phase 4 foundation (preserve uncommitted work).
2. **Finish** `tools/ocr_validate` report gaps (p95, exact-match, tag tables).
3. **Expand** `benchmarks/ocr_dataset/` toward **50–100** labeled samples.
4. **Run** full engine benchmark (paddle, easyocr, tesseract).
5. **Write** `docs/OCR_ENGINE_DECISION.md` with chosen default engine.
6. **Implement** `OCRStage` on event bus → `PatternChangedEvent`.
7. **Update** `CHANGELOG.md`, mark Phase 4 complete in `TASKS.md`.
8. Begin Phase 5 (solver).

---

## Do NOT

- Restart or rewrite Phase 4 from scratch.
- Wire OCR into `main.py` before engine validation sign-off.
- Duplicate OCR logic outside `src/ocr/`.
- Commit `.cache/` or `reports/` (gitignored).

---

## Session log

| Date | Agent | Action |
|------|-------|--------|
| 2026-08-06 | Audit agent | Full repo audit; 31 tests pass; created `HANDOFF.md`; proposed first commit |
