"""Unit tests for the perspective correction module.

Tests cover corner ordering, perspective warping on synthetic trapezoids,
and integration with the ROI detector.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.perspective import (
    order_corners,
    correct_perspective,
    correct_perspective_from_points,
)
from src.preprocessing.roi_detector import detect_best_billet_face
from src.models import BilletROI


# ---------------------------------------------------------------------------
# TestOrderCorners
# ---------------------------------------------------------------------------


class TestOrderCorners:
    """Tests for the corner ordering function."""

    def test_standard_rectangle(self) -> None:
        """Corners of a standard axis-aligned rectangle should be ordered correctly."""
        # Deliberately shuffled order
        points = [(300, 100), (100, 100), (100, 300), (300, 300)]
        ordered = order_corners(points)
        # Expected: TL, TR, BR, BL
        assert ordered[0] == (100.0, 100.0)  # TL
        assert ordered[1] == (300.0, 100.0)  # TR
        assert ordered[2] == (300.0, 300.0)  # BR
        assert ordered[3] == (100.0, 300.0)  # BL

    def test_slightly_rotated_rectangle(self) -> None:
        """A slightly rotated rectangle should be ordered correctly.

        Avoids exact 45-degree diamonds where sum/diff ties cause ambiguity.
        """
        # Slightly tilted rectangle (not axis-aligned, not 45 degrees)
        points = [(80, 50), (320, 80), (300, 280), (60, 250)]
        ordered = order_corners(points)
        assert len(ordered) == 4
        # All 4 points should be present
        original_set = {(float(p[0]), float(p[1])) for p in points}
        ordered_set = set(ordered)
        assert ordered_set == original_set
        # TL should be (80, 50) — smallest sum
        assert ordered[0] == (80.0, 50.0)
        # BR should be (300, 280) — largest sum
        assert ordered[2] == (300.0, 280.0)

    def test_numpy_array_input(self) -> None:
        """Should accept numpy array input in addition to list of tuples."""
        pts = np.array([[100, 100], [300, 100], [300, 300], [100, 300]], dtype=np.float32)
        ordered = order_corners(pts)
        assert len(ordered) == 4
        assert ordered[0] == (100.0, 100.0)  # TL
        assert ordered[2] == (300.0, 300.0)  # BR

    def test_wrong_number_of_points_raises(self) -> None:
        """Should raise ValueError if not exactly 4 points."""
        with pytest.raises(ValueError, match="Expected 4 points"):
            order_corners([(0, 0), (1, 1), (2, 2)])

    def test_collinear_points(self) -> None:
        """Should not crash on degenerate (collinear) points."""
        # All on a line — degenerate but should not error
        points = [(0, 0), (100, 0), (200, 0), (300, 0)]
        ordered = order_corners(points)
        assert len(ordered) == 4


# ---------------------------------------------------------------------------
# TestCorrectPerspectiveFromPoints
# ---------------------------------------------------------------------------


class TestCorrectPerspectiveFromPoints:
    """Tests for the low-level correct_perspective_from_points function."""

    def test_output_is_square(self) -> None:
        """Output should be a square image of the specified target size."""
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), -1)

        src_pts = [(100.0, 100.0), (400.0, 100.0), (400.0, 400.0), (100.0, 400.0)]
        warped, matrix = correct_perspective_from_points(img, src_pts, target_size=256)

        assert warped.shape[0] == 256
        assert warped.shape[1] == 256

    def test_returns_transform_matrix(self) -> None:
        """Should return the 3x3 perspective transform matrix."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        src_pts = [(10, 10), (190, 10), (190, 190), (10, 190)]
        _, matrix = correct_perspective_from_points(img, src_pts, target_size=128)
        assert matrix.shape == (3, 3)

    def test_trapezoid_to_square(self) -> None:
        """A drawn trapezoid should be warped to roughly fill the output square."""
        # Create image with a white trapezoid (simulating angled billet face)
        img = np.zeros((400, 400, 3), dtype=np.uint8)
        trap_pts = np.array([
            [120, 80],   # TL (shifted in from top-left)
            [280, 80],   # TR (shifted in from top-right)
            [350, 320],  # BR
            [50, 320],   # BL
        ], dtype=np.int32)
        cv2.fillPoly(img, [trap_pts], (255, 255, 255))

        src = [
            (120.0, 80.0), (280.0, 80.0),
            (350.0, 320.0), (50.0, 320.0),
        ]
        warped, _ = correct_perspective_from_points(
            img, src, target_size=300, border_percent=0.05
        )

        # The warped white region should be roughly rectangular (more uniform)
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        white_pixels = np.sum(gray > 128)
        total_pixels = warped.shape[0] * warped.shape[1]
        # Should fill a significant portion of the output
        fill_ratio = white_pixels / total_pixels
        assert fill_ratio > 0.5, f"Fill ratio too low: {fill_ratio:.2f}"

    def test_custom_target_size(self) -> None:
        """Output should match the custom target_size parameter."""
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        src = [(50, 50), (250, 50), (250, 250), (50, 250)]
        warped, _ = correct_perspective_from_points(img, src, target_size=1024)
        assert warped.shape == (1024, 1024, 3)

    def test_grayscale_input(self) -> None:
        """Should handle grayscale (2-D) images."""
        img = np.zeros((300, 300), dtype=np.uint8)
        cv2.rectangle(img, (50, 50), (250, 250), 255, -1)
        src = [(50, 50), (250, 50), (250, 250), (50, 250)]
        warped, _ = correct_perspective_from_points(img, src, target_size=128)
        assert warped.shape == (128, 128)

    def test_border_percent_zero(self) -> None:
        """Zero border should still produce correct output shape."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        src = [(10, 10), (190, 10), (190, 190), (10, 190)]
        warped, _ = correct_perspective_from_points(
            img, src, target_size=256, border_percent=0.0
        )
        assert warped.shape == (256, 256, 3)


# ---------------------------------------------------------------------------
# TestCorrectPerspective (with BilletROI)
# ---------------------------------------------------------------------------


class TestCorrectPerspective:
    """Tests for the high-level correct_perspective function."""

    def test_with_billet_roi(self) -> None:
        """Should accept a BilletROI and return warped image + info dict."""
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), -1)

        roi = BilletROI(
            corners=[(100, 100), (400, 100), (400, 400), (100, 400)],
            bounding_rect=(100, 100, 300, 300),
            area=90000.0,
            confidence=0.9,
        )

        warped, info = correct_perspective(img, roi, target_size=256)
        assert warped.shape == (256, 256, 3)
        assert "ordered_corners" in info
        assert "transform_matrix" in info
        assert info["target_size"] == 256

    def test_info_dict_contains_ordered_corners(self) -> None:
        """Info dict should contain properly ordered corners."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        roi = BilletROI(
            corners=[(150, 10), (10, 10), (10, 150), (150, 150)],
            bounding_rect=(10, 10, 140, 140),
            area=19600.0,
            confidence=0.8,
        )
        _, info = correct_perspective(img, roi, target_size=128)
        corners = info["ordered_corners"]
        assert len(corners) == 4
        # TL should have smallest sum
        sums = [c[0] + c[1] for c in corners]
        assert sums[0] <= sums[2]  # TL sum <= BR sum


# ---------------------------------------------------------------------------
# Integration with ROI detector
# ---------------------------------------------------------------------------


class TestPerspectiveIntegration:
    """Integration tests combining ROI detection with perspective correction."""

    def test_detect_then_correct(self) -> None:
        """Full pipeline: detect ROI on synthetic image, then correct perspective."""
        # Create image with a clear white square
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), -1)

        roi = detect_best_billet_face(img)
        assert roi is not None

        warped, info = correct_perspective(img, roi, target_size=256)
        assert warped.shape == (256, 256, 3)

        # The warped image should have significant white content
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        white_ratio = np.sum(gray > 128) / (256 * 256)
        assert white_ratio > 0.3

    @pytest.mark.slow
    def test_on_real_images(self, all_raw_image_paths: list[Path]) -> None:
        """Perspective correction should not crash on real billet images."""
        if not all_raw_image_paths:
            pytest.skip("No raw images found in data/raw/")

        for path in all_raw_image_paths[:3]:  # Test first 3 for speed
            img = cv2.imread(str(path))
            assert img is not None, f"Failed to load {path.name}"

            roi = detect_best_billet_face(img)
            assert roi is not None, f"No ROI for {path.name}"

            warped, info = correct_perspective(img, roi)
            assert warped.shape[0] > 0
            assert warped.shape[1] > 0
