# GuessWord AI

Real-time desktop helper for **Guess the Word**–style games: capture a screen region, read visible letters with OCR, search a dictionary, and show ranked guesses in a floating overlay.

**Target latency:** under 200 ms after the on-screen word changes.

## Requirements

- Python 3.12+
- See [requirements.txt](requirements.txt) for runtime dependencies (full stack used from Phase 2 onward)

## Quick start (Phase 2–3)

Install dependencies first (`pip install -r requirements-dev.txt` creates a venv with PySide6, MSS, OpenCV, and test tools).

```bash
cd GuessTheWord
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
python main.py
```

On first launch (or with `--pick-region`), drag a rectangle over the game area and press **Enter**. Coordinates are saved to `config/default.toml` automatically.

Set `[debug] enabled = false` in config to hide the capture preview window. Use the preview dropdown to switch between the original frame, grayscale, threshold, and final processed image (Phase 3).

Optional: edit [config/default.toml](config/default.toml) or set environment variables prefixed with `GUESSWORD_`, for example:

```bash
export GUESSWORD_CAPTURE_WIDTH=1024
export GUESSWORD_LOGGING_LEVEL=DEBUG
```

## Project docs

| Document | Purpose |
|----------|---------|
| [PROJECT.md](PROJECT.md) | Goals, module responsibilities, roadmap |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Data flow and design decisions |
| [TASKS.md](TASKS.md) | Phase checklist |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## License

TBD
