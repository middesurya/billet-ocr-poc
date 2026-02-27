"""FastAPI application for the Billet OCR demo.

Serves pre-computed inference results (browse mode) and live inference
on uploaded images. ML models are lazy-loaded on first /api/infer call.

Usage:
    python -m uvicorn src.api.main:app --reload
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import traceback
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

from src.api.schemas import (
    BilletPrediction,
    BrowseStatsResponse,
    HealthResponse,
    ImageListItem,
    ImageResult,
    InferenceResponse,
)
from src.config import (
    FLORENCE2_BBOX_PAD_RATIO,
    GT_BBOX_PAD_RATIO,
    INFERENCE_REVIEW_ANNOTATED_DIR,
    INFERENCE_REVIEW_CROPS_DIR,
    INFERENCE_REVIEW_DIR,
    INFERENCE_REVIEW_LIVE_DIR,
    INFERENCE_REVIEW_SOURCES_DIR,
    SUPPORTED_FORMATS,
)

app = FastAPI(
    title="Billet OCR Demo",
    description="V11 Ensemble: Florence-2 + PaddleOCR + VLM fallback",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler — ensures ALL errors return JSON with traceback
# ---------------------------------------------------------------------------
from fastapi.requests import Request
from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch any unhandled exception and return JSON with full traceback."""
    tb = traceback.format_exc()
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}", "traceback": tb},
    )


# ---------------------------------------------------------------------------
# In-memory cache for pre-computed results
# ---------------------------------------------------------------------------
_results_cache: Optional[dict] = None
_models_loaded: bool = False


def _load_results() -> dict:
    """Load results.json into memory (cached after first call)."""
    global _results_cache
    if _results_cache is not None:
        return _results_cache

    results_path = INFERENCE_REVIEW_DIR / "results.json"
    if not results_path.exists():
        _results_cache = {"metadata": {}, "images": []}
        return _results_cache

    with open(results_path, encoding="utf-8") as f:
        _results_cache = json.load(f)
    return _results_cache


def _is_valid_5digit(heat: Optional[str]) -> bool:
    """Check if a heat number is a valid 5-digit number."""
    return bool(heat and re.match(r"^\d{5}$", heat))


def _build_confidence_summary(billets: list[dict]) -> dict:
    """Count billets by confidence tier."""
    high = medium = low = 0
    for b in billets:
        conf = b.get("predictions", {}).get("ensemble", {}).get("confidence", 0.0)
        if conf >= 0.80:
            high += 1
        elif conf >= 0.50:
            medium += 1
        else:
            low += 1
    return {"high": high, "medium": medium, "low": low}


def _get_distinct_heats(billets: list[dict]) -> list[str]:
    """Extract sorted unique valid 5-digit heat numbers."""
    heats: set[str] = set()
    for b in billets:
        ht = b.get("predictions", {}).get("ensemble", {}).get("heat_number")
        if _is_valid_5digit(ht):
            heats.add(ht)
    return sorted(heats)


def _billet_to_prediction(billet: dict, base_path: str = "") -> BilletPrediction:
    """Convert a raw billet dict from results.json to a BilletPrediction."""
    preds = billet.get("predictions", {})
    crop_path = billet.get("crop_path", "")
    crop_url = f"{base_path}/{crop_path}" if base_path else f"/images/crops/{Path(crop_path).name}"

    return BilletPrediction(
        bbox_index=billet.get("bbox_index", 0),
        bbox=billet.get("bbox", {}),
        crop_url=crop_url,
        f2_orient=preds.get("f2_orient", {}),
        paddle=preds.get("paddle", {}),
        ensemble=preds.get("ensemble", {}),
    )


# ---------------------------------------------------------------------------
# Static file mounts (must be after route definitions — see below)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Browse endpoints — serve pre-computed data
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Basic health check."""
    data = _load_results()
    return HealthResponse(
        status="ok",
        pipeline=data.get("metadata", {}).get("pipeline", "unknown"),
        browse_images=len(data.get("images", [])),
        models_loaded=_models_loaded,
    )


@app.get("/api/browse/images", response_model=list[ImageListItem])
def browse_images() -> list[ImageListItem]:
    """List all pre-computed inference images with summary stats."""
    data = _load_results()
    items: list[ImageListItem] = []

    for img in data.get("images", []):
        billets = img.get("billets", [])
        conf = _build_confidence_summary(billets)
        heats = _get_distinct_heats(billets)

        items.append(ImageListItem(
            friendly_name=img["friendly_name"],
            num_billets=len(billets),
            confidence_summary=conf,
            distinct_heats=heats,
            is_consistent=len(heats) <= 1,
        ))

    return items


@app.get("/api/browse/images/{friendly_name}", response_model=ImageResult)
def browse_image_detail(friendly_name: str) -> ImageResult:
    """Get full billet detail for a single image."""
    data = _load_results()

    for img in data.get("images", []):
        if img["friendly_name"] == friendly_name:
            billets = img.get("billets", [])
            predictions = [_billet_to_prediction(b) for b in billets]

            return ImageResult(
                friendly_name=img["friendly_name"],
                source_url=f"/images/sources/{friendly_name}.jpg",
                annotated_url=f"/images/annotated/{friendly_name}_annotated.jpg",
                num_billets=len(billets),
                billets=predictions,
                confidence_summary=_build_confidence_summary(billets),
                distinct_heats=_get_distinct_heats(billets),
            )

    raise HTTPException(status_code=404, detail=f"Image '{friendly_name}' not found")


@app.get("/api/browse/stats", response_model=BrowseStatsResponse)
def browse_stats() -> BrowseStatsResponse:
    """Aggregate confidence + decision distributions."""
    data = _load_results()
    metadata = data.get("metadata", {})
    images = data.get("images", [])

    all_billets: list[dict] = []
    for img in images:
        all_billets.extend(img.get("billets", []))

    # Confidence distribution
    high = medium = low = 0
    for b in all_billets:
        conf = b.get("predictions", {}).get("ensemble", {}).get("confidence", 0.0)
        if conf >= 0.80:
            high += 1
        elif conf >= 0.50:
            medium += 1
        else:
            low += 1

    # Decision distribution
    decisions: dict[str, int] = {}
    for b in all_billets:
        dec = b.get("predictions", {}).get("ensemble", {}).get("decision", "ERROR")
        decisions[dec] = decisions.get(dec, 0) + 1

    # Consistency
    consistent = inconsistent = 0
    for img in images:
        heats = _get_distinct_heats(img.get("billets", []))
        if len(heats) <= 1:
            consistent += 1
        else:
            inconsistent += 1

    return BrowseStatsResponse(
        total_images=len(images),
        total_billets=len(all_billets),
        pipeline=metadata.get("pipeline", "unknown"),
        confidence_distribution={"high": high, "medium": medium, "low": low},
        decision_distribution=decisions,
        consistency={"consistent": consistent, "inconsistent": inconsistent},
    )


# ---------------------------------------------------------------------------
# Live inference endpoint
# ---------------------------------------------------------------------------

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB


def _run_inference_sync(raw_img: np.ndarray, filename: str = "") -> dict:
    """Run the full inference pipeline synchronously (called in threadpool).

    Args:
        raw_img: BGR image array.
        filename: Original upload filename (used for Roboflow bbox lookup).

    Returns:
        Dict with bboxes, predictions, live_id, elapsed_ms, bbox_source.
    """
    global _models_loaded
    t_start = time.perf_counter()

    # Detect bboxes — three-tier fallback:
    #   1. Roboflow annotation lookup (known dataset images only)
    #   2. YOLOv8 trained detector (works on any new image)
    #   3. Edge detection (last resort)
    from src.preprocessing.roboflow_detect import detect_billets_roboflow

    bboxes: list[dict] = []
    bbox_source = "edge_detection"

    if filename:
        roboflow_bboxes = detect_billets_roboflow(filename)
        if roboflow_bboxes is not None:
            bboxes = roboflow_bboxes
            bbox_source = "roboflow_annotations"
            logger.info("[infer] Roboflow annotations: %d billets for '%s'", len(bboxes), filename)

    if not bboxes:
        # Tier 2: YOLOv8 trained detector
        from src.preprocessing.yolo_detector import detect_billets_yolo

        yolo_bboxes = detect_billets_yolo(raw_img)
        if yolo_bboxes is not None and len(yolo_bboxes) > 0:
            bboxes = yolo_bboxes
            bbox_source = "yolo_detector"
            logger.info("[infer] YOLO detector: %d billets", len(bboxes))

    if not bboxes:
        # Tier 3: edge-based ROI detection
        from src.preprocessing.roi_detector import detect_billet_faces

        rois = detect_billet_faces(raw_img, max_faces=20)
        for roi in rois:
            x, y, w, h = roi.bounding_rect
            bboxes.append({"x": x, "y": y, "width": w, "height": h})
        bbox_source = "edge_detection"
        logger.info("[infer] Edge detection fallback: %d billets", len(bboxes))

    # Run inference on each billet
    from src.ocr.inference import (
        crop_to_bbox,
        draw_annotated_image,
        run_billet_inference,
    )

    predictions: list[dict] = []
    for bbox in bboxes:
        bbox_crop = crop_to_bbox(raw_img, bbox, pad_ratio=FLORENCE2_BBOX_PAD_RATIO)
        pred = run_billet_inference(bbox_crop)
        predictions.append(pred)

    _models_loaded = True

    # Save outputs to live directory
    live_id = uuid.uuid4().hex[:8]
    src_path = INFERENCE_REVIEW_LIVE_DIR / f"live_{live_id}.jpg"
    cv2.imwrite(str(src_path), raw_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # Save annotated image
    annotated = draw_annotated_image(raw_img, bboxes, predictions)
    ann_path = INFERENCE_REVIEW_LIVE_DIR / f"live_{live_id}_annotated.jpg"
    cv2.imwrite(str(ann_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # Save per-billet crops
    crop_names: list[str] = []
    for idx, bbox in enumerate(bboxes):
        crop = crop_to_bbox(raw_img, bbox, pad_ratio=GT_BBOX_PAD_RATIO)
        crop_name = f"live_{live_id}_bbox{idx:02d}.jpg"
        crop_path = INFERENCE_REVIEW_LIVE_DIR / crop_name
        cv2.imwrite(str(crop_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        crop_names.append(crop_name)

    elapsed_ms = (time.perf_counter() - t_start) * 1000

    return {
        "bboxes": bboxes,
        "predictions": predictions,
        "live_id": live_id,
        "crop_names": crop_names,
        "elapsed_ms": elapsed_ms,
        "bbox_source": bbox_source,
    }


@app.post("/api/infer", response_model=InferenceResponse)
async def infer(file: UploadFile = File(...)) -> InferenceResponse:
    """Upload an image, detect bboxes, run ensemble, return results.

    Bbox detection strategy:
    1. Roboflow annotations (if image name matches)
    2. Edge-based ROI detection fallback

    Blocking ML inference runs in a threadpool to avoid blocking the
    async event loop.
    """
    logger.info("[infer] Request received, filename=%s", file.filename)

    # Validate file type
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format '{ext}'. Use: {SUPPORTED_FORMATS}",
            )

    # Read image bytes (async)
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    # Decode image
    nparr = np.frombuffer(contents, np.uint8)
    raw_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if raw_img is None:
        raise HTTPException(status_code=400, detail="Failed to decode image")

    # Run blocking inference in threadpool
    upload_filename = file.filename or ""
    logger.info("[infer] Image decoded: shape=%s, filename='%s', starting inference...", raw_img.shape, upload_filename)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: _run_inference_sync(raw_img, filename=upload_filename)
        )
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("Inference failed: %s\n%s", exc, tb)
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}")

    # Build response from sync results
    bboxes = result["bboxes"]
    predictions = result["predictions"]
    live_id = result["live_id"]
    crop_names = result["crop_names"]

    billet_preds: list[BilletPrediction] = []
    for idx, (bbox, pred, crop_name) in enumerate(
        zip(bboxes, predictions, crop_names)
    ):
        billet_preds.append(BilletPrediction(
            bbox_index=idx,
            bbox=bbox,
            crop_url=f"/images/live/{crop_name}",
            f2_orient=pred.get("f2_orient", {}),
            paddle=pred.get("paddle", {}),
            ensemble=pred.get("ensemble", {}),
        ))

    return InferenceResponse(
        source_url=f"/images/live/live_{live_id}.jpg",
        annotated_url=f"/images/live/live_{live_id}_annotated.jpg",
        num_billets=len(bboxes),
        billets=billet_preds,
        elapsed_ms=round(result["elapsed_ms"], 1),
        bbox_source=result["bbox_source"],
    )


# ---------------------------------------------------------------------------
# Static file mounts — order matters (most specific first)
# ---------------------------------------------------------------------------

# Image directories
if INFERENCE_REVIEW_SOURCES_DIR.exists():
    app.mount(
        "/images/sources",
        StaticFiles(directory=str(INFERENCE_REVIEW_SOURCES_DIR)),
        name="sources",
    )
if INFERENCE_REVIEW_ANNOTATED_DIR.exists():
    app.mount(
        "/images/annotated",
        StaticFiles(directory=str(INFERENCE_REVIEW_ANNOTATED_DIR)),
        name="annotated",
    )
if INFERENCE_REVIEW_CROPS_DIR.exists():
    app.mount(
        "/images/crops",
        StaticFiles(directory=str(INFERENCE_REVIEW_CROPS_DIR)),
        name="crops",
    )
if INFERENCE_REVIEW_LIVE_DIR.exists():
    app.mount(
        "/images/live",
        StaticFiles(directory=str(INFERENCE_REVIEW_LIVE_DIR)),
        name="live",
    )

# Frontend — must be last (catches all remaining paths)
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
