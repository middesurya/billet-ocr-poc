"""EasyOCR wrapper for billet stamp recognition.

EasyOCR is a PyTorch-based OCR engine supporting 80+ languages with a
simple API. It uses CRAFT for detection and a CRNN for recognition.

Compared to PaddleOCR:
- Simpler setup (pip install easyocr)
- Slightly slower inference
- Better at handling rotated text
- Worse on very low-contrast images (in our testing)

Usage:
    from src.ocr.easyocr_reader import run_easyocr_pipeline
    reading = run_easyocr_pipeline("data/raw/image_22.png")
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

from src.config import EASYOCR_GPU, EASYOCR_LANGUAGES
from src.models import BilletReading, BoundingBox, OCRMethod, OCRResult


# Singleton instance
_reader: Optional["easyocr.Reader"] = None


def initialize_easyocr(
    languages: list[str] = EASYOCR_LANGUAGES,
    gpu: bool = EASYOCR_GPU,
) -> "easyocr.Reader":
    """Initialize EasyOCR reader (singleton, loaded once).

    Args:
        languages: List of language codes (e.g., ['en']).
        gpu: Whether to use GPU acceleration.

    Returns:
        EasyOCR Reader instance.

    Raises:
        ImportError: If easyocr is not installed.
    """
    global _reader
    if _reader is not None:
        return _reader

    try:
        import easyocr
    except ImportError:
        raise ImportError(
            "easyocr not installed. Run: pip install easyocr"
        )

    logger.info("Initializing EasyOCR (languages={}, gpu={})", languages, gpu)
    t0 = time.perf_counter()
    # Suppress stdout during init to avoid Windows charmap errors
    # from EasyOCR's download progress bars (Unicode █ character)
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        _reader = easyocr.Reader(languages, gpu=gpu, verbose=False)
    finally:
        sys.stdout = old_stdout
    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("EasyOCR initialized in {:.0f}ms", elapsed)

    return _reader


def run_ocr(
    image: Union[str, Path, np.ndarray],
) -> list[OCRResult]:
    """Run EasyOCR on an image and return structured results.

    Args:
        image: File path or numpy array (BGR format).

    Returns:
        List of OCRResult sorted by Y-coordinate (top-to-bottom).
    """
    from src.preprocessing.pipeline import load_image

    reader = initialize_easyocr()
    img = load_image(image)

    # EasyOCR expects RGB
    if img.ndim == 3:
        import cv2
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        img_rgb = img

    # Run OCR
    # EasyOCR returns: [[bbox_points, text, confidence], ...]
    raw_results = reader.readtext(img_rgb)

    if not raw_results:
        logger.warning("EasyOCR: no text detected")
        return []

    results: list[OCRResult] = []
    for bbox_points, text, confidence in raw_results:
        # bbox_points is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        points = [(float(p[0]), float(p[1])) for p in bbox_points]
        bbox = BoundingBox(points=points)
        results.append(OCRResult(text=text, confidence=float(confidence), bbox=bbox))

    # Sort by Y-coordinate (top-to-bottom)
    results.sort(key=lambda r: r.bbox.points[0][1] if r.bbox else 0)

    logger.info(
        "EasyOCR: detected {} text regions, texts={}",
        len(results),
        [r.text for r in results],
    )
    return results


def extract_billet_info(ocr_results: list[OCRResult]) -> BilletReading:
    """Extract structured billet reading from EasyOCR results.

    Follows the same two-line grouping logic as paddle_ocr.py:
    - Line 1: 6-digit heat number
    - Line 2: strand + sequence

    Args:
        ocr_results: OCR results sorted top-to-bottom.

    Returns:
        BilletReading with extracted fields.
    """
    from src.ocr.paddle_ocr import extract_billet_info as paddle_extract

    # Reuse PaddleOCR's extraction logic since the output format is compatible
    reading = paddle_extract(ocr_results)
    reading.method = OCRMethod.EASYOCR
    return reading


def run_easyocr_pipeline(
    image: Union[str, Path, np.ndarray],
    method: OCRMethod = OCRMethod.EASYOCR,
) -> BilletReading:
    """Run the full EasyOCR pipeline on a billet image.

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
        logger.warning("EasyOCR pipeline: no text detected")
        return BilletReading(method=method)

    reading = extract_billet_info(ocr_results)
    reading.method = method

    logger.info(
        "EasyOCR pipeline: heat={} strand={} seq={} conf={:.2f} time={:.0f}ms",
        reading.heat_number, reading.strand, reading.sequence,
        reading.confidence, elapsed,
    )
    return reading
