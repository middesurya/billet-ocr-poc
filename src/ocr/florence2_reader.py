"""Florence-2 local VLM integration for billet stamp reading.

Microsoft Florence-2-base (0.23B params) provides zero-shot OCR via task
prompts (<OCR>, <OCR_WITH_REGION>). This module mirrors the interface of
vlm_reader.py so it can be used as a drop-in local alternative to Claude
Vision -- no API key required, runs entirely on CPU/GPU.

Key differences from vlm_reader.py:
- No API calls -- model runs locally via HuggingFace transformers
- Model loaded once via singleton pattern (~500MB download on first run)
- Uses torch for inference, not an HTTP client
- Output is raw text (not structured JSON) -- needs more parsing
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from loguru import logger

from src.config import (
    FLORENCE2_DEVICE,
    FLORENCE2_LORA_PATH,
    FLORENCE2_MAX_NEW_TOKENS,
    FLORENCE2_MODEL_ID,
    FLORENCE2_TASK,
    HEAT_NUMBER_PATTERN,
    MULTI_ORIENT_ANGLES,
    SEQUENCE_PATTERN,
    STRAND_PATTERN,
)
from src.models import BilletReading, OCRMethod
from src.postprocess.char_replace import replace_and_score_ocr_text

# ---------------------------------------------------------------------------
# Module-level singleton for model + processor
# ---------------------------------------------------------------------------

_model = None
_processor = None
_active_device: Optional[str] = None  # Track actual device after fallback


def _resolve_device() -> str:
    """Resolve the compute device, falling back to CPU if CUDA unavailable.

    Returns:
        Device string ('cuda' or 'cpu').
    """
    import torch

    device = FLORENCE2_DEVICE
    if device == "cuda" and not torch.cuda.is_available():
        logger.warning(
            "[Florence-2] CUDA requested but not available — falling back to CPU. "
            "Set FLORENCE2_DEVICE='cpu' in config.py to suppress this warning."
        )
        device = "cpu"
    return device


def _get_model_and_processor(
    model_id: str = FLORENCE2_MODEL_ID,
    lora_path: Optional[str] = FLORENCE2_LORA_PATH,
) -> tuple:
    """Load Florence-2 model and processor (singleton -- loads once).

    When ``lora_path`` is provided, loads LoRA adapter weights on top of
    the base model using the ``peft`` library.

    Args:
        model_id: HuggingFace model ID for Florence-2.
        lora_path: Path to LoRA adapter directory. None = zero-shot.

    Returns:
        Tuple of (model, processor).

    Raises:
        ImportError: If torch or transformers is not installed.
        RuntimeError: If model download or loading fails.
    """
    global _model, _processor, _active_device

    if _model is not None and _processor is not None:
        return _model, _processor

    import torch
    from transformers import AutoProcessor, Florence2ForConditionalGeneration

    logger.info(f"[Florence-2] Loading model: {model_id} (first run downloads ~500MB)")
    t0 = time.perf_counter()

    device = _resolve_device()
    _active_device = device
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    _model = Florence2ForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=dtype,
    )

    # Load LoRA adapter if provided
    if lora_path is not None:
        lora_dir = Path(lora_path)
        if lora_dir.exists():
            try:
                from peft import PeftModel

                logger.info(f"[Florence-2] Loading LoRA adapter from: {lora_path}")
                _model = PeftModel.from_pretrained(_model, lora_path)
                _model = _model.merge_and_unload()
                logger.info("[Florence-2] LoRA adapter merged successfully")
            except ImportError:
                logger.error(
                    "[Florence-2] peft not installed — cannot load LoRA adapter. "
                    "Install with: pip install peft>=0.14.0"
                )
            except Exception as exc:
                logger.error(f"[Florence-2] Failed to load LoRA adapter: {exc}")
        else:
            logger.warning(
                f"[Florence-2] LoRA path does not exist: {lora_path} — using base model"
            )

    _model.to(device)

    _processor = AutoProcessor.from_pretrained(model_id)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    lora_status = f" | lora={'yes' if lora_path else 'no'}"
    logger.info(
        f"[Florence-2] Model loaded | device={device} | "
        f"dtype={dtype}{lora_status} | elapsed_ms={elapsed_ms:.0f}"
    )

    return _model, _processor


def _prepare_pil_image(image: Union[str, Path, np.ndarray]):
    """Convert input image to PIL Image (RGB).

    Accepts file paths (str/Path) or numpy arrays (BGR from OpenCV).
    Florence-2 expects PIL Images in RGB format.

    Args:
        image: File path or BGR numpy array.

    Returns:
        PIL.Image.Image in RGB mode.

    Raises:
        FileNotFoundError: If a path is given but the file does not exist.
        ValueError: If the numpy array is invalid.
    """
    from PIL import Image

    if isinstance(image, np.ndarray):
        # OpenCV uses BGR; convert to RGB for PIL
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif len(image.shape) == 2:
            # Grayscale -- convert to RGB
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb = image
        return Image.fromarray(rgb)

    path = Path(image)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    return Image.open(path).convert("RGB")


def _run_florence2_inference(
    pil_image,
    task: str = FLORENCE2_TASK,
    model_id: str = FLORENCE2_MODEL_ID,
) -> dict:
    """Run Florence-2 inference on a PIL image with a task prompt.

    Args:
        pil_image: PIL Image in RGB mode.
        task: Florence-2 task prompt (e.g., "<OCR>", "<OCR_WITH_REGION>").
        model_id: HuggingFace model ID.

    Returns:
        Dict with task-specific output. For <OCR>: {'<OCR>': 'text string'}.
        For <OCR_WITH_REGION>: bounding boxes + labels.
    """
    import torch

    model, processor = _get_model_and_processor(model_id)
    device = _active_device or _resolve_device()

    inputs = processor(
        text=task,
        images=pil_image,
        return_tensors="pt",
    )
    # Move inputs to the same device and dtype as model
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    inputs = {k: v.to(device, dtype) if v.is_floating_point() else v.to(device)
              for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=FLORENCE2_MAX_NEW_TOKENS,
        )

    # Decode generated tokens
    decoded = processor.batch_decode(
        generated_ids, skip_special_tokens=False,
    )[0]

    # Post-process to get structured output
    result = processor.post_process_generation(
        decoded,
        task=task,
        image_size=pil_image.size,
    )

    return result


def _parse_florence2_output(
    result: dict,
    task: str = FLORENCE2_TASK,
) -> tuple[Optional[str], Optional[str], Optional[str], list[str]]:
    """Parse Florence-2 output into billet reading fields.

    For <OCR> task, the output is a raw text string that may contain the
    heat number and strand/sequence on separate lines or space-separated.

    Args:
        result: Florence-2 post-processed output dict.
        task: The task prompt used.

    Returns:
        Tuple of (heat_number, strand, sequence, raw_texts).
    """
    heat_re = re.compile(HEAT_NUMBER_PATTERN)
    strand_re = re.compile(STRAND_PATTERN)
    seq_re = re.compile(SEQUENCE_PATTERN)

    if task == "<OCR>":
        raw_text = result.get("<OCR>", "")
    elif task == "<OCR_WITH_REGION>":
        # Concatenate all labels from region detection
        region_data = result.get("<OCR_WITH_REGION>", {})
        labels = region_data.get("labels", [])
        raw_text = " ".join(labels)
    else:
        raw_text = ""

    if not raw_text or not raw_text.strip():
        return None, None, None, []

    # Apply character replacement before parsing
    cleaned_text, _conf = replace_and_score_ocr_text(raw_text)

    # Split into lines (newline or multiple spaces)
    lines = [line.strip() for line in re.split(r"[\n\r]+", cleaned_text) if line.strip()]
    raw_texts = [line.strip() for line in re.split(r"[\n\r]+", raw_text) if line.strip()]

    heat_number: Optional[str] = None
    strand: Optional[str] = None
    sequence: Optional[str] = None

    # Strategy: look for a 5-7 digit heat number in the text
    # Then look for strand + sequence pattern
    for line in lines:
        # Remove spaces and check if entire line is a heat number
        digits_only = line.replace(" ", "")
        if heat_number is None and heat_re.match(digits_only):
            heat_number = digits_only
            continue

        # Try to parse strand + sequence from line (e.g., "3 09", "3 09 1")
        tokens = line.split()
        for i, token in enumerate(tokens):
            if strand is None and strand_re.match(token):
                strand = token
                # Next token(s) might be sequence
                if i + 1 < len(tokens) and seq_re.match(tokens[i + 1]):
                    sequence = tokens[i + 1]
                continue
            if sequence is None and seq_re.match(token):
                sequence = token

    # If we didn't find a heat number via clean lines, try extracting
    # the longest digit run from the full text
    if heat_number is None:
        all_digits = re.findall(r"\d{5,7}", cleaned_text.replace(" ", ""))
        if all_digits:
            heat_number = max(all_digits, key=len)

    return heat_number, strand, sequence, raw_texts


def read_billet_with_florence2(
    image: Union[str, Path, np.ndarray],
    task: str = FLORENCE2_TASK,
    model_id: str = FLORENCE2_MODEL_ID,
) -> BilletReading:
    """Run Florence-2 OCR on a billet image and return a structured reading.

    This is the primary entry point for Florence-2 inference. It mirrors
    the interface of ``read_billet_with_vlm()`` in vlm_reader.py.

    The function:
    1. Converts input to PIL Image (RGB)
    2. Runs Florence-2 inference with the specified task prompt
    3. Parses the raw text output into heat_number, strand, sequence
    4. Applies character replacement (B->8, O->0, etc.)
    5. Returns a BilletReading with method=OCRMethod.VLM_FLORENCE2

    Args:
        image: File path (str or Path) or BGR numpy array from OpenCV.
        task: Florence-2 task prompt. Default "<OCR>".
        model_id: HuggingFace model ID. Default "microsoft/Florence-2-base".

    Returns:
        A BilletReading with method=OCRMethod.VLM_FLORENCE2. On failure,
        an empty BilletReading with confidence=0.0 is returned.
    """
    image_name = _image_label(image)
    logger.info(
        f"[Florence-2] Starting inference | image={image_name} | "
        f"task={task} | model={model_id}"
    )

    # Step 1: Prepare PIL image
    try:
        pil_image = _prepare_pil_image(image)
    except (FileNotFoundError, ValueError) as exc:
        logger.error(f"[Florence-2] Image preparation failed | image={image_name} | error={exc}")
        return BilletReading(method=OCRMethod.VLM_FLORENCE2)

    # Step 2: Run inference
    try:
        t0 = time.perf_counter()
        result = _run_florence2_inference(pil_image, task=task, model_id=model_id)
        elapsed_ms = (time.perf_counter() - t0) * 1000
    except Exception as exc:
        logger.error(
            f"[Florence-2] Inference failed | image={image_name} | error={exc}"
        )
        return BilletReading(method=OCRMethod.VLM_FLORENCE2)

    # Log raw output
    raw_output = result.get(task, "")
    logger.info(
        f"[Florence-2] Inference complete | image={image_name} | "
        f"elapsed_ms={elapsed_ms:.0f} | raw_output={str(raw_output)[:200]!r}"
    )

    # Step 3: Parse output
    heat_number, strand, sequence, raw_texts = _parse_florence2_output(result, task)

    # Step 4: Compute confidence from character replacement
    if raw_output:
        _, replacement_confidence = replace_and_score_ocr_text(str(raw_output))
    else:
        replacement_confidence = 0.0

    # Confidence scaling depends on whether a fine-tuned (LoRA) model is loaded.
    # Zero-shot: capped at 0.70 (0.3 + 0.4*1.0) — below OCR_CONFIDENCE_THRESHOLD
    #   so it always triggers VLM fallback if used as primary OCR path.
    # Fine-tuned: uncapped (0.5 + 0.5*1.0 = 1.0) — can serve as primary OCR.
    is_finetuned = FLORENCE2_LORA_PATH is not None
    if heat_number is not None:
        if is_finetuned:
            confidence = 0.5 + (0.5 * replacement_confidence)
        else:
            confidence = 0.3 + (0.4 * replacement_confidence)
    else:
        confidence = 0.1 * replacement_confidence

    reading = BilletReading(
        heat_number=heat_number,
        strand=strand,
        sequence=sequence,
        confidence=round(confidence, 2),
        method=OCRMethod.VLM_FLORENCE2,
        raw_texts=raw_texts,
    )

    logger.info(
        f"[Florence-2] Result | image={image_name} | "
        f"heat={reading.heat_number} | strand={reading.strand} | "
        f"seq={reading.sequence} | confidence={reading.confidence:.2f}"
    )

    return reading


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _image_label(image: Union[str, Path, np.ndarray]) -> str:
    """Return a short label identifying the image source for log messages.

    Args:
        image: File path or numpy array.

    Returns:
        The filename (for paths) or '<numpy_array>' for arrays.
    """
    if isinstance(image, np.ndarray):
        return "<numpy_array>"
    return Path(image).name


def rotate_image(image: np.ndarray, angle: int) -> np.ndarray:
    """Rotate image by a fixed angle (0, 90, 180, 270).

    Args:
        image: Input BGR/RGB numpy array.
        angle: Rotation angle in degrees. Must be 0, 90, 180, or 270.

    Returns:
        Rotated image. Returns original if angle is 0.
    """
    if angle == 0:
        return image
    elif angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    elif angle == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        logger.warning(f"[Florence-2] Unsupported rotation angle: {angle}")
        return image


def read_billet_with_orientation(
    image: Union[str, Path, np.ndarray],
    orientations: Optional[list[int]] = None,
    task: str = FLORENCE2_TASK,
    model_id: str = FLORENCE2_MODEL_ID,
) -> BilletReading:
    """Try multiple image orientations and return the best Florence-2 result.

    Some billets are photographed upside-down. This function tries 0° first
    and short-circuits if the result is a valid 5-digit heat number. Otherwise,
    it tries 180° and returns whichever orientation produced the best result.

    Args:
        image: File path or BGR numpy array.
        orientations: List of angles to try (default: from config MULTI_ORIENT_ANGLES).
        task: Florence-2 task prompt.
        model_id: HuggingFace model ID.

    Returns:
        BilletReading from the best orientation.
    """
    if orientations is None:
        orientations = MULTI_ORIENT_ANGLES

    # Convert to numpy array once (avoid re-reading file for each rotation)
    if isinstance(image, (str, Path)):
        img_array = cv2.imread(str(image))
        if img_array is None:
            logger.error(f"[Florence-2] Failed to load image: {image}")
            return BilletReading(method=OCRMethod.VLM_FLORENCE2)
    else:
        img_array = image

    best_result: Optional[BilletReading] = None
    best_score: float = -1.0

    for angle in orientations:
        rotated = rotate_image(img_array, angle)
        result = read_billet_with_florence2(rotated, task=task, model_id=model_id)

        # Score: valid 5-digit heat = high, any digits = medium, else low
        score = 0.0
        if result.heat_number and re.match(r"^\d{5}$", result.heat_number):
            score = 2.0 + result.confidence
        elif result.heat_number and result.heat_number.isdigit():
            score = 1.0 + result.confidence
        else:
            score = result.confidence

        logger.debug(
            f"[Florence-2] Orientation {angle}° | heat={result.heat_number} | "
            f"score={score:.2f}"
        )

        if score > best_score:
            best_score = score
            best_result = result

        # Short-circuit: if 0° gives a valid 5-digit result, skip other angles
        if angle == 0 and result.heat_number and re.match(r"^\d{5}$", result.heat_number):
            logger.debug("[Florence-2] 0° orientation valid, skipping rotation")
            break

    return best_result or BilletReading(method=OCRMethod.VLM_FLORENCE2)
