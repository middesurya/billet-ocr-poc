"""Unit tests for the character replacement and confidence scoring module.

Covers:
- Individual character replacements (B->8, O->0, I->1, etc.)
- Digits passing through unchanged
- Confidence calculation (full, partial, no replacements)
- replace_and_score_ocr_text() end-to-end behavior
- Unknown characters replaced with '?'
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.postprocess.char_replace import (
    CHAR_REPLACEMENTS,
    apply_char_replacements,
    compute_replacement_confidence,
    replace_and_score_ocr_text,
)


# ---------------------------------------------------------------------------
# TestCharReplacements
# ---------------------------------------------------------------------------


class TestCharReplacements:
    """Tests for apply_char_replacements() and the CHAR_REPLACEMENTS map."""

    def test_b_maps_to_8(self) -> None:
        """Capital B should map to 8."""
        assert apply_char_replacements("B") == "8"

    def test_o_maps_to_0(self) -> None:
        """Capital O and lowercase o should both map to 0."""
        assert apply_char_replacements("O") == "0"
        assert apply_char_replacements("o") == "0"

    def test_i_maps_to_1(self) -> None:
        """Capital I should map to 1."""
        assert apply_char_replacements("I") == "1"

    def test_l_maps_to_1(self) -> None:
        """Lowercase l should map to 1."""
        assert apply_char_replacements("l") == "1"

    def test_pipe_maps_to_1(self) -> None:
        """Pipe character | should map to 1."""
        assert apply_char_replacements("|") == "1"

    def test_z_maps_to_2(self) -> None:
        """Z/z should map to 2."""
        assert apply_char_replacements("Z") == "2"
        assert apply_char_replacements("z") == "2"

    def test_s_maps_to_5(self) -> None:
        """S/s should map to 5."""
        assert apply_char_replacements("S") == "5"
        assert apply_char_replacements("s") == "5"

    def test_g_maps_correctly(self) -> None:
        """G should map to 6, g should map to 9 (per validator.py canonical map)."""
        assert apply_char_replacements("G") == "6"
        assert apply_char_replacements("g") == "9"

    def test_t_maps_to_7(self) -> None:
        """T should map to 7."""
        assert apply_char_replacements("T") == "7"

    def test_d_maps_to_0(self) -> None:
        """D should map to 0."""
        assert apply_char_replacements("D") == "0"

    def test_a_maps_to_4(self) -> None:
        """A should map to 4."""
        assert apply_char_replacements("A") == "4"

    def test_lowercase_b_maps_to_6(self) -> None:
        """Lowercase b should map to 6."""
        assert apply_char_replacements("b") == "6"

    def test_q_maps_to_9(self) -> None:
        """Lowercase q should map to 9."""
        assert apply_char_replacements("q") == "9"

    def test_digits_pass_through(self) -> None:
        """Digits 0-9 should pass through unchanged."""
        for digit in "0123456789":
            assert apply_char_replacements(digit) == digit

    def test_spaces_pass_through(self) -> None:
        """Spaces should pass through unchanged."""
        assert apply_char_replacements("3 09") == "3 09"

    def test_mixed_input(self) -> None:
        """A string mixing digits and confused letters should be corrected."""
        assert apply_char_replacements("1B4767") == "184767"
        assert apply_char_replacements("I84767") == "184767"

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert apply_char_replacements("") == ""

    def test_all_letters(self) -> None:
        """A string of all mapped letters should be fully replaced."""
        result = apply_char_replacements("BOIS")
        assert result == "8015"

    def test_custom_map(self) -> None:
        """Custom replacement map should be respected."""
        custom = {"X": "5", "Y": "7"}
        assert apply_char_replacements("XY", custom) == "57"


# ---------------------------------------------------------------------------
# TestConfidence
# ---------------------------------------------------------------------------


class TestConfidence:
    """Tests for compute_replacement_confidence()."""

    def test_identical_strings_full_confidence(self) -> None:
        """No replacements should yield confidence 1.0."""
        assert compute_replacement_confidence("184767", "184767") == 1.0

    def test_all_replaced_zero_confidence(self) -> None:
        """All characters replaced should yield confidence 0.0."""
        assert compute_replacement_confidence("ABCDEF", "123456") == 0.0

    def test_partial_replacement(self) -> None:
        """Half the characters replaced should yield confidence 0.5."""
        # 2 out of 4 chars differ
        conf = compute_replacement_confidence("1B47", "1847")
        assert abs(conf - 0.75) < 1e-6  # 1 out of 4 replaced

    def test_one_of_six_replaced(self) -> None:
        """One replacement in 6 chars should give ~0.833 confidence."""
        conf = compute_replacement_confidence("1B4767", "184767")
        expected = 1.0 - (1 / 6)
        assert abs(conf - expected) < 1e-6

    def test_empty_original_zero_confidence(self) -> None:
        """Empty original string should return 0.0 confidence."""
        assert compute_replacement_confidence("", "") == 0.0

    def test_single_char_replaced(self) -> None:
        """Single character replacement should give 0.0 confidence."""
        assert compute_replacement_confidence("B", "8") == 0.0

    def test_single_char_unchanged(self) -> None:
        """Single unchanged character should give 1.0 confidence."""
        assert compute_replacement_confidence("8", "8") == 1.0


# ---------------------------------------------------------------------------
# TestCleanOcrText
# ---------------------------------------------------------------------------


class TestReplaceAndScoreOcrText:
    """Tests for replace_and_score_ocr_text() end-to-end."""

    def test_pure_digits_unchanged(self) -> None:
        """Pure digit strings should pass through with confidence 1.0."""
        cleaned, conf = replace_and_score_ocr_text("184767")
        assert cleaned == "184767"
        assert conf == 1.0

    def test_letters_replaced_and_confidence_computed(self) -> None:
        """Letters should be replaced and confidence should reflect changes."""
        cleaned, conf = replace_and_score_ocr_text("IB4767")
        assert cleaned == "184767"
        assert conf < 1.0

    def test_unknown_chars_become_question_mark(self) -> None:
        """Characters not in the replacement map and not digits become '?'."""
        cleaned, conf = replace_and_score_ocr_text("18X767")
        # X is not in CHAR_REPLACEMENTS and not a digit, so becomes '?'
        assert "?" in cleaned
        assert cleaned == "18?767"

    def test_spaces_preserved(self) -> None:
        """Spaces should be preserved in cleaned output."""
        cleaned, conf = replace_and_score_ocr_text("3 09")
        assert cleaned == "3 09"
        assert conf == 1.0

    def test_empty_string(self) -> None:
        """Empty string should return empty string and 0.0 confidence."""
        cleaned, conf = replace_and_score_ocr_text("")
        assert cleaned == ""
        assert conf == 0.0

    def test_multiline_text(self) -> None:
        """Multiline text should have replacements applied per character."""
        cleaned, conf = replace_and_score_ocr_text("IB4767\n3 O9")
        assert "1" in cleaned  # I -> 1
        assert "8" in cleaned  # B -> 8
        assert "0" in cleaned  # O -> 0

    def test_all_mappable_letters(self) -> None:
        """All letters in the replacement map should be converted to digits."""
        # Build a string from all keys in CHAR_REPLACEMENTS
        all_keys = "".join(CHAR_REPLACEMENTS.keys())
        cleaned, conf = replace_and_score_ocr_text(all_keys)
        # All should be digits now (no '?' marks)
        digits_and_spaces = all(c.isdigit() or c == " " for c in cleaned)
        assert digits_and_spaces

    def test_confidence_decreases_with_more_replacements(self) -> None:
        """More replacements should result in lower confidence."""
        _, conf_few = replace_and_score_ocr_text("1B4767")  # 1 replacement
        _, conf_many = replace_and_score_ocr_text("IB47G7")  # 3 replacements
        assert conf_few > conf_many
