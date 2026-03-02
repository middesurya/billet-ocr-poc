"""Roboflow annotation-based billet bounding box lookup.

Loads pre-computed COCO bounding boxes from roboflow_bboxes.json and
matches uploaded images by filename. The Roboflow project (ztai/steel-billet)
has annotations only — no trained detection model — so we use the static
annotation file instead of the Roboflow inference API.

Usage:
    from src.preprocessing.roboflow_detect import detect_billets_roboflow
    bboxes = detect_billets_roboflow(filename="screenshot_2025-04-07_10-57-54_jpg.rf.abc123.jpg")
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from src.config import BBOX_ANNOTATIONS_PATH

logger = logging.getLogger(__name__)

# Lazy-loaded annotation cache
_annotations: Optional[dict[str, list[dict]]] = None
# Reverse index: rf_hash → filename (for fuzzy matching)
_hash_index: Optional[dict[str, str]] = None


def _load_annotations() -> dict[str, list[dict]]:
    """Lazy-load and cache the roboflow_bboxes.json annotations.

    Returns:
        Dict mapping filename → list of bbox dicts.
    """
    global _annotations, _hash_index
    if _annotations is not None:
        return _annotations

    if not BBOX_ANNOTATIONS_PATH.exists():
        logger.warning(
            "Bbox annotations not found at %s — run parse_roboflow_annotations.py first",
            BBOX_ANNOTATIONS_PATH,
        )
        _annotations = {}
        _hash_index = {}
        return _annotations

    with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as f:
        _annotations = json.load(f)

    # Build reverse index by Roboflow hash for fuzzy matching
    _hash_index = {}
    for fname in _annotations:
        rf_hash = _extract_rf_hash(fname)
        if rf_hash:
            _hash_index[rf_hash] = fname

    logger.info(
        "Loaded %d image annotations from %s",
        len(_annotations),
        BBOX_ANNOTATIONS_PATH.name,
    )
    return _annotations


def _extract_rf_hash(filename: str) -> Optional[str]:
    """Extract the Roboflow augmentation hash from a filename.

    Roboflow filenames follow: {base}_jpg.rf.{hash}.jpg
    The hash is a unique 32-char hex string per augmentation.

    Args:
        filename: Roboflow image filename.

    Returns:
        The hash string, or None if not a Roboflow filename.
    """
    match = re.search(r"\.rf\.([a-f0-9]+)\.", filename)
    return match.group(1) if match else None


def _normalize_filename(filename: str) -> str:
    """Normalize a filename for comparison by replacing dashes with underscores.

    Roboflow sometimes uses underscores where the original had dashes
    (e.g., 'screenshot-2025' → 'screenshot_2025').

    Args:
        filename: Original filename.

    Returns:
        Normalized filename.
    """
    return filename.replace("-", "_")


def detect_billets_roboflow(filename: str) -> Optional[list[dict]]:
    """Look up pre-computed bounding boxes for an image by filename.

    Matching strategy (in order):
    1. Exact filename match
    2. Normalized match (dashes → underscores)
    3. Roboflow hash match (unique per augmentation)

    Args:
        filename: The uploaded image filename.

    Returns:
        List of bbox dicts sorted by area descending, or None if no
        match found (triggers edge detection fallback).
    """
    annotations = _load_annotations()
    if not annotations:
        return None

    # Strategy 1: exact match
    if filename in annotations:
        bboxes = annotations[filename]
        logger.info("Bbox lookup: exact match '%s' → %d bboxes", filename, len(bboxes))
        return _sort_by_area(bboxes)

    # Strategy 2: normalized match (dashes → underscores)
    norm_name = _normalize_filename(filename)
    for ann_fname in annotations:
        if _normalize_filename(ann_fname) == norm_name:
            bboxes = annotations[ann_fname]
            logger.info(
                "Bbox lookup: normalized match '%s' → '%s' → %d bboxes",
                filename,
                ann_fname,
                len(bboxes),
            )
            return _sort_by_area(bboxes)

    # Strategy 3: match by Roboflow hash
    rf_hash = _extract_rf_hash(filename)
    if rf_hash and _hash_index and rf_hash in _hash_index:
        ann_fname = _hash_index[rf_hash]
        bboxes = annotations[ann_fname]
        logger.info(
            "Bbox lookup: hash match '%s' → '%s' → %d bboxes",
            filename,
            ann_fname,
            len(bboxes),
        )
        return _sort_by_area(bboxes)

    logger.info("Bbox lookup: no match for '%s' — falling back to edge detection", filename)
    return None


def _sort_by_area(bboxes: list[dict]) -> list[dict]:
    """Sort bboxes by area descending (largest first).

    Args:
        bboxes: List of bbox dicts with width and height keys.

    Returns:
        Sorted copy of the list.
    """
    return sorted(bboxes, key=lambda b: b["width"] * b["height"], reverse=True)
