"""TrOCR wrapper for billet stamp recognition.

TrOCR (Transformer-based OCR) is Microsoft's encoder-decoder model that
combines a ViT image encoder with a text decoder. The 'large-printed'
variant is specifically trained on printed text -- a good match for
dot-matrix stamps.

Key characteristics:
- Recognition-only model (no detection -- needs separate text detection)
- Uses PaddleOCR's DBNet++ for detection, then TrOCR for recognition
- Strong on printed/stamped text (608M params, large model)
- Slower than PaddleOCR but potentially more accurate on degraded text

Usage:
    from src.ocr.trocr_reader import run_trocr_pipeline
    reading = run_trocr_pipeline("data/raw/image_22.png")
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

from src.config import TROCR_DEVICE, TROCR_MODEL_ID
from src.models import BilletReading, OCRMethod, OCRResult


# Singleton instances
_processor: Optional[object] = None
_model: Optional[object] = None


def initialize_trocr(
    model_id: str = TROCR_MODEL_ID,
    device: str = TROCR_DEVICE,
) -> tuple:
    """Initialize TrOCR processor and model (singleton).

    Args:
        model_id: HuggingFace model ID for TrOCR.
        device: Device to run on ('cuda' or 'cpu').

    Returns:
        Tuple of (processor, model).

    Raises:
        ImportError: If transformers is not installed.
    """
    global _processor, _model
    if _processor is not None and _model is not None:
        return _processor, _model

    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    except ImportError:
        raise ImportError(
            "transformers not installed. Run: pip install transformers"
        )

    logger.info("Initializing TrOCR (model={}, device={})", model_id, device)
    t0 = time.perf_counter()

    _processor = TrOCRProcessor.from_pretrained(model_id)
    _model = VisionEncoderDecoderModel.from_pretrained(model_id)

    import torch
    actual_device = device if torch.cuda.is_available() or device == "cpu" else "cpu"
    _model = _model.to(actual_device)
    # Set model to inference mode
    _model.requires_grad_(False)

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("TrOCR initialized in {:.0f}ms on {}", elapsed, actual_device)

    return _processor, _model


def _detect_text_regions(image: np.ndarray) -> list[tuple[np.ndarray, float]]:
    """Detect text regions using PaddleOCR's detector.

    TrOCR is recognition-only, so we need a separate detector.
    We reuse PaddleOCR's DBNet++ detector for text region detection.

    Args:
        image: BGR image array.

    Returns:
        List of (cropped_region, y_coord) tuples for each detected text line.
    """
    from src.ocr.paddle_ocr import initialize_paddle_ocr

    ocr = initialize_paddle_ocr()

    # Use PaddleOCR for detection only
    result = ocr.predict(image, print_result=False)
    if result is None or len(result) == 0:
        return []

    regions = []
    for res in result:
        if not hasattr(res, "dt_polys") or res.dt_polys is None:
            continue
        for poly in res.dt_polys:
            pts = np.array(poly, dtype=np.int32)
            x_min, y_min = pts.min(axis=0)
            x_max, y_max = pts.max(axis=0)

            # Add padding
            pad = 5
            x_min = max(0, x_min - pad)
            y_min = max(0, y_min - pad)
            x_max = min(image.shape[1], x_max + pad)
            y_max = min(image.shape[0], y_max + pad)

            crop = image[y_min:y_max, x_min:x_max]
            if crop.size > 0:
                regions.append((crop, float(y_min)))

    # Sort top-to-bottom
    regions.sort(key=lambda x: x[1])
    return regions


def _recognize_region(
    region: np.ndarray,
    processor: object,
    model: object,
) -> tuple[str, float]:
    """Recognize text in a single cropped region using TrOCR.

    Args:
        region: Cropped BGR image of a text line.
        processor: TrOCR processor.
        model: TrOCR model.

    Returns:
        Tuple of (recognized_text, confidence_score).
    """
    import torch
    from PIL import Image
    import cv2

    # Convert BGR -> RGB -> PIL
    rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    # Process
    pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
    device = next(model.parameters()).device
    pixel_values = pixel_values.to(device)

    with torch.no_grad():
        outputs = model.generate(
            pixel_values,
            max_length=32,
            num_beams=4,
            output_scores=True,
            return_dict_in_generate=True,
        )

    # Decode
    text = processor.batch_decode(outputs.sequences, skip_special_tokens=True)[0]

    # Compute confidence from beam scores
    if hasattr(outputs, "sequences_scores") and outputs.sequences_scores is not None:
        # Log probability -> probability
        confidence = float(torch.exp(outputs.sequences_scores[0]).item())
        confidence = min(max(confidence, 0.0), 1.0)
    else:
        confidence = 0.5  # Default if scores unavailable

    return text.strip(), confidence


def run_trocr_pipeline(
    image: Union[str, Path, np.ndarray],
    method: OCRMethod = OCRMethod.TROCR,
) -> BilletReading:
    """Run the full TrOCR pipeline on a billet image.

    Pipeline: PaddleOCR detection -> TrOCR recognition -> billet extraction.

    Args:
        image: File path or numpy array (BGR format).
        method: OCR method tag for the result.

    Returns:
        BilletReading with extracted fields.
    """
    from src.preprocessing.pipeline import load_image

    t0 = time.perf_counter()
    img = load_image(image)

    # Initialize TrOCR
    processor, model = initialize_trocr()

    # Detect text regions
    regions = _detect_text_regions(img)
    if not regions:
        logger.warning("TrOCR pipeline: no text regions detected")
        return BilletReading(method=method)

    # Recognize each region
    ocr_results: list[OCRResult] = []
    for region_img, y_coord in regions:
        text, conf = _recognize_region(region_img, processor, model)
        if text:
            ocr_results.append(OCRResult(text=text, confidence=conf))

    if not ocr_results:
        logger.warning("TrOCR pipeline: no text recognized")
        return BilletReading(method=method)

    # Extract billet info using shared extraction logic
    from src.ocr.paddle_ocr import extract_billet_info
    reading = extract_billet_info(ocr_results)
    reading.method = method

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info(
        "TrOCR pipeline: heat={} strand={} seq={} conf={:.2f} time={:.0f}ms",
        reading.heat_number, reading.strand, reading.sequence,
        reading.confidence, elapsed,
    )
    return reading
