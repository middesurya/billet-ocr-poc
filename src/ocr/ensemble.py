"""Ensemble pipeline orchestrating PaddleOCR and VLM (Claude Vision) fallback.

The ensemble runs a confidence-gated cascade:
1. PaddleOCR processes the image first (fast, free, offline-capable).
2. If PaddleOCR confidence is below the threshold, Claude Vision is invoked
   as a fallback on the same image.
3. If both engines struggle, the reading with higher confidence wins.

The ``skip_paddle`` flag bypasses PaddleOCR entirely for VLM-only evaluation.

Every call logs which execution path was taken and the confidence scores of
each engine that ran, enabling downstream analysis of routing decisions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

from src.config import OCR_CONFIDENCE_THRESHOLD
from src.models import BilletReading, OCRMethod


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
