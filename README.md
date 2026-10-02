# GuessWord AI

Real-time desktop helper for **Guess the Word**–style games: capture a screen region, read visible letters with OCR, search a dictionary, and show ranked guesses in a floating overlay.

**Target latency:** under 200 ms after the on-screen word changes.

## Requirements

- Python 3.12+
- See [requirements.txt](requirements.txt) for runtime dependencies (full stack used from Phase 2 onward)

## Quick start

Install the dependencies in a virtual environment:

```bash
cd GuessTheWord
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
python main.py
```

Every launch opens the region selection flow. Drag a rectangle around the game's word area and press **Enter**. Coordinates are saved to `config/default.toml` automatically. The app preprocesses changed frames, reads visible letters with PaddleOCR, searches the local word list, and shows ranked guesses in a movable always-on-top overlay.

PaddleOCR downloads its recognition models on first use; after that, recognition runs locally. Set `[debug] enabled = false` in config to hide the capture preview window. Use the preview dropdown to inspect the original frame, grayscale, threshold, and final processed image.

On Wayland, the app asks for screen-sharing permission first. Approve the desktop portal prompt and choose the monitor containing the game. The app then shows a preview of that shared screen; drag over the game area and press **Enter**. This requires a working XDG Desktop Portal ScreenCast service, PipeWire, and Qt's FFmpeg multimedia backend.

To use a custom newline-separated dictionary, set `dictionary_path` in `[solver]` in `config/default.toml`. Without one, the solver uses the installed English word-frequency list.

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
