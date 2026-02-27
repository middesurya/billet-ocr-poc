"""Format-aware post-processing for Florence-2 and multi-billet OCR output.

Florence-2 often reads ALL billet stamps visible in the frame, producing
concatenated text with 7+ digits when the ground truth is only 5 digits.
This module extracts the most likely heat number from noisy multi-billet
output using format validation and positional heuristics.

Strategy:
    1. Apply character confusion correction (O->0, B->8, etc.)
    2. Extract all 5-7 digit substrings from the raw text
    3. Score candidates by position (center of text = most likely target)
    4. Return the best candidate matching the expected billet number format
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger

from src.postprocess.validator import CHAR_CONFUSION_MAP


def extract_heat_number_candidates(text: str) -> list[str]:
    """Extract all possible heat number candidates from OCR text.

    Finds all substrings of 5-7 consecutive digits, after applying
    character confusion correction and stripping non-alphanumeric noise.

    Args:
        text: Raw OCR output text (may contain multiple billet readings).

    Returns:
        List of digit-only strings, each 5-7 characters long.
    """
    if not text:
        return []

    # Apply character confusion correction
    corrected = "".join(CHAR_CONFUSION_MAP.get(c, c) for c in text)

    # Remove everything except digits and whitespace
    digits_and_spaces = re.sub(r"[^\d\s]", "", corrected)

    # Find all runs of 5-7 consecutive digits
    candidates = re.findall(r"\d{5,7}", digits_and_spaces)

    # Also try joining adjacent short digit groups (e.g., "600 08" -> "60008")
    # This handles cases where OCR inserts spaces within a number
    collapsed = re.sub(r"\s+", "", digits_and_spaces)
    collapsed_candidates = re.findall(r"\d{5,7}", collapsed)

    # For 6-7 digit matches, also extract the 5-digit prefix as a candidate.
    # Florence-2 often appends extra digits from adjacent billets, but the
    # correct heat number is almost always at the start (93% of cases).
    prefix_candidates: list[str] = []
    for c in candidates + collapsed_candidates:
        if len(c) > 5:
            prefix_candidates.append(c[:5])

    # Merge all lists, preserving order, removing duplicates
    seen = set()
    all_candidates = []
    for c in candidates + collapsed_candidates + prefix_candidates:
        if c not in seen:
            seen.add(c)
            all_candidates.append(c)

    return all_candidates


def score_candidate_by_position(
    candidate: str,
    full_text: str,
) -> float:
    """Score a candidate heat number by its position in the text.

    Numbers appearing near the center of the output text are more likely
    to be the target billet (the one the camera was focused on). Numbers
    at the start or end are more likely to be adjacent billets.

    Args:
        candidate: A heat number candidate string.
        full_text: The full OCR output text.

    Returns:
        Score in [0.0, 1.0] where 1.0 means perfectly centered.
    """
    if not full_text or candidate not in full_text:
        return 0.0

    # Find the candidate position in the text
    idx = full_text.find(candidate)
    if idx < 0:
        return 0.0

    center_of_candidate = idx + len(candidate) / 2
    center_of_text = len(full_text) / 2

    # Distance from center, normalized to [0, 1]
    max_distance = len(full_text) / 2
    if max_distance == 0:
        return 1.0

    distance = abs(center_of_candidate - center_of_text) / max_distance
    return max(0.0, 1.0 - distance)


def extract_best_heat_number(
    raw_text: str,
    expected_length: Optional[int] = None,
) -> Optional[str]:
    """Extract the most likely heat number from noisy OCR output.

    Applies format validation and positional scoring to select the best
    candidate from multi-billet output.

    Args:
        raw_text: Raw OCR output text from Florence-2 or any engine.
        expected_length: If known, prefer candidates of this exact length.
            Common values: 5 (Roboflow dataset), 6 (original dot-matrix).

    Returns:
        Best heat number candidate, or None if no valid candidate found.
    """
    candidates = extract_heat_number_candidates(raw_text)

    if not candidates:
        logger.debug(f"[FormatValidator] No candidates in: {raw_text!r}")
        return None

    if len(candidates) == 1:
        candidate = candidates[0]
        # If single candidate is 6-7 digits, prefer the 5-digit prefix
        # (Roboflow heat numbers are always 5 digits)
        if len(candidate) > 5 and (expected_length is None or expected_length == 5):
            candidate = candidate[:5]
        logger.debug(
            f"[FormatValidator] Single candidate: {candidate} "
            f"from: {raw_text!r}"
        )
        return candidate

    # Score each candidate
    scored = []
    # Apply confusion correction to get a clean version for position matching
    corrected_text = "".join(CHAR_CONFUSION_MAP.get(c, c) for c in raw_text)

    for candidate in candidates:
        position_score = score_candidate_by_position(candidate, corrected_text)
        length_score = 0.0

        if expected_length is not None:
            # Prefer exact length match
            if len(candidate) == expected_length:
                length_score = 1.0
            else:
                length_score = 0.5
        else:
            # Without expected length, strongly prefer 5-digit (Roboflow) format.
            # Florence-2 often appends extra digits from adjacent billets, so
            # 6-7 digit outputs are almost always wrong — the correct heat is
            # at the start (prefix).
            if len(candidate) == 5:
                length_score = 1.0
            elif len(candidate) == 6:
                length_score = 0.4
            else:
                length_score = 0.2

        # Combined score: position matters more than length
        total_score = 0.6 * position_score + 0.4 * length_score
        scored.append((candidate, total_score, position_score, length_score))

    # Sort by total score descending
    scored.sort(key=lambda x: -x[1])

    best = scored[0]
    logger.debug(
        f"[FormatValidator] {len(candidates)} candidates from: {raw_text!r}"
    )
    for cand, total, pos, length in scored:
        logger.debug(
            f"  candidate={cand} total={total:.2f} "
            f"pos={pos:.2f} len={length:.2f}"
        )

    logger.info(
        f"[FormatValidator] Selected '{best[0]}' (score={best[1]:.2f}) "
        f"from {len(candidates)} candidates"
    )
    return best[0]


def validate_florence2_output(
    raw_text: str,
    parsed_heat: Optional[str],
    expected_length: Optional[int] = None,
) -> Optional[str]:
    """Validate and potentially fix a Florence-2 parsed heat number.

    If the parsed heat number looks wrong (wrong length, contains letters,
    etc.), re-extracts from the raw text using format-aware heuristics.

    Args:
        raw_text: The full raw OCR output from Florence-2.
        parsed_heat: The heat number as parsed by florence2_reader.
        expected_length: Expected heat number length if known.

    Returns:
        Corrected heat number, or None if unrecoverable.
    """
    # If parsed heat is an exact 5-digit match, accept it immediately.
    # For 6-7 digits, fall through to extract_best_heat_number() which will
    # extract the 5-digit prefix — Florence-2 often appends extra digits
    # from adjacent billets in the crop.
    if parsed_heat and re.match(r"^\d{5}$", parsed_heat):
        if expected_length is None or len(parsed_heat) == expected_length:
            return parsed_heat
    # Also accept if expected_length is explicitly 6 or 7 and matches
    if (
        parsed_heat
        and expected_length is not None
        and re.match(r"^\d+$", parsed_heat)
        and len(parsed_heat) == expected_length
    ):
        return parsed_heat

    # Re-extract from raw text
    best = extract_best_heat_number(raw_text, expected_length)
    if best is not None:
        if parsed_heat and parsed_heat != best:
            logger.info(
                f"[FormatValidator] Corrected '{parsed_heat}' -> '{best}' "
                f"from raw: {raw_text!r}"
            )
        return best

    # Last resort: return the parsed heat if it's at least digits
    if parsed_heat and re.match(r"^\d+$", parsed_heat):
        return parsed_heat

    return None


def extract_heat_and_sequence(raw_text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract both heat number and sequence from raw OCR text.

    Recovers the sequence suffix when a 5-digit heat is extracted from a
    longer digit string. For example:
        "612535383" → heat="61253", sequence="5383"
        "60008 5383" → heat="60008", sequence="5383"

    Args:
        raw_text: Raw OCR output text.

    Returns:
        Tuple of (heat_number, sequence). Either may be None.
    """
    if not raw_text:
        return None, None

    # Apply character confusion correction
    corrected = "".join(CHAR_CONFUSION_MAP.get(c, c) for c in raw_text)

    # Remove non-digit/non-whitespace
    digits_and_spaces = re.sub(r"[^\d\s]", "", corrected)
    collapsed = re.sub(r"\s+", "", digits_and_spaces)

    # Case 1: 8-10 digit concatenated string → split at position 5
    if re.match(r"^\d{8,10}$", collapsed):
        heat = collapsed[:5]
        seq = collapsed[5:]
        # Only return sequence if it looks like 3-4 digits
        if re.match(r"^\d{3,4}$", seq):
            logger.debug(
                f"[FormatValidator] Split concat: '{collapsed}' → heat={heat} seq={seq}"
            )
            return heat, seq
        return heat, None

    # Case 2: space-separated tokens — look for 5-digit heat + 3-4 digit seq
    tokens = digits_and_spaces.split()
    heat: Optional[str] = None
    sequence: Optional[str] = None

    for token in tokens:
        if heat is None and re.match(r"^\d{5}$", token):
            heat = token
        elif heat is not None and sequence is None and re.match(r"^\d{3,4}$", token):
            sequence = token
            break
        elif heat is None and re.match(r"^\d{6,7}$", token):
            # Longer heat candidate — extract 5-digit prefix, suffix = seq
            heat = token[:5]
            suffix = token[5:]
            if re.match(r"^\d{1,2}$", suffix):
                sequence = suffix
            break

    return heat, sequence
