"""Contextual character replacement and entropy-based confidence for OCR output.

Billet stamps contain only digits 0-9. Any letter in the OCR output is a
misread from dot-matrix pattern ambiguity. This module provides:

- Character replacement using the canonical map from validator.py
- Entropy-based confidence scoring (how many chars needed fixing)
- A combined replace-and-score function for Florence-2 output

Note: The character map is imported from ``src.postprocess.validator`` to
maintain a single source of truth. Both PaddleOCR and Florence-2 paths use
the same confusion corrections.
"""

import re

from loguru import logger

from src.postprocess.validator import CHAR_CONFUSION_MAP

# Re-export under the name used in this module for clarity.
# This is the same map as validator.CHAR_CONFUSION_MAP -- single source of truth.
CHAR_REPLACEMENTS = CHAR_CONFUSION_MAP


def apply_char_replacements(
    text: str,
    replacements: dict[str, str] = CHAR_REPLACEMENTS,
) -> str:
    """Replace known letter-to-digit confusions in OCR text.

    Args:
        text: Raw OCR text string.
        replacements: Mapping from misread character to correct digit.

    Returns:
        Text with all known confusions replaced.
    """
    if not text:
        return text
    return "".join(replacements.get(c, c) for c in text)


def compute_replacement_confidence(original: str, corrected: str) -> float:
    """Compute confidence based on how many characters needed replacement.

    A score of 1.0 means no replacements were needed (high confidence in the
    original OCR output). A score of 0.0 means every character was replaced
    (the OCR output was entirely wrong).

    Args:
        original: The raw OCR text before replacement.
        corrected: The text after character replacement.

    Returns:
        Float in [0.0, 1.0] representing replacement confidence.
    """
    if not original:
        return 0.0
    replacements = sum(1 for a, b in zip(original, corrected) if a != b)
    return 1.0 - (replacements / len(original))


def replace_and_score_ocr_text(raw_text: str) -> tuple[str, float]:
    """Replace common OCR letter-to-digit confusions and compute confidence.

    Named distinctly from ``validator.clean_ocr_text`` (which strips artifacts
    but does not score) to avoid shadowing.

    Steps:
    1. Apply character replacements (B->8, O->0, etc.)
    2. Replace any remaining non-digit, non-space characters with '?'
    3. Compute confidence from the number of replacements made

    Args:
        raw_text: Raw OCR output text.

    Returns:
        Tuple of (cleaned_text, confidence_score). The confidence score is
        in [0.0, 1.0] where 1.0 means no replacements were needed.
    """
    if not raw_text:
        return "", 0.0

    # Step 1: Apply known letter-to-digit replacements
    replaced = apply_char_replacements(raw_text)

    # Step 2: Replace any remaining non-digit, non-space chars with '?'
    cleaned = re.sub(r"[^\d\s]", "?", replaced)

    # Step 3: Compute confidence based on total changes from original
    confidence = compute_replacement_confidence(raw_text, cleaned)

    if cleaned != raw_text:
        logger.debug(
            f'char_replace: "{raw_text}" -> "{cleaned}" '
            f"(confidence={confidence:.2f})"
        )

    return cleaned, confidence
