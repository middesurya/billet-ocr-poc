"""Unit tests for the ROI (Region of Interest) detector module.

Tests cover synthetic images (white squares on black backgrounds),
edge cases (blank images, tiny images), cropping, and visualization.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.roi_detector import (
    detect_billet_faces,
    detect_best_billet_face,
    crop_to_roi,
    visualize_roi,
)
from src.models import BilletROI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def white_square_on_black() -> np.ndarray:
    """Create a 500x500 image with a white 200x200 square centered."""
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.rectangle(img, (150, 150), (350, 350), (255, 255, 255), -1)
    return img


@pytest.fixture
def multi_square_image() -> np.ndarray:
    """Create an image with 3 white squares of different sizes."""
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    # Large square (200x200)
    cv2.rectangle(img, (50, 50), (250, 250), (255, 255, 255), -1)
    # Medium square (120x120)
    cv2.rectangle(img, (400, 100), (520, 220), (255, 255, 255), -1)
    # Small square (60x60)
    cv2.rectangle(img, (600, 400), (660, 460), (255, 255, 255), -1)
    return img


@pytest.fixture
def blank_image() -> np.ndarray:
    """Create a uniform gray image with no edges."""
    return np.full((400, 400, 3), 128, dtype=np.uint8)


# ---------------------------------------------------------------------------
# TestDetectBilletFaces
# ---------------------------------------------------------------------------


class TestDetectBilletFaces:
    """Tests for the main detect_billet_faces function."""

    def test_detects_white_square(self, white_square_on_black: np.ndarray) -> None:
        """A clear white square on black background should be detected."""
        rois = detect_billet_faces(white_square_on_black)
        assert len(rois) >= 1
        assert isinstance(rois[0], BilletROI)
        assert rois[0].confidence > 0.0

    def test_returns_list_of_billet_roi(self, white_square_on_black: np.ndarray) -> None:
        """Return type must be a list of BilletROI objects."""
        rois = detect_billet_faces(white_square_on_black)
        for roi in rois:
            assert isinstance(roi, BilletROI)
            assert len(roi.corners) == 4
            assert roi.area > 0

    def test_blank_image_returns_center_crop(self, blank_image: np.ndarray) -> None:
        """A blank image with no edges should fall back to center crop."""
        rois = detect_billet_faces(blank_image)
        assert len(rois) >= 1
        # Center crop fallback has low confidence
        assert rois[0].confidence <= 0.3

    def test_max_faces_limit(self, multi_square_image: np.ndarray) -> None:
        """max_faces parameter should limit the number of results."""
        rois = detect_billet_faces(multi_square_image, max_faces=1)
        assert len(rois) <= 1

    def test_sorted_by_confidence(self, multi_square_image: np.ndarray) -> None:
        """Returned ROIs should be sorted by confidence, descending."""
        rois = detect_billet_faces(multi_square_image, max_faces=5)
        if len(rois) > 1:
            for i in range(len(rois) - 1):
                assert rois[i].confidence >= rois[i + 1].confidence

    def test_bounding_rect_within_image(
        self, white_square_on_black: np.ndarray
    ) -> None:
        """Bounding rect should be within image dimensions."""
        h, w = white_square_on_black.shape[:2]
        rois = detect_billet_faces(white_square_on_black)
        for roi in rois:
            x, y, rw, rh = roi.bounding_rect
            assert x >= 0
            assert y >= 0
            assert x + rw <= w
            assert y + rh <= h

    def test_grayscale_input(self) -> None:
        """Should handle grayscale (2-D) input images."""
        img = np.zeros((500, 500), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (300, 300), 255, -1)
        rois = detect_billet_faces(img)
        assert len(rois) >= 1

    def test_does_not_crash_on_tiny_image(self) -> None:
        """Should not crash on very small images."""
        tiny = np.zeros((10, 10, 3), dtype=np.uint8)
        rois = detect_billet_faces(tiny)
        assert isinstance(rois, list)


# ---------------------------------------------------------------------------
# TestDetectBestBilletFace
# ---------------------------------------------------------------------------


class TestDetectBestBilletFace:
    """Tests for the convenience detect_best_billet_face function."""

    def test_returns_single_roi(self, white_square_on_black: np.ndarray) -> None:
        """Should return a single BilletROI (not a list)."""
        roi = detect_best_billet_face(white_square_on_black)
        assert isinstance(roi, BilletROI)

    def test_highest_confidence(self, multi_square_image: np.ndarray) -> None:
        """Should return the same ROI as the first in detect_billet_faces."""
        all_rois = detect_billet_faces(multi_square_image)
        best = detect_best_billet_face(multi_square_image)
        if all_rois and best:
            assert best.confidence == all_rois[0].confidence


# ---------------------------------------------------------------------------
# TestCropToROI
# ---------------------------------------------------------------------------


class TestCropToROI:
    """Tests for the crop_to_roi function."""

    def test_crop_produces_smaller_image(
        self, white_square_on_black: np.ndarray
    ) -> None:
        """Cropped image should be smaller than the original."""
        roi = detect_best_billet_face(white_square_on_black)
        assert roi is not None
        cropped = crop_to_roi(white_square_on_black, roi)
        assert cropped.shape[0] < white_square_on_black.shape[0]
        assert cropped.shape[1] < white_square_on_black.shape[1]

    def test_crop_not_empty(self, white_square_on_black: np.ndarray) -> None:
        """Cropped image should have non-zero dimensions."""
        roi = detect_best_billet_face(white_square_on_black)
        assert roi is not None
        cropped = crop_to_roi(white_square_on_black, roi)
        assert cropped.shape[0] > 0
        assert cropped.shape[1] > 0

    def test_crop_with_padding(self, white_square_on_black: np.ndarray) -> None:
        """Larger padding should produce a larger crop."""
        roi = detect_best_billet_face(white_square_on_black)
        assert roi is not None
        small_pad = crop_to_roi(white_square_on_black, roi, padding_percent=0.0)
        large_pad = crop_to_roi(white_square_on_black, roi, padding_percent=0.2)
        assert large_pad.shape[0] >= small_pad.shape[0]
        assert large_pad.shape[1] >= small_pad.shape[1]

    def test_crop_clips_to_image_bounds(self) -> None:
        """Crop should not exceed image boundaries even with large padding."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        roi = BilletROI(
            corners=[(0, 0), (99, 0), (99, 99), (0, 99)],
            bounding_rect=(0, 0, 100, 100),
            area=10000.0,
            confidence=0.5,
        )
        cropped = crop_to_roi(img, roi, padding_percent=0.5)
        assert cropped.shape[0] <= img.shape[0]
        assert cropped.shape[1] <= img.shape[1]


# ---------------------------------------------------------------------------
# TestVisualizeROI
# ---------------------------------------------------------------------------


class TestVisualizeROI:
    """Tests for the visualize_roi function."""

    def test_returns_annotated_image(
        self, white_square_on_black: np.ndarray
    ) -> None:
        """Should return a BGR image with same dimensions as input."""
        rois = detect_billet_faces(white_square_on_black)
        vis = visualize_roi(white_square_on_black, rois)
        assert vis.shape == white_square_on_black.shape
        # Should be different from original (has drawings)
        assert not np.array_equal(vis, white_square_on_black)

    def test_does_not_modify_original(
        self, white_square_on_black: np.ndarray
    ) -> None:
        """Should not modify the original image (works on a copy)."""
        original = white_square_on_black.copy()
        rois = detect_billet_faces(white_square_on_black)
        visualize_roi(white_square_on_black, rois)
        assert np.array_equal(white_square_on_black, original)

    def test_empty_rois(self, white_square_on_black: np.ndarray) -> None:
        """Should handle empty ROI list without crashing."""
        vis = visualize_roi(white_square_on_black, [])
        assert vis.shape == white_square_on_black.shape

    def test_save_to_file(self, white_square_on_black: np.ndarray) -> None:
        """Should save annotated image to file when output_path is given."""
        from src.config import DEBUG_DIR

        rois = detect_billet_faces(white_square_on_black)
        out_path = DEBUG_DIR / "test_roi_vis.png"
        vis = visualize_roi(white_square_on_black, rois, output_path=out_path)
        assert out_path.exists()
        assert vis.shape == white_square_on_black.shape
        try:
            out_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Slow tests (require real images)
# ---------------------------------------------------------------------------


class TestROIOnRealImages:
    """Integration tests on real billet images (marked slow)."""

    @pytest.mark.slow
    def test_detects_faces_in_all_raw_images(
        self, all_raw_image_paths: list[Path]
    ) -> None:
        """ROI detection should return at least 1 face per real image."""
        if not all_raw_image_paths:
            pytest.skip("No raw images found in data/raw/")
        for path in all_raw_image_paths:
            rois = detect_billet_faces(str(path))
            assert len(rois) >= 1, f"No ROI detected for {path.name}"
            assert rois[0].confidence > 0.0, f"Zero confidence for {path.name}"
