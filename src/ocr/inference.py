"""Shared inference functions for the V11 ensemble pipeline.

Provides reusable functions for per-billet inference, bbox cropping,
and visual annotation. Used by both `scripts/visual_inference.py`
and `src/api/main.py`.
"""

from __future__ import annotations

import re
from typing import Optional

import cv2
import numpy as np

from src.config import FLORENCE2_BBOX_PAD_RATIO
from src.models import BilletReading, OCRMethod


def crop_to_bbox(
    image: np.ndarray,
    bbox: dict,
    pad_ratio: float = FLORENCE2_BBOX_PAD_RATIO,
) -> np.ndarray:
    """Crop image to bounding box with padding.

    Args:
        image: Input BGR image array.
        bbox: Dict with x, y, width, height keys.
        pad_ratio: Padding fraction on each side.

    Returns:
        Cropped image region.
    """
    x = int(bbox["x"])
    y = int(bbox["y"])
    w = int(bbox["width"])
    h = int(bbox["height"])

    pad_x = int(w * pad_ratio)
    pad_y = int(h * pad_ratio)

    img_h, img_w = image.shape[:2]
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, y + h + pad_y)

    return image[y1:y2, x1:x2]


def is_valid_5digit(heat: Optional[str]) -> bool:
    """Check if a heat number is a valid 5-digit number.

    Args:
        heat: Heat number string to validate.

    Returns:
        True if the string is exactly 5 digits.
    """
    return bool(heat and re.match(r"^\d{5}$", heat))


def infer_decision(
    f2: BilletReading,
    paddle: BilletReading,
    ensemble: BilletReading,
) -> str:
    """Infer the cross-validation decision type from results.

    Args:
        f2: Florence-2 multi-orient reading.
        paddle: PaddleOCR reading.
        ensemble: Cross-validation ensemble result.

    Returns:
        Decision string: AGREE, DISAGREE_PADDLE, F2_ONLY, PADDLE_ONLY,
        or NEITHER_VALID.
    """
    f2_valid = is_valid_5digit(f2.heat_number)
    paddle_valid = is_valid_5digit(paddle.heat_number)

    if f2_valid and paddle_valid:
        if f2.heat_number == paddle.heat_number:
            return "AGREE"
        else:
            return "DISAGREE_PADDLE"
    elif f2_valid and not paddle_valid:
        return "F2_ONLY"
    elif paddle_valid and not f2_valid:
        return "PADDLE_ONLY"
    else:
        return "NEITHER_VALID"


def run_billet_inference(bbox_crop: np.ndarray) -> dict:
    """Run the V11 ensemble pipeline on a single billet crop.

    Mirrors benchmark Stages 5+3+6:
    1. F2 Multi-Orient (0 + 180) + format validation
    2. PaddleOCR + CLAHE + character correction
    3. Cross-validation ensemble

    Args:
        bbox_crop: BGR numpy array of the billet crop (with F2 padding).

    Returns:
        Dict with f2_orient, paddle, and ensemble prediction details.
    """
    from src.ocr.ensemble import cross_validate_f2_paddle
    from src.ocr.florence2_reader import read_billet_with_orientation
    from src.ocr.paddle_ocr import run_paddle_pipeline
    from src.postprocess.format_validator import (
        extract_heat_and_sequence,
        validate_florence2_output,
    )
    from src.postprocess.validator import validate_and_correct_reading
    from src.preprocessing.pipeline import preprocess_billet_image

    result: dict = {
        "f2_orient": {"heat_number": None, "confidence": 0.0, "raw_texts": []},
        "paddle": {"heat_number": None, "confidence": 0.0},
        "ensemble": {"heat_number": None, "confidence": 0.0, "decision": "ERROR"},
    }

    # --- F2 Multi-Orient ---
    f2_reading = BilletReading(method=OCRMethod.VLM_FLORENCE2)
    try:
        f2_reading = read_billet_with_orientation(bbox_crop)
        raw_output = " ".join(f2_reading.raw_texts) if f2_reading.raw_texts else ""
        validated_heat = validate_florence2_output(raw_output, f2_reading.heat_number)
        if validated_heat != f2_reading.heat_number:
            f2_reading = BilletReading(
                heat_number=validated_heat,
                sequence=f2_reading.sequence,
                confidence=f2_reading.confidence,
                method=f2_reading.method,
                raw_texts=f2_reading.raw_texts,
            )
        # Recover sequence from raw text if F2 didn't parse it
        if f2_reading.sequence is None and f2_reading.raw_texts:
            raw_output = " ".join(f2_reading.raw_texts)
            _, recovered_seq = extract_heat_and_sequence(raw_output)
            if recovered_seq:
                f2_reading = BilletReading(
                    heat_number=f2_reading.heat_number,
                    sequence=recovered_seq,
                    confidence=f2_reading.confidence,
                    method=f2_reading.method,
                    raw_texts=f2_reading.raw_texts,
                )
        result["f2_orient"] = {
            "heat_number": f2_reading.heat_number,
            "sequence": f2_reading.sequence,
            "confidence": f2_reading.confidence,
            "raw_texts": f2_reading.raw_texts,
        }
    except Exception as exc:
        result["f2_orient"]["error"] = str(exc)

    # --- PaddleOCR + CLAHE ---
    paddle_reading = BilletReading(method=OCRMethod.PADDLE_BBOX_CROP)
    try:
        preprocessed, _ = preprocess_billet_image(bbox_crop)
        paddle_reading = run_paddle_pipeline(
            preprocessed, method=OCRMethod.PADDLE_BBOX_CROP
        )
        paddle_reading = validate_and_correct_reading(paddle_reading)
        result["paddle"] = {
            "heat_number": paddle_reading.heat_number,
            "sequence": paddle_reading.sequence,
            "confidence": paddle_reading.confidence,
        }
    except Exception as exc:
        result["paddle"]["error"] = str(exc)

    # --- Cross-validation ensemble ---
    try:
        ensemble_result = cross_validate_f2_paddle(f2_reading, paddle_reading)
        decision = infer_decision(f2_reading, paddle_reading, ensemble_result)
        result["ensemble"] = {
            "heat_number": ensemble_result.heat_number,
            "sequence": ensemble_result.sequence,
            "confidence": ensemble_result.confidence,
            "decision": decision,
        }
    except Exception as exc:
        result["ensemble"]["error"] = str(exc)

    return result


def draw_annotated_image(
    image: np.ndarray,
    bboxes: list[dict],
    predictions: list[dict],
) -> np.ndarray:
    """Draw bounding boxes and predictions on the source image.

    Args:
        image: BGR source image.
        bboxes: List of bbox dicts with x, y, width, height.
        predictions: List of per-billet prediction dicts (from run_billet_inference).

    Returns:
        Annotated BGR image.
    """
    annotated = image.copy()

    for idx, (bbox, pred) in enumerate(zip(bboxes, predictions)):
        ens = pred.get("ensemble", {})
        heat = ens.get("heat_number") or "???"
        conf = ens.get("confidence", 0.0)

        # Color by confidence
        if conf >= 0.80:
            color = (0, 200, 0)  # green
        elif conf >= 0.50:
            color = (0, 200, 255)  # yellow (BGR)
        else:
            color = (0, 0, 200)  # red

        x = int(bbox["x"])
        y = int(bbox["y"])
        w = int(bbox["width"])
        h = int(bbox["height"])

        # Draw rectangle
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        # Label
        seq = ens.get("sequence") or ""
        label = f"[{idx}] {heat} / {seq} ({conf:.0%})" if seq else f"[{idx}] {heat} ({conf:.0%})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)

        # Background rectangle for readability
        label_y = max(y - 6, th + 4)
        cv2.rectangle(
            annotated,
            (x, label_y - th - 4),
            (x + tw + 4, label_y + baseline),
            color,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (x + 2, label_y - 2),
            font,
            scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    return annotated
