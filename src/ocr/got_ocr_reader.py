"""GOT-OCR-2.0 wrapper for billet stamp recognition.

GOT-OCR-2.0 (General OCR Theory) by StepFun is a unified OCR model that
performs both detection and recognition in a single forward pass. It's a
560M parameter model that handles scene text, documents, and more.

Key characteristics:
- Single-pass detection + recognition (no separate detector needed)
- 560M params -- requires GPU for reasonable speed
- Good at scene text and complex layouts
- Requires significant VRAM (~4GB)

Usage:
    from src.ocr.got_ocr_reader import run_got_ocr_pipeline
    reading = run_got_ocr_pipeline("data/raw/image_22.png")
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

from src.config import GOT_OCR_DEVICE, GOT_OCR_MODEL_ID
from src.models import BilletReading, OCRMethod, OCRResult


# Singleton instances
_tokenizer: Optional[object] = None
_model: Optional[object] = None


def is_gpu_available() -> bool:
    """Check if CUDA GPU is available.

    Returns:
        True if CUDA is available and has at least one GPU.
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def initialize_got_ocr(
    model_id: str = GOT_OCR_MODEL_ID,
    device: str = GOT_OCR_DEVICE,
) -> tuple:
    """Initialize GOT-OCR tokenizer and model (singleton).

    Args:
        model_id: HuggingFace model ID.
        device: Device to run on ('cuda' required).

    Returns:
        Tuple of (tokenizer, model).

    Raises:
        ImportError: If transformers/torch not installed.
        RuntimeError: If GPU not available (GOT-OCR requires GPU).
    """
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    if not is_gpu_available():
        raise RuntimeError(
            "GOT-OCR-2.0 requires a CUDA GPU. No GPU detected. "
            "Use PaddleOCR or EasyOCR instead for CPU inference."
        )

    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
    except ImportError:
        raise ImportError(
            "transformers and torch required. Run: pip install transformers torch"
        )

    logger.info("Initializing GOT-OCR (model={}, device={})", model_id, device)
    t0 = time.perf_counter()

    _tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    _model = AutoModel.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=torch.float16,
        device_map=device,
    )
    # Set model to inference mode (no gradient computation)
    _model.requires_grad_(False)

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("GOT-OCR initialized in {:.0f}ms", elapsed)

    return _tokenizer, _model


def run_got_ocr_pipeline(
    image: Union[str, Path, np.ndarray],
    method: OCRMethod = OCRMethod.GOT_OCR,
) -> BilletReading:
    """Run the full GOT-OCR pipeline on a billet image.

    GOT-OCR operates on image files, so numpy arrays are saved to a
    temporary file first.

    Args:
        image: File path or numpy array (BGR format).
        method: OCR method tag for the result.

    Returns:
        BilletReading with extracted fields.
    """
    import tempfile
    import cv2

    from src.preprocessing.pipeline import load_image

    t0 = time.perf_counter()

    # GOT-OCR needs a file path
    if isinstance(image, np.ndarray):
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cv2.imwrite(tmp.name, image)
        img_path = tmp.name
    elif isinstance(image, (str, Path)):
        img_path = str(image)
    else:
        raise TypeError(f"Expected str, Path, or ndarray, got {type(image)}")

    try:
        tokenizer, model = initialize_got_ocr()

        # GOT-OCR chat interface
        result = model.chat(tokenizer, img_path, ocr_type="ocr")

        if not result or not result.strip():
            logger.warning("GOT-OCR: no text detected")
            return BilletReading(method=method)

        # Parse the OCR result text
        raw_text = result.strip()
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

        logger.info("GOT-OCR raw output: {}", lines)

        # Create OCR results and extract billet info
        ocr_results = [
            OCRResult(text=line, confidence=0.7)  # GOT-OCR lacks per-line confidence
            for line in lines
        ]

        from src.ocr.paddle_ocr import extract_billet_info
        reading = extract_billet_info(ocr_results)
        reading.method = method

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "GOT-OCR pipeline: heat={} strand={} seq={} conf={:.2f} time={:.0f}ms",
            reading.heat_number, reading.strand, reading.sequence,
            reading.confidence, elapsed,
        )
        return reading

    finally:
        # Clean up temp file if we created one
        if isinstance(image, np.ndarray):
            import os
            try:
                os.unlink(img_path)
            except OSError:
                pass
