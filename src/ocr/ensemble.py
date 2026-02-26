"""Ensemble pipeline orchestrating PaddleOCR and VLM (Claude Vision) fallback.

The ensemble runs a confidence-gated cascade:
1. PaddleOCR processes the image first (fast, free, offline-capable).
2. If PaddleOCR confidence is below the threshold, Claude Vision is invoked
   as a fallback on the same image.
3. If both engines struggle, the reading with higher confidence wins.

The ``skip_paddle`` flag bypasses PaddleOCR entirely for VLM-only evaluation.

Ensemble V2 (Florence-2-first cascade):
1. Florence-2 fine-tuned on bbox crop (fast, ~200ms)
2. Florence-2 fine-tuned on center crop (backup, ~200ms)
3. Cross-validate: if both agree, boost confidence
4. VLM Claude Vision API fallback for genuinely hard cases

Every call logs which execution path was taken and the confidence scores of
each engine that ran, enabling downstream analysis of routing decisions.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from loguru import logger

from src.config import (
    BBOX_ANNOTATIONS_PATH,
    FLORENCE2_BBOX_PAD_RATIO,
    OCR_CONFIDENCE_THRESHOLD,
)
from src.models import BilletReading, OCRMethod


# ---------------------------------------------------------------------------
# Ensemble V2 result tracking
# ---------------------------------------------------------------------------

@dataclass
class EnsembleV2Result:
    """Detailed result from the V2 ensemble pipeline.

    Tracks which tier produced the final answer, per-tier readings,
    latency breakdown, and whether VLM was invoked.

    Attributes:
        reading: The final BilletReading selected by the ensemble.
        tier: Which tier produced the answer (1-4).
        tier_label: Human-readable tier description.
        florence2_bbox_reading: Tier 1 result (bbox crop).
        florence2_crop_reading: Tier 2 result (center crop).
        vlm_reading: Tier 4 result (VLM fallback), None if not invoked.
        vlm_called: Whether the VLM API was invoked.
        total_ms: Total pipeline wall-clock time in milliseconds.
        tier_times_ms: Per-tier latency breakdown.
    """
    reading: BilletReading
    tier: int = 0
    tier_label: str = ""
    florence2_bbox_reading: Optional[BilletReading] = None
    florence2_crop_reading: Optional[BilletReading] = None
    vlm_reading: Optional[BilletReading] = None
    vlm_called: bool = False
    total_ms: float = 0.0
    tier_times_ms: dict[str, float] = field(default_factory=dict)


def _is_valid_heat(heat: Optional[str]) -> bool:
    """Check if a heat number looks valid (5-7 digits).

    Args:
        heat: Heat number string to validate.

    Returns:
        True if the string is 5-7 digits.
    """
    if not heat:
        return False
    return bool(re.match(r"^\d{5,7}$", heat))


def _is_valid_5digit_heat(heat: Optional[str]) -> bool:
    """Check if a heat number is a valid 5-digit Roboflow-format number.

    Args:
        heat: Heat number string to validate.

    Returns:
        True if the string is exactly 5 digits.
    """
    if not heat:
        return False
    return bool(re.match(r"^\d{5}$", heat))


def cross_validate_f2_paddle(
    f2_result: BilletReading,
    paddle_result: BilletReading,
    vlm_result: Optional[BilletReading] = None,
) -> BilletReading:
    """Cross-validate Florence-2 and PaddleOCR results for higher accuracy.

    Decision rules:
        1. Both agree on same 5-digit heat → high confidence, use either
        2. Both valid 5-digit but disagree → prefer F2 Orient (69.9% > 65.2%)
        3. Only one valid → use the valid one
        4. Neither valid → use VLM fallback if available, else best partial

    Args:
        f2_result: BilletReading from Florence-2 (with format validation).
        paddle_result: BilletReading from PaddleOCR + CLAHE.
        vlm_result: Optional BilletReading from Claude Vision (VLM fallback).

    Returns:
        Best combined BilletReading with method indicating the source.
    """
    f2_valid = _is_valid_5digit_heat(f2_result.heat_number)
    paddle_valid = _is_valid_5digit_heat(paddle_result.heat_number)

    if f2_valid and paddle_valid:
        if f2_result.heat_number == paddle_result.heat_number:
            # Agreement — high confidence
            boosted_conf = min(1.0, max(f2_result.confidence, paddle_result.confidence) + 0.2)
            logger.info(
                f"[CrossValidate] AGREE | heat={f2_result.heat_number} | "
                f"conf={boosted_conf:.2f}"
            )
            return BilletReading(
                heat_number=f2_result.heat_number,
                sequence=f2_result.sequence or paddle_result.sequence,
                confidence=boosted_conf,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=f2_result.raw_texts,
            )
        else:
            # Disagreement — prefer PaddleOCR (fewer confident errors on disagree subset).
            # F2 zero-shot confidence capped at 0.70, Paddle reaches 0.98+.
            # Tested: prefer-F2 dropped ensemble 77→72%, confidence-weighted
            # is functionally identical to prefer-Paddle. Keep simple rule.
            logger.info(
                f"[CrossValidate] DISAGREE | f2={f2_result.heat_number} "
                f"paddle={paddle_result.heat_number} → prefer PaddleOCR"
            )
            return BilletReading(
                heat_number=paddle_result.heat_number,
                sequence=paddle_result.sequence,
                confidence=paddle_result.confidence * 0.9,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=paddle_result.raw_texts,
            )
    elif f2_valid:
        logger.info(
            f"[CrossValidate] F2_ONLY | heat={f2_result.heat_number}"
        )
        return BilletReading(
            heat_number=f2_result.heat_number,
            sequence=f2_result.sequence,
            confidence=f2_result.confidence,
            method=OCRMethod.ENSEMBLE_V2,
            raw_texts=f2_result.raw_texts,
        )
    elif paddle_valid:
        logger.info(
            f"[CrossValidate] PADDLE_ONLY | heat={paddle_result.heat_number}"
        )
        return BilletReading(
            heat_number=paddle_result.heat_number,
            sequence=paddle_result.sequence,
            confidence=paddle_result.confidence,
            method=OCRMethod.ENSEMBLE_V2,
            raw_texts=paddle_result.raw_texts,
        )
    else:
        # Neither F2 nor Paddle produced a valid 5-digit heat.
        # Try VLM fallback if available — highest value when both engines fail.
        if vlm_result is not None and vlm_result.heat_number:
            vlm_valid = _is_valid_5digit_heat(vlm_result.heat_number)
            logger.info(
                f"[CrossValidate] NEITHER_VALID → VLM fallback | "
                f"vlm_heat={vlm_result.heat_number} valid_5d={vlm_valid} | "
                f"f2={f2_result.heat_number} paddle={paddle_result.heat_number}"
            )
            return BilletReading(
                heat_number=vlm_result.heat_number,
                sequence=vlm_result.sequence,
                confidence=vlm_result.confidence * 0.8,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=vlm_result.raw_texts,
            )

        # No VLM available — return best partial from F2 or Paddle
        logger.info(
            f"[CrossValidate] NEITHER_VALID | f2={f2_result.heat_number} "
            f"paddle={paddle_result.heat_number} → fallback best partial"
        )
        return BilletReading(
            heat_number=paddle_result.heat_number or f2_result.heat_number,
            sequence=paddle_result.sequence or f2_result.sequence,
            confidence=max(paddle_result.confidence, f2_result.confidence) * 0.5,
            method=OCRMethod.ENSEMBLE_V2,
            raw_texts=paddle_result.raw_texts or f2_result.raw_texts,
        )


def _load_bbox_for_image(
    image_path: Union[str, Path],
) -> Optional[dict]:
    """Load the largest bounding box for the given image from annotations.

    Args:
        image_path: Path to the image file.

    Returns:
        The largest bbox dict, or None if not available.
    """
    if not BBOX_ANNOTATIONS_PATH.exists():
        return None

    import json

    with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as f:
        all_bboxes = json.load(f)

    img_name = Path(image_path).name
    bboxes = all_bboxes.get(img_name, [])
    if not bboxes:
        return None

    return max(bboxes, key=lambda b: b.get("width", 0) * b.get("height", 0))


def _load_all_bboxes_for_image(
    image_path: Union[str, Path],
) -> list[dict]:
    """Load ALL bounding boxes for the given image, sorted by area descending.

    Args:
        image_path: Path to the image file.

    Returns:
        List of bbox dicts sorted by area (largest first). Empty if none found.
    """
    if not BBOX_ANNOTATIONS_PATH.exists():
        return []

    import json

    with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as f:
        all_bboxes = json.load(f)

    img_name = Path(image_path).name
    bboxes = all_bboxes.get(img_name, [])
    return sorted(bboxes, key=lambda b: b.get("width", 0) * b.get("height", 0), reverse=True)


def read_all_billets(
    image: Union[str, Path, np.ndarray],
    confidence_threshold: float = 0.80,
    skip_vlm: bool = False,
) -> list[BilletReading]:
    """Read ALL billets in a surveillance image.

    Production API for edge deployment (Jetson Orin). Processes every detected
    billet bounding box independently through the Florence-2 + VLM cascade.

    Pipeline per billet:
        1. Crop to bbox with padding
        2. Florence-2 OCR on crop
        3. Format validation
        4. If confidence < threshold and skip_vlm is False: VLM fallback on crop

    Args:
        image: Raw surveillance image — file path or BGR numpy array.
        confidence_threshold: Minimum confidence to accept without VLM fallback.
        skip_vlm: If True, skip VLM fallback (cost-free inference only).

    Returns:
        List of BilletReadings (one per detected billet). Empty if no bboxes found.
    """
    # Load image
    raw_img: np.ndarray
    image_path: Optional[Path] = None
    if isinstance(image, (str, Path)):
        raw_img = cv2.imread(str(image))
        if raw_img is None:
            logger.error(f"[ReadAllBillets] Failed to load image: {image}")
            return []
        image_path = Path(image)
    else:
        raw_img = image

    # Load all bboxes
    if image_path is not None:
        bboxes = _load_all_bboxes_for_image(image_path)
    else:
        logger.warning("[ReadAllBillets] numpy input — cannot auto-load bboxes")
        return []

    if not bboxes:
        logger.warning(f"[ReadAllBillets] No bboxes found for {image_path}")
        return []

    logger.info(f"[ReadAllBillets] Processing {len(bboxes)} billets from {image_path.name}")

    readings: list[BilletReading] = []
    for idx, bbox in enumerate(bboxes):
        try:
            bbox_crop = _crop_to_bbox(raw_img, bbox)

            # Florence-2 OCR
            from src.ocr.florence2_reader import read_billet_with_florence2
            from src.postprocess.format_validator import validate_florence2_output

            reading = read_billet_with_florence2(bbox_crop)

            # Format validation
            raw_output = " ".join(reading.raw_texts) if reading.raw_texts else ""
            validated_heat = validate_florence2_output(raw_output, reading.heat_number)
            if validated_heat != reading.heat_number:
                reading = BilletReading(
                    heat_number=validated_heat,
                    strand=reading.strand,
                    sequence=reading.sequence,
                    confidence=reading.confidence,
                    method=reading.method,
                    raw_texts=reading.raw_texts,
                )

            # VLM fallback for low confidence
            if (
                not skip_vlm
                and reading.confidence < confidence_threshold
            ):
                vlm_reading = _run_vlm(bbox_crop)
                if vlm_reading.heat_number and vlm_reading.confidence > reading.confidence:
                    reading = vlm_reading

            readings.append(reading)
            logger.info(
                f"  Billet[{idx}] heat={reading.heat_number} "
                f"conf={reading.confidence:.2f}"
            )
        except Exception as exc:
            logger.error(f"  Billet[{idx}] error: {exc}")
            readings.append(BilletReading(method=OCRMethod.ENSEMBLE_V2))

    logger.info(f"[ReadAllBillets] Completed: {len(readings)} billets processed")
    return readings


def _crop_to_bbox(
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


def _center_crop(image: np.ndarray, crop_ratio: float = 0.6) -> np.ndarray:
    """Crop center portion of image.

    Args:
        image: Input image array.
        crop_ratio: Fraction of each dimension to keep.

    Returns:
        Center-cropped image.
    """
    h, w = image.shape[:2]
    margin_x = int(w * (1 - crop_ratio) / 2)
    margin_y = int(h * (1 - crop_ratio) / 2)
    return image[margin_y:h - margin_y, margin_x:w - margin_x]


def read_billet(
    image: Union[str, Path, np.ndarray],
    strategy: str = "ensemble_v2",
    confidence_threshold: float = 0.80,
    bbox: Optional[dict] = None,
) -> BilletReading:
    """Production entry point — runs the optimal pipeline.

    Dispatches to either the V1 ensemble (PaddleOCR → VLM) or the V2
    ensemble (Florence-2 cascade → VLM fallback) based on strategy.

    Args:
        image: Raw image — file path or BGR numpy array.
        strategy: Pipeline strategy. "ensemble_v2" (default) or "ensemble_v1".
        confidence_threshold: Minimum confidence to accept a reading.
        bbox: Optional pre-loaded bounding box dict. If None, auto-loaded.

    Returns:
        A BilletReading with the best available result.
    """
    if strategy == "ensemble_v1":
        return run_ensemble_pipeline(image)
    elif strategy == "ensemble_v2":
        result = run_ensemble_v2(
            image,
            confidence_threshold=confidence_threshold,
            bbox=bbox,
        )
        return result.reading
    else:
        raise ValueError(f"Unknown strategy: {strategy!r}")


def run_ensemble_v2(
    image: Union[str, Path, np.ndarray],
    confidence_threshold: float = 0.80,
    bbox: Optional[dict] = None,
    skip_vlm: bool = False,
) -> EnsembleV2Result:
    """Run the V2 Florence-2-first ensemble cascade.

    4-tier cascade:
        Tier 1: Florence-2 fine-tuned on bbox crop (fast, ~200ms).
                If heat_number is valid and confidence >= threshold → DONE.
        Tier 2: Florence-2 fine-tuned on center crop (backup, ~200ms).
                If agrees with Tier 1 OR confidence >= threshold → DONE.
        Tier 3: Cross-validate — if Tier 1 and Tier 2 agree, boost
                confidence and return → DONE.
        Tier 4: VLM Claude Vision API fallback (~2s, $0.01/image).
                Final answer for genuinely hard cases.

    Args:
        image: Raw image — file path (str/Path) or BGR numpy array.
        confidence_threshold: Minimum confidence to accept without fallback.
        bbox: Optional pre-loaded bounding box dict. If None, auto-loaded
            from roboflow_bboxes.json.
        skip_vlm: If True, skip the VLM fallback tier (for cost-free benchmarks).

    Returns:
        EnsembleV2Result with detailed tier breakdown.
    """
    t_start = time.perf_counter()
    tier_times: dict[str, float] = {}

    # Load image as numpy array if it's a path
    raw_img: np.ndarray
    if isinstance(image, (str, Path)):
        raw_img = cv2.imread(str(image))
        if raw_img is None:
            logger.error(f"[EnsembleV2] Failed to load image: {image}")
            return EnsembleV2Result(
                reading=BilletReading(method=OCRMethod.ENSEMBLE_V2),
                tier=0,
                tier_label="load_failed",
            )
        image_path = Path(image)
    else:
        raw_img = image
        image_path = None

    # Auto-load bbox if not provided
    if bbox is None and image_path is not None:
        bbox = _load_bbox_for_image(image_path)

    # ------------------------------------------------------------------
    # Tier 1: Florence-2 on bbox crop
    # ------------------------------------------------------------------
    t1 = time.perf_counter()
    f2_bbox_reading: Optional[BilletReading] = None

    if bbox is not None:
        try:
            bbox_crop = _crop_to_bbox(raw_img, bbox)

            # Apply super-resolution to small crops
            from src.preprocessing.super_resolution import upscale_image
            bbox_crop = upscale_image(bbox_crop)

            from src.ocr.florence2_reader import read_billet_with_florence2
            f2_bbox_reading = read_billet_with_florence2(bbox_crop)

            # Apply format validation
            from src.postprocess.format_validator import validate_florence2_output
            raw_output = " ".join(f2_bbox_reading.raw_texts) if f2_bbox_reading.raw_texts else ""
            validated_heat = validate_florence2_output(raw_output, f2_bbox_reading.heat_number)
            if validated_heat != f2_bbox_reading.heat_number:
                f2_bbox_reading = BilletReading(
                    heat_number=validated_heat,
                    strand=f2_bbox_reading.strand,
                    sequence=f2_bbox_reading.sequence,
                    confidence=f2_bbox_reading.confidence,
                    method=f2_bbox_reading.method,
                    raw_texts=f2_bbox_reading.raw_texts,
                )
        except Exception as exc:
            logger.error(f"[EnsembleV2] Tier 1 (bbox crop) error: {exc}")

    tier_times["tier1_bbox_ms"] = (time.perf_counter() - t1) * 1000

    # Check Tier 1 result
    if (
        f2_bbox_reading is not None
        and _is_valid_heat(f2_bbox_reading.heat_number)
        and f2_bbox_reading.confidence >= confidence_threshold
    ):
        total_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"[EnsembleV2] Tier 1 ACCEPTED | heat={f2_bbox_reading.heat_number} | "
            f"conf={f2_bbox_reading.confidence:.2f} | time={total_ms:.0f}ms"
        )
        return EnsembleV2Result(
            reading=BilletReading(
                heat_number=f2_bbox_reading.heat_number,
                strand=f2_bbox_reading.strand,
                sequence=f2_bbox_reading.sequence,
                confidence=f2_bbox_reading.confidence,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=f2_bbox_reading.raw_texts,
            ),
            tier=1,
            tier_label="florence2_bbox_crop",
            florence2_bbox_reading=f2_bbox_reading,
            total_ms=total_ms,
            tier_times_ms=tier_times,
        )

    # ------------------------------------------------------------------
    # Tier 2: Florence-2 on center crop
    # ------------------------------------------------------------------
    t2 = time.perf_counter()
    f2_crop_reading: Optional[BilletReading] = None

    try:
        center_cropped = _center_crop(raw_img)

        from src.ocr.florence2_reader import read_billet_with_florence2
        f2_crop_reading = read_billet_with_florence2(center_cropped)

        # Apply format validation
        from src.postprocess.format_validator import validate_florence2_output
        raw_output = " ".join(f2_crop_reading.raw_texts) if f2_crop_reading.raw_texts else ""
        validated_heat = validate_florence2_output(raw_output, f2_crop_reading.heat_number)
        if validated_heat != f2_crop_reading.heat_number:
            f2_crop_reading = BilletReading(
                heat_number=validated_heat,
                strand=f2_crop_reading.strand,
                sequence=f2_crop_reading.sequence,
                confidence=f2_crop_reading.confidence,
                method=f2_crop_reading.method,
                raw_texts=f2_crop_reading.raw_texts,
            )
    except Exception as exc:
        logger.error(f"[EnsembleV2] Tier 2 (center crop) error: {exc}")

    tier_times["tier2_crop_ms"] = (time.perf_counter() - t2) * 1000

    # Check Tier 2: accept if confidence >= threshold
    if (
        f2_crop_reading is not None
        and _is_valid_heat(f2_crop_reading.heat_number)
        and f2_crop_reading.confidence >= confidence_threshold
    ):
        total_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"[EnsembleV2] Tier 2 ACCEPTED | heat={f2_crop_reading.heat_number} | "
            f"conf={f2_crop_reading.confidence:.2f} | time={total_ms:.0f}ms"
        )
        return EnsembleV2Result(
            reading=BilletReading(
                heat_number=f2_crop_reading.heat_number,
                strand=f2_crop_reading.strand,
                sequence=f2_crop_reading.sequence,
                confidence=f2_crop_reading.confidence,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=f2_crop_reading.raw_texts,
            ),
            tier=2,
            tier_label="florence2_center_crop",
            florence2_bbox_reading=f2_bbox_reading,
            florence2_crop_reading=f2_crop_reading,
            total_ms=total_ms,
            tier_times_ms=tier_times,
        )

    # ------------------------------------------------------------------
    # Tier 3: Cross-validate Tier 1 and Tier 2
    # ------------------------------------------------------------------
    bbox_heat = f2_bbox_reading.heat_number if f2_bbox_reading else None
    crop_heat = f2_crop_reading.heat_number if f2_crop_reading else None

    if (
        _is_valid_heat(bbox_heat)
        and _is_valid_heat(crop_heat)
        and bbox_heat == crop_heat
    ):
        # Both agree — boost confidence and return
        bbox_conf = f2_bbox_reading.confidence if f2_bbox_reading else 0.0
        crop_conf = f2_crop_reading.confidence if f2_crop_reading else 0.0
        boosted_conf = min(1.0, max(bbox_conf, crop_conf) + 0.15)

        total_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"[EnsembleV2] Tier 3 CROSS-VALIDATED | heat={bbox_heat} | "
            f"bbox_conf={bbox_conf:.2f} crop_conf={crop_conf:.2f} "
            f"boosted={boosted_conf:.2f} | time={total_ms:.0f}ms"
        )
        return EnsembleV2Result(
            reading=BilletReading(
                heat_number=bbox_heat,
                strand=f2_bbox_reading.strand if f2_bbox_reading else None,
                sequence=f2_bbox_reading.sequence if f2_bbox_reading else None,
                confidence=boosted_conf,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=(f2_bbox_reading.raw_texts if f2_bbox_reading else []),
            ),
            tier=3,
            tier_label="cross_validated",
            florence2_bbox_reading=f2_bbox_reading,
            florence2_crop_reading=f2_crop_reading,
            total_ms=total_ms,
            tier_times_ms=tier_times,
        )

    # ------------------------------------------------------------------
    # Tier 4: VLM Claude Vision fallback (use preprocessed image for best accuracy)
    # ------------------------------------------------------------------
    vlm_reading: Optional[BilletReading] = None

    if not skip_vlm:
        t4 = time.perf_counter()
        try:
            # Preprocess (CLAHE + bilateral) boosts VLM accuracy ~7% over raw
            from src.preprocessing.pipeline import preprocess_billet_image
            vlm_img, _ = preprocess_billet_image(raw_img)
            vlm_reading = _run_vlm(vlm_img)
        except Exception as exc:
            logger.error(f"[EnsembleV2] Tier 4 (VLM) error: {exc}")
            # Fallback to raw if preprocessing fails
            try:
                vlm_reading = _run_vlm(raw_img)
            except Exception as exc2:
                logger.error(f"[EnsembleV2] Tier 4 (VLM raw fallback) error: {exc2}")
        tier_times["tier4_vlm_ms"] = (time.perf_counter() - t4) * 1000

        # Accept VLM result if it has any heat number (even with letters).
        # VLM on preprocessed images is the best method for low-res Roboflow data.
        if vlm_reading is not None and vlm_reading.heat_number:
            total_ms = (time.perf_counter() - t_start) * 1000
            logger.info(
                f"[EnsembleV2] Tier 4 VLM FALLBACK | heat={vlm_reading.heat_number} | "
                f"conf={vlm_reading.confidence:.2f} | valid={_is_valid_heat(vlm_reading.heat_number)} | "
                f"time={total_ms:.0f}ms"
            )
            return EnsembleV2Result(
                reading=BilletReading(
                    heat_number=vlm_reading.heat_number,
                    strand=vlm_reading.strand,
                    sequence=vlm_reading.sequence,
                    confidence=vlm_reading.confidence,
                    method=OCRMethod.ENSEMBLE_V2,
                    raw_texts=vlm_reading.raw_texts,
                ),
                tier=4,
                tier_label="vlm_fallback",
                florence2_bbox_reading=f2_bbox_reading,
                florence2_crop_reading=f2_crop_reading,
                vlm_reading=vlm_reading,
                vlm_called=True,
                total_ms=total_ms,
                tier_times_ms=tier_times,
            )

    # ------------------------------------------------------------------
    # Fallback: return the best Florence-2 result (even if below threshold)
    # ------------------------------------------------------------------
    best_reading: Optional[BilletReading] = None
    best_conf = 0.0
    chosen_tier = 0
    chosen_label = "none"

    for reading, tier_num, label in [
        (f2_bbox_reading, 1, "florence2_bbox_crop"),
        (f2_crop_reading, 2, "florence2_center_crop"),
        (vlm_reading, 4, "vlm_fallback"),
    ]:
        if reading is not None and reading.confidence > best_conf:
            best_reading = reading
            best_conf = reading.confidence
            chosen_tier = tier_num
            chosen_label = label

    total_ms = (time.perf_counter() - t_start) * 1000

    if best_reading is not None:
        logger.warning(
            f"[EnsembleV2] BEST_OF_ALL | tier={chosen_tier} ({chosen_label}) | "
            f"heat={best_reading.heat_number} | conf={best_conf:.2f} | "
            f"time={total_ms:.0f}ms"
        )
        return EnsembleV2Result(
            reading=BilletReading(
                heat_number=best_reading.heat_number,
                strand=best_reading.strand,
                sequence=best_reading.sequence,
                confidence=best_reading.confidence,
                method=OCRMethod.ENSEMBLE_V2,
                raw_texts=best_reading.raw_texts,
            ),
            tier=chosen_tier,
            tier_label=f"best_of_all_{chosen_label}",
            florence2_bbox_reading=f2_bbox_reading,
            florence2_crop_reading=f2_crop_reading,
            vlm_reading=vlm_reading,
            vlm_called=vlm_reading is not None,
            total_ms=total_ms,
            tier_times_ms=tier_times,
        )

    logger.warning("[EnsembleV2] All tiers failed to produce a result")
    return EnsembleV2Result(
        reading=BilletReading(method=OCRMethod.ENSEMBLE_V2),
        tier=0,
        tier_label="all_failed",
        florence2_bbox_reading=f2_bbox_reading,
        florence2_crop_reading=f2_crop_reading,
        vlm_reading=vlm_reading,
        vlm_called=vlm_reading is not None,
        total_ms=total_ms,
        tier_times_ms=tier_times,
    )


# ---------------------------------------------------------------------------
# V1 Ensemble (PaddleOCR → VLM) — preserved for backward compatibility
# ---------------------------------------------------------------------------


def run_ensemble_pipeline(
    image: Union[str, Path, np.ndarray],
    preprocessed: Optional[np.ndarray] = None,
    confidence_threshold: float = OCR_CONFIDENCE_THRESHOLD,
    skip_paddle: bool = False,
    vlm_use_raw: bool = True,
    vlm_center_crop: bool = False,
) -> BilletReading:
    """Run the full ensemble OCR pipeline on a billet image.

    Execution paths:
    - ``paddle_only``: PaddleOCR confidence >= threshold; VLM not invoked.
    - ``vlm_fallback``: PaddleOCR confidence < threshold; VLM used.
    - ``vlm_only``: ``skip_paddle=True``; PaddleOCR skipped entirely.
    - ``best_of_two``: Both engines ran but neither met threshold; the
      reading with the higher confidence is returned.

    Args:
        image: Raw image — file path (str or Path) or BGR numpy array.
        preprocessed: Optional preprocessed (ROI + CLAHE) numpy array.
            When provided, PaddleOCR runs on this instead of *image*.
        confidence_threshold: PaddleOCR confidence must meet or exceed
            this value to skip VLM.  Defaults to ``OCR_CONFIDENCE_THRESHOLD``.
        skip_paddle: If ``True``, skip PaddleOCR and go straight to VLM.
        vlm_use_raw: If ``True`` (default), send the raw image to the VLM
            instead of the CLAHE-preprocessed version.  VLMs perform better
            on natural images without heavy preprocessing.
        vlm_center_crop: If ``True``, center-crop the VLM input image to
            focus on the stamp region.  Defaults to ``False``.

    Returns:
        A :class:`~src.models.BilletReading` with the best available result.
        The ``method`` field indicates which engine produced the reading.
    """
    paddle_reading: Optional[BilletReading] = None
    vlm_reading: Optional[BilletReading] = None

    # ------------------------------------------------------------------
    # Step 1: PaddleOCR (unless skipped)
    # ------------------------------------------------------------------
    if not skip_paddle:
        paddle_reading = _run_paddle(image, preprocessed)

        if paddle_reading.confidence >= confidence_threshold:
            logger.info(
                f"[Ensemble] paddle_only | "
                f"paddle_conf={paddle_reading.confidence:.3f} >= "
                f"threshold={confidence_threshold} | skipping VLM"
            )
            return paddle_reading

        logger.info(
            f"[Ensemble] PaddleOCR below threshold | "
            f"paddle_conf={paddle_reading.confidence:.3f} < "
            f"threshold={confidence_threshold} | triggering VLM fallback"
        )

    # ------------------------------------------------------------------
    # Step 2: VLM fallback
    # ------------------------------------------------------------------
    # VLM works better on raw images (not CLAHE-processed)
    if vlm_use_raw:
        vlm_input = image
    else:
        vlm_input = preprocessed if preprocessed is not None else image

    if vlm_center_crop and isinstance(vlm_input, np.ndarray):
        from src.preprocessing.pipeline import center_crop_for_vlm
        vlm_input = center_crop_for_vlm(vlm_input)

    vlm_reading = _run_vlm(vlm_input)

    if skip_paddle:
        path = "vlm_only"
    else:
        path = "vlm_fallback"

    if vlm_reading.confidence > 0.0:
        logger.info(
            f"[Ensemble] {path} | vlm_conf={vlm_reading.confidence:.3f}"
        )
        return vlm_reading

    # ------------------------------------------------------------------
    # Step 3: Both struggled — return whichever has higher confidence
    # ------------------------------------------------------------------
    if paddle_reading is not None and paddle_reading.confidence > 0.0:
        logger.warning(
            f"[Ensemble] best_of_two | VLM failed, returning PaddleOCR | "
            f"paddle_conf={paddle_reading.confidence:.3f}"
        )
        return BilletReading(
            heat_number=paddle_reading.heat_number,
            strand=paddle_reading.strand,
            sequence=paddle_reading.sequence,
            confidence=paddle_reading.confidence,
            method=OCRMethod.ENSEMBLE,
            raw_texts=paddle_reading.raw_texts,
        )

    logger.warning(
        "[Ensemble] best_of_two | Both engines failed to produce a result"
    )
    return BilletReading(method=OCRMethod.ENSEMBLE)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _run_paddle(
    image: Union[str, Path, np.ndarray],
    preprocessed: Optional[np.ndarray],
) -> BilletReading:
    """Run PaddleOCR + post-processing on the best available image.

    Uses *preprocessed* when available, otherwise falls back to *image*.
    Character confusion correction is applied via the validator.

    Args:
        image: Raw image input.
        preprocessed: Optional CLAHE-enhanced image.

    Returns:
        A :class:`~src.models.BilletReading` from PaddleOCR.
    """
    from src.ocr.paddle_ocr import run_paddle_pipeline
    from src.postprocess.validator import validate_and_correct_reading

    ocr_input = preprocessed if preprocessed is not None else image
    method = (
        OCRMethod.PADDLE_PREPROCESSED
        if preprocessed is not None
        else OCRMethod.PADDLE_RAW
    )

    try:
        reading = run_paddle_pipeline(ocr_input, method=method)
        reading = validate_and_correct_reading(reading)
    except Exception as exc:
        logger.error(f"[Ensemble] PaddleOCR pipeline error: {exc}")
        reading = BilletReading(method=method)

    return reading


def _run_vlm(
    image: Union[str, Path, np.ndarray],
) -> BilletReading:
    """Run Claude Vision on the supplied image.

    Args:
        image: Image to send to the VLM (prefer preprocessed).

    Returns:
        A :class:`~src.models.BilletReading` from Claude Vision.
    """
    from src.ocr.vlm_reader import read_billet_with_vlm

    try:
        return read_billet_with_vlm(image)
    except Exception as exc:
        logger.error(f"[Ensemble] VLM pipeline error: {exc}")
        return BilletReading(method=OCRMethod.VLM_CLAUDE)
