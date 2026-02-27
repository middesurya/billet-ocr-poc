"""PaddleOCR wrapper for billet stamp recognition.

Uses PaddleOCR PP-OCRv5 (v3.4.0 API) as the primary OCR engine.
Handles the v3 predict-style result dicts and converts them into
structured OCRResult / BilletReading objects.
"""

import os
import re
import warnings
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

import cv2

from src.config import (
    PADDLEOCR_LANG,
    PADDLEOCR_MAX_SIDE_LEN,
    PADDLEOCR_USE_ANGLE_CLS,
    PADDLEOCR_USE_GPU,
)
from src.models import BilletReading, BoundingBox, OCRMethod, OCRResult

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------

_paddle_instance: Optional["PaddleOCR"] = None  # type: ignore[type-arg]

# PaddleOCR v3 uses oneDNN (MKLDNN) by default on CPU, which triggers a
# NotImplementedError with the current Paddle 3.3 build on Windows.
# We patch both the det and rec model predictors to use the plain 'paddle'
# run mode (no MKLDNN) and disable the experimental new IR compiler.
_Y_LINE_CLUSTER_THRESHOLD = 30  # px – controls multi-line grouping


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _suppress_paddle_logs() -> None:
    """Suppress verbose logging from PaddleOCR / PaddleX / HuggingFace."""
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    import logging

    for noisy in (
        "paddleocr",
        "paddlex",
        "paddle",
        "huggingface_hub",
        "filelock",
        "urllib3",
    ):
        logging.getLogger(noisy).setLevel(logging.ERROR)


def _patch_predictor_run_mode(ocr_instance: "PaddleOCR") -> None:  # type: ignore[type-arg]
    """Rebuild model predictors without MKLDNN / new-IR to avoid the
    ``ConvertPirAttribute2RuntimeAttribute`` NotImplementedError on Windows.

    Args:
        ocr_instance: An already-constructed PaddleOCR instance.
    """
    pipeline = getattr(ocr_instance, "paddlex_pipeline", None)
    if pipeline is None:
        logger.debug("No paddlex_pipeline found; skipping predictor patch.")
        return

    for attr in ("text_det_model", "text_rec_model"):
        model = getattr(pipeline, attr, None)
        if model is None:
            continue
        try:
            infer = model.infer
            opt = infer._option
            if opt.run_mode != "paddle":
                opt.run_mode = "paddle"
            opt.enable_new_ir = False
            infer.predictor = infer._create()
            # PaddleInferChainLegacy wraps the raw predictor
            infer.infer = type(infer.infer)(infer.predictor)
            logger.debug(
                "Patched {attr}: run_mode=paddle, enable_new_ir=False", attr=attr
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not patch predictor for {attr}: {exc}", attr=attr, exc=exc
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def initialize_paddle_ocr(
    lang: str = PADDLEOCR_LANG,
    use_angle_cls: bool = PADDLEOCR_USE_ANGLE_CLS,
    use_gpu: bool = PADDLEOCR_USE_GPU,
) -> "PaddleOCR":  # type: ignore[type-arg]
    """Initialize (or return the cached) PaddleOCR singleton.

    Models are loaded only once.  The first call may take several seconds;
    subsequent calls return the cached instance immediately.

    Args:
        lang: Language code passed to PaddleOCR (e.g. ``"en"``).
        use_angle_cls: Whether to enable text-angle classification.
            Note: PaddleOCR v3 controls this via the
            ``use_textline_orientation`` pipeline parameter.
        use_gpu: Whether to use GPU for inference.

    Returns:
        A ready-to-use ``PaddleOCR`` instance.
    """
    global _paddle_instance

    if _paddle_instance is not None:
        logger.debug("Returning cached PaddleOCR singleton.")
        return _paddle_instance

    _suppress_paddle_logs()

    logger.info(
        "Initializing PaddleOCR: lang={lang}, use_angle_cls={angle}, use_gpu={gpu}",
        lang=lang,
        angle=use_angle_cls,
        gpu=use_gpu,
    )

    # PaddleOCR v3.4.0 does not accept show_log or use_angle_cls directly.
    # use_textline_orientation is the v3 equivalent of use_angle_cls.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from paddleocr import PaddleOCR as _PaddleOCR  # type: ignore

        instance = _PaddleOCR(
            lang=lang,
            use_textline_orientation=use_angle_cls,
        )

    _patch_predictor_run_mode(instance)

    _paddle_instance = instance
    logger.info("PaddleOCR initialized successfully.")
    return _paddle_instance


def run_ocr(
    image: Union[str, Path, np.ndarray],
) -> list[OCRResult]:
    """Run PaddleOCR on an image and return a list of OCRResult objects.

    Results are sorted top-to-bottom by the vertical centre of each
    bounding box so that line ordering is deterministic.

    Args:
        image: Image to process.  Accepts a file-system path (str or Path)
            or a numpy array in either BGR (OpenCV) or RGB colour order.

    Returns:
        List of :class:`~src.models.OCRResult` objects, sorted by ascending
        Y-coordinate (top of image first).  Returns an empty list if
        PaddleOCR produces no detections.
    """
    ocr = initialize_paddle_ocr()

    # PaddleOCR v3 needs a str path or ndarray; convert Path to str.
    if isinstance(image, Path):
        image = str(image)

    # Load file path to ndarray so we can resize if needed.
    if isinstance(image, str):
        img_arr = cv2.imread(image)
        if img_arr is None:
            logger.error("Failed to load image: {p}", p=image)
            return []
        image = img_arr

    # Resize large images to avoid PaddlePaddle static-inference crashes on
    # Windows and to match the model's optimal input scale.
    h, w = image.shape[:2]
    max_side = max(h, w)
    if max_side > PADDLEOCR_MAX_SIDE_LEN:
        scale = PADDLEOCR_MAX_SIDE_LEN / max_side
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug(
            "Resized image from ({ow}x{oh}) to ({nw}x{nh}) for PaddleOCR",
            ow=w, oh=h, nw=new_w, nh=new_h,
        )

    logger.debug("Running PaddleOCR on input type={t}", t=type(image).__name__)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw_result = ocr.ocr(image)
    except Exception as exc:  # noqa: BLE001
        logger.error("PaddleOCR.ocr() raised an exception: {exc}", exc=exc)
        return []

    # v3 returns a list of page dicts; None / empty list are both possible.
    if not raw_result:
        logger.warning("PaddleOCR returned no result (None or empty list).")
        return []

    page = raw_result[0]
    if page is None:
        logger.warning("PaddleOCR page[0] is None – no text detected.")
        return []

    rec_texts: list[str] = page.get("rec_texts", []) or []
    rec_scores: list[float] = page.get("rec_scores", []) or []
    rec_polys: list = page.get("rec_polys", []) or []

    if not rec_texts:
        logger.info("PaddleOCR detected no text regions in the image.")
        return []

    results: list[OCRResult] = []
    for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
        # poly is an ndarray of shape (4, 2): [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        try:
            points = [(float(p[0]), float(p[1])) for p in poly]
            bbox = BoundingBox(points=points)
        except Exception:  # noqa: BLE001
            bbox = None  # type: ignore[assignment]

        result = OCRResult(text=text, confidence=float(score), bbox=bbox)
        logger.debug(
            'OCR result: text="{text}" confidence={conf:.4f}',
            text=text,
            conf=score,
        )
        results.append(result)

    # Sort top-to-bottom by the mean Y of the bounding-box corners.
    def _center_y(r: OCRResult) -> float:
        if r.bbox is None:
            return 0.0
        return sum(pt[1] for pt in r.bbox.points) / len(r.bbox.points)

    results.sort(key=_center_y)

    logger.info(
        "PaddleOCR returned {n} text region(s).",
        n=len(results),
    )
    return results


def extract_billet_info(
    ocr_results: list[OCRResult],
    method: OCRMethod = OCRMethod.PADDLE_RAW,
) -> BilletReading:
    """Group OCR results into billet fields (heat number, strand, sequence).

    Billet stamps follow a two-line layout:
    - Line 1 (topmost): 5–7-digit heat number, e.g. ``"184767"``
    - Line 2: strand + sequence separated by whitespace, e.g. ``"3 09"``

    Results are grouped into lines by clustering on Y-coordinate proximity
    (threshold: ``_Y_LINE_CLUSTER_THRESHOLD`` pixels).  Within each line
    the text is joined left-to-right.

    Args:
        ocr_results: OCR results sorted top-to-bottom (output of
            :func:`run_ocr`).
        method: The :class:`~src.models.OCRMethod` to record in the
            returned reading.

    Returns:
        A :class:`~src.models.BilletReading` with parsed fields.  Fields
        that cannot be extracted are left as ``None``.
    """
    if not ocr_results:
        logger.warning("extract_billet_info: no OCR results to process.")
        return BilletReading(method=method)

    raw_texts = [r.text for r in ocr_results]
    overall_confidence = (
        sum(r.confidence for r in ocr_results) / len(ocr_results)
        if ocr_results
        else 0.0
    )

    # ------------------------------------------------------------------
    # Group into lines by Y-proximity
    # ------------------------------------------------------------------
    def _center_y(r: OCRResult) -> float:
        if r.bbox is None:
            return 0.0
        return sum(pt[1] for pt in r.bbox.points) / len(r.bbox.points)

    lines: list[list[OCRResult]] = []
    for result in ocr_results:
        cy = _center_y(result)
        placed = False
        for line in lines:
            line_cy = sum(_center_y(r) for r in line) / len(line)
            if abs(cy - line_cy) <= _Y_LINE_CLUSTER_THRESHOLD:
                line.append(result)
                placed = True
                break
        if not placed:
            lines.append([result])

    # Sort each line left-to-right by X centre.
    def _center_x(r: OCRResult) -> float:
        if r.bbox is None:
            return 0.0
        return sum(pt[0] for pt in r.bbox.points) / len(r.bbox.points)

    for line in lines:
        line.sort(key=_center_x)

    line_texts = [" ".join(r.text for r in line) for line in lines]
    logger.debug("Line groups: {lines}", lines=line_texts)

    # ------------------------------------------------------------------
    # Parse heat number from line 0
    # ------------------------------------------------------------------
    heat_number: Optional[str] = None
    strand: Optional[str] = None
    sequence: Optional[str] = None

    if len(lines) >= 1:
        heat_number = " ".join(r.text for r in lines[0]).strip()
        logger.debug('Heat number candidate: "{h}"', h=heat_number)

    # ------------------------------------------------------------------
    # Parse strand + sequence from line 1
    # ------------------------------------------------------------------
    if len(lines) >= 2:
        line2_text = " ".join(r.text for r in lines[1]).strip()
        logger.debug('Strand/sequence candidate: "{l}"', l=line2_text)

        # Parse strand + sequence from line 2.
        # Paint-stencil format: line 2 is a single 3-4 digit sequence (no strand).
        # Dot-matrix format: line 2 is "[strand] [sequence]" with space.
        parts = line2_text.split()
        if len(parts) == 1 and re.match(r"^\d{3,4}$", parts[0]):
            # Paint-stencil: line 2 IS the full sequence (e.g., "5383")
            sequence = parts[0].strip()
        elif len(parts) >= 1:
            strand = parts[0].strip()
            if len(parts) >= 2:
                # Dot-matrix: join remaining parts as sequence
                sequence = "".join(parts[1:]).strip()

    reading = BilletReading(
        heat_number=heat_number,
        strand=strand,
        sequence=sequence,
        confidence=overall_confidence,
        method=method,
        raw_texts=raw_texts,
    )

    logger.info(
        "Extracted billet reading: heat={h}, strand={s}, seq={q}, conf={c:.4f}",
        h=heat_number,
        s=strand,
        q=sequence,
        c=overall_confidence,
    )
    return reading


def run_paddle_pipeline(
    image: Union[str, Path, np.ndarray],
    method: OCRMethod = OCRMethod.PADDLE_RAW,
) -> BilletReading:
    """End-to-end convenience function: OCR + field extraction in one call.

    Runs :func:`run_ocr` followed by :func:`extract_billet_info`.

    Args:
        image: Image to process.  Accepts a file-system path (str or Path)
            or a numpy array (BGR or RGB).
        method: OCR method tag to embed in the returned
            :class:`~src.models.BilletReading`.

    Returns:
        A :class:`~src.models.BilletReading` populated with whatever fields
        could be extracted.  Returns an empty reading if OCR produces no
        results.
    """
    logger.info("run_paddle_pipeline: starting.")
    ocr_results = run_ocr(image)
    reading = extract_billet_info(ocr_results, method=method)
    logger.info("run_paddle_pipeline: complete.")
    return reading
