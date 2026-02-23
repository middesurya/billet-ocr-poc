"""ROI (Region of Interest) detection for billet end faces.

Finds the square billet end face within a full photo using a multi-strategy
cascade:
    1. Edge-based quadrilateral detection (primary)
    2. Largest-contour bounding rect (fallback for close-ups)
    3. Center-weighted crop (last resort)

The detected ROI can then be cropped and passed to the perspective correction
and CLAHE preprocessing stages before OCR.
"""

from __future__ import annotations

from typing import Optional, Union
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from src.config import (
    ROI_CANNY_THRESHOLD1,
    ROI_CANNY_THRESHOLD2,
    ROI_MIN_AREA_RATIO,
    ROI_MAX_AREA_RATIO,
    ROI_ASPECT_RATIO_RANGE,
    ROI_APPROX_EPSILON,
    ROI_BLUR_KERNEL,
    ROI_DILATE_KERNEL,
    ROI_DILATE_ITERATIONS,
)
from src.models import BilletROI


def _get_edge_map(gray: np.ndarray) -> np.ndarray:
    """Produce a dilated Canny edge map from a grayscale image.

    Pipeline: Gaussian blur -> Canny -> dilation (close small gaps).

    Args:
        gray: Single-channel grayscale image (H, W).

    Returns:
        Binary edge map with dilated edges.
    """
    blurred = cv2.GaussianBlur(gray, ROI_BLUR_KERNEL, 0)
    edges = cv2.Canny(blurred, ROI_CANNY_THRESHOLD1, ROI_CANNY_THRESHOLD2)
    kernel = np.ones(ROI_DILATE_KERNEL, np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=ROI_DILATE_ITERATIONS)
    return dilated


def _contour_to_roi(
    contour: np.ndarray,
    image_area: float,
    corners: np.ndarray,
) -> Optional[BilletROI]:
    """Convert a contour and its corner points into a BilletROI if valid.

    Validates area range and aspect ratio before creating the ROI.

    Args:
        contour: Raw OpenCV contour.
        image_area: Total image area in pixels (H * W).
        corners: 4 corner points as (4, 2) array.

    Returns:
        BilletROI if valid, None otherwise.
    """
    area = cv2.contourArea(contour)
    area_ratio = area / image_area

    if area_ratio < ROI_MIN_AREA_RATIO or area_ratio > ROI_MAX_AREA_RATIO:
        return None

    x, y, w, h = cv2.boundingRect(contour)
    aspect = w / h if h > 0 else 0.0
    min_ar, max_ar = ROI_ASPECT_RATIO_RANGE

    if aspect < min_ar or aspect > max_ar:
        return None

    # Confidence heuristic: reward squareness and size
    # min(aspect, 1/aspect) gives 1.0 for perfect square, degrades smoothly
    squareness = min(aspect, 1.0 / aspect) if aspect > 0 else 0.0
    size_score = min(area_ratio / 0.1, 1.0)  # Saturates at 10% of image
    is_convex = cv2.isContourConvex(corners.reshape(-1, 1, 2))
    convexity_bonus = 1.0 if is_convex else 0.7

    confidence = squareness * size_score * convexity_bonus
    confidence = min(max(confidence, 0.0), 1.0)

    corner_list = [(float(pt[0]), float(pt[1])) for pt in corners]

    return BilletROI(
        corners=corner_list,
        bounding_rect=(x, y, w, h),
        area=float(area),
        confidence=confidence,
        contour=contour,
    )


def _strategy_quadrilateral(
    gray: np.ndarray,
    image_area: float,
) -> list[BilletROI]:
    """Strategy 1: Find 4-vertex polygons via edge detection + approxPolyDP.

    Args:
        gray: Grayscale image.
        image_area: Total image area (H * W).

    Returns:
        List of BilletROI candidates sorted by confidence (descending).
    """
    edges = _get_edge_map(gray)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[BilletROI] = []

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, ROI_APPROX_EPSILON * peri, True)

        if len(approx) != 4:
            continue

        corners = approx.reshape(4, 2)
        roi = _contour_to_roi(contour, image_area, corners)
        if roi is not None:
            candidates.append(roi)

    candidates.sort(key=lambda r: r.confidence, reverse=True)
    logger.debug(
        "Strategy 1 (quadrilateral): found {} candidates", len(candidates)
    )
    return candidates


def _strategy_largest_contour(
    gray: np.ndarray,
    image_area: float,
) -> list[BilletROI]:
    """Strategy 2: Take the largest contour and fit a minAreaRect.

    Used when Strategy 1 finds no clean quadrilaterals. The largest contour
    is likely the billet face boundary even if it's not a perfect polygon.

    Args:
        gray: Grayscale image.
        image_area: Total image area (H * W).

    Returns:
        List with 0 or 1 BilletROI.
    """
    edges = _get_edge_map(gray)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        logger.debug("Strategy 2 (largest contour): no contours found")
        return []

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    area_ratio = area / image_area

    if area_ratio < ROI_MIN_AREA_RATIO:
        logger.debug(
            "Strategy 2: largest contour too small ({:.3f}% of image)",
            area_ratio * 100,
        )
        return []

    rect = cv2.minAreaRect(largest)
    box = cv2.boxPoints(rect)
    corners = box.astype(np.float32)

    roi = _contour_to_roi(largest, image_area, corners)
    if roi is not None:
        # Slightly penalize since this is a fallback strategy
        roi.confidence *= 0.8
        logger.debug(
            "Strategy 2 (largest contour): found ROI with confidence {:.2f}",
            roi.confidence,
        )
        return [roi]

    return []


def _strategy_center_crop(
    image_shape: tuple[int, ...],
) -> list[BilletROI]:
    """Strategy 3: Assume face is centered and crop to central 70%.

    Last resort when edge detection fails entirely. Returns a low-confidence
    ROI centered in the image.

    Args:
        image_shape: Shape tuple (H, W) or (H, W, C).

    Returns:
        List with exactly 1 BilletROI at low confidence.
    """
    h, w = image_shape[:2]
    margin_x = int(w * 0.15)
    margin_y = int(h * 0.15)

    x1, y1 = margin_x, margin_y
    x2, y2 = w - margin_x, h - margin_y
    crop_w, crop_h = x2 - x1, y2 - y1

    corners = [
        (float(x1), float(y1)),  # TL
        (float(x2), float(y1)),  # TR
        (float(x2), float(y2)),  # BR
        (float(x1), float(y2)),  # BL
    ]

    roi = BilletROI(
        corners=corners,
        bounding_rect=(x1, y1, crop_w, crop_h),
        area=float(crop_w * crop_h),
        confidence=0.2,
        contour=None,
    )
    logger.debug("Strategy 3 (center crop): fallback ROI at confidence 0.2")
    return [roi]


def detect_billet_faces(
    image: Union[np.ndarray, str, Path],
    max_faces: int = 5,
) -> list[BilletROI]:
    """Detect billet end faces in an image using a multi-strategy cascade.

    Strategies are tried in order:
        1. Edge-based quadrilateral detection
        2. Largest-contour bounding rect
        3. Center-weighted crop (always produces a result)

    Args:
        image: BGR image array, or path to an image file.
        max_faces: Maximum number of faces to return.

    Returns:
        List of BilletROI sorted by confidence (descending), up to max_faces.
    """
    from src.preprocessing.pipeline import load_image

    img = load_image(image)

    if img.ndim == 2:
        gray = img
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    image_area = float(gray.shape[0] * gray.shape[1])

    # Strategy 1: quadrilateral detection
    candidates = _strategy_quadrilateral(gray, image_area)
    if candidates:
        logger.info(
            "detect_billet_faces: Strategy 1 found {} candidates", len(candidates)
        )
        return candidates[:max_faces]

    # Strategy 2: largest contour
    candidates = _strategy_largest_contour(gray, image_area)
    if candidates:
        logger.info("detect_billet_faces: Strategy 2 found largest-contour ROI")
        return candidates[:max_faces]

    # Strategy 3: center crop fallback
    logger.warning("detect_billet_faces: falling back to center crop (Strategy 3)")
    return _strategy_center_crop(img.shape)[:max_faces]


def detect_best_billet_face(
    image: Union[np.ndarray, str, Path],
) -> Optional[BilletROI]:
    """Detect the single best billet end face in an image.

    Convenience wrapper around detect_billet_faces that returns the
    highest-confidence face or None.

    Args:
        image: BGR image array, or path to an image file.

    Returns:
        The highest-confidence BilletROI, or None if detection fails.
    """
    faces = detect_billet_faces(image, max_faces=1)
    return faces[0] if faces else None


def crop_to_roi(
    image: np.ndarray,
    roi: BilletROI,
    padding_percent: float = 0.05,
) -> np.ndarray:
    """Crop an image to the detected ROI with optional padding.

    Uses the axis-aligned bounding rect for cropping, expanded by
    padding_percent on each side. Clips to image boundaries.

    Args:
        image: BGR or grayscale image array.
        roi: Detected BilletROI to crop to.
        padding_percent: Fraction of ROI dimensions to add as padding.

    Returns:
        Cropped image region as numpy array.
    """
    h_img, w_img = image.shape[:2]
    x, y, w, h = roi.bounding_rect

    pad_x = int(w * padding_percent)
    pad_y = int(h * padding_percent)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w_img, x + w + pad_x)
    y2 = min(h_img, y + h + pad_y)

    cropped = image[y1:y2, x1:x2]
    logger.debug(
        "crop_to_roi: ({},{}) -> ({},{}) = {}x{} pixels",
        x1, y1, x2, y2, x2 - x1, y2 - y1,
    )
    return cropped


def visualize_roi(
    image: np.ndarray,
    rois: list[BilletROI],
    output_path: Optional[Union[str, Path]] = None,
) -> np.ndarray:
    """Draw detected ROI overlays on an image for debugging.

    Each ROI is drawn as a green polygon with its confidence label.
    The best (first) ROI is drawn in green; others are drawn in yellow.

    Args:
        image: BGR image to draw on (a copy is made).
        rois: List of BilletROI to visualize.
        output_path: Optional path to save the annotated image.

    Returns:
        Annotated BGR image with ROI overlays.
    """
    vis = image.copy()

    for i, roi in enumerate(rois):
        color = (0, 255, 0) if i == 0 else (0, 255, 255)
        thickness = 3 if i == 0 else 2

        pts = np.array(roi.corners, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(vis, [pts], isClosed=True, color=color, thickness=thickness)

        # Label with confidence
        label_pos = (int(roi.corners[0][0]), int(roi.corners[0][1]) - 10)
        cv2.putText(
            vis,
            f"ROI #{i+1} conf={roi.confidence:.2f}",
            label_pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), vis)
        logger.debug("visualize_roi: saved to '{}'", out_path)

    return vis
