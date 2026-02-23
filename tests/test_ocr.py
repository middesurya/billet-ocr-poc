"""Unit tests for the PaddleOCR wrapper module.

Tests cover PaddleOCR initialisation (singleton pattern), the OCR result
format, top-to-bottom sorting, and billet field extraction from structured
OCR results.

PaddleOCR model loading takes 5-30 s on first call.  Tests that require the
live model are marked @pytest.mark.slow so they can be excluded with:

    pytest tests/test_ocr.py -v -m "not slow"
"""
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure the project root is on the path when run directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

import src.ocr.paddle_ocr as _ocr_module
from src.models import BilletReading, BoundingBox, OCRMethod, OCRResult
from src.ocr.paddle_ocr import (
    extract_billet_info,
    initialize_paddle_ocr,
    run_ocr,
    run_paddle_pipeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    text: str,
    confidence: float = 0.95,
    y_center: float = 0.0,
    x_center: float = 0.0,
) -> OCRResult:
    """Build an OCRResult with a square bounding box centred at (x_center, y_center).

    Args:
        text: Recognised text string.
        confidence: Confidence score (0–1).
        y_center: Vertical centre pixel coordinate of the bounding box.
        x_center: Horizontal centre pixel coordinate of the bounding box.

    Returns:
        OCRResult with a 4-point bounding box.
    """
    half = 10.0
    points = [
        (x_center - half, y_center - half),
        (x_center + half, y_center - half),
        (x_center + half, y_center + half),
        (x_center - half, y_center + half),
    ]
    return OCRResult(text=text, confidence=confidence, bbox=BoundingBox(points=points))


# ---------------------------------------------------------------------------
# TestInitializePaddleOCR
# ---------------------------------------------------------------------------


class TestInitializePaddleOCR:
    """Tests for initialize_paddle_ocr() – model loading and singleton caching."""

    def setup_method(self) -> None:
        """Reset the module-level singleton before each test so tests are isolated."""
        _ocr_module._paddle_instance = None

    @pytest.mark.slow
    def test_returns_instance(self) -> None:
        """initialize_paddle_ocr() must return a non-None PaddleOCR instance."""
        instance = initialize_paddle_ocr()
        assert instance is not None

    @pytest.mark.slow
    def test_singleton_pattern(self) -> None:
        """Two calls to initialize_paddle_ocr() must return the same object (singleton)."""
        first = initialize_paddle_ocr()
        second = initialize_paddle_ocr()
        assert first is second

    def test_singleton_cached_after_mock_init(self) -> None:
        """When a fake instance is pre-set the second call must return it (no reload).

        Uses a MagicMock to avoid loading the heavy model.
        """
        fake = MagicMock(name="FakePaddleOCR")
        _ocr_module._paddle_instance = fake
        result = initialize_paddle_ocr()
        assert result is fake


# ---------------------------------------------------------------------------
# TestRunOCR
# ---------------------------------------------------------------------------


class TestRunOCR:
    """Tests for run_ocr() – result structure and edge cases.

    run_ocr() internally calls initialize_paddle_ocr().  Most tests mock the
    paddle instance to avoid slow model loading.
    """

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        _ocr_module._paddle_instance = None

    def _install_mock_ocr(self, page_dict: Optional[dict]) -> MagicMock:
        """Install a MagicMock as the PaddleOCR singleton and configure its .ocr() return.

        Args:
            page_dict: The dict that ocr() should return as page[0], or None.

        Returns:
            The installed MagicMock instance.
        """
        import numpy as _np

        mock_instance = MagicMock(name="MockPaddle")
        if page_dict is None:
            mock_instance.ocr.return_value = [None]
        else:
            mock_instance.ocr.return_value = [page_dict]
        _ocr_module._paddle_instance = mock_instance
        return mock_instance

    def test_returns_list_of_ocr_results(self) -> None:
        """run_ocr() must return a list of OCRResult objects, never None."""
        poly = np.array([[0, 0], [100, 0], [100, 30], [0, 30]])
        page = {
            "rec_texts": ["184767"],
            "rec_scores": [0.97],
            "rec_polys": [poly],
        }
        self._install_mock_ocr(page)

        results = run_ocr(np.zeros((100, 200, 3), dtype=np.uint8))
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], OCRResult)
        assert results[0].text == "184767"
        assert abs(results[0].confidence - 0.97) < 1e-6

    def test_handles_numpy_array_input(self) -> None:
        """run_ocr() must accept a numpy ndarray without raising."""
        self._install_mock_ocr({"rec_texts": [], "rec_scores": [], "rec_polys": []})
        results = run_ocr(np.zeros((50, 50, 3), dtype=np.uint8))
        assert isinstance(results, list)

    def test_empty_image_returns_empty_list(self) -> None:
        """When PaddleOCR detects no text the return value is an empty list."""
        self._install_mock_ocr({"rec_texts": [], "rec_scores": [], "rec_polys": []})
        results = run_ocr(np.zeros((100, 100, 3), dtype=np.uint8))
        assert results == []

    def test_none_page_returns_empty_list(self) -> None:
        """When page[0] is None (no detections) return an empty list."""
        self._install_mock_ocr(None)
        results = run_ocr(np.zeros((80, 80, 3), dtype=np.uint8))
        assert results == []

    def test_results_sorted_top_to_bottom(self) -> None:
        """Results must be sorted ascending by the mean Y coordinate of each bbox."""
        poly_top = np.array([[0, 5], [100, 5], [100, 25], [0, 25]])     # y≈15
        poly_bot = np.array([[0, 80], [100, 80], [100, 100], [0, 100]])  # y≈90
        page = {
            # Deliberately insert in bottom-first order; run_ocr should sort them.
            "rec_texts": ["3 09", "184767"],
            "rec_scores": [0.91, 0.98],
            "rec_polys": [poly_bot, poly_top],
        }
        self._install_mock_ocr(page)

        results = run_ocr(np.zeros((120, 200, 3), dtype=np.uint8))
        assert len(results) == 2
        # After sorting, "184767" (y≈15) comes before "3 09" (y≈90).
        assert results[0].text == "184767"
        assert results[1].text == "3 09"

    def test_exception_in_ocr_returns_empty_list(self) -> None:
        """If PaddleOCR raises an exception run_ocr must return [] not re-raise."""
        mock_instance = MagicMock()
        mock_instance.ocr.side_effect = RuntimeError("GPU error")
        _ocr_module._paddle_instance = mock_instance

        results = run_ocr(np.zeros((50, 50, 3), dtype=np.uint8))
        assert results == []

    @pytest.mark.slow
    def test_real_model_on_sample_image(self, sample_image_path: Path) -> None:
        """Smoke test: run the actual PaddleOCR model on a known billet image.

        Args:
            sample_image_path: Pytest fixture providing a valid image path.
        """
        results = run_ocr(sample_image_path)
        # We don't assert specific text (OCR is non-deterministic on real images),
        # but the return type must always be a list of OCRResult.
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, OCRResult)
            assert 0.0 <= r.confidence <= 1.0


# ---------------------------------------------------------------------------
# TestExtractBilletInfo
# ---------------------------------------------------------------------------


class TestExtractBilletInfo:
    """Tests for extract_billet_info() – field extraction from OCRResult lists."""

    def test_extracts_heat_number_from_first_line(self) -> None:
        """Heat number must come from the topmost detected text region.

        We provide two results: the top one carries the heat number, the bottom
        one the strand/sequence.
        """
        results = [
            _make_result("184767", y_center=20.0),
            _make_result("3 09", y_center=80.0),
        ]
        reading = extract_billet_info(results)
        assert reading.heat_number == "184767"

    def test_extracts_strand_and_sequence_from_second_line(self) -> None:
        """Strand and sequence are parsed from the second line text.

        The second line text '3 09' splits into strand='3', sequence='09'.
        """
        results = [
            _make_result("184767", y_center=20.0),
            _make_result("3 09", y_center=80.0),
        ]
        reading = extract_billet_info(results)
        assert reading.strand == "3"
        assert reading.sequence == "09"

    def test_handles_empty_results_list(self) -> None:
        """An empty OCR result list must return a BilletReading with all None fields."""
        reading = extract_billet_info([])
        assert isinstance(reading, BilletReading)
        assert reading.heat_number is None
        assert reading.strand is None
        assert reading.sequence is None

    def test_method_recorded_in_reading(self) -> None:
        """The method parameter must be stored in the returned BilletReading."""
        results = [_make_result("184767", y_center=10.0)]
        reading = extract_billet_info(results, method=OCRMethod.PADDLE_PREPROCESSED)
        assert reading.method == OCRMethod.PADDLE_PREPROCESSED

    def test_default_method_is_paddle_raw(self) -> None:
        """Default method attribute must be OCRMethod.PADDLE_RAW."""
        results = [_make_result("184767", y_center=10.0)]
        reading = extract_billet_info(results)
        assert reading.method == OCRMethod.PADDLE_RAW

    def test_single_line_only_sets_heat_number(self) -> None:
        """When only one text region exists, only heat_number is populated."""
        results = [_make_result("184767", y_center=30.0)]
        reading = extract_billet_info(results)
        assert reading.heat_number == "184767"
        assert reading.strand is None
        assert reading.sequence is None

    def test_confidence_averaged_over_results(self) -> None:
        """Overall confidence must equal the mean of individual result confidences."""
        results = [
            _make_result("184767", confidence=0.90, y_center=20.0),
            _make_result("3 09", confidence=0.80, y_center=80.0),
        ]
        reading = extract_billet_info(results)
        expected = (0.90 + 0.80) / 2
        assert abs(reading.confidence - expected) < 1e-6

    def test_raw_texts_list_populated(self) -> None:
        """raw_texts attribute must contain the plain text of every OCR result."""
        results = [
            _make_result("184767", y_center=20.0),
            _make_result("3 09", y_center=80.0),
        ]
        reading = extract_billet_info(results)
        assert "184767" in reading.raw_texts
        assert "3 09" in reading.raw_texts
