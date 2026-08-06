"""CLI for standalone OCR pipeline validation."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config.settings import OCRSettings, VisionSettings  # noqa: E402
from ocr.dataset import load_benchmark_dataset  # noqa: E402
from ocr.engines import available_engine_names, create_engine  # noqa: E402
from ocr.pattern_recognizer import PatternRecognizer  # noqa: E402
from tools.ocr_validate.debug_output import save_debug_artifacts  # noqa: E402
from tools.ocr_validate.report import write_reports  # noqa: E402
from tools.ocr_validate.runner import BenchmarkRunConfig, run_benchmark  # noqa: E402

logger = logging.getLogger(__name__)

_DEFAULT_DATASET = _PROJECT_ROOT / "benchmarks" / "ocr_dataset"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate OCR pattern pipeline offline")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_DEFAULT_DATASET,
        help="Benchmark dataset root (contains dataset.json)",
    )
    parser.add_argument(
        "--engines",
        default="",
        help="Comma-separated engine names (default: all available)",
    )
    parser.add_argument("--runs", type=int, default=3, help="Timed runs per sample")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per sample")
    parser.add_argument("--report", type=Path, default=None, help="Markdown report path")
    parser.add_argument("--json", type=Path, default=None, help="JSON report path")
    parser.add_argument("--debug-dir", type=Path, default=None, help="Debug image output")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU for OCR backends")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    dataset = load_benchmark_dataset(args.dataset.resolve())
    engine_names = _resolve_engines(args.engines)
    if not engine_names:
        logger.error("No OCR engines available in this environment")
        return 1

    config = BenchmarkRunConfig(runs=args.runs, warmup=args.warmup, use_gpu=args.use_gpu)
    metrics = run_benchmark(
        dataset,
        engine_names,
        config=config,
        vision_settings=VisionSettings(),
        ocr_settings=OCRSettings(use_gpu=args.use_gpu),
    )

    if args.debug_dir is not None:
        _write_debug(dataset, engine_names, args.debug_dir, args.use_gpu)

    body = write_reports(
        metrics,
        markdown_path=args.report,
        json_path=args.json,
        dataset_name=dataset.name,
    )
    print(body)
    return 0


def _resolve_engines(raw: str) -> tuple[str, ...]:
    if raw.strip():
        return tuple(name.strip().lower() for name in raw.split(",") if name.strip())
    return available_engine_names()


def _write_debug(dataset, engine_names: tuple[str, ...], debug_dir: Path, use_gpu: bool) -> None:
    import cv2

    ocr = OCRSettings(use_gpu=use_gpu)
    for engine_name in engine_names:
        try:
            engine = create_engine(engine_name, use_gpu=use_gpu, lang=ocr.lang)
        except RuntimeError as exc:
            logger.warning("Skip debug for %s: %s", engine_name, exc)
            continue
        recognizer = PatternRecognizer(engine, ocr_settings=ocr)
        for sample in dataset.samples:
            frame = cv2.imread(str(sample.image_path))
            if frame is None:
                continue
            output = recognizer.recognize_frame(frame)
            save_debug_artifacts(debug_dir, sample.id, engine_name, output)


if __name__ == "__main__":
    raise SystemExit(main())
