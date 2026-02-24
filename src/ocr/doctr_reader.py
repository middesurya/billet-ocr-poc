"""docTR wrapper for billet stamp recognition.

docTR (Document Text Recognition) combines detection + recognition in a
single pipeline. With the PARSeq recognizer (~24M params), it's one of
the fastest scene text recognizers while maintaining good accuracy.

Key characteristics:
- End-to-end detection + recognition (like PaddleOCR)
- PARSeq recognizer is very fast on CPU (~24M params)
- Good at scene text (signs, labels, stamps)
- PyTorch or TensorFlow backends

Usage:
    from src.ocr.doctr_reader import run_doctr_pipeline
    reading = run_doctr_pipeline("data/raw/image_22.png")
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

from src.config import DOCTR_DET_ARCH, DOCTR_DEVICE, DOCTR_RECO_ARCH
from src.models import BilletReading, BoundingBox, OCRMethod, OCRResult


# Singleton instance
_predictor: Optional[object] = None


def initialize_doctr(
    det_arch: str = DOCTR_DET_ARCH,
    reco_arch: str = DOCTR_RECO_ARCH,
    device: str = DOCTR_DEVICE,
) -> object:
    """Initialize docTR OCR predictor (singleton).

    Args:
        det_arch: Detection model architecture (e.g., 'db_resnet50').
        reco_arch: Recognition model architecture (e.g., 'parseq').
        device: Device to run on ('cuda' or 'cpu').

    Returns:
        docTR OCRPredictor instance.

    Raises:
        ImportError: If doctr is not installed.
    """
    global _predictor
    if _predictor is not None:
        return _predictor

    try:
        from doctr.models import ocr_predictor
    except ImportError:
        raise ImportError(
            "doctr not installed. Run: pip install python-doctr[torch]"
        )

    logger.info(
        "Initializing docTR (det={}, reco={}, device={})",
        det_arch, reco_arch, device,
    )
    t0 = time.perf_counter()

    use_gpu = device == "cuda"
    _predictor = ocr_predictor(
        det_arch=det_arch,
        reco_arch=reco_arch,
        pretrained=True,
    )

    if use_gpu:
        try:
            import torch
            if torch.cuda.is_available():
                _predictor = _predictor.cuda()
        except Exception:
            logger.warning("CUDA not available, falling back to CPU")

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("docTR initialized in {:.0f}ms", elapsed)

    return _predictor


def run_ocr(
    image: Union[str, Path, np.ndarray],
) -> list[OCRResult]:
    """Run docTR OCR on an image and return structured results.

    Args:
        image: File path or numpy array (BGR format).

    Returns:
        List of OCRResult sorted by Y-coordinate (top-to-bottom).
    """
    from src.preprocessing.pipeline import load_image

    predictor = initialize_doctr()
    img = load_image(image)

    # docTR expects RGB numpy array
    if img.ndim == 3:
        import cv2
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        # Convert grayscale to 3-channel
        import cv2
        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # docTR expects [0, 1] float or uint8
    # Run prediction
    from doctr.io import DocumentFile
    # docTR can accept numpy arrays directly
    result = predictor([img_rgb])

    ocr_results: list[OCRResult] = []
    h, w = img.shape[:2]

    # docTR result structure: result.pages[0].blocks[].lines[].words[]
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                line_text_parts = []
                line_confidences = []
                line_y_min = float("inf")

                for word in line.words:
                    line_text_parts.append(word.value)
                    line_confidences.append(word.confidence)

                    # word.geometry is ((x_min, y_min), (x_max, y_max)) normalized
                    y_min_norm = word.geometry[0][1]
                    line_y_min = min(line_y_min, y_min_norm)

                if line_text_parts:
                    text = " ".join(line_text_parts)
                    confidence = sum(line_confidences) / len(line_confidences)

                    # Convert normalized coords to pixel coords for bbox
                    if line.geometry:
                        x1 = line.geometry[0][0] * w
                        y1 = line.geometry[0][1] * h
                        x2 = line.geometry[1][0] * w
                        y2 = line.geometry[1][1] * h
                        points = [
                            (x1, y1), (x2, y1),
                            (x2, y2), (x1, y2),
                        ]
                        bbox = BoundingBox(points=points)
                    else:
                        bbox = None

                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=float(confidence),
                        bbox=bbox,
                    ))

    # Sort by Y-coordinate (top-to-bottom)
    ocr_results.sort(
        key=lambda r: r.bbox.points[0][1] if r.bbox else 0
    )

    logger.info(
        "docTR: detected {} text lines, texts={}",
        len(ocr_results),
        [r.text for r in ocr_results],
    )
    return ocr_results


def run_doctr_pipeline(
    image: Union[str, Path, np.ndarray],
    method: OCRMethod = OCRMethod.DOCTR,
) -> BilletReading:
    """Run the full docTR pipeline on a billet image.

    Args:
        image: File path or numpy array (BGR format).
        method: OCR method tag for the result.

    Returns:
        BilletReading with extracted fields.
    """
    t0 = time.perf_counter()
    ocr_results = run_ocr(image)
    elapsed = (time.perf_counter() - t0) * 1000

    if not ocr_results:
        logger.warning("docTR pipeline: no text detected")
        return BilletReading(method=method)

    # Reuse PaddleOCR's extraction logic
    from src.ocr.paddle_ocr import extract_billet_info
    reading = extract_billet_info(ocr_results)
    reading.method = method

    logger.info(
        "docTR pipeline: heat={} strand={} seq={} conf={:.2f} time={:.0f}ms",
        reading.heat_number, reading.strand, reading.sequence,
        reading.confidence, elapsed,
    )
    return reading
