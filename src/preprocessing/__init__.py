"""Public API for the billet image preprocessing package."""

from src.preprocessing.pipeline import (
    load_image,
    apply_clahe,
    apply_bilateral_filter,
    preprocess_billet_image,
    save_debug_image,
)
from src.preprocessing.roi_detector import (
    detect_billet_faces,
    detect_best_billet_face,
    crop_to_roi,
    visualize_roi,
)
from src.preprocessing.perspective import (
    order_corners,
    correct_perspective,
    correct_perspective_from_points,
)
from src.preprocessing.super_resolution import (
    needs_upscale,
    upscale_image,
)

__all__ = [
    "load_image",
    "apply_clahe",
    "apply_bilateral_filter",
    "preprocess_billet_image",
    "save_debug_image",
    "detect_billet_faces",
    "detect_best_billet_face",
    "crop_to_roi",
    "visualize_roi",
    "order_corners",
    "correct_perspective",
    "correct_perspective_from_points",
    "needs_upscale",
    "upscale_image",
]
