"""Value types for the vision preprocessing pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class VisionProcessResult:
    """
    Outputs from each preprocessing stage.

    Arrays are copies safe to retain after the next ``process`` call.
    ``processed`` is the binary image OCR will consume in Phase 4.
    """

    original_bgr: np.ndarray
    grayscale: np.ndarray
    thresholded: np.ndarray
    processed: np.ndarray
