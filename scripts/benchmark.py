"""Standalone accuracy benchmark script for the Billet OCR pipeline.

Evaluates multiple processing methods on every annotated image and produces a
Markdown report at docs/BENCHMARK_V3.md (or a path supplied via --output).

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --vlm-only --output docs/BENCHMARK_V3_sonnet.md
    python scripts/benchmark.py --vlm-only --vlm-model claude-opus-4-6 --output docs/BENCHMARK_V3_opus.md

Pipeline stages evaluated:
    1. PaddleOCR on raw image (no preprocessing)
    2. PaddleOCR on CLAHE + bilateral-filter preprocessed image
    2b. ROI + CLAHE preprocessing + PaddleOCR
    3. CLAHE preprocessed + character confusion correction
    4. VLM fallback (Claude Vision) when PaddleOCR confidence < threshold
    5a. VLM on preprocessed image (baseline)
    5b. VLM on raw image (A/B test — no CLAHE preprocessing)
    5c. VLM on center-cropped raw image (zoomed-in view)
    6. Ensemble (PaddleOCR → VLM fallback via run_ensemble_pipeline)

Accuracy metrics:
    - Character accuracy: Levenshtein-based, implemented inline.
    - Word accuracy: Binary exact match (1.0 or 0.0).

Diagnostic features (V3):
    - Character-level diff logging (e.g., GT=192435 VLM=192458 diff=..XX..)
    - Per-character confusion matrix in the report
    - Model comparison via --vlm-model flag

No external accuracy libraries are used – Levenshtein distance is computed
via a standard two-row DP algorithm.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup – make the project root importable regardless of cwd.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import random

from src.config import (
    ANNOTATED_DIR,
    BBOX_ANNOTATIONS_PATH,
    BILATERAL_D,
    BILATERAL_SIGMA_COLOR,
    BILATERAL_SIGMA_SPACE,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID,
    OCR_CONFIDENCE_THRESHOLD,
    RAW_DIR,
    VLM_CROP_RATIO,
    VLM_MODEL,
    VLM_PROMPT_VERSION,
)
from src.models import BilletReading, OCRMethod


# ---------------------------------------------------------------------------
# Levenshtein distance (inline – no external dependency)
# ---------------------------------------------------------------------------


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings.

    Standard two-row DP implementation in O(m*n) time, O(min(m,n)) space.
    No external libraries required.

    Args:
        a: First string.
        b: Second string.

    Returns:
        Integer edit distance.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a  # iterate over shorter string
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            if ca == cb:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[len(b)]


def calculate_character_accuracy(predicted: Optional[str], actual: Optional[str]) -> float:
    """Compute Levenshtein-based character-level accuracy.

    Accuracy = 1 - edit_distance / max(len(predicted), len(actual)).
    Both inputs are coerced to empty strings when None.

    Args:
        predicted: OCR predicted string (may be None).
        actual: Ground truth string (may be None).

    Returns:
        Float in [0.0, 1.0]; 1.0 means perfect match.
    """
    p = (predicted or "").strip()
    a = (actual or "").strip()
    if not p and not a:
        return 1.0
    max_len = max(len(p), len(a))
    if max_len == 0:
        return 1.0
    return max(0.0, 1.0 - _levenshtein(p, a) / max_len)


def calculate_word_accuracy(predicted: Optional[str], actual: Optional[str]) -> float:
    """Compute binary exact-match accuracy.

    Args:
        predicted: OCR predicted string (may be None).
        actual: Ground truth string (may be None).

    Returns:
        1.0 if stripped strings are identical, else 0.0.
    """
    p = (predicted or "").strip()
    a = (actual or "").strip()
    return 1.0 if p == a else 0.0


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------


def _char_diff(predicted: Optional[str], actual: Optional[str]) -> str:
    """Build a character-level diff string comparing predicted vs actual.

    Each position is marked '.' if characters match, 'X' if they differ.
    If lengths differ, extra characters are marked with '+' (extra in predicted)
    or '-' (missing from predicted).

    Args:
        predicted: OCR predicted string (may be None).
        actual: Ground truth string (may be None).

    Returns:
        Diff string, e.g. '..XX..' for a 6-char comparison where positions
        3 and 4 differ.
    """
    p = (predicted or "").strip()
    a = (actual or "").strip()
    if not p and not a:
        return ""
    min_len = min(len(p), len(a))
    diff = []
    for i in range(min_len):
        diff.append("." if p[i] == a[i] else "X")
    # Handle length differences.
    if len(p) > len(a):
        diff.extend("+" * (len(p) - len(a)))
    elif len(a) > len(p):
        diff.extend("-" * (len(a) - len(p)))
    return "".join(diff)


def _collect_confusions(
    all_results: list[dict],
    method_key: str,
) -> dict[tuple[str, str], int]:
    """Collect character-level confusion counts for a given method.

    Compares predicted vs actual heat numbers character by character. Only
    counts positions where both strings exist and have the same length
    (to avoid alignment ambiguity).

    Args:
        all_results: List of per-image result dicts.
        method_key: Method key in the results dict (e.g., 'vlm_raw').

    Returns:
        Dict mapping (predicted_char, actual_char) pairs to occurrence counts.
        Only includes mismatched pairs.
    """
    confusions: dict[tuple[str, str], int] = {}
    for res in all_results:
        m = res["methods"].get(method_key, {})
        predicted = (m.get("heat_number") or "").strip()
        actual = (res["ground_truth"].get("heat_number") or "").strip()
        if not predicted or not actual or len(predicted) != len(actual):
            continue
        for pc, ac in zip(predicted, actual):
            if pc != ac:
                key = (pc, ac)
                confusions[key] = confusions.get(key, 0) + 1
    return confusions


# ---------------------------------------------------------------------------
# Per-image benchmark
# ---------------------------------------------------------------------------


def _run_image_benchmark(
    entry: dict,
    use_vlm: bool,
    vlm_only: bool = False,
    vlm_model: str = VLM_MODEL,
    use_florence2: bool = False,
    use_bbox_crop: bool = False,
    bbox_annotations: Optional[dict] = None,
    use_ensemble_v2: bool = False,
) -> dict:
    """Run all pipeline stages on a single image and collect results.

    Args:
        entry: Ground truth dict with keys: image, heat_number, strand, sequence.
        use_vlm: Whether to invoke Claude Vision when PaddleOCR confidence is low.
        vlm_only: If True, skip PaddleOCR stages and only run VLM + ensemble.
        vlm_model: Claude model ID for VLM stages.
        use_florence2: Whether to run Florence-2 stages.
        use_bbox_crop: Whether to run bbox-crop + PaddleOCR stages.
        bbox_annotations: Pre-loaded Roboflow bbox annotations dict.
        use_ensemble_v2: Whether to run the V2 ensemble (Florence-2 cascade + VLM).

    Returns:
        Result dict with keys: image, ground_truth, methods (nested dict),
        preprocessing_ms, errors.
    """
    # Lazy imports (PaddleOCR takes several seconds to load on first call).
    from src.ocr.paddle_ocr import run_paddle_pipeline
    from src.postprocess.validator import validate_and_correct_reading
    from src.preprocessing.pipeline import center_crop_for_vlm, preprocess_billet_image

    img_path = RAW_DIR / entry["image"]
    gt_heat = (entry.get("heat_number") or "").strip()
    gt_strand = (entry.get("strand") or "").strip()
    gt_sequence = (entry.get("sequence") or "").strip()

    result: dict = {
        "image": entry["image"],
        "difficulty": entry.get("difficulty", ""),
        "ground_truth": {
            "heat_number": gt_heat,
            "strand": gt_strand,
            "sequence": gt_sequence,
        },
        "methods": {},
        "preprocessing_ms": 0.0,
        "errors": [],
    }

    if not img_path.exists():
        result["errors"].append(f"Image not found: {img_path}")
        return result

    # ------------------------------------------------------------------
    # Preprocessing (always needed, even in vlm_only mode for ROI input)
    # ------------------------------------------------------------------
    preprocessed = None
    roi_preprocessed = None
    preproc_ms = 0.0
    pre_reading = BilletReading(method=OCRMethod.PADDLE_PREPROCESSED)

    try:
        preprocessed, preproc_timing = preprocess_billet_image(img_path)
        preproc_ms = preproc_timing["total_ms"]
    except Exception as exc:
        result["errors"].append(f"Preprocessing error: {exc}")

    result["preprocessing_ms"] = preproc_ms

    try:
        roi_preprocessed, roi_preproc_timing = preprocess_billet_image(
            img_path, detect_roi=True, correct_perspective=True,
        )
    except Exception as exc:
        roi_preprocessed = None
        result["errors"].append(f"ROI preprocessing error: {exc}")

    if not vlm_only:
        # ------------------------------------------------------------------
        # Stage 1: Raw PaddleOCR
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        try:
            raw_reading = run_paddle_pipeline(img_path, method=OCRMethod.PADDLE_RAW)
        except Exception as exc:
            raw_reading = BilletReading(method=OCRMethod.PADDLE_RAW)
            result["errors"].append(f"Raw OCR error: {exc}")
        raw_time_ms = (time.perf_counter() - t0) * 1000

        result["methods"]["raw"] = {
            "heat_number": raw_reading.heat_number,
            "strand": raw_reading.strand,
            "sequence": raw_reading.sequence,
            "confidence": raw_reading.confidence,
            "ocr_time_ms": raw_time_ms,
            "char_acc": calculate_character_accuracy(raw_reading.heat_number, gt_heat),
            "word_acc": calculate_word_accuracy(raw_reading.heat_number, gt_heat),
        }

        # ------------------------------------------------------------------
        # Stage 2: CLAHE preprocessing + PaddleOCR
        # ------------------------------------------------------------------
        if preprocessed is not None:
            t0 = time.perf_counter()
            try:
                pre_reading = run_paddle_pipeline(preprocessed, method=OCRMethod.PADDLE_PREPROCESSED)
            except Exception as exc:
                pre_reading = BilletReading(method=OCRMethod.PADDLE_PREPROCESSED)
                result["errors"].append(f"Preprocessed OCR error: {exc}")
            pre_time_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["preprocessed"] = {
                "heat_number": pre_reading.heat_number,
                "strand": pre_reading.strand,
                "sequence": pre_reading.sequence,
                "confidence": pre_reading.confidence,
                "preproc_time_ms": preproc_ms,
                "ocr_time_ms": pre_time_ms,
                "char_acc": calculate_character_accuracy(pre_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(pre_reading.heat_number, gt_heat),
            }

        # ------------------------------------------------------------------
        # Stage 2b: ROI + CLAHE preprocessing + PaddleOCR
        # ------------------------------------------------------------------
        if roi_preprocessed is not None:
            t0 = time.perf_counter()
            try:
                roi_reading = run_paddle_pipeline(
                    roi_preprocessed, method=OCRMethod.PADDLE_PREPROCESSED
                )
            except Exception as exc:
                roi_reading = BilletReading(method=OCRMethod.PADDLE_PREPROCESSED)
                result["errors"].append(f"ROI OCR error: {exc}")
            roi_ocr_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["roi_preprocessed"] = {
                "heat_number": roi_reading.heat_number,
                "strand": roi_reading.strand,
                "sequence": roi_reading.sequence,
                "confidence": roi_reading.confidence,
                "preproc_time_ms": roi_preproc_timing.get("total_ms", 0.0),
                "ocr_time_ms": roi_ocr_ms,
                "roi_ms": roi_preproc_timing.get("roi_ms", 0.0),
                "perspective_ms": roi_preproc_timing.get("perspective_ms", 0.0),
                "char_acc": calculate_character_accuracy(roi_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(roi_reading.heat_number, gt_heat),
            }
        else:
            result["methods"]["roi_preprocessed"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
                "preproc_time_ms": 0.0,
                "ocr_time_ms": 0.0,
            }

        # ------------------------------------------------------------------
        # Stage 3: Post-processing (character confusion correction)
        # ------------------------------------------------------------------
        try:
            post_reading = validate_and_correct_reading(pre_reading)
        except Exception as exc:
            post_reading = pre_reading
            result["errors"].append(f"Postprocess error: {exc}")

        result["methods"]["postprocessed"] = {
            "heat_number": post_reading.heat_number,
            "strand": post_reading.strand,
            "sequence": post_reading.sequence,
            "confidence": post_reading.confidence,
            "char_acc": calculate_character_accuracy(post_reading.heat_number, gt_heat),
            "word_acc": calculate_word_accuracy(post_reading.heat_number, gt_heat),
        }

        # ------------------------------------------------------------------
        # Stage 4: VLM fallback (only when PaddleOCR confidence is low)
        # ------------------------------------------------------------------
        vlm_triggered = post_reading.confidence < OCR_CONFIDENCE_THRESHOLD

        if use_vlm and vlm_triggered:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key:
                try:
                    from src.ocr.vlm_reader import read_billet_with_vlm

                    vlm_input = roi_preprocessed if roi_preprocessed is not None else preprocessed
                    t0 = time.perf_counter()
                    vlm_reading = read_billet_with_vlm(
                        vlm_input if vlm_input is not None else img_path,
                        model=vlm_model,
                    )
                    vlm_time_ms = (time.perf_counter() - t0) * 1000

                    result["methods"]["vlm"] = {
                        "heat_number": vlm_reading.heat_number,
                        "strand": vlm_reading.strand,
                        "sequence": vlm_reading.sequence,
                        "confidence": vlm_reading.confidence,
                        "ocr_time_ms": vlm_time_ms,
                        "char_acc": calculate_character_accuracy(vlm_reading.heat_number, gt_heat),
                        "word_acc": calculate_word_accuracy(vlm_reading.heat_number, gt_heat),
                        "triggered": True,
                    }
                except Exception as exc:
                    result["errors"].append(f"VLM error: {exc}")
            else:
                result["methods"]["vlm"] = {
                    "heat_number": None,
                    "char_acc": 0.0,
                    "word_acc": 0.0,
                    "triggered": True,
                    "skipped": "No ANTHROPIC_API_KEY set",
                }
        else:
            result["methods"]["vlm"] = {
                "heat_number": None,
                "char_acc": None,
                "word_acc": None,
                "triggered": False,
            }

    # ------------------------------------------------------------------
    # Stage 5a: VLM-only on preprocessed image (original behavior)
    # ------------------------------------------------------------------
    if use_vlm:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from src.ocr.vlm_reader import read_billet_with_vlm

                vlm_input = roi_preprocessed if roi_preprocessed is not None else preprocessed
                t0 = time.perf_counter()
                vlm_only_reading = read_billet_with_vlm(
                    vlm_input if vlm_input is not None else img_path,
                    model=vlm_model,
                )
                vlm_only_time_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["vlm_only"] = {
                    "heat_number": vlm_only_reading.heat_number,
                    "strand": vlm_only_reading.strand,
                    "sequence": vlm_only_reading.sequence,
                    "confidence": vlm_only_reading.confidence,
                    "ocr_time_ms": vlm_only_time_ms,
                    "char_acc": calculate_character_accuracy(vlm_only_reading.heat_number, gt_heat),
                    "word_acc": calculate_word_accuracy(vlm_only_reading.heat_number, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"VLM-only error: {exc}")
                result["methods"]["vlm_only"] = {
                    "heat_number": None,
                    "char_acc": 0.0,
                    "word_acc": 0.0,
                }
        else:
            result["methods"]["vlm_only"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
                "skipped": "No ANTHROPIC_API_KEY set",
            }
    else:
        result["methods"]["vlm_only"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5b: VLM on raw image (no preprocessing — A/B test)
    # Loads the raw image as numpy array (no CLAHE/bilateral) and sends
    # it to the VLM. Using numpy instead of file path avoids the 5 MB
    # base64 limit on raw PNGs (they get JPEG-encoded at quality 95).
    # ------------------------------------------------------------------
    if use_vlm:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from src.ocr.vlm_reader import read_billet_with_vlm
                from src.preprocessing.pipeline import load_image

                raw_img = load_image(img_path)
                t0 = time.perf_counter()
                vlm_raw_reading = read_billet_with_vlm(
                    raw_img,
                    model=vlm_model,
                )
                vlm_raw_time_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["vlm_raw"] = {
                    "heat_number": vlm_raw_reading.heat_number,
                    "strand": vlm_raw_reading.strand,
                    "sequence": vlm_raw_reading.sequence,
                    "confidence": vlm_raw_reading.confidence,
                    "ocr_time_ms": vlm_raw_time_ms,
                    "char_acc": calculate_character_accuracy(vlm_raw_reading.heat_number, gt_heat),
                    "word_acc": calculate_word_accuracy(vlm_raw_reading.heat_number, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"VLM-raw error: {exc}")
                result["methods"]["vlm_raw"] = {
                    "heat_number": None,
                    "char_acc": 0.0,
                    "word_acc": 0.0,
                }
        else:
            result["methods"]["vlm_raw"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
                "skipped": "No ANTHROPIC_API_KEY set",
            }
    else:
        result["methods"]["vlm_raw"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5c: VLM on center-cropped raw image
    # ------------------------------------------------------------------
    if use_vlm:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from src.ocr.vlm_reader import read_billet_with_vlm
                from src.preprocessing.pipeline import load_image

                raw_img = load_image(img_path)
                cropped = center_crop_for_vlm(raw_img)

                t0 = time.perf_counter()
                vlm_crop_reading = read_billet_with_vlm(
                    cropped,
                    model=vlm_model,
                )
                vlm_crop_time_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["vlm_center_crop"] = {
                    "heat_number": vlm_crop_reading.heat_number,
                    "strand": vlm_crop_reading.strand,
                    "sequence": vlm_crop_reading.sequence,
                    "confidence": vlm_crop_reading.confidence,
                    "ocr_time_ms": vlm_crop_time_ms,
                    "char_acc": calculate_character_accuracy(vlm_crop_reading.heat_number, gt_heat),
                    "word_acc": calculate_word_accuracy(vlm_crop_reading.heat_number, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"VLM-center-crop error: {exc}")
                result["methods"]["vlm_center_crop"] = {
                    "heat_number": None,
                    "char_acc": 0.0,
                    "word_acc": 0.0,
                }
        else:
            result["methods"]["vlm_center_crop"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
                "skipped": "No ANTHROPIC_API_KEY set",
            }
    else:
        result["methods"]["vlm_center_crop"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5d: Florence-2 on raw image (zero-shot <OCR>)
    # ------------------------------------------------------------------
    if use_florence2:
        try:
            from src.ocr.florence2_reader import read_billet_with_florence2
            from src.preprocessing.pipeline import load_image

            raw_img = load_image(img_path)
            t0 = time.perf_counter()
            f2_raw_reading = read_billet_with_florence2(raw_img)
            f2_raw_time_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["florence2_raw"] = {
                "heat_number": f2_raw_reading.heat_number,
                "strand": f2_raw_reading.strand,
                "sequence": f2_raw_reading.sequence,
                "confidence": f2_raw_reading.confidence,
                "ocr_time_ms": f2_raw_time_ms,
                "raw_texts": f2_raw_reading.raw_texts,
                "char_acc": calculate_character_accuracy(f2_raw_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(f2_raw_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"Florence-2 raw error: {exc}")
            result["methods"]["florence2_raw"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
            }
    else:
        result["methods"]["florence2_raw"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5e: Florence-2 on center-cropped raw image
    # ------------------------------------------------------------------
    if use_florence2:
        try:
            from src.ocr.florence2_reader import read_billet_with_florence2
            from src.preprocessing.pipeline import load_image

            raw_img = load_image(img_path)
            cropped = center_crop_for_vlm(raw_img)

            t0 = time.perf_counter()
            f2_crop_reading = read_billet_with_florence2(cropped)
            f2_crop_time_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["florence2_crop"] = {
                "heat_number": f2_crop_reading.heat_number,
                "strand": f2_crop_reading.strand,
                "sequence": f2_crop_reading.sequence,
                "confidence": f2_crop_reading.confidence,
                "ocr_time_ms": f2_crop_time_ms,
                "raw_texts": f2_crop_reading.raw_texts,
                "char_acc": calculate_character_accuracy(f2_crop_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(f2_crop_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"Florence-2 crop error: {exc}")
            result["methods"]["florence2_crop"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
            }
    else:
        result["methods"]["florence2_crop"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5f: Florence-2 on bbox-cropped raw image (Roboflow annotations)
    #   Improvements over previous version:
    #   - Uses LARGEST bbox per image (not first) — targets the most visible billet
    #   - Uses 25% padding (up from 10%) — gives Florence-2 more context
    #   - Applies format validation to handle multi-billet contamination
    # ------------------------------------------------------------------
    if use_florence2 and use_bbox_crop and bbox_annotations:
        img_name = entry["image"]
        if img_name in bbox_annotations:
            try:
                from src.config import FLORENCE2_BBOX_PAD_RATIO
                from src.ocr.florence2_reader import read_billet_with_florence2
                from src.postprocess.format_validator import validate_florence2_output
                from src.preprocessing.pipeline import load_image

                raw_img = load_image(img_path)
                # Use LARGEST bbox (by area) instead of first
                bboxes = bbox_annotations[img_name]
                bbox = max(bboxes, key=lambda b: b["width"] * b["height"])
                x = int(bbox["x"])
                y = int(bbox["y"])
                w = int(bbox["width"])
                h = int(bbox["height"])
                pad_x = int(w * FLORENCE2_BBOX_PAD_RATIO)
                pad_y = int(h * FLORENCE2_BBOX_PAD_RATIO)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(raw_img.shape[1], x + w + pad_x)
                y2 = min(raw_img.shape[0], y + h + pad_y)
                bbox_cropped = raw_img[y1:y2, x1:x2]

                t0 = time.perf_counter()
                f2_bbox_reading = read_billet_with_florence2(bbox_cropped)
                f2_bbox_time_ms = (time.perf_counter() - t0) * 1000

                # Apply format validation to fix multi-billet contamination
                raw_output = " ".join(f2_bbox_reading.raw_texts) if f2_bbox_reading.raw_texts else ""
                validated_heat = validate_florence2_output(
                    raw_output, f2_bbox_reading.heat_number,
                )

                result["methods"]["florence2_bbox_crop"] = {
                    "heat_number": validated_heat,
                    "strand": f2_bbox_reading.strand,
                    "sequence": f2_bbox_reading.sequence,
                    "confidence": f2_bbox_reading.confidence,
                    "ocr_time_ms": f2_bbox_time_ms,
                    "raw_texts": f2_bbox_reading.raw_texts,
                    "bbox_area": w * h,
                    "char_acc": calculate_character_accuracy(validated_heat, gt_heat),
                    "word_acc": calculate_word_accuracy(validated_heat, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"Florence-2 bbox-crop error: {exc}")
                result["methods"]["florence2_bbox_crop"] = {
                    "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
                }
        else:
            result["methods"]["florence2_bbox_crop"] = {
                "heat_number": None, "char_acc": None, "word_acc": None,
                "skipped": "No bbox annotation for this image",
            }
    else:
        result["methods"]["florence2_bbox_crop"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5g: Florence-2 bbox crop + super-resolution upscaling
    #   Upscales tiny bbox crops (50-100px) to 400px+ before OCR.
    #   This addresses the #1 failure mode: resolution crisis.
    # ------------------------------------------------------------------
    if use_florence2 and use_bbox_crop and bbox_annotations:
        img_name = entry["image"]
        if img_name in bbox_annotations:
            try:
                from src.config import FLORENCE2_BBOX_PAD_RATIO
                from src.ocr.florence2_reader import read_billet_with_florence2
                from src.postprocess.format_validator import validate_florence2_output
                from src.preprocessing.pipeline import load_image
                from src.preprocessing.super_resolution import upscale_image

                raw_img = load_image(img_path)
                bboxes = bbox_annotations[img_name]
                bbox = max(bboxes, key=lambda b: b["width"] * b["height"])
                x = int(bbox["x"])
                y = int(bbox["y"])
                w = int(bbox["width"])
                h = int(bbox["height"])
                pad_x = int(w * FLORENCE2_BBOX_PAD_RATIO)
                pad_y = int(h * FLORENCE2_BBOX_PAD_RATIO)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(raw_img.shape[1], x + w + pad_x)
                y2 = min(raw_img.shape[0], y + h + pad_y)
                bbox_cropped = raw_img[y1:y2, x1:x2]

                # Super-resolution upscale
                bbox_upscaled = upscale_image(bbox_cropped)

                t0 = time.perf_counter()
                f2_sr_reading = read_billet_with_florence2(bbox_upscaled)
                f2_sr_time_ms = (time.perf_counter() - t0) * 1000

                # Apply format validation
                raw_output = " ".join(f2_sr_reading.raw_texts) if f2_sr_reading.raw_texts else ""
                validated_heat = validate_florence2_output(
                    raw_output, f2_sr_reading.heat_number,
                )

                crop_h, crop_w = bbox_cropped.shape[:2]
                up_h, up_w = bbox_upscaled.shape[:2]
                result["methods"]["florence2_bbox_superres"] = {
                    "heat_number": validated_heat,
                    "strand": f2_sr_reading.strand,
                    "sequence": f2_sr_reading.sequence,
                    "confidence": f2_sr_reading.confidence,
                    "ocr_time_ms": f2_sr_time_ms,
                    "raw_texts": f2_sr_reading.raw_texts,
                    "crop_size": f"{crop_w}x{crop_h}",
                    "upscaled_size": f"{up_w}x{up_h}",
                    "char_acc": calculate_character_accuracy(validated_heat, gt_heat),
                    "word_acc": calculate_word_accuracy(validated_heat, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"Florence-2 bbox-superres error: {exc}")
                result["methods"]["florence2_bbox_superres"] = {
                    "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
                }
        else:
            result["methods"]["florence2_bbox_superres"] = {
                "heat_number": None, "char_acc": None, "word_acc": None,
                "skipped": "No bbox annotation for this image",
            }
    else:
        result["methods"]["florence2_bbox_superres"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 5h: Florence-2 raw + format validation (no bbox crop)
    #   Applies format validation to the existing Florence-2 raw output
    #   to fix multi-billet contamination without bbox crops.
    # ------------------------------------------------------------------
    if use_florence2:
        f2_raw_method = result["methods"].get("florence2_raw", {})
        raw_texts = f2_raw_method.get("raw_texts", [])
        raw_output = " ".join(raw_texts) if raw_texts else ""
        parsed_heat = f2_raw_method.get("heat_number")

        if raw_output or parsed_heat:
            try:
                from src.postprocess.format_validator import validate_florence2_output
                validated_heat = validate_florence2_output(raw_output, parsed_heat)

                result["methods"]["florence2_raw_validated"] = {
                    "heat_number": validated_heat,
                    "strand": f2_raw_method.get("strand"),
                    "sequence": f2_raw_method.get("sequence"),
                    "confidence": f2_raw_method.get("confidence", 0.0),
                    "raw_texts": raw_texts,
                    "char_acc": calculate_character_accuracy(validated_heat, gt_heat),
                    "word_acc": calculate_word_accuracy(validated_heat, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"Florence-2 raw validated error: {exc}")
                result["methods"]["florence2_raw_validated"] = {
                    "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
                }
        else:
            result["methods"]["florence2_raw_validated"] = {
                "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
            }
    else:
        result["methods"]["florence2_raw_validated"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 6: Ensemble (PaddleOCR -> VLM fallback)
    # ------------------------------------------------------------------
    if use_vlm and not vlm_only:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from src.ocr.ensemble import run_ensemble_pipeline

                t0 = time.perf_counter()
                ensemble_reading = run_ensemble_pipeline(
                    img_path,
                    preprocessed=roi_preprocessed if roi_preprocessed is not None else preprocessed,
                )
                ensemble_time_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["ensemble"] = {
                    "heat_number": ensemble_reading.heat_number,
                    "strand": ensemble_reading.strand,
                    "sequence": ensemble_reading.sequence,
                    "confidence": ensemble_reading.confidence,
                    "method": ensemble_reading.method.value,
                    "ocr_time_ms": ensemble_time_ms,
                    "char_acc": calculate_character_accuracy(ensemble_reading.heat_number, gt_heat),
                    "word_acc": calculate_word_accuracy(ensemble_reading.heat_number, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"Ensemble error: {exc}")
                result["methods"]["ensemble"] = {
                    "heat_number": None,
                    "char_acc": 0.0,
                    "word_acc": 0.0,
                }
        else:
            result["methods"]["ensemble"] = {
                "heat_number": None,
                "char_acc": 0.0,
                "word_acc": 0.0,
                "skipped": "No ANTHROPIC_API_KEY set",
            }
    else:
        result["methods"]["ensemble"] = {
            "heat_number": None,
            "char_acc": None,
            "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 7: Bbox-crop + CLAHE + PaddleOCR (Roboflow annotations)
    # ------------------------------------------------------------------
    if use_bbox_crop and bbox_annotations and not vlm_only:
        img_name = entry["image"]
        if img_name in bbox_annotations:
            try:
                from src.ocr.paddle_ocr import run_paddle_pipeline

                bboxes = bbox_annotations[img_name]
                bbox = max(bboxes, key=lambda b: b["width"] * b["height"])
                bbox_preprocessed, bbox_timing = preprocess_billet_image(
                    img_path, roi_bbox=bbox,
                )
                t0 = time.perf_counter()
                bbox_reading = run_paddle_pipeline(
                    bbox_preprocessed, method=OCRMethod.PADDLE_BBOX_CROP,
                )
                bbox_ocr_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["bbox_crop"] = {
                    "heat_number": bbox_reading.heat_number,
                    "strand": bbox_reading.strand,
                    "sequence": bbox_reading.sequence,
                    "confidence": bbox_reading.confidence,
                    "preproc_time_ms": bbox_timing["total_ms"],
                    "ocr_time_ms": bbox_ocr_ms,
                    "char_acc": calculate_character_accuracy(bbox_reading.heat_number, gt_heat),
                    "word_acc": calculate_word_accuracy(bbox_reading.heat_number, gt_heat),
                }
            except Exception as exc:
                result["errors"].append(f"Bbox-crop error: {exc}")
                result["methods"]["bbox_crop"] = {
                    "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
                }
        else:
            result["methods"]["bbox_crop"] = {
                "heat_number": None, "char_acc": None, "word_acc": None,
                "skipped": "No bbox annotation for this image",
            }
    else:
        result["methods"]["bbox_crop"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 8: Ensemble V2 (Florence-2 cascade + VLM fallback)
    # ------------------------------------------------------------------
    if use_ensemble_v2:
        try:
            from src.ocr.ensemble import run_ensemble_v2

            # Load bbox for this image
            img_name = entry["image"]
            bbox = None
            if bbox_annotations and img_name in bbox_annotations:
                bboxes = bbox_annotations[img_name]
                bbox = max(bboxes, key=lambda b: b["width"] * b["height"])

            skip_vlm = not use_vlm
            t0 = time.perf_counter()
            v2_result = run_ensemble_v2(
                img_path,
                bbox=bbox,
                skip_vlm=skip_vlm,
            )
            v2_time_ms = (time.perf_counter() - t0) * 1000

            v2_reading = v2_result.reading
            result["methods"]["ensemble_v2"] = {
                "heat_number": v2_reading.heat_number,
                "strand": v2_reading.strand,
                "sequence": v2_reading.sequence,
                "confidence": v2_reading.confidence,
                "ocr_time_ms": v2_time_ms,
                "tier": v2_result.tier,
                "tier_label": v2_result.tier_label,
                "vlm_called": v2_result.vlm_called,
                "tier_times_ms": v2_result.tier_times_ms,
                "char_acc": calculate_character_accuracy(v2_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(v2_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"Ensemble V2 error: {exc}")
            result["methods"]["ensemble_v2"] = {
                "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
                "tier": 0, "tier_label": "error", "vlm_called": False,
            }
    else:
        result["methods"]["ensemble_v2"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    return result


# ---------------------------------------------------------------------------
# Per-billet benchmark (GT V2 format — multi-billet)
# ---------------------------------------------------------------------------


def _run_billet_benchmark(
    entry: dict,
    use_vlm: bool,
    vlm_model: str = VLM_MODEL,
    use_florence2: bool = False,
) -> dict:
    """Run benchmark stages on a single billet using its exact GT bbox.

    Unlike _run_image_benchmark, this function receives a per-billet GT entry
    that includes bbox_index and bbox coordinates. It crops to THAT EXACT bbox
    and runs OCR on the crop — ensuring GT and benchmark use the same billet.

    Args:
        entry: Per-billet GT dict with keys: image, bbox_index, bbox,
            heat_number, sequence, strand.
        use_vlm: Whether to invoke Claude Vision.
        vlm_model: Claude model ID for VLM stages.
        use_florence2: Whether to run Florence-2 stages.

    Returns:
        Result dict with keys: image, bbox_index, ground_truth, methods, errors.
    """
    from src.preprocessing.pipeline import load_image

    img_path = RAW_DIR / entry["image"]
    bbox = entry["bbox"]
    bbox_index = entry.get("bbox_index", 0)
    gt_heat = (entry.get("heat_number") or "").strip()
    gt_seq = (entry.get("sequence") or "").strip()

    result: dict = {
        "image": entry["image"],
        "bbox_index": bbox_index,
        "ground_truth": {
            "heat_number": gt_heat,
            "sequence": gt_seq,
            "strand": (entry.get("strand") or "").strip(),
        },
        "methods": {},
        "errors": [],
    }

    if not img_path.exists():
        result["errors"].append(f"Image not found: {img_path}")
        return result

    # Load and crop to the GT bbox
    try:
        raw_img = load_image(img_path)
    except Exception as exc:
        result["errors"].append(f"Image load error: {exc}")
        return result

    import cv2

    from src.config import FLORENCE2_BBOX_PAD_RATIO

    x = int(bbox["x"])
    y = int(bbox["y"])
    w = int(bbox["width"])
    h = int(bbox["height"])

    # Crop with Florence-2 padding (25%)
    pad_x = int(w * FLORENCE2_BBOX_PAD_RATIO)
    pad_y = int(h * FLORENCE2_BBOX_PAD_RATIO)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(raw_img.shape[1], x + w + pad_x)
    y2 = min(raw_img.shape[0], y + h + pad_y)
    bbox_crop = raw_img[y1:y2, x1:x2]

    # ------------------------------------------------------------------
    # Stage 1: Florence-2 on bbox crop
    # ------------------------------------------------------------------
    if use_florence2:
        try:
            from src.ocr.florence2_reader import read_billet_with_florence2
            from src.postprocess.format_validator import validate_florence2_output

            t0 = time.perf_counter()
            f2_reading = read_billet_with_florence2(bbox_crop)
            f2_time_ms = (time.perf_counter() - t0) * 1000

            raw_output = " ".join(f2_reading.raw_texts) if f2_reading.raw_texts else ""
            validated_heat = validate_florence2_output(raw_output, f2_reading.heat_number)

            result["methods"]["florence2_bbox_crop"] = {
                "heat_number": validated_heat,
                "sequence": f2_reading.sequence,
                "confidence": f2_reading.confidence,
                "ocr_time_ms": f2_time_ms,
                "raw_texts": f2_reading.raw_texts,
                "crop_size": f"{bbox_crop.shape[1]}x{bbox_crop.shape[0]}",
                "char_acc_heat": calculate_character_accuracy(validated_heat, gt_heat),
                "word_acc_heat": calculate_word_accuracy(validated_heat, gt_heat),
                "char_acc_seq": calculate_character_accuracy(f2_reading.sequence, gt_seq) if gt_seq else None,
            }
        except Exception as exc:
            result["errors"].append(f"Florence-2 bbox-crop error: {exc}")
            result["methods"]["florence2_bbox_crop"] = {
                "heat_number": None, "char_acc_heat": 0.0, "word_acc_heat": 0.0,
            }
    else:
        result["methods"]["florence2_bbox_crop"] = {
            "heat_number": None, "char_acc_heat": None, "word_acc_heat": None,
        }

    # ------------------------------------------------------------------
    # Stage 2: Florence-2 on bbox crop + super-resolution
    # ------------------------------------------------------------------
    if use_florence2:
        try:
            from src.ocr.florence2_reader import read_billet_with_florence2
            from src.postprocess.format_validator import validate_florence2_output
            from src.preprocessing.super_resolution import upscale_image

            bbox_upscaled = upscale_image(bbox_crop)

            t0 = time.perf_counter()
            f2_sr_reading = read_billet_with_florence2(bbox_upscaled)
            f2_sr_time_ms = (time.perf_counter() - t0) * 1000

            raw_output = " ".join(f2_sr_reading.raw_texts) if f2_sr_reading.raw_texts else ""
            validated_heat = validate_florence2_output(raw_output, f2_sr_reading.heat_number)

            result["methods"]["florence2_bbox_superres"] = {
                "heat_number": validated_heat,
                "sequence": f2_sr_reading.sequence,
                "confidence": f2_sr_reading.confidence,
                "ocr_time_ms": f2_sr_time_ms,
                "raw_texts": f2_sr_reading.raw_texts,
                "crop_size": f"{bbox_crop.shape[1]}x{bbox_crop.shape[0]}",
                "upscaled_size": f"{bbox_upscaled.shape[1]}x{bbox_upscaled.shape[0]}",
                "char_acc_heat": calculate_character_accuracy(validated_heat, gt_heat),
                "word_acc_heat": calculate_word_accuracy(validated_heat, gt_heat),
                "char_acc_seq": calculate_character_accuracy(f2_sr_reading.sequence, gt_seq) if gt_seq else None,
            }
        except Exception as exc:
            result["errors"].append(f"Florence-2 bbox-superres error: {exc}")
            result["methods"]["florence2_bbox_superres"] = {
                "heat_number": None, "char_acc_heat": 0.0, "word_acc_heat": 0.0,
            }
    else:
        result["methods"]["florence2_bbox_superres"] = {
            "heat_number": None, "char_acc_heat": None, "word_acc_heat": None,
        }

    # ------------------------------------------------------------------
    # Stage 3: PaddleOCR on bbox crop + CLAHE
    # ------------------------------------------------------------------
    try:
        from src.ocr.paddle_ocr import run_paddle_pipeline
        from src.preprocessing.pipeline import preprocess_billet_image

        bbox_preprocessed, bbox_timing = preprocess_billet_image(bbox_crop)
        t0 = time.perf_counter()
        paddle_reading = run_paddle_pipeline(
            bbox_preprocessed, method=OCRMethod.PADDLE_BBOX_CROP,
        )
        paddle_ms = (time.perf_counter() - t0) * 1000

        result["methods"]["paddle_bbox_crop"] = {
            "heat_number": paddle_reading.heat_number,
            "sequence": paddle_reading.sequence,
            "confidence": paddle_reading.confidence,
            "ocr_time_ms": paddle_ms,
            "char_acc_heat": calculate_character_accuracy(paddle_reading.heat_number, gt_heat),
            "word_acc_heat": calculate_word_accuracy(paddle_reading.heat_number, gt_heat),
        }
    except Exception as exc:
        result["errors"].append(f"PaddleOCR bbox-crop error: {exc}")
        result["methods"]["paddle_bbox_crop"] = {
            "heat_number": None, "char_acc_heat": 0.0, "word_acc_heat": 0.0,
        }

    # ------------------------------------------------------------------
    # Stage 4: VLM on bbox crop (Claude Vision)
    # ------------------------------------------------------------------
    if use_vlm:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from src.ocr.vlm_reader import read_billet_with_vlm

                t0 = time.perf_counter()
                vlm_reading = read_billet_with_vlm(bbox_crop, model=vlm_model)
                vlm_ms = (time.perf_counter() - t0) * 1000

                result["methods"]["vlm_bbox_crop"] = {
                    "heat_number": vlm_reading.heat_number,
                    "sequence": vlm_reading.sequence,
                    "confidence": vlm_reading.confidence,
                    "ocr_time_ms": vlm_ms,
                    "char_acc_heat": calculate_character_accuracy(vlm_reading.heat_number, gt_heat),
                    "word_acc_heat": calculate_word_accuracy(vlm_reading.heat_number, gt_heat),
                    "char_acc_seq": calculate_character_accuracy(vlm_reading.sequence, gt_seq) if gt_seq else None,
                }
            except Exception as exc:
                result["errors"].append(f"VLM bbox-crop error: {exc}")
                result["methods"]["vlm_bbox_crop"] = {
                    "heat_number": None, "char_acc_heat": 0.0, "word_acc_heat": 0.0,
                }
        else:
            result["methods"]["vlm_bbox_crop"] = {
                "heat_number": None, "char_acc_heat": 0.0, "word_acc_heat": 0.0,
                "skipped": "No ANTHROPIC_API_KEY",
            }
    else:
        result["methods"]["vlm_bbox_crop"] = {
            "heat_number": None, "char_acc_heat": None, "word_acc_heat": None,
        }

    return result


def generate_billet_markdown_report(
    all_results: list[dict],
    output_path: Path,
    timestamp: str,
    vlm_model: str = VLM_MODEL,
) -> None:
    """Write a per-billet Markdown benchmark report.

    Each row = 1 billet (not 1 image). Results are grouped by image for readability.

    Args:
        all_results: List of per-billet result dicts from _run_billet_benchmark().
        output_path: Where to write the .md file.
        timestamp: ISO timestamp for header.
        vlm_model: Claude model used.
    """
    lines: list[str] = []

    # Count unique images
    unique_images = len({r["image"] for r in all_results})

    lines.append("# Billet OCR Benchmark Report — Per-Billet (V2)\n")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Billets evaluated:** {len(all_results)} (across {unique_images} images)  ")
    lines.append(f"**VLM model:** `{vlm_model}`  ")
    lines.append(f"**Prompt version:** V{VLM_PROMPT_VERSION}  \n")

    # Method keys for per-billet
    method_keys = [
        "florence2_bbox_crop", "florence2_bbox_superres",
        "paddle_bbox_crop", "vlm_bbox_crop",
    ]
    method_labels = {
        "florence2_bbox_crop": "F2 Bbox Crop",
        "florence2_bbox_superres": "F2 Bbox+SR",
        "paddle_bbox_crop": "Paddle Bbox",
        "vlm_bbox_crop": "VLM Bbox Crop",
    }

    # Aggregate stats
    method_heat_accs: dict[str, list[float]] = {k: [] for k in method_keys}
    method_word_accs: dict[str, list[float]] = {k: [] for k in method_keys}
    method_seq_accs: dict[str, list[float]] = {k: [] for k in method_keys}

    for res in all_results:
        for mk in method_keys:
            m = res["methods"].get(mk, {})
            if m.get("char_acc_heat") is not None:
                method_heat_accs[mk].append(m["char_acc_heat"])
            if m.get("word_acc_heat") is not None:
                method_word_accs[mk].append(m["word_acc_heat"])
            if m.get("char_acc_seq") is not None:
                method_seq_accs[mk].append(m["char_acc_seq"])

    def _avg(lst: list[float]) -> Optional[float]:
        return sum(lst) / len(lst) if lst else None

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Method | Avg Heat Char Acc | Avg Heat Exact | Avg Seq Char Acc | N |")
    lines.append("|--------|-------------------|----------------|------------------|---|")
    for mk in method_keys:
        label = method_labels.get(mk, mk)
        avg_char = _avg(method_heat_accs[mk])
        avg_word = _avg(method_word_accs[mk])
        avg_seq = _avg(method_seq_accs[mk])
        n = len(method_heat_accs[mk])
        lines.append(
            f"| {label} | {_format_acc(avg_char)} | "
            f"{_format_acc(avg_word)} | {_format_acc(avg_seq)} | {n} |"
        )
    lines.append("")

    # Per-billet breakdown, grouped by image
    lines.append("## Per-Billet Breakdown\n")
    lines.append(
        "| Image | Bbox# | GT Heat | GT Seq | F2 Heat | F2 Acc | "
        "F2+SR Heat | F2+SR Acc | Paddle | VLM |"
    )
    lines.append(
        "|-------|-------|---------|--------|---------|--------|"
        "------------|-----------|--------|-----|"
    )

    # Group by image
    from itertools import groupby
    sorted_results = sorted(all_results, key=lambda r: (r["image"], r["bbox_index"]))
    for _img, group in groupby(sorted_results, key=lambda r: r["image"]):
        for res in group:
            img_short = res["image"][:40]
            bbox_idx = res["bbox_index"]
            gt = res["ground_truth"]
            gt_h = gt.get("heat_number", "")
            gt_s = gt.get("sequence", "")

            f2 = res["methods"].get("florence2_bbox_crop", {})
            f2sr = res["methods"].get("florence2_bbox_superres", {})
            pad = res["methods"].get("paddle_bbox_crop", {})
            vlm = res["methods"].get("vlm_bbox_crop", {})

            lines.append(
                f"| {img_short} | {bbox_idx} | {gt_h} | {gt_s} | "
                f"{f2.get('heat_number') or '-'} | {_format_acc(f2.get('char_acc_heat'))} | "
                f"{f2sr.get('heat_number') or '-'} | {_format_acc(f2sr.get('char_acc_heat'))} | "
                f"{_format_acc(pad.get('char_acc_heat'))} | "
                f"{_format_acc(vlm.get('char_acc_heat'))} |"
            )

    lines.append("")

    # Errors
    all_errors = [
        (r["image"], r["bbox_index"], e)
        for r in all_results for e in r.get("errors", [])
    ]
    if all_errors:
        lines.append("## Errors\n")
        for img, bbox_idx, err in all_errors:
            lines.append(f"- **{img}** bbox[{bbox_idx}]: {err}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by `scripts/benchmark.py --gt-v2`.*")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {output_path}")


# ---------------------------------------------------------------------------
# Markdown report generator (legacy per-image)
# ---------------------------------------------------------------------------

_METHOD_LABELS = {
    "raw": "PaddleOCR Raw",
    "preprocessed": "PaddleOCR + CLAHE",
    "roi_preprocessed": "ROI + CLAHE",
    "postprocessed": "CLAHE + Correction",
    "bbox_crop": "Bbox Crop + CLAHE",
    "vlm": "VLM Fallback",
    "vlm_only": "VLM Preprocessed",
    "vlm_raw": "VLM Raw",
    "vlm_center_crop": "VLM Center Crop",
    "florence2_raw": "Florence-2 Raw",
    "florence2_crop": "Florence-2 Crop",
    "florence2_bbox_crop": "Florence-2 Bbox Crop",
    "florence2_bbox_superres": "F2 Bbox+SuperRes",
    "florence2_raw_validated": "F2 Raw+Validated",
    "ensemble": "Ensemble",
    "ensemble_v2": "Ensemble V2",
}


def _format_acc(value: Optional[float]) -> str:
    """Format an accuracy value as a percentage string, or '-' if None.

    Args:
        value: Accuracy float in [0, 1] or None.

    Returns:
        String like '87.5%' or '-'.
    """
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _format_ms(value: Optional[float]) -> str:
    """Format a millisecond timing value, or '-' if None.

    Args:
        value: Timing in milliseconds or None.

    Returns:
        String like '123ms' or '-'.
    """
    if value is None:
        return "-"
    return f"{value:.0f}ms"


def generate_markdown_report(
    all_results: list[dict],
    output_path: Path,
    timestamp: str,
    vlm_model: str = VLM_MODEL,
) -> None:
    """Write a Markdown benchmark report to output_path.

    Sections:
    - Header with timestamp and model info
    - Configuration table
    - Summary table (avg char acc, avg word acc, avg time per method)
    - VLM A/B comparison table (preprocessed vs raw vs center-crop)
    - VLM diagnostic diffs (character-level)
    - Character confusion matrix
    - Per-image breakdown table
    - Errors

    Args:
        all_results: List of per-image result dicts from _run_image_benchmark().
        output_path: Absolute path where the .md file will be written.
        timestamp: ISO-format timestamp string for the report header.
        vlm_model: Claude model ID used for VLM stages.
    """
    lines: list[str] = []

    lines.append("# Billet OCR Benchmark Report — V3\n")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Images evaluated:** {len(all_results)}  ")
    lines.append(f"**VLM model:** `{vlm_model}`  ")
    lines.append(f"**Prompt version:** V{VLM_PROMPT_VERSION}  ")
    lines.append(f"**VLM crop ratio:** {VLM_CROP_RATIO}  \n")

    # ------------------------------------------------------------------
    # Configuration section
    # ------------------------------------------------------------------
    lines.append("## Configuration\n")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| CLAHE clip limit | {CLAHE_CLIP_LIMIT} |")
    lines.append(f"| CLAHE tile grid | {CLAHE_TILE_GRID} |")
    lines.append(f"| Bilateral d | {BILATERAL_D} |")
    lines.append(f"| Bilateral sigma color | {BILATERAL_SIGMA_COLOR} |")
    lines.append(f"| Bilateral sigma space | {BILATERAL_SIGMA_SPACE} |")
    lines.append(f"| OCR confidence threshold | {OCR_CONFIDENCE_THRESHOLD} |")
    lines.append(f"| VLM model | `{vlm_model}` |")
    lines.append(f"| VLM prompt version | {VLM_PROMPT_VERSION} |")
    lines.append(f"| VLM crop ratio | {VLM_CROP_RATIO} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Aggregate statistics
    # ------------------------------------------------------------------
    method_keys = [
        "raw", "preprocessed", "roi_preprocessed", "postprocessed",
        "bbox_crop",
        "vlm", "vlm_only", "vlm_raw", "vlm_center_crop",
        "florence2_raw", "florence2_crop", "florence2_bbox_crop",
        "florence2_bbox_superres", "florence2_raw_validated",
        "ensemble", "ensemble_v2",
    ]

    # Collect per-method accuracy lists (skip None values for VLM not triggered).
    method_char_accs: dict[str, list[float]] = {k: [] for k in method_keys}
    method_word_accs: dict[str, list[float]] = {k: [] for k in method_keys}
    method_times: dict[str, list[float]] = {k: [] for k in method_keys}

    for res in all_results:
        for mk in method_keys:
            m = res["methods"].get(mk, {})
            if m.get("char_acc") is not None:
                method_char_accs[mk].append(m["char_acc"])
            if m.get("word_acc") is not None:
                method_word_accs[mk].append(m["word_acc"])

            # Timing: raw and preprocessed have ocr_time_ms; preprocessed
            # also has preproc_time_ms.
            ocr_t = m.get("ocr_time_ms")
            pre_t = m.get("preproc_time_ms", 0.0)
            if ocr_t is not None:
                method_times[mk].append((ocr_t or 0.0) + (pre_t or 0.0))

    def _avg(lst: list[float]) -> Optional[float]:
        return sum(lst) / len(lst) if lst else None

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    lines.append("## Summary\n")
    lines.append("| Method | Avg Char Accuracy | Avg Word Accuracy | Avg Time |")
    lines.append("|--------|-------------------|-------------------|----------|")
    for mk in method_keys:
        label = _METHOD_LABELS.get(mk, mk)
        avg_char = _avg(method_char_accs[mk])
        avg_word = _avg(method_word_accs[mk])
        avg_time = _avg(method_times[mk])
        lines.append(
            f"| {label} | {_format_acc(avg_char)} | "
            f"{_format_acc(avg_word)} | {_format_ms(avg_time)} |"
        )
    lines.append("")

    # ------------------------------------------------------------------
    # VLM A/B comparison table
    # ------------------------------------------------------------------
    vlm_methods = ["vlm_only", "vlm_raw", "vlm_center_crop"]
    florence2_methods = [
        "florence2_raw", "florence2_crop", "florence2_bbox_crop",
        "florence2_bbox_superres", "florence2_raw_validated",
    ]
    all_vlm_methods = vlm_methods + florence2_methods
    has_vlm_data = any(
        method_char_accs.get(mk) for mk in all_vlm_methods
    )
    has_florence2_data = any(
        method_char_accs.get(mk) for mk in florence2_methods
    )
    if has_vlm_data:
        lines.append("## VLM A/B Comparison\n")
        header = "| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop |"
        separator = "|-------|---------|------------------|---------|-----------------|"
        if has_florence2_data:
            header += " F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |"
            separator += "--------|---------|---------|------------|------------|"
        lines.append(header)
        lines.append(separator)
        for res in all_results:
            img = res["image"]
            gt_heat = res["ground_truth"].get("heat_number", "")
            vlm_pre = res["methods"].get("vlm_only", {})
            vlm_raw_m = res["methods"].get("vlm_raw", {})
            vlm_crop = res["methods"].get("vlm_center_crop", {})
            f2_raw = res["methods"].get("florence2_raw", {})
            f2_crop = res["methods"].get("florence2_crop", {})
            f2_bbox = res["methods"].get("florence2_bbox_crop", {})
            f2_sr = res["methods"].get("florence2_bbox_superres", {})
            f2_val = res["methods"].get("florence2_raw_validated", {})

            def _fmt_vlm_cell(m: dict) -> str:
                hn = m.get("heat_number") or "-"
                acc = m.get("char_acc")
                if acc is not None:
                    return f"{hn} ({acc * 100:.0f}%)"
                return hn

            row = (
                f"| {img} | {gt_heat} | "
                f"{_fmt_vlm_cell(vlm_pre)} | "
                f"{_fmt_vlm_cell(vlm_raw_m)} | "
                f"{_fmt_vlm_cell(vlm_crop)} |"
            )
            if has_florence2_data:
                row += (
                    f" {_fmt_vlm_cell(f2_raw)} |"
                    f" {_fmt_vlm_cell(f2_crop)} |"
                    f" {_fmt_vlm_cell(f2_bbox)} |"
                    f" {_fmt_vlm_cell(f2_sr)} |"
                    f" {_fmt_vlm_cell(f2_val)} |"
                )
            lines.append(row)
        lines.append("")

    # ------------------------------------------------------------------
    # VLM diagnostic diffs (character-level)
    # ------------------------------------------------------------------
    if has_vlm_data:
        lines.append("## VLM Diagnostic Diffs\n")
        lines.append("Character-level comparison: `.` = match, `X` = mismatch, "
                      "`+` = extra, `-` = missing\n")
        lines.append("| Image | GT Heat | Method | Predicted | Diff | Char Acc |")
        lines.append("|-------|---------|--------|-----------|------|----------|")
        diff_methods = vlm_methods + (florence2_methods if has_florence2_data else [])
        for res in all_results:
            img = res["image"]
            gt_heat = res["ground_truth"].get("heat_number", "")
            for mk in diff_methods:
                m = res["methods"].get(mk, {})
                predicted = m.get("heat_number")
                if predicted is None and m.get("char_acc") is None:
                    continue
                diff = _char_diff(predicted, gt_heat)
                label = _METHOD_LABELS.get(mk, mk)
                lines.append(
                    f"| {img} | {gt_heat} | {label} | "
                    f"{predicted or '-'} | `{diff}` | "
                    f"{_format_acc(m.get('char_acc'))} |"
                )
        lines.append("")

    # ------------------------------------------------------------------
    # Character confusion matrix
    # ------------------------------------------------------------------
    if has_vlm_data:
        lines.append("## Character Confusions (VLM)\n")
        # Aggregate confusions across all VLM methods.
        all_confusions: dict[tuple[str, str], int] = {}
        confusion_methods = vlm_methods + (florence2_methods if has_florence2_data else [])
        for mk in confusion_methods:
            conf = _collect_confusions(all_results, mk)
            for pair, count in conf.items():
                all_confusions[pair] = all_confusions.get(pair, 0) + count

        if all_confusions:
            # Sort by count descending.
            sorted_conf = sorted(all_confusions.items(), key=lambda x: -x[1])
            lines.append("| Predicted | Actual | Count |")
            lines.append("|-----------|--------|-------|")
            for (pred, actual), count in sorted_conf:
                lines.append(f"| {pred} | {actual} | {count} |")
        else:
            lines.append("No character-level confusions detected (lengths may differ).")
        lines.append("")

    # ------------------------------------------------------------------
    # Ensemble V2 tier breakdown
    # ------------------------------------------------------------------
    has_ens_v2 = any(
        r["methods"].get("ensemble_v2", {}).get("char_acc") is not None
        for r in all_results
    )
    if has_ens_v2:
        lines.append("## Ensemble V2 Tier Breakdown\n")
        lines.append(
            "| Image | GT Heat | Predicted | Char Acc | Tier | Tier Label | VLM? | Time |"
        )
        lines.append(
            "|-------|---------|-----------|----------|------|------------|------|------|"
        )
        vlm_call_count = 0
        for res in all_results:
            v2 = res["methods"].get("ensemble_v2", {})
            if v2.get("char_acc") is None:
                continue
            gt_h = res["ground_truth"].get("heat_number", "")
            pred = v2.get("heat_number") or "-"
            char_a = _format_acc(v2.get("char_acc"))
            tier_n = v2.get("tier", "?")
            tier_l = v2.get("tier_label", "?")
            vlm_c = "Yes" if v2.get("vlm_called") else "No"
            t_ms = _format_ms(v2.get("ocr_time_ms"))
            if v2.get("vlm_called"):
                vlm_call_count += 1
            lines.append(
                f"| {res['image']} | {gt_h} | {pred} | {char_a} | "
                f"{tier_n} | {tier_l} | {vlm_c} | {t_ms} |"
            )
        total_v2 = sum(
            1 for r in all_results
            if r["methods"].get("ensemble_v2", {}).get("char_acc") is not None
        )
        vlm_rate = vlm_call_count / total_v2 * 100 if total_v2 > 0 else 0
        lines.append(
            f"\n**VLM fallback rate:** {vlm_call_count}/{total_v2} "
            f"({vlm_rate:.0f}%)\n"
        )

    # ------------------------------------------------------------------
    # Per-image breakdown
    # ------------------------------------------------------------------
    lines.append("## Per-Image Breakdown\n")
    header = (
        "| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | "
        "Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop |"
    )
    separator = (
        "|-------|------------|---------|----------|----------|----------|"
        "-----------|----------|---------|---------|----------|"
    )
    if has_florence2_data:
        header += " F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |"
        separator += "--------|---------|---------|------------|------------|"
    header += " Ensemble | Ens V2 |"
    separator += "----------|--------|"
    lines.append(header)
    lines.append(separator)

    for res in all_results:
        img = res["image"]
        difficulty = res.get("difficulty", "")
        gt = res["ground_truth"]
        gt_heat = gt.get("heat_number", "")
        raw = res["methods"].get("raw", {})
        pre = res["methods"].get("preprocessed", {})
        roi = res["methods"].get("roi_preprocessed", {})
        post = res["methods"].get("postprocessed", {})
        vlm = res["methods"].get("vlm", {})
        vlm_only = res["methods"].get("vlm_only", {})
        vlm_raw_m = res["methods"].get("vlm_raw", {})
        vlm_crop = res["methods"].get("vlm_center_crop", {})
        f2_raw = res["methods"].get("florence2_raw", {})
        f2_crop_m = res["methods"].get("florence2_crop", {})
        f2_bbox_m = res["methods"].get("florence2_bbox_crop", {})
        f2_sr = res["methods"].get("florence2_bbox_superres", {})
        f2_val = res["methods"].get("florence2_raw_validated", {})
        ensemble = res["methods"].get("ensemble", {})
        ens_v2 = res["methods"].get("ensemble_v2", {})

        vlm_char = (
            _format_acc(vlm.get("char_acc"))
            if vlm.get("triggered") and vlm.get("char_acc") is not None
            else "-"
        )

        row = (
            f"| {img} | {difficulty} | {gt_heat} | "
            f"{_format_acc(raw.get('char_acc'))} | "
            f"{_format_acc(pre.get('char_acc'))} | "
            f"{_format_acc(roi.get('char_acc'))} | "
            f"{_format_acc(post.get('char_acc'))} | "
            f"{vlm_char} | "
            f"{_format_acc(vlm_only.get('char_acc'))} | "
            f"{_format_acc(vlm_raw_m.get('char_acc'))} | "
            f"{_format_acc(vlm_crop.get('char_acc'))} |"
        )
        if has_florence2_data:
            row += (
                f" {_format_acc(f2_raw.get('char_acc'))} |"
                f" {_format_acc(f2_crop_m.get('char_acc'))} |"
                f" {_format_acc(f2_bbox_m.get('char_acc'))} |"
                f" {_format_acc(f2_sr.get('char_acc'))} |"
                f" {_format_acc(f2_val.get('char_acc'))} |"
            )
        row += f" {_format_acc(ensemble.get('char_acc'))} |"
        row += f" {_format_acc(ens_v2.get('char_acc'))} |"
        lines.append(row)

    lines.append("")

    # ------------------------------------------------------------------
    # Errors section (if any)
    # ------------------------------------------------------------------
    all_errors = [
        (r["image"], e) for r in all_results for e in r.get("errors", [])
    ]
    if all_errors:
        lines.append("## Errors\n")
        for img, err in all_errors:
            lines.append(f"- **{img}**: {err}")
        lines.append("")

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    lines.append("---")
    lines.append("*Generated by `scripts/benchmark.py`.*")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and run the full benchmark pipeline.

    Loads ground truth from data/annotated/ground_truth.json, runs all three
    OCR stages on each image, and generates a Markdown report.

    Raises:
        SystemExit: If the ground truth file is missing.
    """
    parser = argparse.ArgumentParser(
        description="Billet OCR accuracy benchmark",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default=str(_PROJECT_ROOT / "docs" / "BENCHMARK_V1.md"),
        help="Path for the generated Markdown report.",
    )
    parser.add_argument(
        "--no-vlm",
        action="store_true",
        help="Skip VLM fallback even when confidence is below threshold.",
    )
    parser.add_argument(
        "--vlm-only",
        action="store_true",
        help="Skip PaddleOCR stages; only run VLM-only and preprocessing.",
    )
    parser.add_argument(
        "--vlm-model",
        default=VLM_MODEL,
        help="Claude model for VLM stages (e.g., claude-opus-4-6).",
    )
    parser.add_argument(
        "--florence2",
        action="store_true",
        default=False,
        help="Include Florence-2 stages in the benchmark.",
    )
    parser.add_argument(
        "--bbox-crop",
        action="store_true",
        default=False,
        help="Include bbox-crop + PaddleOCR using Roboflow annotations.",
    )
    parser.add_argument(
        "--ensemble-v2",
        action="store_true",
        default=False,
        help="Include Ensemble V2 (Florence-2 cascade + VLM fallback) stage.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Max images to benchmark (0 = all). Useful for quick testing.",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        default=False,
        help="Randomize image order before benchmarking.",
    )
    parser.add_argument(
        "--gt-v2",
        action="store_true",
        default=False,
        help="Use per-billet ground truth (ground_truth_v2.json) for multi-billet evaluation.",
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    use_vlm = not args.no_vlm
    vlm_only = args.vlm_only
    vlm_model = args.vlm_model
    use_florence2 = args.florence2
    use_bbox_crop = args.bbox_crop
    use_ensemble_v2 = args.ensemble_v2
    use_gt_v2 = args.gt_v2

    # --vlm-only implies VLM is enabled (unless --no-vlm also set).
    if vlm_only and not args.no_vlm:
        use_vlm = True

    # ------------------------------------------------------------------
    # GT V2: Per-billet benchmark (multi-billet mode)
    # ------------------------------------------------------------------
    if use_gt_v2:
        from src.config import GT_OUTPUT_PATH
        gt_v2_path = GT_OUTPUT_PATH
        if not gt_v2_path.exists():
            print(f"ERROR: GT V2 file not found: {gt_v2_path}", file=sys.stderr)
            print("Run scripts/extract_ground_truth.py --use-bbox --all-bboxes first.", file=sys.stderr)
            sys.exit(1)

        with open(gt_v2_path, encoding="utf-8") as fh:
            gt_v2_all: list[dict] = json.load(fh)

        # Filter entries with valid heat numbers and bbox
        gt_v2 = [
            e for e in gt_v2_all
            if (e.get("heat_number") or "").strip() and e.get("bbox")
        ]
        print(f"Loaded {len(gt_v2_all)} per-billet GT entries from {gt_v2_path}")
        print(f"  Benchmarking: {len(gt_v2)} billets with heat numbers + bbox")

        # Shuffle billets (grouped by image)
        if args.shuffle:
            # Shuffle at image level to keep billets from the same image together
            from itertools import groupby
            images_billets: dict[str, list[dict]] = {}
            for e in gt_v2:
                images_billets.setdefault(e["image"], []).append(e)
            image_keys = list(images_billets.keys())
            random.shuffle(image_keys)
            gt_v2 = []
            for k in image_keys:
                gt_v2.extend(images_billets[k])
            print(f"Shuffled {len(image_keys)} images")

        if args.max_images > 0:
            # Limit by number of images (not billets)
            seen_images: set[str] = set()
            limited: list[dict] = []
            for e in gt_v2:
                seen_images.add(e["image"])
                if len(seen_images) > args.max_images:
                    break
                limited.append(e)
            gt_v2 = limited
            print(f"Limited to {args.max_images} images ({len(gt_v2)} billets)")

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        all_results: list[dict] = []
        total_start = time.perf_counter()

        for idx, entry in enumerate(gt_v2, start=1):
            img_name = entry.get("image", "?")
            bbox_idx = entry.get("bbox_index", 0)
            print(f"\n[{idx}/{len(gt_v2)}] {img_name} bbox[{bbox_idx}]")

            result = _run_billet_benchmark(
                entry,
                use_vlm=use_vlm,
                vlm_model=vlm_model,
                use_florence2=use_florence2,
            )
            all_results.append(result)

            # Brief summary
            gt_h = result["ground_truth"].get("heat_number", "")
            f2 = result["methods"].get("florence2_bbox_crop", {})
            f2sr = result["methods"].get("florence2_bbox_superres", {})
            pad = result["methods"].get("paddle_bbox_crop", {})
            vlm_m = result["methods"].get("vlm_bbox_crop", {})

            f2_info = f"F2={f2.get('heat_number') or '-'} ({_format_acc(f2.get('char_acc_heat'))})"
            sr_info = f"F2+SR=({_format_acc(f2sr.get('char_acc_heat'))})"
            pad_info = f"Pad=({_format_acc(pad.get('char_acc_heat'))})"
            vlm_info = f"VLM=({_format_acc(vlm_m.get('char_acc_heat'))})"
            print(f"  GT={gt_h} | {f2_info} | {sr_info} | {pad_info} | {vlm_info}")

            if result["errors"]:
                for err in result["errors"]:
                    print(f"  WARNING: {err}")

        total_elapsed = time.perf_counter() - total_start
        print(f"\nBenchmark complete in {total_elapsed:.1f}s ({len(all_results)} billets)")

        generate_billet_markdown_report(all_results, output_path, timestamp, vlm_model)

        # Print aggregate summary
        summary_keys = [
            "florence2_bbox_crop", "florence2_bbox_superres",
            "paddle_bbox_crop", "vlm_bbox_crop",
        ]
        summary_labels = {
            "florence2_bbox_crop": "F2 Bbox Crop",
            "florence2_bbox_superres": "F2 Bbox+SR",
            "paddle_bbox_crop": "Paddle Bbox",
            "vlm_bbox_crop": "VLM Bbox Crop",
        }
        print("\n=== PER-BILLET SUMMARY ===")
        print(f"{'Method':<20} {'Heat Char%':>11} {'Heat Exact%':>12} {'N':>5}")
        print("-" * 52)
        for mk in summary_keys:
            accs = [
                r["methods"].get(mk, {}).get("char_acc_heat")
                for r in all_results
                if r["methods"].get(mk, {}).get("char_acc_heat") is not None
            ]
            word_accs = [
                r["methods"].get(mk, {}).get("word_acc_heat")
                for r in all_results
                if r["methods"].get(mk, {}).get("word_acc_heat") is not None
            ]
            if not accs:
                continue
            avg_char = sum(accs) / len(accs)
            avg_word = sum(word_accs) / len(word_accs) if word_accs else 0.0
            label = summary_labels.get(mk, mk)
            print(f"{label:<20} {avg_char * 100:>10.1f}% {avg_word * 100:>11.1f}% {len(accs):>5}")

        sys.exit(0)

    # ------------------------------------------------------------------
    # Load ground truth (legacy per-image format)
    # ------------------------------------------------------------------
    gt_path = ANNOTATED_DIR / "ground_truth.json"
    if not gt_path.exists():
        print(f"ERROR: Ground truth file not found: {gt_path}", file=sys.stderr)
        print("Run scripts/extract_ground_truth.py first.", file=sys.stderr)
        sys.exit(1)

    with open(gt_path, encoding="utf-8") as fh:
        ground_truth_all: list[dict] = json.load(fh)

    if not ground_truth_all:
        print("ERROR: Ground truth file is empty.", file=sys.stderr)
        sys.exit(1)

    # Filter out images with no readable ground truth (impossible/unreadable).
    # Only benchmark images that have a non-empty heat_number.
    _EXCLUDED_DIFFICULTIES = {"impossible"}
    ground_truth: list[dict] = []
    excluded: list[dict] = []
    for entry in ground_truth_all:
        difficulty = entry.get("difficulty", "")
        has_heat = bool((entry.get("heat_number") or "").strip())
        if difficulty in _EXCLUDED_DIFFICULTIES or not has_heat:
            excluded.append(entry)
        else:
            ground_truth.append(entry)

    print(f"Loaded {len(ground_truth_all)} ground truth entries from {gt_path}")
    print(f"  Benchmarking: {len(ground_truth)} images with readable ground truth")
    if excluded:
        print(f"  Excluded: {len(excluded)} images (no readable text / impossible):")
        for ex in excluded:
            print(f"    - {ex['image']} (difficulty={ex.get('difficulty', 'N/A')})")
    print(f"Output report: {output_path}")
    if vlm_only:
        api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
        print(f"Mode: VLM-only (ANTHROPIC_API_KEY set: {api_key_set})")
    elif use_vlm:
        api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
        print(f"VLM fallback: enabled (ANTHROPIC_API_KEY set: {api_key_set})")
    else:
        print("VLM fallback: disabled (--no-vlm)")
    if use_vlm:
        print(f"VLM model: {vlm_model}")
        print(f"VLM prompt version: V{VLM_PROMPT_VERSION}")
    if use_florence2:
        from src.config import FLORENCE2_MODEL_ID as _f2_id, FLORENCE2_LORA_PATH as _lora_path
        print(f"Florence-2: enabled (model={_f2_id}, lora={_lora_path})")
    if use_ensemble_v2:
        print("Ensemble V2: enabled (Florence-2 cascade + VLM fallback)")
    # Load bbox annotations if needed
    bbox_annotations: Optional[dict] = None
    if use_bbox_crop:
        if BBOX_ANNOTATIONS_PATH.exists():
            with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as fh:
                bbox_annotations = json.load(fh)
            print(f"Bbox annotations: loaded {len(bbox_annotations)} images")
        else:
            print(f"WARNING: Bbox annotations not found at {BBOX_ANNOTATIONS_PATH}")
            print("  Run scripts/parse_roboflow_annotations.py first.")
            use_bbox_crop = False

    # Shuffle and limit
    if args.shuffle:
        random.shuffle(ground_truth)
        print(f"Shuffled {len(ground_truth)} images")
    if args.max_images > 0:
        ground_truth = ground_truth[:args.max_images]
        print(f"Limited to {args.max_images} images")

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ------------------------------------------------------------------
    # Run benchmark for each image
    # ------------------------------------------------------------------
    all_results: list[dict] = []
    total_start = time.perf_counter()

    for idx, entry in enumerate(ground_truth, start=1):
        img_name = entry.get("image", "?")
        print(f"\n[{idx}/{len(ground_truth)}] Processing: {img_name}")

        result = _run_image_benchmark(
            entry, use_vlm=use_vlm, vlm_only=vlm_only, vlm_model=vlm_model,
            use_florence2=use_florence2,
            use_bbox_crop=use_bbox_crop,
            bbox_annotations=bbox_annotations,
            use_ensemble_v2=use_ensemble_v2,
        )
        all_results.append(result)

        # Brief per-image summary to stdout.
        gt_heat = result["ground_truth"].get("heat_number", "")
        if vlm_only:
            vlm_o = result["methods"].get("vlm_only", {})
            vlm_r = result["methods"].get("vlm_raw", {})
            vlm_c = result["methods"].get("vlm_center_crop", {})
            print(
                f"  VLM-Pre heat={vlm_o.get('heat_number')!r:12s} "
                f"acc={_format_acc(vlm_o.get('char_acc')):6s}  |  "
                f"VLM-Raw heat={vlm_r.get('heat_number')!r:12s} "
                f"acc={_format_acc(vlm_r.get('char_acc')):6s}  |  "
                f"VLM-Crop acc={_format_acc(vlm_c.get('char_acc')):6s}"
            )
            # Diagnostic diffs for VLM-raw.
            vlm_raw_hn = vlm_r.get("heat_number")
            if vlm_raw_hn:
                diff = _char_diff(vlm_raw_hn, gt_heat)
                print(f"    GT={gt_heat}  VLM-Raw={vlm_raw_hn}  diff={diff}")
        else:
            raw = result["methods"].get("raw", {})
            post = result["methods"].get("postprocessed", {})
            vlm_o = result["methods"].get("vlm_only", {})
            vlm_r = result["methods"].get("vlm_raw", {})
            ens = result["methods"].get("ensemble", {})
            print(
                f"  Raw heat={raw.get('heat_number')!r:12s} "
                f"char_acc={_format_acc(raw.get('char_acc')):6s}  |  "
                f"Post heat={post.get('heat_number')!r:12s} "
                f"char_acc={_format_acc(post.get('char_acc')):6s}  |  "
                f"VLM-Pre={_format_acc(vlm_o.get('char_acc')):6s}  "
                f"VLM-Raw={_format_acc(vlm_r.get('char_acc')):6s}  "
                f"Ens={_format_acc(ens.get('char_acc')):6s}"
            )
            # Diagnostic diffs for VLM-raw.
            vlm_raw_hn = vlm_r.get("heat_number")
            if vlm_raw_hn:
                diff = _char_diff(vlm_raw_hn, gt_heat)
                print(f"    GT={gt_heat}  VLM-Raw={vlm_raw_hn}  diff={diff}")
        # Florence-2 summary (if enabled).
        f2_raw = result["methods"].get("florence2_raw", {})
        f2_crop = result["methods"].get("florence2_crop", {})
        f2_bbox = result["methods"].get("florence2_bbox_crop", {})
        f2_sr = result["methods"].get("florence2_bbox_superres", {})
        f2_val = result["methods"].get("florence2_raw_validated", {})
        if f2_raw.get("char_acc") is not None:
            f2_line = (
                f"  F2-Raw heat={f2_raw.get('heat_number')!r:12s} "
                f"acc={_format_acc(f2_raw.get('char_acc')):6s}  |  "
                f"F2-Crop acc={_format_acc(f2_crop.get('char_acc')):6s}"
            )
            if f2_bbox.get("char_acc") is not None:
                f2_line += f"  |  F2-Bbox acc={_format_acc(f2_bbox.get('char_acc')):6s}"
            if f2_sr.get("char_acc") is not None:
                f2_line += f"  |  F2-SR acc={_format_acc(f2_sr.get('char_acc')):6s}"
            if f2_val.get("char_acc") is not None:
                f2_line += f"  |  F2-Val acc={_format_acc(f2_val.get('char_acc')):6s}"
            print(f2_line)
        # Ensemble V2 summary (if enabled).
        v2_m = result["methods"].get("ensemble_v2", {})
        if v2_m.get("char_acc") is not None:
            tier_info = f"tier={v2_m.get('tier', '?')}"
            vlm_info = "VLM=yes" if v2_m.get("vlm_called") else "VLM=no"
            print(
                f"  EnsV2 heat={v2_m.get('heat_number')!r:12s} "
                f"acc={_format_acc(v2_m.get('char_acc')):6s} | "
                f"{tier_info} | {vlm_info}"
            )
        # Alternative OCR engines summary.
        alt_engines = [
            ("Bbox-Crop", "bbox_crop"),
        ]
        alt_parts = []
        for label, key in alt_engines:
            m = result["methods"].get(key, {})
            if m.get("char_acc") is not None:
                alt_parts.append(f"{label}={_format_acc(m.get('char_acc'))}")
        if alt_parts:
            print(f"  Alt: {' | '.join(alt_parts)}")
        if result["errors"]:
            for err in result["errors"]:
                print(f"  WARNING: {err}")

    total_elapsed = (time.perf_counter() - total_start)
    print(f"\nBenchmark complete in {total_elapsed:.1f}s")

    # ------------------------------------------------------------------
    # Generate report
    # ------------------------------------------------------------------
    generate_markdown_report(all_results, output_path, timestamp, vlm_model=vlm_model)

    # ------------------------------------------------------------------
    # Print aggregate summary to stdout as well
    # ------------------------------------------------------------------
    summary_keys = [
        "raw", "preprocessed", "roi_preprocessed", "postprocessed",
        "bbox_crop",
        "vlm_only", "vlm_raw", "vlm_center_crop",
        "florence2_raw", "florence2_crop", "florence2_bbox_crop",
        "florence2_bbox_superres", "florence2_raw_validated",
        "ensemble", "ensemble_v2",
    ]
    print("\n=== SUMMARY ===")
    print(f"{'Method':<25} {'Avg Char Acc':>13} {'Avg Word Acc':>13}")
    print("-" * 55)
    for mk in summary_keys:
        accs = [
            r["methods"].get(mk, {}).get("char_acc")
            for r in all_results
            if r["methods"].get(mk, {}).get("char_acc") is not None
        ]
        word_accs = [
            r["methods"].get(mk, {}).get("word_acc")
            for r in all_results
            if r["methods"].get(mk, {}).get("word_acc") is not None
        ]
        if not accs:
            continue
        avg_char = sum(accs) / len(accs) if accs else 0.0
        avg_word = sum(word_accs) / len(word_accs) if word_accs else 0.0
        label = _METHOD_LABELS[mk]
        print(f"{label:<25} {avg_char * 100:>12.1f}% {avg_word * 100:>12.1f}%")


if __name__ == "__main__":
    main()
