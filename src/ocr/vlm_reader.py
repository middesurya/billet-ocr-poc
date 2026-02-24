"""Claude Vision API integration for billet stamp reading and ground truth extraction.

This module is the VLM fallback path in the two-stage OCR pipeline. It is only
invoked when PaddleOCR confidence falls below OCR_CONFIDENCE_THRESHOLD, or when
running ground truth extraction over a raw image set.

Rules enforced here:
- Temperature is always 0.0 for deterministic output.
- Raw images (not CLAHE-preprocessed) are preferred for VLM input.
- Every API call is logged with image name, truncated response, and cost estimate.
- Transient API errors (rate limit, connection, server) are retried with backoff.
- On any permanent API or parse error, an empty BilletReading is returned (never raises).
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

# Load .env file from project root (for ANTHROPIC_API_KEY)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import anthropic
import cv2
import httpx
import numpy as np
from loguru import logger

from src.config import VLM_MAX_TOKENS, VLM_MODEL, VLM_PROMPT_VERSION, VLM_TEMPERATURE
from src.models import BilletReading, OCRMethod

# ---------------------------------------------------------------------------
# Cost estimation constants (claude-sonnet-4-5-20250929 pricing, Feb 2026).
# Input:  $3.00 / 1M tokens   Output: $15.00 / 1M tokens
# A typical billet image encodes to ~1 500 input tokens (image + prompt).
# ---------------------------------------------------------------------------
_INPUT_COST_PER_TOKEN = 3.00 / 1_000_000
_OUTPUT_COST_PER_TOKEN = 15.00 / 1_000_000

# Mapping from Claude's textual confidence labels to numeric scores.
# Used as fallback when the VLM returns text labels instead of floats.
_CONFIDENCE_MAP: dict[str, float] = {
    "high": 0.95,
    "medium": 0.75,
    "low": 0.50,
}

# Retry configuration for transient API errors.
_MAX_RETRIES = 3
_BASE_DELAY_S = 1.0  # seconds; doubles each retry (exponential backoff)

# Transient error types that warrant a retry.
_RETRYABLE_ERRORS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def encode_image_to_base64(
    image: Union[str, Path, np.ndarray],
) -> tuple[str, str]:
    """Encode an image to a base64 string suitable for the Claude Vision API.

    For file paths the raw file bytes are read directly so the original
    compression/format is preserved.  For numpy arrays the image is encoded
    as a JPEG in memory (quality 95).

    Args:
        image: Absolute file path (str or Path) or BGR/RGB numpy array.

    Returns:
        A 2-tuple of (base64_string, media_type) where media_type is one of
        ``"image/jpeg"``, ``"image/png"``, or ``"image/bmp"``.

    Raises:
        ValueError: If the file extension is not in SUPPORTED_FORMATS or the
            numpy array cannot be encoded.
        FileNotFoundError: If a path is given but the file does not exist.
    """
    if isinstance(image, np.ndarray):
        success, buffer = cv2.imencode(
            ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95]
        )
        if not success:
            raise ValueError("cv2.imencode failed for the supplied numpy array.")
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return b64, "image/jpeg"

    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    suffix = path.suffix.lower()
    _EXT_TO_MIME: dict[str, str] = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
    }
    media_type = _EXT_TO_MIME.get(suffix, "image/jpeg")
    raw_bytes = path.read_bytes()

    # Anthropic API has a 5 MB base64 limit.  Large PNGs/BMPs easily exceed
    # this, so fall back to JPEG compression when the payload is too big.
    _MAX_BASE64_BYTES = 5_000_000  # ~3.75 MB raw → ~5 MB base64
    if len(raw_bytes) > _MAX_BASE64_BYTES:
        logger.debug(
            f"[VLM] File {path.name} is {len(raw_bytes)} bytes — "
            f"re-encoding as JPEG to stay under 5 MB API limit"
        )
        img_array = cv2.imread(str(path))
        if img_array is None:
            raise ValueError(f"cv2.imread failed for {path}")
        success, buffer = cv2.imencode(
            ".jpg", img_array, [cv2.IMWRITE_JPEG_QUALITY, 95]
        )
        if not success:
            raise ValueError(f"cv2.imencode failed for {path}")
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return b64, "image/jpeg"

    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return b64, media_type


def build_billet_ocr_prompt(version: int = VLM_PROMPT_VERSION) -> str:
    """Return the carefully engineered prompt for billet stamp recognition.

    Args:
        version: Prompt version to use.
            ``1`` — original prompt with basic OCR instructions.
            ``2`` — chain-of-thought prompt with analysis steps and
            more precise domain terminology (PIN-MATRIX, dot indentations).

    Returns:
        A multi-line prompt string ready to be used as the text part of a
        Claude Vision API message.
    """
    if version == 1:
        return _PROMPT_V1
    if version == 3:
        return _PROMPT_V3
    return _PROMPT_V2


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_PROMPT_V1 = (
    "You are reading stamped identification codes on a steel billet end face.\n"
    "The stamps are dot-matrix style (made of small dots) on grey/oxidized steel.\n"
    "Ignore any yellow paint markings — read only the stamped dots.\n"
    "\n"
    "Format:\n"
    "- Line 1: 6-digit HEAT NUMBER (digits only, e.g., 184767)\n"
    "- Line 2: STRAND (1 digit) + SEQUENCE (1-2 digits), may have spaces\n"
    "\n"
    "Rules:\n"
    "- Characters are ONLY digits 0-9\n"
    "- Common confusions: O looks like 0, I looks like 1, B looks like 8\n"
    "- If you cannot read a character with confidence, use '?' as placeholder\n"
    "- Always return your best reading even if uncertain\n"
    "\n"
    "Return ONLY a JSON object:\n"
    '{"heat_number": "XXXXXX", "strand": "X", "sequence": "XX", '
    '"confidence": 0.XX, "raw_text": "full text as seen"}'
)

_PROMPT_V2 = (
    "You are an expert OCR system reading stamped identification codes on a "
    "steel billet end face.\n"
    "\n"
    "The stamps are PIN-MATRIX style — each character is formed by small "
    "circular dot indentations arranged in a grid pattern on grey/oxidized "
    "steel. The dots are subtle and may be partially obscured by rust, scale, "
    "or surface texture.\n"
    "\n"
    "Ignore any yellow/colored paint markings — read ONLY the pin-stamped "
    "dot patterns.\n"
    "\n"
    "LAYOUT:\n"
    "- Line 1 (top): 6-digit HEAT NUMBER (e.g., 192435, 184767)\n"
    "- Line 2 (bottom): STRAND (1 digit) + space + SEQUENCE (1-2 digits, "
    'e.g., "1 07", "3 12")\n'
    "\n"
    "ANALYSIS STEPS:\n"
    "1. Locate the stamped region on the billet face\n"
    "2. Identify each character by its dot pattern — characters are ONLY "
    "digits 0-9\n"
    "3. Common dot-pattern confusions: 3↔8, 5↔6, 0↔8, 1↔7\n"
    "4. If a character is unclear, use '?' as placeholder\n"
    "5. Count: Line 1 should have exactly 6 digits\n"
    "\n"
    "Return ONLY this JSON (no explanation, no markdown):\n"
    '{"heat_number": "XXXXXX", "strand": "X", "sequence": "XX", '
    '"confidence": 0.XX, "raw_text": "full text as seen"}'
)

_PROMPT_V3 = (
    "You are an expert OCR system reading identification numbers painted or "
    "stamped on steel billet end faces.\n"
    "\n"
    "The numbers may be:\n"
    "- White paint stenciled characters\n"
    "- Dot-matrix / pin-matrix stamped indentations\n"
    "- Any printed/marked numbers on the square cross-section face\n"
    "\n"
    "TYPICAL LAYOUT (varies by mill):\n"
    "- Line 1 (top): HEAT NUMBER — typically 5-6 digits (e.g., 60008, 184767)\n"
    "- Line 2 (bottom): SEQUENCE/STRAND — typically 2-4 digits (e.g., 5383, 3 09)\n"
    "\n"
    "ANALYSIS STEPS:\n"
    "1. Locate the stamped/painted region on the billet face\n"
    "2. Read each character carefully — characters are primarily digits 0-9\n"
    "3. If there are multiple billets visible, read the LARGEST / most centered one\n"
    "4. If a character is unclear, use '?' as placeholder\n"
    "\n"
    "Return ONLY this JSON (no explanation, no markdown):\n"
    '{"heat_number": "XXXXX", "strand": null, "sequence": "XXXX", '
    '"confidence": 0.XX, "raw_text": "full text as seen", '
    '"all_text": ["line1", "line2"]}'
)


def read_billet_with_vlm(
    image: Union[str, Path, np.ndarray],
    model: str = VLM_MODEL,
    temperature: float = VLM_TEMPERATURE,
    max_tokens: int = VLM_MAX_TOKENS,
) -> BilletReading:
    """Send a billet image to Claude Vision and return a structured BilletReading.

    This is the primary entry point for the VLM fallback path.  It encodes the
    image, constructs the API request, parses the JSON response, and maps the
    result to a BilletReading dataclass.

    Transient API errors (rate limit, connection, server) are retried up to
    ``_MAX_RETRIES`` times with exponential backoff.  Permanent errors (auth,
    bad request) fail immediately.

    Temperature is locked to 0.0 unless overridden explicitly in tests. Raw
    images are preferred over CLAHE-preprocessed images for VLM input.

    Args:
        image: Absolute file path (str or Path) or BGR numpy array.  Passing
            the raw image (not CLAHE-processed) yields better VLM accuracy.
        model: Claude model ID to use.  Defaults to ``VLM_MODEL`` from config.
        temperature: Sampling temperature.  Must be 0.0 for deterministic OCR.
        max_tokens: Maximum tokens in the completion.

    Returns:
        A BilletReading with ``method=OCRMethod.VLM_CLAUDE``.  On failure an
        empty BilletReading with ``confidence=0.0`` is returned.
    """
    image_name = _image_label(image)
    logger.info(f"[VLM] Starting Claude Vision call | image={image_name} | model={model}")

    try:
        b64_data, media_type = encode_image_to_base64(image)
    except (ValueError, FileNotFoundError) as exc:
        logger.error(f"[VLM] Image encoding failed | image={image_name} | error={exc}")
        return BilletReading(method=OCRMethod.VLM_CLAUDE)

    prompt_text = build_billet_ocr_prompt()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_data,
                    },
                },
                {"type": "text", "text": prompt_text},
            ],
        }
    ]

    response = _call_api_with_retry(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
        image_name=image_name,
        log_prefix="[VLM]",
    )
    if response is None:
        return BilletReading(method=OCRMethod.VLM_CLAUDE)

    # Extract raw text content from the response.
    raw_content = response.content[0].text if response.content else ""

    # Estimate cost from usage tokens.
    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0
    estimated_cost = (
        input_tokens * _INPUT_COST_PER_TOKEN
        + output_tokens * _OUTPUT_COST_PER_TOKEN
    )

    logger.info(
        f"[VLM] API response received | image={image_name} | "
        f"input_tokens={input_tokens} | output_tokens={output_tokens} | "
        f"estimated_cost_usd=${estimated_cost:.5f} | "
        f"raw_response={raw_content[:200]!r}"
    )

    parsed = _parse_vlm_json(raw_content, image_name)
    if parsed is None:
        return BilletReading(method=OCRMethod.VLM_CLAUDE)

    confidence_score = _parse_confidence(parsed)
    raw_texts = _extract_raw_texts(parsed)

    reading = BilletReading(
        heat_number=_str_or_none(parsed.get("heat_number")),
        strand=_str_or_none(parsed.get("strand")),
        sequence=_str_or_none(parsed.get("sequence")),
        confidence=confidence_score,
        method=OCRMethod.VLM_CLAUDE,
        raw_texts=raw_texts,
    )

    logger.info(
        f"[VLM] Parsed result | image={image_name} | "
        f"heat={reading.heat_number} | strand={reading.strand} | "
        f"seq={reading.sequence} | confidence={confidence_score:.2f}"
    )
    return reading


def read_billet_with_vlm_for_ground_truth(
    image: Union[str, Path, np.ndarray],
) -> dict:
    """Run Claude Vision on a billet image and return the full response dict.

    Unlike :func:`read_billet_with_vlm` this function returns the raw parsed
    JSON dict (including ``raw_text``, ``confidence`` fields) so that the
    ground truth extraction script can persist all metadata.

    Uses the same retry logic and timeout as :func:`read_billet_with_vlm`.

    Args:
        image: Absolute file path (str or Path) or BGR numpy array.

    Returns:
        The parsed JSON dictionary from Claude's response.  On failure an empty
        dict is returned.  Keys: ``heat_number``, ``strand``, ``sequence``,
        ``confidence``, ``raw_text``.
    """
    image_name = _image_label(image)
    logger.info(
        f"[VLM-GT] Ground truth extraction call | image={image_name}"
    )

    try:
        b64_data, media_type = encode_image_to_base64(image)
    except (ValueError, FileNotFoundError) as exc:
        logger.error(
            f"[VLM-GT] Image encoding failed | image={image_name} | error={exc}"
        )
        return {}

    prompt_text = build_billet_ocr_prompt()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_data,
                    },
                },
                {"type": "text", "text": prompt_text},
            ],
        }
    ]

    response = _call_api_with_retry(
        model=VLM_MODEL,
        max_tokens=VLM_MAX_TOKENS,
        temperature=VLM_TEMPERATURE,
        messages=messages,
        image_name=image_name,
        log_prefix="[VLM-GT]",
    )
    if response is None:
        return {}

    raw_content = response.content[0].text if response.content else ""

    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0
    estimated_cost = (
        input_tokens * _INPUT_COST_PER_TOKEN
        + output_tokens * _OUTPUT_COST_PER_TOKEN
    )

    logger.info(
        f"[VLM-GT] API response received | image={image_name} | "
        f"input_tokens={input_tokens} | output_tokens={output_tokens} | "
        f"estimated_cost_usd=${estimated_cost:.5f} | "
        f"raw_response={raw_content[:200]!r}"
    )

    parsed = _parse_vlm_json(raw_content, image_name)
    if parsed is None:
        return {}

    logger.info(
        f"[VLM-GT] Parsed result | image={image_name} | data={parsed}"
    )
    return parsed


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _call_api_with_retry(
    *,
    model: str,
    max_tokens: int,
    temperature: float,
    messages: list[dict],
    image_name: str,
    log_prefix: str,
) -> "anthropic.types.Message | None":
    """Call the Anthropic API with retry logic for transient errors.

    Retries up to ``_MAX_RETRIES`` times on rate-limit, connection, and
    internal-server errors using exponential backoff.  Permanent errors
    (authentication, bad request) fail immediately.

    Args:
        model: Claude model ID.
        max_tokens: Maximum tokens in the completion.
        temperature: Sampling temperature.
        messages: The messages payload for the API call.
        image_name: Short label for log messages.
        log_prefix: Log line prefix, e.g. ``"[VLM]"`` or ``"[VLM-GT]"``.

    Returns:
        The API response on success, or ``None`` on exhausted retries / error.
    """
    client = anthropic.Anthropic(
        timeout=httpx.Timeout(60.0, connect=10.0),
    )

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            t0 = time.perf_counter()
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                f"{log_prefix} API call complete | image={image_name} | "
                f"attempt={attempt + 1} | elapsed_ms={elapsed_ms:.0f}"
            )
            return response

        except _RETRYABLE_ERRORS as exc:
            last_exc = exc
            delay = _BASE_DELAY_S * (2 ** attempt)
            logger.warning(
                f"{log_prefix} Transient API error (attempt {attempt + 1}/{_MAX_RETRIES}) | "
                f"image={image_name} | error={exc} | retrying in {delay:.1f}s"
            )
            time.sleep(delay)

        except anthropic.APIError as exc:
            # Permanent error — do not retry.
            logger.error(
                f"{log_prefix} Permanent API error | image={image_name} | error={exc}"
            )
            return None

        except Exception as exc:
            logger.error(
                f"{log_prefix} Unexpected error during API call | "
                f"image={image_name} | error={exc}"
            )
            return None

    logger.error(
        f"{log_prefix} All {_MAX_RETRIES} retries exhausted | "
        f"image={image_name} | last_error={last_exc}"
    )
    return None


def _parse_confidence(parsed: dict) -> float:
    """Extract a numeric confidence score from the parsed VLM response.

    Supports two schemas:
    - New: ``"confidence": 0.85`` (float)
    - Legacy: ``"confidence": "high"`` (text label mapped via ``_CONFIDENCE_MAP``)

    The result is clamped to [0.0, 1.0].

    Args:
        parsed: Parsed JSON dict from the VLM response.

    Returns:
        Float confidence in [0.0, 1.0].
    """
    raw = parsed.get("confidence", 0.5)

    # Try numeric first (new prompt format).
    if isinstance(raw, (int, float)):
        return max(0.0, min(1.0, float(raw)))

    # Fall back to text label (legacy format).
    if isinstance(raw, str):
        # Try parsing as a numeric string first (e.g. "0.85").
        try:
            return max(0.0, min(1.0, float(raw)))
        except ValueError:
            pass
        return _CONFIDENCE_MAP.get(raw.strip().lower(), 0.50)

    return 0.50


def _extract_raw_texts(parsed: dict) -> list[str]:
    """Extract raw text lines from the parsed VLM response.

    Supports two schemas:
    - New: ``"raw_text": "184767\\n3 09"`` (single string)
    - Legacy: ``"all_text": ["184767", "3 09"]`` (list of strings)

    Args:
        parsed: Parsed JSON dict from the VLM response.

    Returns:
        List of text line strings.
    """
    # Try new schema first.
    raw_text = parsed.get("raw_text")
    if isinstance(raw_text, str) and raw_text.strip():
        return [line.strip() for line in raw_text.split("\n") if line.strip()]

    # Fall back to legacy schema.
    all_text = parsed.get("all_text", [])
    if isinstance(all_text, list):
        return [str(t) for t in all_text if t]

    return []


def _image_label(image: Union[str, Path, np.ndarray]) -> str:
    """Return a short label identifying the image source for log messages.

    Args:
        image: File path or numpy array.

    Returns:
        The filename stem (for paths) or ``"<numpy_array>"`` for arrays.
    """
    if isinstance(image, np.ndarray):
        return "<numpy_array>"
    return Path(image).name


def _parse_vlm_json(raw_text: str, image_name: str) -> dict | None:
    """Extract and parse the JSON object from Claude's raw response text.

    Claude occasionally wraps its JSON in markdown code fences even when
    instructed not to.  This function strips those fences before parsing.

    Args:
        raw_text: The raw string returned by the Claude API.
        image_name: Image label used in log messages.

    Returns:
        Parsed dict on success, or ``None`` if parsing fails.
    """
    if not raw_text.strip():
        logger.warning(f"[VLM] Empty response | image={image_name}")
        return None

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    clean = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()

    # If the response contains extra text before/after the JSON object,
    # isolate the first {...} block.
    json_match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not json_match:
        logger.warning(
            f"[VLM] No JSON object found in response | image={image_name} | "
            f"raw={raw_text[:300]!r}"
        )
        return None

    json_str = json_match.group(0)
    try:
        parsed: dict = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as exc:
        logger.warning(
            f"[VLM] JSON parse error | image={image_name} | "
            f"error={exc} | json_str={json_str[:300]!r}"
        )
        return None


def _str_or_none(value: object) -> str | None:
    """Convert a value to a stripped string, or None for falsy/null values.

    Args:
        value: Any value from the parsed JSON dict.

    Returns:
        Stripped string, or ``None`` if the value is falsy or the string
        ``"null"`` / ``"none"``.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in {"", "null", "none", "n/a", "unknown"}:
        return None
    return s
