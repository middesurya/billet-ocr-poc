"""Format validation and character confusion correction for billet OCR results.

Applies domain-specific post-processing to raw OCR text:
- Character-level confusion map (e.g. ``O`` → ``0``, ``I`` → ``1``)
- Regex-based format validation for heat numbers, strand IDs, and sequences
- Full pipeline that cleans, corrects, and validates a :class:`~src.models.BilletReading`
"""

import re
import string
from typing import Optional

from loguru import logger

from src.config import HEAT_NUMBER_PATTERN, SEQUENCE_PATTERN, STRAND_PATTERN
from src.models import BilletReading, OCRMethod

# ---------------------------------------------------------------------------
# Character confusion map
# ---------------------------------------------------------------------------

#: Common OCR mis-reads in dot-matrix / industrial stamp contexts.
#: Keys are the wrongly-recognised character; values are the correct digit.
CHAR_CONFUSION_MAP: dict[str, str] = {
    "O": "0",
    "o": "0",
    "I": "1",
    "l": "1",
    "|": "1",
    "Z": "2",
    "z": "2",
    "A": "4",
    "S": "5",
    "s": "5",
    "G": "6",
    "b": "6",
    "T": "7",
    "B": "8",
    "g": "9",
    "q": "9",
    "D": "0",
    "Q": "0",
}

# Pre-compiled patterns for performance.
_HEAT_RE = re.compile(HEAT_NUMBER_PATTERN)
_STRAND_RE = re.compile(STRAND_PATTERN)
_SEQ_RE = re.compile(SEQUENCE_PATTERN)

# Characters we consider "stray punctuation / OCR artifacts" to strip.
# We keep digits, letters, and plain spaces.
_ARTIFACT_CHARS = set(string.punctuation) - {" "}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def correct_character_confusion(
    text: str,
    confusion_map: dict[str, str] = CHAR_CONFUSION_MAP,
) -> str:
    """Replace characters that are commonly mis-recognised by OCR engines.

    Each character in *text* is looked up in *confusion_map*; if found it is
    replaced with the mapped value.  Characters not in the map pass through
    unchanged.

    Args:
        text: Raw OCR text string to correct.
        confusion_map: Mapping from mis-recognised character to correct
            character.  Defaults to :data:`CHAR_CONFUSION_MAP`.

    Returns:
        Corrected text string.
    """
    if not text:
        return text
    corrected = "".join(confusion_map.get(ch, ch) for ch in text)
    if corrected != text:
        logger.debug(
            'Confusion correction: "{before}" → "{after}"',
            before=text,
            after=corrected,
        )
    return corrected


def validate_heat_number(text: str) -> bool:
    """Validate that *text* matches the expected heat-number format.

    A valid heat number is 5–7 consecutive digits (no spaces).

    Args:
        text: Text to validate.

    Returns:
        ``True`` if *text* matches :data:`~src.config.HEAT_NUMBER_PATTERN`,
        ``False`` otherwise.
    """
    if not text:
        return False
    return bool(_HEAT_RE.match(text))


def validate_strand(text: str) -> bool:
    """Validate that *text* is a single digit (strand identifier).

    Args:
        text: Text to validate.

    Returns:
        ``True`` if *text* matches :data:`~src.config.STRAND_PATTERN`.
    """
    if not text:
        return False
    return bool(_STRAND_RE.match(text))


def validate_sequence(text: str) -> bool:
    """Validate that *text* is a 1–3-digit sequence number.

    Args:
        text: Text to validate.

    Returns:
        ``True`` if *text* matches :data:`~src.config.SEQUENCE_PATTERN`.
    """
    if not text:
        return False
    return bool(_SEQ_RE.match(text))


def clean_ocr_text(text: str) -> str:
    """Strip leading/trailing whitespace and remove stray OCR artifact characters.

    Artifact characters are punctuation symbols that are unlikely to appear
    in billet stamp codes (e.g. ``@``, ``#``, ``*``).  Internal spaces are
    preserved so that strand/sequence token splitting still works.

    Args:
        text: Raw text from an OCR engine.

    Returns:
        Cleaned text string.
    """
    if not text:
        return text
    # Remove stray punctuation/artifact characters
    cleaned = "".join(ch for ch in text if ch not in _ARTIFACT_CHARS)
    # Collapse multiple consecutive spaces into one
    cleaned = re.sub(r" {2,}", " ", cleaned)
    cleaned = cleaned.strip()
    if cleaned != text:
        logger.debug(
            'Text cleaning: "{before}" → "{after}"',
            before=text,
            after=cleaned,
        )
    return cleaned


def validate_and_correct_reading(reading: BilletReading) -> BilletReading:
    """Apply the full post-processing pipeline to a :class:`~src.models.BilletReading`.

    Steps applied to each field (heat number, strand, sequence):
    1. ``clean_ocr_text`` – strip whitespace, remove artifact chars
    2. ``correct_character_confusion`` – apply the confusion map
    3. Format validation – log a warning for any field that fails

    The original *reading* is **not** mutated.  A new ``BilletReading`` is
    returned with all corrected values.

    Args:
        reading: Raw billet reading (typically from
            :func:`~src.ocr.paddle_ocr.extract_billet_info`).

    Returns:
        A new :class:`~src.models.BilletReading` with cleaned, corrected,
        and validated fields.  The ``method``, ``confidence``, and
        ``raw_texts`` fields are carried over from the original unchanged.
    """

    def _process(value: Optional[str], label: str) -> Optional[str]:
        """Clean → correct → return."""
        if value is None:
            return None
        cleaned = clean_ocr_text(value)
        corrected = correct_character_confusion(cleaned)
        return corrected

    new_heat = _process(reading.heat_number, "heat_number")
    new_strand = _process(reading.strand, "strand")
    new_seq = _process(reading.sequence, "sequence")

    # Validation with warnings
    if new_heat is not None and not validate_heat_number(new_heat):
        logger.warning(
            'Heat number "{v}" does not match expected pattern {p}.',
            v=new_heat,
            p=HEAT_NUMBER_PATTERN,
        )

    if new_strand is not None and not validate_strand(new_strand):
        logger.warning(
            'Strand "{v}" does not match expected pattern {p}.',
            v=new_strand,
            p=STRAND_PATTERN,
        )

    if new_seq is not None and not validate_sequence(new_seq):
        logger.warning(
            'Sequence "{v}" does not match expected pattern {p}.',
            v=new_seq,
            p=SEQUENCE_PATTERN,
        )

    corrected_reading = BilletReading(
        heat_number=new_heat,
        strand=new_strand,
        sequence=new_seq,
        confidence=reading.confidence,
        method=reading.method,
        raw_texts=list(reading.raw_texts),  # shallow copy, immutable pattern
    )

    logger.info(
        "validate_and_correct_reading: heat={h}, strand={s}, seq={q}",
        h=new_heat,
        s=new_strand,
        q=new_seq,
    )
    return corrected_reading
