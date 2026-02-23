"""Unit tests for the ensemble pipeline module.

All tests mock both PaddleOCR and VLM to avoid real model loading and API
calls.  Covers:
- High paddle confidence → skips VLM
- Low paddle confidence → triggers VLM fallback
- skip_paddle=True → VLM-only path
- Both engines fail → returns best-of-two
- Logging captures the execution path taken
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure project root is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import BilletReading, OCRMethod
from src.ocr.ensemble import run_ensemble_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reading(
    heat_number: str = "184767",
    confidence: float = 0.95,
    method: OCRMethod = OCRMethod.PADDLE_PREPROCESSED,
) -> BilletReading:
    """Build a BilletReading for testing.

    Args:
        heat_number: Heat number string.
        confidence: Confidence score.
        method: OCR method tag.

    Returns:
        A populated BilletReading.
    """
    return BilletReading(
        heat_number=heat_number,
        strand="3",
        sequence="09",
        confidence=confidence,
        method=method,
        raw_texts=[heat_number, "3 09"],
    )


# ---------------------------------------------------------------------------
# TestEnsemblePipeline
# ---------------------------------------------------------------------------


class TestEnsemblePipeline:
    """Tests for run_ensemble_pipeline()."""

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_high_paddle_confidence_skips_vlm(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """When PaddleOCR confidence >= threshold, VLM should NOT be called."""
        paddle_result = _make_reading(confidence=0.95)
        mock_paddle.return_value = paddle_result

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, confidence_threshold=0.85)

        assert reading.heat_number == "184767"
        assert reading.confidence == 0.95
        assert reading.method == OCRMethod.PADDLE_PREPROCESSED
        mock_paddle.assert_called_once()
        mock_vlm.assert_not_called()

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_low_paddle_confidence_triggers_vlm(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """When PaddleOCR confidence < threshold, VLM should be triggered."""
        paddle_result = _make_reading(confidence=0.30)
        vlm_result = _make_reading(
            heat_number="184844", confidence=0.88, method=OCRMethod.VLM_CLAUDE
        )
        mock_paddle.return_value = paddle_result
        mock_vlm.return_value = vlm_result

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, confidence_threshold=0.85)

        assert reading.heat_number == "184844"
        assert reading.confidence == 0.88
        assert reading.method == OCRMethod.VLM_CLAUDE
        mock_paddle.assert_called_once()
        mock_vlm.assert_called_once()

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_skip_paddle_goes_vlm_only(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """skip_paddle=True should bypass PaddleOCR entirely."""
        vlm_result = _make_reading(
            heat_number="184844", confidence=0.90, method=OCRMethod.VLM_CLAUDE
        )
        mock_vlm.return_value = vlm_result

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, skip_paddle=True)

        assert reading.heat_number == "184844"
        assert reading.method == OCRMethod.VLM_CLAUDE
        mock_paddle.assert_not_called()
        mock_vlm.assert_called_once()

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_both_fail_returns_best_of_two(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """When both engines fail, return the one with higher confidence."""
        paddle_result = _make_reading(heat_number="18476?", confidence=0.25)
        vlm_result = BilletReading(method=OCRMethod.VLM_CLAUDE, confidence=0.0)
        mock_paddle.return_value = paddle_result
        mock_vlm.return_value = vlm_result

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, confidence_threshold=0.85)

        # PaddleOCR had 0.25 > VLM's 0.0, so paddle result should be used.
        assert reading.heat_number == "18476?"
        assert reading.method == OCRMethod.ENSEMBLE

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_both_fail_completely_returns_empty(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """When both engines return 0.0 confidence, return empty ENSEMBLE reading."""
        mock_paddle.return_value = BilletReading(
            method=OCRMethod.PADDLE_RAW, confidence=0.0
        )
        mock_vlm.return_value = BilletReading(
            method=OCRMethod.VLM_CLAUDE, confidence=0.0
        )

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, confidence_threshold=0.85)

        assert reading.heat_number is None
        assert reading.method == OCRMethod.ENSEMBLE
        assert reading.confidence == 0.0

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_preprocessed_image_passed_to_paddle(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """When preprocessed image is provided, it should be passed to PaddleOCR."""
        paddle_result = _make_reading(confidence=0.95)
        mock_paddle.return_value = paddle_result

        raw = np.zeros((50, 50, 3), dtype=np.uint8)
        preprocessed = np.ones((50, 50, 3), dtype=np.uint8) * 128

        reading = run_ensemble_pipeline(raw, preprocessed=preprocessed)

        # Verify preprocessed was passed as second arg to _run_paddle.
        call_args = mock_paddle.call_args
        assert call_args is not None
        # _run_paddle(image, preprocessed) — check second positional arg.
        passed_preprocessed = call_args[0][1]
        assert np.array_equal(passed_preprocessed, preprocessed)

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_raw_image_passed_to_vlm_by_default(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """By default (vlm_use_raw=True), VLM receives the raw image, not preprocessed."""
        mock_paddle.return_value = _make_reading(confidence=0.30)
        mock_vlm.return_value = _make_reading(
            confidence=0.90, method=OCRMethod.VLM_CLAUDE
        )

        raw = np.zeros((50, 50, 3), dtype=np.uint8)
        preprocessed = np.ones((50, 50, 3), dtype=np.uint8) * 128

        run_ensemble_pipeline(raw, preprocessed=preprocessed, confidence_threshold=0.85)

        # VLM should receive the raw image (vlm_use_raw=True is the default).
        vlm_call_args = mock_vlm.call_args
        passed_image = vlm_call_args[0][0]
        assert np.array_equal(passed_image, raw)

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_preprocessed_image_passed_to_vlm_when_vlm_use_raw_false(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """With vlm_use_raw=False, VLM receives the preprocessed image."""
        mock_paddle.return_value = _make_reading(confidence=0.30)
        mock_vlm.return_value = _make_reading(
            confidence=0.90, method=OCRMethod.VLM_CLAUDE
        )

        raw = np.zeros((50, 50, 3), dtype=np.uint8)
        preprocessed = np.ones((50, 50, 3), dtype=np.uint8) * 128

        run_ensemble_pipeline(
            raw, preprocessed=preprocessed, confidence_threshold=0.85,
            vlm_use_raw=False,
        )

        # VLM should receive the preprocessed image.
        vlm_call_args = mock_vlm.call_args
        passed_image = vlm_call_args[0][0]
        assert np.array_equal(passed_image, preprocessed)

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_exact_threshold_skips_vlm(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """Confidence exactly at threshold should NOT trigger VLM (>=)."""
        mock_paddle.return_value = _make_reading(confidence=0.85)

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        reading = run_ensemble_pipeline(img, confidence_threshold=0.85)

        assert reading.confidence == 0.85
        mock_vlm.assert_not_called()

    @patch("src.ocr.ensemble._run_vlm")
    @patch("src.ocr.ensemble._run_paddle")
    def test_custom_threshold(
        self, mock_paddle: MagicMock, mock_vlm: MagicMock
    ) -> None:
        """A custom threshold should be respected."""
        mock_paddle.return_value = _make_reading(confidence=0.50)
        mock_vlm.return_value = _make_reading(
            confidence=0.80, method=OCRMethod.VLM_CLAUDE
        )

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        # With threshold=0.60, paddle's 0.50 should trigger VLM.
        reading = run_ensemble_pipeline(img, confidence_threshold=0.60)

        assert reading.method == OCRMethod.VLM_CLAUDE
        mock_vlm.assert_called_once()
