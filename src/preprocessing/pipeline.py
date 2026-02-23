"""Preprocessing pipeline for billet end-face OCR.

Transforms raw billet photos into high-contrast grayscale images suitable
for PaddleOCR inference. The pipeline order is deliberately:
    load -> bilateral filter -> CLAHE -> (optional unsharp mask)

Bilateral filter first smooths sensor noise without blurring stamp edges;
CLAHE then amplifies local contrast so dot-matrix characters become visible.
Adaptive thresholding is intentionally omitted -- it destroys gradient
information that the neural network detector relies on.

References:
    Wei & Zhou (Feb 2025) -- DBNet+SVTR on billet stamps, 91-94 % accuracy.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from loguru import logger

from src.config import (
    BILATERAL_D,
    BILATERAL_SIGMA_COLOR,
    BILATERAL_SIGMA_SPACE,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID,
    DEBUG_DIR,
    SUPPORTED_FORMATS,
    VLM_CROP_RATIO,
)


# ---------------------------------------------------------------------------
# 1. Image loading
# ---------------------------------------------------------------------------

def load_image(source: Union[str, Path, np.ndarray]) -> np.ndarray:
    """Load a billet image from a file path or pass through an existing array.

    The returned array is always in BGR format with dtype uint8, matching the
    OpenCV convention used throughout the rest of the pipeline.

    Args:
        source: A file-system path (str or Path) to a supported image file,
            or a numpy ndarray that has already been loaded by the caller.

    Returns:
        BGR image as a numpy ndarray with shape (H, W, 3) or (H, W) for
        grayscale inputs that were passed as arrays.

    Raises:
        FileNotFoundError: If *source* is a path that does not exist on disk.
        ValueError: If *source* is a path with an unsupported extension, the
            file cannot be decoded by OpenCV, or *source* is a numpy array
            with an unexpected number of dimensions.
        TypeError: If *source* is not a str, Path, or numpy ndarray.
    """
    if isinstance(source, np.ndarray):
        if source.ndim not in (2, 3):
            raise ValueError(
                f"numpy array must be 2-D (grayscale) or 3-D (BGR/BGRA), "
                f"got shape {source.shape}"
            )
        logger.debug("load_image: received numpy array with shape {}", source.shape)
        return source

    path = Path(source)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported: {SUPPORTED_FORMATS}"
        )

    # cv2.imread returns None on decode failure (corrupt file, wrong extension)
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"OpenCV could not decode image file: {path}")

    logger.debug(
        "load_image: loaded '{}' -> shape={} dtype={}",
        path.name,
        image.shape,
        image.dtype,
    )
    return image


# ---------------------------------------------------------------------------
# 2. Grayscale conversion
# ---------------------------------------------------------------------------

def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR image to grayscale.

    If the input is already a 2-D (single-channel) array it is returned
    unchanged, making this function safe to call idempotently.

    Args:
        image: BGR image with shape (H, W, 3) or (H, W, 4) (BGRA), or an
            already-grayscale image with shape (H, W).

    Returns:
        Single-channel grayscale image with shape (H, W) and dtype uint8.

    Raises:
        ValueError: If the image has an unexpected number of dimensions or
            an unsupported number of channels.
    """
    if image.ndim == 2:
        logger.debug("convert_to_grayscale: image already grayscale, skipping")
        return image

    if image.ndim == 3:
        channels = image.shape[2]
        if channels == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif channels == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            raise ValueError(
                f"Expected 1, 3, or 4 channels, got {channels}"
            )
        logger.debug(
            "convert_to_grayscale: {} -> shape={}", image.shape, gray.shape
        )
        return gray

    raise ValueError(
        f"Image must be 2-D or 3-D, got {image.ndim}-D array with shape {image.shape}"
    )


# ---------------------------------------------------------------------------
# 3. CLAHE contrast enhancement
# ---------------------------------------------------------------------------

def apply_clahe(
    image: np.ndarray,
    clip_limit: float = CLAHE_CLIP_LIMIT,
    tile_grid_size: tuple[int, int] = CLAHE_TILE_GRID,
) -> np.ndarray:
    """Apply Contrast Limited Adaptive Histogram Equalization (CLAHE).

    For colour (BGR) inputs the function converts to LAB colour space,
    applies CLAHE exclusively to the L (luminance) channel, then converts
    back to BGR.  This preserves hue and saturation while dramatically
    improving local contrast -- critical for revealing faint dot-matrix
    stamps on oxidized steel.

    For grayscale inputs CLAHE is applied directly to the single channel.

    Args:
        image: BGR image with shape (H, W, 3) or grayscale with shape (H, W).
        clip_limit: Threshold for contrast limiting.  Higher values give
            stronger enhancement at the cost of amplifying noise.
            Defaults to ``CLAHE_CLIP_LIMIT`` from config.
        tile_grid_size: Size of the grid of contextual regions.  Smaller
            tiles yield finer local adaptation.
            Defaults to ``CLAHE_TILE_GRID`` from config.

    Returns:
        Contrast-enhanced image in the same colour format as the input
        (BGR for 3-channel input, grayscale for 2-D input).

    Raises:
        ValueError: If *image* has an unsupported shape.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    if image.ndim == 2:
        # Grayscale path -- apply directly
        enhanced = clahe.apply(image)
        logger.debug(
            "apply_clahe: grayscale input clip_limit={} tile_grid={}",
            clip_limit,
            tile_grid_size,
        )
        return enhanced

    if image.ndim == 3 and image.shape[2] == 3:
        # Colour path: BGR -> LAB, enhance L, LAB -> BGR
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_enhanced = clahe.apply(l_channel)
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        bgr_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        logger.debug(
            "apply_clahe: BGR->LAB->CLAHE(L)->BGR clip_limit={} tile_grid={}",
            clip_limit,
            tile_grid_size,
        )
        return bgr_enhanced

    raise ValueError(
        f"apply_clahe expects a 2-D grayscale or 3-channel BGR image, "
        f"got shape {image.shape}"
    )


# ---------------------------------------------------------------------------
# 4. Bilateral filter (edge-preserving noise smoothing)
# ---------------------------------------------------------------------------

def apply_bilateral_filter(
    image: np.ndarray,
    d: int = BILATERAL_D,
    sigma_color: float = BILATERAL_SIGMA_COLOR,
    sigma_space: float = BILATERAL_SIGMA_SPACE,
) -> np.ndarray:
    """Apply a bilateral filter to smooth noise while preserving stamp edges.

    The bilateral filter is preferred over Gaussian blur because it averages
    only pixels with similar intensity, leaving the sharp boundaries of
    dot-matrix characters intact.

    Args:
        image: BGR or grayscale image as a numpy ndarray.
        d: Diameter of the pixel neighbourhood used during filtering.
            Defaults to ``BILATERAL_D`` from config.
        sigma_color: Filter sigma in colour space.  A larger value means
            farther colours within the neighbourhood will be mixed together.
            Defaults to ``BILATERAL_SIGMA_COLOR`` from config.
        sigma_space: Filter sigma in coordinate space.  A larger value means
            farther pixels will influence each other.
            Defaults to ``BILATERAL_SIGMA_SPACE`` from config.

    Returns:
        Filtered image with the same shape and dtype as the input.
    """
    filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    logger.debug(
        "apply_bilateral_filter: d={} sigma_color={} sigma_space={}",
        d,
        sigma_color,
        sigma_space,
    )
    return filtered


# ---------------------------------------------------------------------------
# 5. Unsharp mask (optional edge sharpening)
# ---------------------------------------------------------------------------

def apply_unsharp_mask(
    image: np.ndarray,
    kernel_size: tuple[int, int] = (5, 5),
    sigma: float = 1.0,
    amount: float = 1.5,
    threshold: int = 0,
) -> np.ndarray:
    """Sharpen faint stamp edges using an unsharp mask.

    Computes a blurred version of the image, then adds a scaled difference
    back to the original:  ``output = original + amount * (original - blurred)``
    Pixels whose difference falls below *threshold* are left unchanged to
    avoid amplifying flat noise regions.

    This step is optional and disabled by default in the main pipeline.  It
    can help when stamps are particularly faint but risks amplifying scale
    texture noise on heavily oxidized billets.

    Args:
        image: BGR or grayscale image as a numpy ndarray.
        kernel_size: Gaussian blur kernel dimensions (must be odd).
        sigma: Standard deviation for the Gaussian kernel.
        amount: Sharpening strength multiplier.  Values in [1.0, 2.0] are
            typical; higher values may over-sharpen.
        threshold: Minimum pixel-level difference required to apply
            sharpening.  0 means sharpen everywhere.

    Returns:
        Sharpened image with the same shape and dtype as the input.
    """
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)

    # float32 arithmetic avoids uint8 overflow/underflow during subtraction
    image_f = image.astype(np.float32)
    blurred_f = blurred.astype(np.float32)

    sharpened_f = image_f + amount * (image_f - blurred_f)

    if threshold > 0:
        # Only apply sharpening where the detail signal exceeds the threshold
        low_contrast_mask = np.abs(image_f - blurred_f) < threshold
        sharpened_f[low_contrast_mask] = image_f[low_contrast_mask]

    sharpened = np.clip(sharpened_f, 0, 255).astype(np.uint8)
    logger.debug(
        "apply_unsharp_mask: kernel={} sigma={} amount={} threshold={}",
        kernel_size,
        sigma,
        amount,
        threshold,
    )
    return sharpened


# ---------------------------------------------------------------------------
# 6. Center crop for VLM
# ---------------------------------------------------------------------------


def center_crop_for_vlm(
    image: np.ndarray,
    crop_ratio: float = VLM_CROP_RATIO,
) -> np.ndarray:
    """Crop the center portion of an image for VLM focus.

    Extracts the central region of the image so the VLM receives a
    zoomed-in view of the billet end face.  Stamps are typically centered
    in the photograph, so discarding the peripheral background helps the
    model focus on the characters.

    Args:
        image: BGR or grayscale image as a numpy ndarray.
        crop_ratio: Fraction of each dimension to keep.  0.6 keeps the
            central 60% of width and height.  Must be in (0.0, 1.0].

    Returns:
        Cropped image as a numpy ndarray.  The spatial dimensions are
        scaled by *crop_ratio* relative to the input.

    Raises:
        ValueError: If *crop_ratio* is not in (0.0, 1.0].
    """
    if not (0.0 < crop_ratio <= 1.0):
        raise ValueError(f"crop_ratio must be in (0.0, 1.0], got {crop_ratio}")

    if crop_ratio == 1.0:
        return image

    h, w = image.shape[:2]
    new_h = int(h * crop_ratio)
    new_w = int(w * crop_ratio)

    y_start = (h - new_h) // 2
    x_start = (w - new_w) // 2

    cropped = image[y_start : y_start + new_h, x_start : x_start + new_w]
    logger.debug(
        "center_crop_for_vlm: ({}, {}) -> ({}, {}) ratio={}",
        h, w, new_h, new_w, crop_ratio,
    )
    return cropped


# ---------------------------------------------------------------------------
# 7. Full pipeline (renumbered from 6 after center-crop addition)
# ---------------------------------------------------------------------------

def preprocess_billet_image(
    source: Union[str, Path, np.ndarray],
    apply_sharpening: bool = False,
    detect_roi: bool = False,
    correct_perspective: bool = False,
) -> tuple[np.ndarray, dict[str, float]]:
    """Run the full preprocessing pipeline on a billet image.

    Pipeline order (deliberate):
        1. Load image
        2. ROI detection + crop    (optional, ``detect_roi=True``)
        3. Perspective correction  (optional, ``correct_perspective=True``)
        4. Bilateral filter  -- smooth sensor/JPEG noise, preserve edges
        5. CLAHE             -- enhance local contrast via LAB L-channel
        6. Unsharp mask      -- optional final edge sharpening

    Adaptive thresholding is intentionally excluded: the neural-network OCR
    model needs gradient information that thresholding destroys.

    Args:
        source: File path (str or Path) or numpy ndarray (BGR).
        apply_sharpening: When True, applies ``apply_unsharp_mask`` after
            CLAHE.  Defaults to False.
        detect_roi: When True, runs ROI detection to isolate the billet end
            face before filtering.  Defaults to False.
        correct_perspective: When True, warps the detected ROI to a
            fronto-parallel square.  Requires ``detect_roi=True`` to have
            any effect.  Defaults to False.

    Returns:
        A two-tuple ``(processed_image, timing_dict)`` where:

        - ``processed_image`` is a BGR numpy ndarray ready for OCR inference.
        - ``timing_dict`` has keys ``load_ms``, ``bilateral_ms``,
          ``clahe_ms``, ``sharpen_ms``, and ``total_ms``, each holding the
          elapsed wall-clock time in milliseconds for that stage.  When
          ROI/perspective stages are enabled, ``roi_ms`` and
          ``perspective_ms`` are also included.

    Raises:
        FileNotFoundError: Propagated from ``load_image`` when the path does
            not exist.
        ValueError: Propagated from sub-functions on bad inputs.
    """
    pipeline_start = time.perf_counter()
    timing: dict[str, float] = {}

    # -- Stage 1: Load -------------------------------------------------------
    t0 = time.perf_counter()
    image = load_image(source)
    timing["load_ms"] = (time.perf_counter() - t0) * 1000

    source_label = (
        Path(source).name if isinstance(source, (str, Path)) else f"array{image.shape}"
    )
    logger.info("preprocess_billet_image: starting pipeline for '{}'", source_label)

    # -- Stage 2: ROI detection + crop (optional) ----------------------------
    roi_result = None
    if detect_roi:
        from src.preprocessing.roi_detector import detect_best_billet_face, crop_to_roi

        t0 = time.perf_counter()
        roi_result = detect_best_billet_face(image)
        if roi_result is not None:
            logger.info(
                "preprocess_billet_image: ROI detected with confidence {:.2f}",
                roi_result.confidence,
            )
            if not correct_perspective:
                image = crop_to_roi(image, roi_result)
        else:
            logger.warning("preprocess_billet_image: no ROI detected, using full image")
        timing["roi_ms"] = (time.perf_counter() - t0) * 1000
    else:
        timing["roi_ms"] = 0.0

    # -- Stage 3: Perspective correction (optional) --------------------------
    if correct_perspective and roi_result is not None:
        from src.preprocessing.perspective import correct_perspective as do_perspective

        t0 = time.perf_counter()
        image, _persp_info = do_perspective(image, roi_result)
        timing["perspective_ms"] = (time.perf_counter() - t0) * 1000
        logger.debug("preprocess_billet_image: perspective corrected")
    else:
        timing["perspective_ms"] = 0.0

    # -- Stage 4: Bilateral filter -------------------------------------------
    t0 = time.perf_counter()
    image = apply_bilateral_filter(image)
    timing["bilateral_ms"] = (time.perf_counter() - t0) * 1000

    # -- Stage 5: CLAHE ------------------------------------------------------
    t0 = time.perf_counter()
    image = apply_clahe(image)
    timing["clahe_ms"] = (time.perf_counter() - t0) * 1000

    # -- Stage 6: Optional unsharp mask --------------------------------------
    t0 = time.perf_counter()
    if apply_sharpening:
        image = apply_unsharp_mask(image)
        logger.debug("preprocess_billet_image: unsharp mask applied")
    timing["sharpen_ms"] = (time.perf_counter() - t0) * 1000

    timing["total_ms"] = (time.perf_counter() - pipeline_start) * 1000

    logger.info(
        "preprocess_billet_image: done '{}' | "
        "load={:.1f}ms roi={:.1f}ms perspective={:.1f}ms "
        "bilateral={:.1f}ms clahe={:.1f}ms "
        "sharpen={:.1f}ms total={:.1f}ms",
        source_label,
        timing["load_ms"],
        timing["roi_ms"],
        timing["perspective_ms"],
        timing["bilateral_ms"],
        timing["clahe_ms"],
        timing["sharpen_ms"],
        timing["total_ms"],
    )

    return image, timing


# ---------------------------------------------------------------------------
# 8. Debug image saver
# ---------------------------------------------------------------------------

def save_debug_image(
    image: np.ndarray,
    name: str,
    output_dir: Path = DEBUG_DIR,
) -> Path:
    """Save an intermediate pipeline image for visual inspection.

    The file is written to *output_dir* with a ``.png`` extension.  The
    directory is created if it does not already exist.  Existing files with
    the same name are overwritten without warning.

    Args:
        image: Image array to save (any OpenCV-compatible format).
        name: Base file name without extension (e.g. ``"clahe_output"``).
            Characters that are invalid on the host filesystem should be
            avoided.
        output_dir: Directory to write the file into.  Defaults to
            ``DEBUG_DIR`` from config (``data/debug/``).

    Returns:
        Absolute Path to the written file.

    Raises:
        OSError: If the directory cannot be created or the file cannot be
            written.
        ValueError: If OpenCV fails to encode the image.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"{name}.png"
    success = cv2.imwrite(str(out_path), image)
    if not success:
        raise ValueError(
            f"cv2.imwrite failed for '{out_path}'. "
            "Check that the image array is valid and the path is writable."
        )

    logger.debug("save_debug_image: wrote '{}'", out_path)
    return out_path.resolve()
