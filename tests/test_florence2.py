"""Unit tests for the Florence-2 reader module.

All tests mock the transformers model/processor to avoid downloading the
actual ~500MB model. Covers:
- Singleton model loading
- Image preparation (numpy BGR -> PIL RGB, file path -> PIL)
- Output parsing (raw OCR text -> BilletReading fields)
- Error handling (missing file, inference failure)
- Character replacement integration
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import BilletReading, OCRMethod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_florence2_modules():
    """Set up mock transformers and torch modules for Florence-2 tests.

    Returns a dict with mock objects that can be used in patches.
    """
    mock_model = MagicMock()
    mock_processor = MagicMock()

    # Mock processor call (preparing inputs)
    mock_inputs = {"input_ids": MagicMock(), "pixel_values": MagicMock()}
    mock_inputs["input_ids"].to = MagicMock(return_value=mock_inputs["input_ids"])
    mock_inputs["pixel_values"].to = MagicMock(return_value=mock_inputs["pixel_values"])
    mock_processor.return_value = mock_inputs

    # Mock model.generate
    mock_generated = MagicMock()
    mock_model.generate.return_value = mock_generated
    mock_model.to = MagicMock(return_value=mock_model)

    # Mock processor.batch_decode
    mock_processor.batch_decode.return_value = ["<OCR>184767\n3 09</s>"]

    return {
        "model": mock_model,
        "processor": mock_processor,
    }


# ---------------------------------------------------------------------------
# TestPrepareImage
# ---------------------------------------------------------------------------


class TestPrepareImage:
    """Tests for _prepare_pil_image() — numpy/path to PIL conversion."""

    def test_numpy_bgr_to_pil_rgb(self) -> None:
        """BGR numpy array should be converted to RGB PIL Image."""
        from src.ocr.florence2_reader import _prepare_pil_image

        # Create a BGR image (blue channel = 255)
        bgr = np.zeros((50, 50, 3), dtype=np.uint8)
        bgr[:, :, 0] = 255  # Blue channel in BGR

        pil_img = _prepare_pil_image(bgr)
        assert pil_img.mode == "RGB"
        assert pil_img.size == (50, 50)

        # After BGR->RGB conversion, the red channel should be 0
        # and blue should be 255
        pixel = pil_img.getpixel((0, 0))
        assert pixel[0] == 0    # R (was B in BGR)
        assert pixel[2] == 255  # B (was R=0 in BGR -> B in RGB)

    def test_grayscale_numpy_to_pil(self) -> None:
        """Grayscale numpy array should be converted to RGB PIL Image."""
        from src.ocr.florence2_reader import _prepare_pil_image

        gray = np.ones((50, 50), dtype=np.uint8) * 128
        pil_img = _prepare_pil_image(gray)
        assert pil_img.mode == "RGB"
        assert pil_img.size == (50, 50)

    def test_file_path_loads_image(self, tmp_path: Path) -> None:
        """A valid file path should load as PIL Image."""
        import cv2

        from src.ocr.florence2_reader import _prepare_pil_image

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img_path = tmp_path / "test.jpg"
        cv2.imwrite(str(img_path), img)

        pil_img = _prepare_pil_image(img_path)
        assert pil_img.mode == "RGB"

    def test_missing_file_raises(self) -> None:
        """A nonexistent file path should raise FileNotFoundError."""
        from src.ocr.florence2_reader import _prepare_pil_image

        with pytest.raises(FileNotFoundError):
            _prepare_pil_image(Path("/no/such/file.jpg"))

    def test_string_path(self, tmp_path: Path) -> None:
        """String path should work the same as Path object."""
        import cv2

        from src.ocr.florence2_reader import _prepare_pil_image

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), img)

        pil_img = _prepare_pil_image(str(img_path))
        assert pil_img.mode == "RGB"


# ---------------------------------------------------------------------------
# TestParseOutput
# ---------------------------------------------------------------------------


class TestParseOutput:
    """Tests for _parse_florence2_output() — text parsing."""

    def test_simple_ocr_output(self) -> None:
        """Simple OCR output with heat number and strand/seq on separate lines."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {"<OCR>": "184767\n3 09"}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat == "184767"
        assert strand == "3"
        assert seq == "09"
        assert len(raw) > 0

    def test_single_line_output(self) -> None:
        """Single line with just a heat number should parse heat only."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {"<OCR>": "192435"}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat == "192435"

    def test_letters_replaced(self) -> None:
        """Letters in OCR output should be replaced (B->8, O->0)."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {"<OCR>": "IB4767"}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat == "184767"

    def test_empty_output(self) -> None:
        """Empty OCR output should return all None."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {"<OCR>": ""}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat is None
        assert strand is None
        assert seq is None
        assert raw == []

    def test_missing_key(self) -> None:
        """Missing OCR key should return all None."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat is None

    def test_ocr_with_region_task(self) -> None:
        """OCR_WITH_REGION output should concatenate labels."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {
            "<OCR_WITH_REGION>": {
                "quad_boxes": [[0, 0, 100, 0, 100, 30, 0, 30]],
                "labels": ["184767"],
            }
        }
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR_WITH_REGION>")
        assert heat == "184767"

    def test_noisy_output_extracts_digits(self) -> None:
        """Noisy output with non-digit chars should still find heat number."""
        from src.ocr.florence2_reader import _parse_florence2_output

        result = {"<OCR>": "abc 184767 xyz"}
        heat, strand, seq, raw = _parse_florence2_output(result, "<OCR>")
        assert heat == "184767"


# ---------------------------------------------------------------------------
# TestModelSingleton
# ---------------------------------------------------------------------------


class TestModelSingleton:
    """Tests for model singleton loading pattern."""

    def test_singleton_loads_once(self) -> None:
        """Model and processor should only be loaded once.

        Since _get_model_and_processor() uses lazy imports (import torch and
        import transformers inside the function body), we mock via sys.modules
        rather than patching module-level attributes.
        """
        import types

        import src.ocr.florence2_reader as f2_module

        # Reset singleton
        f2_module._model = None
        f2_module._processor = None

        mock_model = MagicMock()
        mock_model.to = MagicMock(return_value=mock_model)
        mock_processor = MagicMock()

        # Create mock torch module
        mock_torch = types.ModuleType("torch")
        mock_torch.float32 = "float32"
        mock_torch.float16 = "float16"
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.no_grad = MagicMock(return_value=MagicMock(
            __enter__=MagicMock(), __exit__=MagicMock()
        ))

        # Create mock transformers module
        mock_transformers = types.ModuleType("transformers")
        mock_florence2_cls = MagicMock()
        mock_florence2_cls.from_pretrained.return_value = mock_model
        mock_transformers.Florence2ForConditionalGeneration = mock_florence2_cls
        mock_auto_proc = MagicMock()
        mock_auto_proc.from_pretrained.return_value = mock_processor
        mock_transformers.AutoProcessor = mock_auto_proc

        with patch.dict("sys.modules", {
            "torch": mock_torch,
            "transformers": mock_transformers,
        }):
            m1, p1 = f2_module._get_model_and_processor()
            m2, p2 = f2_module._get_model_and_processor()

            # Second call should return same objects (singleton)
            assert m1 is m2
            assert p1 is p2
            # from_pretrained should only be called once
            assert mock_florence2_cls.from_pretrained.call_count == 1

        # Clean up singleton
        f2_module._model = None
        f2_module._processor = None


# ---------------------------------------------------------------------------
# TestReadBilletWithFlorence2
# ---------------------------------------------------------------------------


class TestReadBilletWithFlorence2:
    """Tests for read_billet_with_florence2() with mocked model."""

    def test_missing_file_returns_empty_reading(self) -> None:
        """Missing file should return empty BilletReading."""
        from src.ocr.florence2_reader import read_billet_with_florence2

        reading = read_billet_with_florence2(Path("/nonexistent/image.jpg"))
        assert reading.method == OCRMethod.VLM_FLORENCE2
        assert reading.confidence == 0.0
        assert reading.heat_number is None

    def test_inference_error_returns_empty_reading(self) -> None:
        """Model inference failure should return empty BilletReading."""
        import src.ocr.florence2_reader as f2_module
        from src.ocr.florence2_reader import read_billet_with_florence2

        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch.object(f2_module, "_run_florence2_inference", side_effect=RuntimeError("CUDA error")), \
             patch.object(f2_module, "_prepare_pil_image", return_value=MagicMock()):
            reading = read_billet_with_florence2(img)

        assert reading.method == OCRMethod.VLM_FLORENCE2
        assert reading.confidence == 0.0

    def test_successful_inference(self) -> None:
        """Successful inference should return parsed BilletReading."""
        import src.ocr.florence2_reader as f2_module
        from src.ocr.florence2_reader import read_billet_with_florence2

        mock_pil = MagicMock()
        mock_pil.size = (640, 480)

        mock_result = {"<OCR>": "184767\n3 09"}

        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch.object(f2_module, "_prepare_pil_image", return_value=mock_pil), \
             patch.object(f2_module, "_run_florence2_inference", return_value=mock_result):
            reading = read_billet_with_florence2(img)

        assert reading.method == OCRMethod.VLM_FLORENCE2
        assert reading.heat_number == "184767"
        assert reading.strand == "3"
        assert reading.sequence == "09"
        assert reading.confidence > 0.0

    def test_method_is_vlm_florence2(self) -> None:
        """Reading method should always be VLM_FLORENCE2."""
        import src.ocr.florence2_reader as f2_module
        from src.ocr.florence2_reader import read_billet_with_florence2

        mock_result = {"<OCR>": "184767"}

        with patch.object(f2_module, "_prepare_pil_image", return_value=MagicMock(size=(640, 480))), \
             patch.object(f2_module, "_run_florence2_inference", return_value=mock_result):
            reading = read_billet_with_florence2(np.zeros((50, 50, 3), dtype=np.uint8))

        assert reading.method == OCRMethod.VLM_FLORENCE2

    def test_empty_ocr_output(self) -> None:
        """Empty OCR output should return reading with no heat number."""
        import src.ocr.florence2_reader as f2_module
        from src.ocr.florence2_reader import read_billet_with_florence2

        mock_result = {"<OCR>": ""}

        with patch.object(f2_module, "_prepare_pil_image", return_value=MagicMock(size=(640, 480))), \
             patch.object(f2_module, "_run_florence2_inference", return_value=mock_result):
            reading = read_billet_with_florence2(np.zeros((50, 50, 3), dtype=np.uint8))

        assert reading.heat_number is None
        assert reading.confidence == 0.0
