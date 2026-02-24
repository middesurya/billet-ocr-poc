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
    use_easyocr: bool = False,
    use_trocr: bool = False,
    use_doctr: bool = False,
    use_bbox_crop: bool = False,
    bbox_annotations: Optional[dict] = None,
) -> dict:
    """Run all pipeline stages on a single image and collect results.

    Args:
        entry: Ground truth dict with keys: image, heat_number, strand, sequence.
        use_vlm: Whether to invoke Claude Vision when PaddleOCR confidence is low.
        vlm_only: If True, skip PaddleOCR stages and only run VLM + ensemble.
        vlm_model: Claude model ID for VLM stages.
        use_florence2: Whether to run Florence-2 stages.
        use_easyocr: Whether to run EasyOCR stages.
        use_trocr: Whether to run TrOCR stages.
        use_doctr: Whether to run docTR stages.
        use_bbox_crop: Whether to run bbox-crop + PaddleOCR stages.
        bbox_annotations: Pre-loaded Roboflow bbox annotations dict.

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

                bbox = bbox_annotations[img_name][0]  # First/largest bbox
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
    # Stage 8: EasyOCR on preprocessed image
    # ------------------------------------------------------------------
    if use_easyocr:
        try:
            from src.ocr.easyocr_reader import run_easyocr_pipeline

            ocr_input = preprocessed if preprocessed is not None else img_path
            t0 = time.perf_counter()
            easy_reading = run_easyocr_pipeline(ocr_input)
            easy_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["easyocr"] = {
                "heat_number": easy_reading.heat_number,
                "strand": easy_reading.strand,
                "sequence": easy_reading.sequence,
                "confidence": easy_reading.confidence,
                "ocr_time_ms": easy_ms,
                "char_acc": calculate_character_accuracy(easy_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(easy_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"EasyOCR error: {exc}")
            result["methods"]["easyocr"] = {
                "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
            }
    else:
        result["methods"]["easyocr"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 9: TrOCR on preprocessed image
    # ------------------------------------------------------------------
    if use_trocr:
        try:
            from src.ocr.trocr_reader import run_trocr_pipeline

            ocr_input = preprocessed if preprocessed is not None else img_path
            t0 = time.perf_counter()
            trocr_reading = run_trocr_pipeline(ocr_input)
            trocr_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["trocr"] = {
                "heat_number": trocr_reading.heat_number,
                "strand": trocr_reading.strand,
                "sequence": trocr_reading.sequence,
                "confidence": trocr_reading.confidence,
                "ocr_time_ms": trocr_ms,
                "char_acc": calculate_character_accuracy(trocr_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(trocr_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"TrOCR error: {exc}")
            result["methods"]["trocr"] = {
                "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
            }
    else:
        result["methods"]["trocr"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    # ------------------------------------------------------------------
    # Stage 10: docTR on preprocessed image
    # ------------------------------------------------------------------
    if use_doctr:
        try:
            from src.ocr.doctr_reader import run_doctr_pipeline

            ocr_input = preprocessed if preprocessed is not None else img_path
            t0 = time.perf_counter()
            doctr_reading = run_doctr_pipeline(ocr_input)
            doctr_ms = (time.perf_counter() - t0) * 1000

            result["methods"]["doctr"] = {
                "heat_number": doctr_reading.heat_number,
                "strand": doctr_reading.strand,
                "sequence": doctr_reading.sequence,
                "confidence": doctr_reading.confidence,
                "ocr_time_ms": doctr_ms,
                "char_acc": calculate_character_accuracy(doctr_reading.heat_number, gt_heat),
                "word_acc": calculate_word_accuracy(doctr_reading.heat_number, gt_heat),
            }
        except Exception as exc:
            result["errors"].append(f"docTR error: {exc}")
            result["methods"]["doctr"] = {
                "heat_number": None, "char_acc": 0.0, "word_acc": 0.0,
            }
    else:
        result["methods"]["doctr"] = {
            "heat_number": None, "char_acc": None, "word_acc": None,
        }

    return result


# ---------------------------------------------------------------------------
# Markdown report generator
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
    "easyocr": "EasyOCR",
    "trocr": "TrOCR",
    "doctr": "docTR",
    "ensemble": "Ensemble",
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
        "florence2_raw", "florence2_crop",
        "easyocr", "trocr", "doctr",
        "ensemble",
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
    florence2_methods = ["florence2_raw", "florence2_crop"]
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
            header += " Florence-2 Raw | Florence-2 Crop |"
            separator += "----------------|-----------------|"
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
        header += " F2 Raw | F2 Crop |"
        separator += "--------|---------|"
    header += " Ensemble |"
    separator += "----------|"
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
        ensemble = res["methods"].get("ensemble", {})

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
            )
        row += f" {_format_acc(ensemble.get('char_acc'))} |"
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
        "--easyocr",
        action="store_true",
        default=False,
        help="Include EasyOCR stages in the benchmark.",
    )
    parser.add_argument(
        "--trocr",
        action="store_true",
        default=False,
        help="Include TrOCR stages in the benchmark.",
    )
    parser.add_argument(
        "--doctr",
        action="store_true",
        default=False,
        help="Include docTR stages in the benchmark.",
    )
    parser.add_argument(
        "--bbox-crop",
        action="store_true",
        default=False,
        help="Include bbox-crop + PaddleOCR using Roboflow annotations.",
    )
    parser.add_argument(
        "--all-engines",
        action="store_true",
        default=False,
        help="Enable all alternative OCR engines (EasyOCR, TrOCR, docTR, bbox-crop).",
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
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    use_vlm = not args.no_vlm
    vlm_only = args.vlm_only
    vlm_model = args.vlm_model
    use_florence2 = args.florence2
    use_easyocr = args.easyocr or args.all_engines
    use_trocr = args.trocr or args.all_engines
    use_doctr = args.doctr or args.all_engines
    use_bbox_crop = args.bbox_crop or args.all_engines

    # --vlm-only implies VLM is enabled.
    if vlm_only:
        use_vlm = True

    # ------------------------------------------------------------------
    # Load ground truth
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
        from src.config import FLORENCE2_MODEL_ID as _f2_id
        print(f"Florence-2: enabled (model={_f2_id})")
    if use_easyocr:
        print("EasyOCR: enabled")
    if use_trocr:
        print("TrOCR: enabled")
    if use_doctr:
        print("docTR: enabled")

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
            use_easyocr=use_easyocr, use_trocr=use_trocr,
            use_doctr=use_doctr, use_bbox_crop=use_bbox_crop,
            bbox_annotations=bbox_annotations,
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
        if f2_raw.get("char_acc") is not None:
            print(
                f"  F2-Raw heat={f2_raw.get('heat_number')!r:12s} "
                f"acc={_format_acc(f2_raw.get('char_acc')):6s}  |  "
                f"F2-Crop acc={_format_acc(f2_crop.get('char_acc')):6s}"
            )
        # Alternative OCR engines summary.
        alt_engines = [
            ("Bbox-Crop", "bbox_crop"),
            ("EasyOCR", "easyocr"),
            ("TrOCR", "trocr"),
            ("docTR", "doctr"),
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
        "florence2_raw", "florence2_crop",
        "easyocr", "trocr", "doctr",
        "ensemble",
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
