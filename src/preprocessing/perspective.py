"""Perspective correction for billet end faces.

When a billet is photographed at an angle, the square end face appears as a
trapezoid. This module warps the detected quadrilateral back to a fronto-
parallel square view using OpenCV's perspective transform.

The corner ordering convention is TL, TR, BR, BL (clockwise from top-left).
"""

from __future__ import annotations

from typing import Union
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from src.config import PERSPECTIVE_TARGET_SIZE, PERSPECTIVE_BORDER_PERCENT
from src.models import BilletROI


def order_corners(points: Union[list, np.ndarray]) -> list[tuple[float, float]]:
    """Order 4 corner points as TL, TR, BR, BL (clockwise from top-left).

    Uses the sum (x+y) and difference (y-x) of coordinates:
        - TL: smallest x+y sum
        - BR: largest x+y sum
        - TR: smallest y-x (rightmost, topmost)
        - BL: largest y-x (leftmost, bottommost)

    Args:
        points: 4 points as a list of (x, y) tuples or (4, 2) array.

    Returns:
        List of 4 (x, y) tuples in TL, TR, BR, BL order.

    Raises:
        ValueError: If not exactly 4 points are provided.
    """
    pts = np.array(points, dtype=np.float32)
    if pts.shape[0] != 4:
        raise ValueError(f"Expected 4 points, got {pts.shape[0]}")

    pts = pts.reshape(4, 2)

    s = pts.sum(axis=1)     # x + y
    d = np.diff(pts, axis=1).flatten()  # y - x

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(d)]
    bl = pts[np.argmax(d)]

    ordered = [
        (float(tl[0]), float(tl[1])),
        (float(tr[0]), float(tr[1])),
        (float(br[0]), float(br[1])),
        (float(bl[0]), float(bl[1])),
    ]
    return ordered


def correct_perspective(
    image: np.ndarray,
    roi: BilletROI,
    target_size: int = PERSPECTIVE_TARGET_SIZE,
    border_percent: float = PERSPECTIVE_BORDER_PERCENT,
) -> tuple[np.ndarray, dict]:
    """Warp a detected billet face to a fronto-parallel square view.

    Takes the ROI corners from a BilletROI, orders them, and applies a
    perspective transform to produce a square output image.

    Args:
        image: Source BGR or grayscale image.
        roi: Detected BilletROI with corner points.
        target_size: Output image will be (target_size x target_size).
        border_percent: Fraction of target_size to add as border padding.

    Returns:
        Tuple of (warped_image, info_dict) where info_dict contains:
            - ordered_corners: The source corners in TL,TR,BR,BL order.
            - transform_matrix: The 3x3 perspective transform matrix.
            - target_size: The output dimension used.
    """
    ordered = order_corners(roi.corners)
    warped, matrix = correct_perspective_from_points(
        image, ordered, target_size, border_percent
    )

    info = {
        "ordered_corners": ordered,
        "transform_matrix": matrix,
        "target_size": target_size,
    }
    return warped, info


def correct_perspective_from_points(
    image: np.ndarray,
    source_points: Union[list[tuple[float, float]], np.ndarray],
    target_size: int = PERSPECTIVE_TARGET_SIZE,
    border_percent: float = PERSPECTIVE_BORDER_PERCENT,
) -> tuple[np.ndarray, np.ndarray]:
    """Warp an image region defined by 4 source points to a square.

    Args:
        image: Source image (BGR or grayscale).
        source_points: 4 corner points in TL, TR, BR, BL order.
        target_size: Output image will be (target_size x target_size).
        border_percent: Fraction of target_size to add as border padding
            on each side (prevents clipping edge stamps).

    Returns:
        Tuple of (warped_image, transform_matrix):
            - warped_image: Square output image.
            - transform_matrix: The 3x3 perspective transform matrix.
    """
    src = np.array(source_points, dtype=np.float32).reshape(4, 2)

    border = int(target_size * border_percent)
    inner = target_size - 2 * border

    dst = np.array([
        [border, border],               # TL
        [border + inner, border],        # TR
        [border + inner, border + inner],  # BR
        [border, border + inner],        # BL
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(
        image, matrix, (target_size, target_size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    logger.debug(
        "correct_perspective: warped to {}x{} with {:.0f}% border",
        target_size,
        target_size,
        border_percent * 100,
    )
    return warped, matrix
