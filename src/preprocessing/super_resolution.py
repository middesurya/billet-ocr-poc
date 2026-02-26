"""Super-resolution upscaling for low-resolution billet crops.

Roboflow dataset images are 640x640 with ~9 billets per frame, making each
billet face only ~50-100px.  This is well below the effective resolution for
OCR models.  Super-resolution upscales these tiny crops to a readable size.

Strategy:
    1. Try OpenCV DNN super-resolution (ESPCN x4, ~50ms/image, best quality)
    2. Fall back to bicubic interpolation if dnn_superres unavailable

The ESPCN_x4 model is a pre-trained efficient sub-pixel convolutional network
that produces sharper upscaling than bicubic interpolation, especially for
text/edge features — exactly what we need for stamp characters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from loguru import logger

from src.config import (
    SUPERRES_MIN_SIZE,
    SUPERRES_MODEL_NAME,
    SUPERRES_MODEL_PATH,
    SUPERRES_SCALE,
    SUPERRES_TARGET_SIZE,
)

# ---------------------------------------------------------------------------
# Module-level singleton for the DNN super-resolution model
# ---------------------------------------------------------------------------

_sr_model: Optional[object] = None
_sr_available: Optional[bool] = None


def _check_dnn_superres_available() -> bool:
    """Check if cv2.dnn_superres module is available.

    Returns:
        True if the DNN super-resolution module can be imported.
    """
    global _sr_available
    if _sr_available is not None:
        return _sr_available
    try:
        _sr_available = hasattr(cv2, "dnn_superres")
        if not _sr_available:
            # Try the alternative import path
            from cv2 import dnn_superres  # noqa: F401
            _sr_available = True
    except ImportError:
        _sr_available = False
    return _sr_available


def _get_sr_model(
    model_path: Union[str, Path] = SUPERRES_MODEL_PATH,
    model_name: str = SUPERRES_MODEL_NAME,
    scale: int = SUPERRES_SCALE,
) -> Optional[object]:
    """Load the DNN super-resolution model (singleton).

    Args:
        model_path: Path to the .pb model file.
        model_name: Model algorithm name (e.g., 'espcn', 'edsr', 'fsrcnn').
        scale: Upscaling factor (2, 3, or 4).

    Returns:
        DnnSuperResImpl object, or None if unavailable.
    """
    global _sr_model

    if _sr_model is not None:
        return _sr_model

    if not _check_dnn_superres_available():
        logger.warning(
            "[SuperRes] cv2.dnn_superres not available — "
            "install opencv-contrib-python for DNN super-resolution"
        )
        return None

    model_file = Path(model_path)
    if not model_file.exists():
        logger.warning(
            f"[SuperRes] Model file not found: {model_file} — "
            f"falling back to bicubic interpolation. "
            f"Download from: https://github.com/Saafke/EDSR_Tensorflow/tree/master/models"
        )
        return None

    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(str(model_file))
        sr.setModel(model_name, scale)
        _sr_model = sr
        logger.info(
            f"[SuperRes] Loaded {model_name} x{scale} from {model_file}"
        )
        return _sr_model
    except Exception as exc:
        logger.error(f"[SuperRes] Failed to load model: {exc}")
        return None


def upscale_image(
    image: np.ndarray,
    target_size: int = SUPERRES_TARGET_SIZE,
    min_size: int = SUPERRES_MIN_SIZE,
    scale: int = SUPERRES_SCALE,
) -> np.ndarray:
    """Upscale a small image crop using super-resolution or bicubic fallback.

    Only upscales if the image is smaller than ``min_size`` on its shortest
    side.  When upscaling, the target is ``target_size`` pixels on the
    shortest side.

    Args:
        image: Input image (BGR or grayscale numpy array).
        target_size: Desired minimum dimension after upscaling.
        min_size: Only upscale images smaller than this on their shortest side.
        scale: DNN super-resolution scale factor.

    Returns:
        Upscaled image, or the original if already large enough.
    """
    h, w = image.shape[:2]
    short_side = min(h, w)

    if short_side >= min_size:
        logger.debug(
            f"[SuperRes] Image already large enough ({w}x{h}), skipping upscale"
        )
        return image

    # Calculate how much we need to upscale
    needed_scale = target_size / short_side

    # Try DNN super-resolution first
    sr_model = _get_sr_model()
    if sr_model is not None and needed_scale <= scale:
        try:
            upscaled = sr_model.upsample(image)
            logger.info(
                f"[SuperRes] DNN upscale {w}x{h} -> "
                f"{upscaled.shape[1]}x{upscaled.shape[0]} "
                f"(ESPCN x{scale})"
            )
            # If DNN upscaled too much, resize down to target
            up_h, up_w = upscaled.shape[:2]
            up_short = min(up_h, up_w)
            if up_short > target_size * 1.2:
                resize_factor = target_size / up_short
                new_w = int(up_w * resize_factor)
                new_h = int(up_h * resize_factor)
                upscaled = cv2.resize(
                    upscaled, (new_w, new_h), interpolation=cv2.INTER_AREA
                )
            return upscaled
        except Exception as exc:
            logger.warning(f"[SuperRes] DNN upscale failed: {exc}, using bicubic")

    # Fallback: bicubic interpolation
    resize_factor = target_size / short_side
    new_w = int(w * resize_factor)
    new_h = int(h * resize_factor)
    upscaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    logger.info(
        f"[SuperRes] Bicubic upscale {w}x{h} -> {new_w}x{new_h} "
        f"(factor={resize_factor:.1f}x)"
    )
    return upscaled


def upscale_to_target(
    image: np.ndarray,
    target_size: int = SUPERRES_TARGET_SIZE,
) -> np.ndarray:
    """Upscale iteratively until shortest side >= target_size.

    For very small crops (e.g., <100px), a single 4x DNN pass may not be
    enough. This function calls upscale_image repeatedly until the target
    is met, with a safety cap of 3 iterations.

    Args:
        image: Input image (BGR or grayscale numpy array).
        target_size: Desired minimum shortest-side dimension.

    Returns:
        Upscaled image meeting the target size, or the best achievable.
    """
    h, w = image.shape[:2]
    shortest = min(h, w)
    max_iterations = 3  # Safety cap: avoid runaway upscaling

    iteration = 0
    while shortest < target_size and iteration < max_iterations:
        image = upscale_image(image, target_size=target_size, min_size=shortest)
        h, w = image.shape[:2]
        new_shortest = min(h, w)
        if new_shortest <= shortest:
            # No progress — break to avoid infinite loop
            break
        shortest = new_shortest
        iteration += 1

    if iteration > 1:
        logger.info(
            f"[SuperRes] Iterative upscale: {iteration} passes, "
            f"final size {image.shape[1]}x{image.shape[0]}"
        )
    return image


def needs_upscale(image: np.ndarray, min_size: int = SUPERRES_MIN_SIZE) -> bool:
    """Check if an image needs super-resolution upscaling.

    Args:
        image: Input image array.
        min_size: Minimum acceptable shortest-side dimension.

    Returns:
        True if the image's shortest side is below ``min_size``.
    """
    h, w = image.shape[:2]
    return min(h, w) < min_size
