"""Unit tests for the VLM (Claude Vision) reader module.

All tests mock the Anthropic API to avoid real API calls. Covers:
- Prompt construction
- JSON parsing with both old (text confidence) and new (numeric confidence) schemas
- Retry logic on transient errors
- Timeout configuration
- Base64 encoding for file paths and numpy arrays
- _parse_confidence and _extract_raw_texts helpers
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure project root is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

import src.ocr.vlm_reader as vlm_module
from src.models import BilletReading, OCRMethod
from src.ocr.vlm_reader import (
    build_billet_ocr_prompt,
    encode_image_to_base64,
    read_billet_with_vlm,
    read_billet_with_vlm_for_ground_truth,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_response(
    text: str,
    input_tokens: int = 1500,
    output_tokens: int = 80,
) -> MagicMock:
    """Build a mock Anthropic API response object.

    Args:
        text: The text content of the response.
        input_tokens: Simulated input token count.
        output_tokens: Simulated output token count.

    Returns:
        MagicMock mimicking anthropic.types.Message.
    """
    content_block = MagicMock()
    content_block.text = text

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = MagicMock()
    response.content = [content_block]
    response.usage = usage
    return response


def _patch_anthropic(response: MagicMock):
    """Return a patch context manager that mocks anthropic.Anthropic.

    The mock client's .messages.create() returns the given response.
    """
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response
    return patch("src.ocr.vlm_reader.anthropic.Anthropic", return_value=mock_client)


# ---------------------------------------------------------------------------
# TestBuildPrompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """Tests for build_billet_ocr_prompt() — version 1, 2, and 3."""

    def test_default_prompt_matches_config(self) -> None:
        """Default call should return the prompt matching VLM_PROMPT_VERSION config."""
        from src.config import VLM_PROMPT_VERSION
        prompt = build_billet_ocr_prompt()
        if VLM_PROMPT_VERSION == 2:
            assert "PIN-MATRIX" in prompt
        elif VLM_PROMPT_VERSION == 3:
            assert "paint" in prompt.lower() or "stencil" in prompt.lower()
        assert "ANALYSIS STEPS" in prompt or "Return ONLY" in prompt

    def test_v1_prompt_explicit(self) -> None:
        """Passing version=1 should return V1 prompt (original)."""
        prompt = build_billet_ocr_prompt(version=1)
        assert "dot-matrix" in prompt.lower()
        assert "PIN-MATRIX" not in prompt
        assert "ANALYSIS STEPS" not in prompt

    def test_v2_prompt_explicit(self) -> None:
        """Passing version=2 should return V2 prompt."""
        prompt = build_billet_ocr_prompt(version=2)
        assert "PIN-MATRIX" in prompt
        assert "ANALYSIS STEPS" in prompt

    def test_v3_prompt_explicit(self) -> None:
        """Passing version=3 should return V3 flexible format prompt."""
        prompt = build_billet_ocr_prompt(version=3)
        assert "paint" in prompt.lower()
        assert "all_text" in prompt
        assert "PIN-MATRIX" not in prompt

    def test_v1_contains_key_instructions(self) -> None:
        """V1 prompt must contain critical instructions for OCR accuracy."""
        prompt = build_billet_ocr_prompt(version=1)
        assert "dot-matrix" in prompt.lower()
        assert "digits" in prompt.lower() or "ONLY digits 0-9" in prompt
        assert "yellow paint" in prompt.lower()
        assert "JSON" in prompt

    def test_v2_contains_key_instructions(self) -> None:
        """V2 prompt must contain critical instructions for OCR accuracy."""
        prompt = build_billet_ocr_prompt(version=2)
        assert "pin-matrix" in prompt.lower()
        assert "digits 0-9" in prompt
        assert "yellow" in prompt.lower()
        assert "JSON" in prompt

    def test_v2_has_confusion_pairs(self) -> None:
        """V2 prompt should list common dot-pattern confusion pairs."""
        prompt = build_billet_ocr_prompt(version=2)
        # Check for at least some confusion pairs mentioned in the plan.
        assert "3" in prompt and "8" in prompt

    def test_v2_has_count_instruction(self) -> None:
        """V2 prompt should instruct to count exactly 6 digits on Line 1."""
        prompt = build_billet_ocr_prompt(version=2)
        assert "exactly 6 digits" in prompt

    def test_prompt_requests_numeric_confidence(self) -> None:
        """Both prompts must request numeric 0.XX confidence."""
        for version in (1, 2):
            prompt = build_billet_ocr_prompt(version=version)
            assert "0.XX" in prompt

    def test_prompt_uses_raw_text_field(self) -> None:
        """Both prompts must request 'raw_text'."""
        for version in (1, 2):
            prompt = build_billet_ocr_prompt(version=version)
            assert "raw_text" in prompt

    def test_prompt_mentions_question_mark_placeholder(self) -> None:
        """Both prompts should instruct using '?' for uncertain characters."""
        for version in (1, 2):
            prompt = build_billet_ocr_prompt(version=version)
            assert "?" in prompt


# ---------------------------------------------------------------------------
# TestEncodeImage
# ---------------------------------------------------------------------------


class TestEncodeImage:
    """Tests for encode_image_to_base64()."""

    def test_numpy_array_returns_jpeg(self) -> None:
        """A numpy array should be encoded as JPEG."""
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        b64, media_type = encode_image_to_base64(img)
        assert media_type == "image/jpeg"
        assert len(b64) > 0

    def test_file_path_encoding(self, tmp_path: Path) -> None:
        """A JPEG file path should be encoded with correct media type."""
        import cv2

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img_path = tmp_path / "test.jpg"
        cv2.imwrite(str(img_path), img)

        b64, media_type = encode_image_to_base64(img_path)
        assert media_type == "image/jpeg"
        assert len(b64) > 0

    def test_png_file_path(self, tmp_path: Path) -> None:
        """A PNG file path should return image/png media type."""
        import cv2

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img_path = tmp_path / "test.png"
        cv2.imwrite(str(img_path), img)

        _, media_type = encode_image_to_base64(img_path)
        assert media_type == "image/png"

    def test_missing_file_raises(self) -> None:
        """A nonexistent file path should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64(Path("/no/such/file.jpg"))


# ---------------------------------------------------------------------------
# TestParseConfidence
# ---------------------------------------------------------------------------


class TestParseConfidence:
    """Tests for _parse_confidence() — the dual-schema confidence parser."""

    def test_numeric_float(self) -> None:
        """Numeric float confidence should be returned directly."""
        assert vlm_module._parse_confidence({"confidence": 0.85}) == 0.85

    def test_numeric_int(self) -> None:
        """Integer 1 should clamp to 1.0."""
        assert vlm_module._parse_confidence({"confidence": 1}) == 1.0

    def test_numeric_string(self) -> None:
        """String '0.92' should parse as float."""
        assert abs(vlm_module._parse_confidence({"confidence": "0.92"}) - 0.92) < 1e-6

    def test_text_label_high(self) -> None:
        """Legacy text label 'high' should map to 0.95."""
        assert vlm_module._parse_confidence({"confidence": "high"}) == 0.95

    def test_text_label_medium(self) -> None:
        """Legacy text label 'medium' should map to 0.75."""
        assert vlm_module._parse_confidence({"confidence": "medium"}) == 0.75

    def test_text_label_low(self) -> None:
        """Legacy text label 'low' should map to 0.50."""
        assert vlm_module._parse_confidence({"confidence": "low"}) == 0.50

    def test_missing_key_defaults(self) -> None:
        """Missing 'confidence' key should default to 0.5."""
        assert vlm_module._parse_confidence({}) == 0.50

    def test_clamp_above_one(self) -> None:
        """Values > 1.0 should be clamped to 1.0."""
        assert vlm_module._parse_confidence({"confidence": 1.5}) == 1.0

    def test_clamp_below_zero(self) -> None:
        """Values < 0.0 should be clamped to 0.0."""
        assert vlm_module._parse_confidence({"confidence": -0.1}) == 0.0


# ---------------------------------------------------------------------------
# TestExtractRawTexts
# ---------------------------------------------------------------------------


class TestExtractRawTexts:
    """Tests for _extract_raw_texts() — the dual-schema text extractor."""

    def test_new_schema_raw_text_string(self) -> None:
        """New schema 'raw_text' as single string should split on newlines."""
        texts = vlm_module._extract_raw_texts({"raw_text": "184767\n3 09"})
        assert texts == ["184767", "3 09"]

    def test_legacy_schema_all_text_list(self) -> None:
        """Legacy 'all_text' list should be returned as-is."""
        texts = vlm_module._extract_raw_texts({"all_text": ["184767", "3 09"]})
        assert texts == ["184767", "3 09"]

    def test_new_schema_takes_precedence(self) -> None:
        """When both schemas are present, 'raw_text' takes precedence."""
        texts = vlm_module._extract_raw_texts({
            "raw_text": "184767\n3 09",
            "all_text": ["old1", "old2"],
        })
        assert texts == ["184767", "3 09"]

    def test_empty_returns_empty_list(self) -> None:
        """No text fields should return an empty list."""
        assert vlm_module._extract_raw_texts({}) == []

    def test_empty_raw_text_falls_back_to_all_text(self) -> None:
        """Empty raw_text string should fall back to all_text."""
        texts = vlm_module._extract_raw_texts({
            "raw_text": "",
            "all_text": ["184767"],
        })
        assert texts == ["184767"]


# ---------------------------------------------------------------------------
# TestReadBilletWithVlm
# ---------------------------------------------------------------------------


class TestReadBilletWithVlm:
    """Tests for read_billet_with_vlm() with mocked API."""

    def test_successful_new_schema(self) -> None:
        """Successful API call with new JSON schema should parse correctly."""
        response_json = (
            '{"heat_number": "184767", "strand": "3", "sequence": "09", '
            '"confidence": 0.92, "raw_text": "184767\\n3 09"}'
        )
        mock_resp = _make_mock_response(response_json)
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            reading = read_billet_with_vlm(img)

        assert reading.heat_number == "184767"
        assert reading.strand == "3"
        assert reading.sequence == "09"
        assert abs(reading.confidence - 0.92) < 1e-6
        assert reading.method == OCRMethod.VLM_CLAUDE
        assert "184767" in reading.raw_texts

    def test_successful_legacy_schema(self) -> None:
        """Successful API call with legacy JSON schema should parse correctly."""
        response_json = (
            '{"heat_number": "184767", "strand": "3", "sequence": "09", '
            '"all_text": ["184767", "3 09"], "confidence": "high", '
            '"notes": "clear stamp"}'
        )
        mock_resp = _make_mock_response(response_json)
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            reading = read_billet_with_vlm(img)

        assert reading.heat_number == "184767"
        assert reading.confidence == 0.95  # "high" maps to 0.95
        assert reading.raw_texts == ["184767", "3 09"]

    def test_markdown_wrapped_json(self) -> None:
        """JSON wrapped in markdown code fences should still parse."""
        response_json = (
            '```json\n'
            '{"heat_number": "184844", "strand": "5", "sequence": "12", '
            '"confidence": 0.88, "raw_text": "184844\\n5 12"}\n'
            '```'
        )
        mock_resp = _make_mock_response(response_json)
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            reading = read_billet_with_vlm(img)

        assert reading.heat_number == "184844"

    def test_encoding_error_returns_empty_reading(self) -> None:
        """If image encoding fails, an empty BilletReading is returned."""
        reading = read_billet_with_vlm(Path("/nonexistent/image.jpg"))
        assert reading.method == OCRMethod.VLM_CLAUDE
        assert reading.confidence == 0.0
        assert reading.heat_number is None

    def test_api_permanent_error_returns_empty(self) -> None:
        """Permanent API errors (e.g., AuthenticationError) should not retry."""
        import anthropic as _anthropic

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = _anthropic.AuthenticationError(
            message="Invalid key",
            response=MagicMock(status_code=401),
            body=None,
        )
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch("src.ocr.vlm_reader.anthropic.Anthropic", return_value=mock_client):
            reading = read_billet_with_vlm(img)

        assert reading.confidence == 0.0
        # Should NOT have retried (only 1 call).
        assert mock_client.messages.create.call_count == 1

    @patch("src.ocr.vlm_reader.time.sleep")
    def test_retry_on_rate_limit(self, mock_sleep: MagicMock) -> None:
        """Rate limit errors should trigger retries with exponential backoff."""
        import anthropic as _anthropic

        rate_error = _anthropic.RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429),
            body=None,
        )
        success_json = (
            '{"heat_number": "184767", "strand": "3", "sequence": "09", '
            '"confidence": 0.90, "raw_text": "184767"}'
        )
        success_resp = _make_mock_response(success_json)

        mock_client = MagicMock()
        # First call fails with rate limit, second succeeds.
        mock_client.messages.create.side_effect = [rate_error, success_resp]
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch("src.ocr.vlm_reader.anthropic.Anthropic", return_value=mock_client):
            reading = read_billet_with_vlm(img)

        assert reading.heat_number == "184767"
        assert mock_client.messages.create.call_count == 2
        # Should have slept once (1.0 * 2^0 = 1.0s).
        mock_sleep.assert_called_once_with(1.0)

    @patch("src.ocr.vlm_reader.time.sleep")
    def test_all_retries_exhausted(self, mock_sleep: MagicMock) -> None:
        """When all retries are exhausted, an empty BilletReading is returned."""
        import anthropic as _anthropic

        rate_error = _anthropic.RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429),
            body=None,
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = rate_error
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch("src.ocr.vlm_reader.anthropic.Anthropic", return_value=mock_client):
            reading = read_billet_with_vlm(img)

        assert reading.confidence == 0.0
        assert mock_client.messages.create.call_count == vlm_module._MAX_RETRIES

    def test_empty_response_returns_empty_reading(self) -> None:
        """An empty string response should return an empty BilletReading."""
        mock_resp = _make_mock_response("")
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            reading = read_billet_with_vlm(img)

        assert reading.confidence == 0.0

    def test_null_fields_handled(self) -> None:
        """Null/none values in the JSON should map to None in BilletReading."""
        response_json = (
            '{"heat_number": "184767", "strand": null, "sequence": "none", '
            '"confidence": 0.70, "raw_text": "184767"}'
        )
        mock_resp = _make_mock_response(response_json)
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            reading = read_billet_with_vlm(img)

        assert reading.heat_number == "184767"
        assert reading.strand is None
        assert reading.sequence is None  # "none" maps to None


# ---------------------------------------------------------------------------
# TestReadBilletForGroundTruth
# ---------------------------------------------------------------------------


class TestReadBilletForGroundTruth:
    """Tests for read_billet_with_vlm_for_ground_truth()."""

    def test_returns_parsed_dict(self) -> None:
        """Should return the raw parsed JSON dict, not a BilletReading."""
        response_json = (
            '{"heat_number": "184767", "strand": "3", "sequence": "09", '
            '"confidence": 0.92, "raw_text": "184767\\n3 09"}'
        )
        mock_resp = _make_mock_response(response_json)
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with _patch_anthropic(mock_resp):
            result = read_billet_with_vlm_for_ground_truth(img)

        assert isinstance(result, dict)
        assert result["heat_number"] == "184767"
        assert result["confidence"] == 0.92

    def test_encoding_error_returns_empty_dict(self) -> None:
        """If image encoding fails, an empty dict is returned."""
        result = read_billet_with_vlm_for_ground_truth(Path("/no/file.jpg"))
        assert result == {}

    def test_api_error_returns_empty_dict(self) -> None:
        """API errors should return an empty dict."""
        import anthropic as _anthropic

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = _anthropic.AuthenticationError(
            message="Bad key",
            response=MagicMock(status_code=401),
            body=None,
        )
        img = np.zeros((50, 50, 3), dtype=np.uint8)

        with patch("src.ocr.vlm_reader.anthropic.Anthropic", return_value=mock_client):
            result = read_billet_with_vlm_for_ground_truth(img)

        assert result == {}
