"""Unit tests for the billet image preprocessing pipeline.

Covers image loading, CLAHE contrast enhancement, bilateral filtering,
and the full preprocessing pipeline including timing metadata.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

# Ensure the project root is on the path when run directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.pipeline import (
    apply_bilateral_filter,
    apply_clahe,
    center_crop_for_vlm,
    convert_to_grayscale,
    load_image,
    preprocess_billet_image,
    save_debug_image,
)


# ---------------------------------------------------------------------------
# TestLoadImage
# ---------------------------------------------------------------------------


class TestLoadImage:
    """Tests for load_image() – file path and numpy array input modes."""

    def test_valid_path_returns_ndarray(self, sample_image_path: Path) -> None:
        """Load a known JPEG by path and confirm we get a uint8 BGR array.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        img = load_image(sample_image_path)
        assert isinstance(img, np.ndarray)
        assert img.dtype == np.uint8
        assert img.ndim == 3
        assert img.shape[2] == 3  # BGR

    def test_string_path_works(self, sample_image_path: Path) -> None:
        """Accept a plain string path in addition to a Path object.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        img = load_image(str(sample_image_path))
        assert isinstance(img, np.ndarray)
        assert img.ndim == 3

    def test_numpy_array_passthrough(self, sample_image_array: np.ndarray) -> None:
        """Numpy arrays are returned unchanged (identity, not a copy).

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        result = load_image(sample_image_array)
        assert result is sample_image_array

    def test_grayscale_array_passthrough(self) -> None:
        """A 2-D (grayscale) numpy array is accepted without modification."""
        gray = np.zeros((100, 100), dtype=np.uint8)
        result = load_image(gray)
        assert result is gray

    def test_file_not_found_raises(self) -> None:
        """Missing file path must raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_image("/nonexistent/path/image.jpg")

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        """A supported-extension file with an unsupported suffix must raise ValueError."""
        bad_file = tmp_path / "test.tiff"
        bad_file.write_bytes(b"fake data")
        with pytest.raises(ValueError, match="Unsupported image format"):
            load_image(bad_file)

    def test_4d_array_raises(self) -> None:
        """A 4-D numpy array must raise ValueError (unsupported dimensionality)."""
        bad = np.zeros((2, 100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            load_image(bad)


# ---------------------------------------------------------------------------
# TestApplyCLAHE
# ---------------------------------------------------------------------------


class TestApplyCLAHE:
    """Tests for apply_clahe() – grayscale and BGR code paths."""

    def test_output_shape_matches_grayscale_input(self) -> None:
        """CLAHE on a grayscale image must preserve shape (H, W).

        A uniform image should still pass through without error.
        """
        gray = np.full((80, 120), 128, dtype=np.uint8)
        out = apply_clahe(gray)
        assert out.shape == gray.shape
        assert out.dtype == np.uint8

    def test_output_shape_matches_bgr_input(self, sample_image_array: np.ndarray) -> None:
        """CLAHE on a BGR image must preserve shape (H, W, 3).

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        out = apply_clahe(sample_image_array)
        assert out.shape == sample_image_array.shape
        assert out.dtype == np.uint8

    def test_contrast_enhanced_higher_std_dev(self) -> None:
        """CLAHE should increase pixel value spread (standard deviation).

        A low-contrast synthetic image (values 100-120) should have a higher
        standard deviation after CLAHE than before.
        """
        rng = np.random.default_rng(seed=42)
        low_contrast = rng.integers(100, 120, size=(200, 200), dtype=np.uint8)
        enhanced = apply_clahe(low_contrast)
        assert enhanced.std() > low_contrast.std()

    def test_grayscale_input_handled(self) -> None:
        """Pass a grayscale (2-D) array through the CLAHE function without error."""
        rng = np.random.default_rng(seed=0)
        gray = rng.integers(0, 256, size=(100, 150), dtype=np.uint8)
        out = apply_clahe(gray)
        assert out.ndim == 2
        assert out.shape == gray.shape

    def test_custom_clip_limit(self) -> None:
        """CLAHE with a different clip_limit must still return same-shape output."""
        rng = np.random.default_rng(seed=7)
        img = rng.integers(0, 256, size=(60, 80), dtype=np.uint8)
        out = apply_clahe(img, clip_limit=6.0, tile_grid_size=(4, 4))
        assert out.shape == img.shape

    def test_invalid_shape_raises(self) -> None:
        """A 4-channel image (BGRA) should raise ValueError (unsupported path)."""
        bgra = np.zeros((50, 50, 4), dtype=np.uint8)
        with pytest.raises(ValueError):
            apply_clahe(bgra)


# ---------------------------------------------------------------------------
# TestApplyBilateralFilter
# ---------------------------------------------------------------------------


class TestApplyBilateralFilter:
    """Tests for apply_bilateral_filter() – output shape and noise reduction."""

    def test_output_shape_matches_input(self, sample_image_array: np.ndarray) -> None:
        """Bilateral filter output shape must be identical to input shape.

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        out = apply_bilateral_filter(sample_image_array)
        assert out.shape == sample_image_array.shape
        assert out.dtype == np.uint8

    def test_grayscale_shape_preserved(self) -> None:
        """Bilateral filter on a grayscale (2-D) image preserves shape."""
        rng = np.random.default_rng(seed=1)
        gray = rng.integers(0, 256, size=(120, 160), dtype=np.uint8)
        out = apply_bilateral_filter(gray)
        assert out.shape == gray.shape

    def test_noise_reduced(self) -> None:
        """After bilateral filtering, pixel variance should decrease on a noisy image.

        We construct a nearly-uniform image and add strong salt-and-pepper noise.
        The bilateral filter should reduce variance while keeping the gradient
        at sharp edge transitions.
        """
        rng = np.random.default_rng(seed=99)
        base = np.full((150, 150), 128, dtype=np.uint8)
        noise = rng.integers(-60, 60, size=base.shape, dtype=np.int16)
        noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        filtered = apply_bilateral_filter(noisy)
        # Variance should be smaller after smoothing noisy flat regions.
        assert float(filtered.var()) < float(noisy.var())


# ---------------------------------------------------------------------------
# TestPreprocessPipeline
# ---------------------------------------------------------------------------


class TestPreprocessPipeline:
    """Tests for preprocess_billet_image() – the end-to-end pipeline function."""

    def test_returns_tuple(self, sample_image_path: Path) -> None:
        """preprocess_billet_image must return a 2-tuple (ndarray, dict).

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        result = preprocess_billet_image(sample_image_path)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_first_element_is_ndarray(self, sample_image_path: Path) -> None:
        """First element of the return tuple must be a numpy ndarray.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        img, _ = preprocess_billet_image(sample_image_path)
        assert isinstance(img, np.ndarray)

    def test_timing_dict_has_required_keys(self, sample_image_path: Path) -> None:
        """Timing dict must contain load_ms, bilateral_ms, clahe_ms, sharpen_ms, total_ms.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        _, timing = preprocess_billet_image(sample_image_path)
        required_keys = {"load_ms", "bilateral_ms", "clahe_ms", "sharpen_ms", "total_ms"}
        assert required_keys.issubset(timing.keys())

    def test_timing_values_are_non_negative(self, sample_image_path: Path) -> None:
        """All timing values must be >= 0.0 milliseconds.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        _, timing = preprocess_billet_image(sample_image_path)
        for key, value in timing.items():
            assert value >= 0.0, f"Negative timing for key '{key}': {value}"

    def test_total_ms_is_consistent(self, sample_image_path: Path) -> None:
        """total_ms should be at least the sum of the sub-stage timings.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        _, timing = preprocess_billet_image(sample_image_path)
        component_sum = (
            timing["load_ms"]
            + timing["bilateral_ms"]
            + timing["clahe_ms"]
            + timing["sharpen_ms"]
        )
        # Allow a small tolerance for perf_counter drift.
        assert timing["total_ms"] >= component_sum - 5.0

    def test_output_shape_matches_input(self, sample_image_array: np.ndarray) -> None:
        """Processed image shape must match the input array shape.

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        img, _ = preprocess_billet_image(sample_image_array)
        assert img.shape == sample_image_array.shape

    def test_works_on_numpy_array(self, sample_image_array: np.ndarray) -> None:
        """Pipeline should accept a numpy array directly, not just a file path.

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        img, timing = preprocess_billet_image(sample_image_array)
        assert isinstance(img, np.ndarray)
        assert "total_ms" in timing

    @pytest.mark.slow
    def test_works_on_all_raw_images(self, all_raw_image_paths: list) -> None:
        """Pipeline must process all 10 raw billet images without error.

        Args:
            all_raw_image_paths: Pytest fixture providing paths to all raw images.
        """
        if not all_raw_image_paths:
            pytest.skip("No raw images found in data/raw/")
        for path in all_raw_image_paths:
            img, timing = preprocess_billet_image(path)
            assert isinstance(img, np.ndarray), f"Failed for {path.name}"
            assert "total_ms" in timing, f"Missing timing for {path.name}"

    def test_debug_image_saved(self, sample_image_array: np.ndarray) -> None:
        """save_debug_image must write a PNG file to the data/debug directory.

        Uses the project's own debug directory (data/debug/) instead of
        pytest tmp_path to avoid Windows OneDrive symlink issues with the
        pytest temp directory cleanup.

        Args:
            sample_image_array: Pytest fixture providing a pre-loaded BGR array.
        """
        import tempfile
        import os

        from src.config import DEBUG_DIR

        out = save_debug_image(sample_image_array, "test_debug_unit", output_dir=DEBUG_DIR)
        assert out.exists()
        assert out.suffix == ".png"
        # Verify the saved file is a valid image.
        reloaded = cv2.imread(str(out))
        assert reloaded is not None
        # Clean up the test artifact.
        try:
            out.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# TestCenterCropForVLM
# ---------------------------------------------------------------------------


class TestCenterCropForVLM:
    """Tests for center_crop_for_vlm() — VLM-targeted center cropping."""

    def test_default_crop_ratio(self) -> None:
        """Default crop ratio (0.6) should produce 60% of original dimensions."""
        img = np.zeros((1000, 2000, 3), dtype=np.uint8)
        cropped = center_crop_for_vlm(img)
        assert cropped.shape[0] == 600  # 1000 * 0.6
        assert cropped.shape[1] == 1200  # 2000 * 0.6
        assert cropped.shape[2] == 3

    def test_custom_crop_ratio(self) -> None:
        """A custom crop ratio should scale dimensions accordingly."""
        img = np.zeros((500, 800, 3), dtype=np.uint8)
        cropped = center_crop_for_vlm(img, crop_ratio=0.5)
        assert cropped.shape[0] == 250
        assert cropped.shape[1] == 400

    def test_crop_ratio_one_returns_original(self) -> None:
        """Crop ratio 1.0 should return the original image unchanged."""
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        result = center_crop_for_vlm(img, crop_ratio=1.0)
        assert result is img  # Should be the same object

    def test_grayscale_input(self) -> None:
        """Should work with grayscale (2-D) images too."""
        img = np.zeros((400, 600), dtype=np.uint8)
        cropped = center_crop_for_vlm(img, crop_ratio=0.5)
        assert cropped.shape == (200, 300)

    def test_crop_is_centered(self) -> None:
        """The crop should extract from the center of the image."""
        # Create a 100x100 image with a unique value at center.
        img = np.zeros((100, 100), dtype=np.uint8)
        img[45:55, 45:55] = 255  # White square at center

        cropped = center_crop_for_vlm(img, crop_ratio=0.5)
        # The cropped image is 50x50, starting at (25, 25).
        # The white square was at (45:55, 45:55) in original.
        # In cropped coords: (45-25):(55-25) = (20:30, 20:30)
        assert cropped[20:30, 20:30].mean() == 255.0

    def test_invalid_crop_ratio_zero_raises(self) -> None:
        """Crop ratio 0.0 should raise ValueError."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="crop_ratio"):
            center_crop_for_vlm(img, crop_ratio=0.0)

    def test_invalid_crop_ratio_negative_raises(self) -> None:
        """Negative crop ratio should raise ValueError."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="crop_ratio"):
            center_crop_for_vlm(img, crop_ratio=-0.5)

    def test_invalid_crop_ratio_above_one_raises(self) -> None:
        """Crop ratio > 1.0 should raise ValueError."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="crop_ratio"):
            center_crop_for_vlm(img, crop_ratio=1.5)
