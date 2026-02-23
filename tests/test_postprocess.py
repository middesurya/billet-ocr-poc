"""Unit tests for the post-processing / validation module.

Tests cover:
- Character confusion correction (parametrised over common confusions)
- Format validation of heat number, strand, and sequence fields
- The full validate_and_correct_reading() pipeline
"""
import sys
from pathlib import Path

import pytest

# Ensure the project root is on the path when run directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import BilletReading, OCRMethod
from src.postprocess.validator import (
    CHAR_CONFUSION_MAP,
    correct_character_confusion,
    validate_and_correct_reading,
    validate_heat_number,
    validate_sequence,
    validate_strand,
)


# ---------------------------------------------------------------------------
# TestCharacterConfusion
# ---------------------------------------------------------------------------


class TestCharacterConfusion:
    """Parametrised tests for correct_character_confusion()."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            # O → 0
            ("O84767", "084767"),
            # I → 1
            ("I84767", "184767"),
            # l → 1
            ("l84767", "184767"),
            # No confusion – unchanged
            ("184767", "184767"),
            # Multiple confusions: B→8, S→5, Z→2
            ("B8S5Z2", "885522"),
            # Lowercase o → 0
            ("o84767", "084767"),
            # Pipe | → 1
            ("|84767", "184767"),
            # Mixed upper/lower confusions: O→0, I→1, l→1 (7 chars in, 7 chars out)
            ("OI84l67", "0184167"),
            # G → 6
            ("G84767", "684767"),
            # T → 7
            ("T84767", "784767"),
            # Empty string is a no-op
            ("", ""),
        ],
    )
    def test_confusion_correction(self, raw: str, expected: str) -> None:
        """correct_character_confusion maps known OCR confusions to correct digits.

        Args:
            raw: Input text containing OCR confusion characters.
            expected: Expected output after confusion correction.
        """
        result = correct_character_confusion(raw)
        assert result == expected, (
            f"correct_character_confusion({raw!r}) = {result!r}, expected {expected!r}"
        )

    def test_custom_confusion_map(self) -> None:
        """A caller-supplied confusion map overrides the default mapping."""
        custom_map = {"X": "1", "Y": "2"}
        assert correct_character_confusion("XY9", custom_map) == "129"

    def test_unrecognised_characters_pass_through(self) -> None:
        """Characters not in the map must be returned unchanged.

        Note: 'b' IS in the default confusion map (b→6), so we use a string
        that contains only characters confirmed absent from CHAR_CONFUSION_MAP.
        """
        # Digits and 'a', 'c' are not in the default confusion map.
        result = correct_character_confusion("a123c")
        assert result == "a123c"

    def test_none_returns_none(self) -> None:
        """The function returns None unchanged (falsy early-exit path).

        The implementation checks ``if not text: return text``, so None is
        returned as-is rather than raising.  This prevents callers from
        having to guard against None explicitly.
        """
        result = correct_character_confusion(None)  # type: ignore[arg-type]
        assert result is None


# ---------------------------------------------------------------------------
# TestValidation
# ---------------------------------------------------------------------------


class TestValidation:
    """Parametrised tests for validate_heat_number(), validate_strand(), validate_sequence()."""

    @pytest.mark.parametrize(
        "heat, expected_valid",
        [
            ("184767", True),   # 6 digits – standard
            ("18476", True),    # 5 digits – lower bound
            ("1847670", True),  # 7 digits – upper bound
            ("1847", False),    # 4 digits – too short
            ("12345678", False),  # 8 digits – too long
            ("18476A", False),  # contains a letter
            ("", False),        # empty string
            ("abcdef", False),  # all letters
            (" 184767", False), # leading space
        ],
    )
    def test_validate_heat_number(self, heat: str, expected_valid: bool) -> None:
        """validate_heat_number correctly identifies 5-7 digit strings.

        Args:
            heat: Candidate heat number string.
            expected_valid: True if the string should pass validation.
        """
        assert validate_heat_number(heat) == expected_valid

    @pytest.mark.parametrize(
        "strand, expected_valid",
        [
            ("3", True),    # single digit
            ("0", True),    # digit zero
            ("9", True),    # digit nine
            ("10", False),  # two digits
            ("", False),    # empty
            ("A", False),   # letter
            (" 3", False),  # leading space
        ],
    )
    def test_validate_strand(self, strand: str, expected_valid: bool) -> None:
        """validate_strand correctly identifies single-digit strings.

        Args:
            strand: Candidate strand string.
            expected_valid: True if the string should pass validation.
        """
        assert validate_strand(strand) == expected_valid

    @pytest.mark.parametrize(
        "sequence, expected_valid",
        [
            ("09", True),    # 2 digits – most common
            ("9", True),     # 1 digit – lower bound
            ("123", True),   # 3 digits – upper bound
            ("1234", False), # 4 digits – too long
            ("", False),     # empty
            ("0A", False),   # contains letter
            (" 09", False),  # leading space
        ],
    )
    def test_validate_sequence(self, sequence: str, expected_valid: bool) -> None:
        """validate_sequence correctly identifies 1-3 digit strings.

        Args:
            sequence: Candidate sequence string.
            expected_valid: True if the string should pass validation.
        """
        assert validate_sequence(sequence) == expected_valid


# ---------------------------------------------------------------------------
# TestValidateAndCorrectReading
# ---------------------------------------------------------------------------


class TestValidateAndCorrectReading:
    """Tests for validate_and_correct_reading() – the full post-processing pipeline."""

    def test_corrects_confused_characters_in_heat_number(self) -> None:
        """Confusion characters in heat_number must be corrected.

        'O84767' contains an uppercase-O instead of zero.  The corrected
        reading should have heat_number='084767'.
        """
        raw = BilletReading(
            heat_number="O84767",
            strand="3",
            sequence="09",
            confidence=0.92,
            method=OCRMethod.PADDLE_RAW,
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.heat_number == "084767"

    def test_corrects_confused_characters_in_strand(self) -> None:
        """Confusion characters in strand must be corrected (e.g. 'I'→'1')."""
        raw = BilletReading(
            heat_number="184767",
            strand="I",
            sequence="09",
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.strand == "1"

    def test_corrects_confused_characters_in_sequence(self) -> None:
        """Confusion characters in sequence must be corrected (e.g. 'O9'→'09')."""
        raw = BilletReading(
            heat_number="184767",
            strand="3",
            sequence="O9",
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.sequence == "09"

    def test_original_reading_not_modified(self) -> None:
        """validate_and_correct_reading must return a new BilletReading object.

        The original reading passed in must remain unchanged.
        """
        original_heat = "O84767"
        raw = BilletReading(heat_number=original_heat, strand="3", sequence="O9")
        validate_and_correct_reading(raw)
        assert raw.heat_number == original_heat  # original unchanged

    def test_clean_reading_passes_through_unchanged(self) -> None:
        """A reading with no confused characters must come out identical."""
        raw = BilletReading(
            heat_number="184767",
            strand="3",
            sequence="09",
            confidence=0.97,
            method=OCRMethod.PADDLE_PREPROCESSED,
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.heat_number == "184767"
        assert corrected.strand == "3"
        assert corrected.sequence == "09"

    def test_confidence_carried_over(self) -> None:
        """Confidence score from the original reading must be preserved."""
        raw = BilletReading(heat_number="184767", strand="3", sequence="09", confidence=0.88)
        corrected = validate_and_correct_reading(raw)
        assert abs(corrected.confidence - 0.88) < 1e-9

    def test_method_carried_over(self) -> None:
        """OCRMethod tag from the original reading must be preserved."""
        raw = BilletReading(
            heat_number="184767",
            strand="3",
            sequence="09",
            method=OCRMethod.PADDLE_PREPROCESSED,
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.method == OCRMethod.PADDLE_PREPROCESSED

    def test_raw_texts_carried_over(self) -> None:
        """raw_texts list from the original reading must be preserved (shallow copy)."""
        raw = BilletReading(
            heat_number="184767",
            strand="3",
            sequence="09",
            raw_texts=["184767", "3 09"],
        )
        corrected = validate_and_correct_reading(raw)
        assert corrected.raw_texts == ["184767", "3 09"]

    def test_none_fields_handled_gracefully(self) -> None:
        """None fields in the reading must not raise any exception."""
        raw = BilletReading(heat_number=None, strand=None, sequence=None)
        corrected = validate_and_correct_reading(raw)
        assert corrected.heat_number is None
        assert corrected.strand is None
        assert corrected.sequence is None

    def test_multiple_confusions_corrected(self) -> None:
        """B→8, S→5, Z→2 confusions in the heat number are all corrected."""
        raw = BilletReading(heat_number="B8S5Z2", strand="3", sequence="09")
        corrected = validate_and_correct_reading(raw)
        assert corrected.heat_number == "885522"
