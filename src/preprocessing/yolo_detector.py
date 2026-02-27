"""YOLOv8-based billet detection for surveillance images.

Uses a YOLOv8n model trained on the Roboflow billet dataset to detect
individual billets in multi-billet surveillance frames. This replaces
the edge detection fallback with a learned detector.

Usage:
    from src.preprocessing.yolo_detector import detect_billets_yolo
    bboxes = detect_billets_yolo(image)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import numpy as np

from src.config import (
    YOLO_CONFIDENCE_THRESHOLD,
    YOLO_IOU_THRESHOLD,
    YOLO_MODEL_PATH,
)

logger = logging.getLogger(__name__)

# Singleton model instance
_yolo_model = None


def _load_model():
    """Lazy-load the YOLOv8 model (singleton).

    Returns:
        YOLO model instance, or None if weights don't exist.
    """
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model

    if not YOLO_MODEL_PATH.exists():
        logger.info(
            "YOLO model not found at %s — detector unavailable. "
            "Train with: python scripts/train_yolo_detector.py",
            YOLO_MODEL_PATH,
        )
        return None

    from ultralytics import YOLO

    logger.info("Loading YOLO billet detector from %s", YOLO_MODEL_PATH)
    _yolo_model = YOLO(str(YOLO_MODEL_PATH))
    logger.info("YOLO billet detector loaded successfully")
    return _yolo_model


def detect_billets_yolo(
    image: Union[str, Path, np.ndarray],
    conf: float = YOLO_CONFIDENCE_THRESHOLD,
    iou: float = YOLO_IOU_THRESHOLD,
) -> Optional[list[dict]]:
    """Detect billets in an image using the trained YOLOv8 model.

    Args:
        image: File path or BGR numpy array.
        conf: Minimum confidence threshold for detections.
        iou: IoU threshold for NMS.

    Returns:
        List of bbox dicts with x, y, width, height keys (sorted by area
        descending), or None if the model is not available.
    """
    model = _load_model()
    if model is None:
        return None

    # Convert Path to str for YOLO
    if isinstance(image, Path):
        image = str(image)

    results = model(image, conf=conf, iou=iou, verbose=False)

    if not results or len(results) == 0:
        logger.info("[YOLO] No detections")
        return []

    result = results[0]
    boxes = result.boxes

    if boxes is None or len(boxes) == 0:
        logger.info("[YOLO] No bounding boxes detected")
        return []

    # Convert xyxy format to {x, y, width, height}
    bboxes: list[dict] = []
    for box in boxes:
        xyxy = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
        bboxes.append({
            "x": round(x1),
            "y": round(y1),
            "width": round(x2 - x1),
            "height": round(y2 - y1),
        })

    # Sort by area descending (largest first)
    bboxes.sort(key=lambda b: b["width"] * b["height"], reverse=True)

    logger.info("[YOLO] Detected %d billets", len(bboxes))
    return bboxes
