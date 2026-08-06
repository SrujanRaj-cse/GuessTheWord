"""Execute benchmark runs over a labeled dataset."""

from __future__ import annotations

import time
from dataclasses import dataclass

import cv2

from config.settings import OCRSettings, VisionSettings
from ocr.dataset import BenchmarkDataset, BenchmarkSample
from ocr.engines import create_engine
from ocr.pattern_recognizer import PatternRecognizer
from tools.ocr_validate.metrics import SampleMetrics, build_sample_metrics


@dataclass(frozen=True)
class BenchmarkRunConfig:
    """Parameters for one validation benchmark."""

    runs: int = 3
    warmup: int = 1
    use_gpu: bool = False


def run_benchmark(
    dataset: BenchmarkDataset,
    engine_names: tuple[str, ...],
    config: BenchmarkRunConfig | None = None,
    vision_settings: VisionSettings | None = None,
    ocr_settings: OCRSettings | None = None,
) -> list[SampleMetrics]:
    """
    Benchmark each engine on every dataset sample.

    Skips engines that fail to construct (caller should log errors separately).
    """
    cfg = config or BenchmarkRunConfig()
    vision = vision_settings or VisionSettings()
    ocr = ocr_settings or OCRSettings()
    metrics: list[SampleMetrics] = []

    for engine_name in engine_names:
        try:
            engine = create_engine(engine_name, use_gpu=cfg.use_gpu, lang=ocr.lang)
        except RuntimeError:
            continue
        recognizer = PatternRecognizer(engine, vision_settings=vision, ocr_settings=ocr)
        for sample in dataset.samples:
            row = _benchmark_sample(recognizer, sample, cfg)
            metrics.append(row)
    return metrics


def _benchmark_sample(
    recognizer: PatternRecognizer,
    sample: BenchmarkSample,
    config: BenchmarkRunConfig,
) -> SampleMetrics:
    frame = cv2.imread(str(sample.image_path))
    if frame is None:
        raise ValueError(f"Failed to read image {sample.image_path}")

    for _ in range(config.warmup):
        recognizer.recognize_frame(frame)

    latencies: list[float] = []
    cpu_times: list[float] = []
    last = recognizer.recognize_frame(frame)
    for _ in range(max(config.runs - 1, 0)):
        cpu_start = time.process_time()
        start = time.perf_counter()
        last = recognizer.recognize_frame(frame)
        latencies.append((time.perf_counter() - start) * 1000.0)
        cpu_times.append(time.process_time() - cpu_start)

    if not latencies:
        latencies = [last.timing.total_ms]
        cpu_times = [0.0]

    return build_sample_metrics(
        sample_id=sample.id,
        engine=recognizer.engine_name,
        expected_letters=sample.expected_letters,
        expected_pattern=sample.expected_pattern,
        actual_letters=last.result.letters,
        actual_pattern=last.result.pattern,
        confidence=last.result.confidence,
        latency_ms=sum(latencies) / len(latencies),
        cpu_seconds=sum(cpu_times) / len(cpu_times),
    )
