"""OCR engine wrappers for the Billet OCR pipeline."""

from src.ocr.ensemble import run_ensemble_pipeline
from src.ocr.paddle_ocr import (
    extract_billet_info,
    initialize_paddle_ocr,
    run_ocr,
    run_paddle_pipeline,
)
from src.ocr.vlm_reader import (
    read_billet_with_vlm,
    read_billet_with_vlm_for_ground_truth,
)

__all__ = [
    "initialize_paddle_ocr",
    "run_ocr",
    "extract_billet_info",
    "run_paddle_pipeline",
    "read_billet_with_vlm",
    "read_billet_with_vlm_for_ground_truth",
    "run_ensemble_pipeline",
]

# Florence-2 is optional (requires torch + transformers).
try:
    from src.ocr.florence2_reader import read_billet_with_florence2

    __all__.append("read_billet_with_florence2")
except ImportError:
    pass
