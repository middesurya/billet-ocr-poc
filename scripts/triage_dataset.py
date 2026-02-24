"""Triage downloaded billet images for stamp visibility.

Performs a quick VLM scan on a subset of images to categorize them as:
- has_stamp: Clear stamped text visible on billet face
- no_stamp: No visible stamp (blank billet, wrong angle, etc.)
- unclear: Ambiguous — may have faint/partial stamps

This filters out images without readable stamps before the expensive
ground truth extraction step, saving API cost and time.

Usage:
    python scripts/triage_dataset.py
    python scripts/triage_dataset.py --max-images 50 --output data/annotated/triage.json
    python scripts/triage_dataset.py --use-bbox  # Crop to Roboflow bboxes first
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from loguru import logger

from src.config import (
    ANNOTATED_DIR,
    BBOX_ANNOTATIONS_PATH,
    RAW_DIR,
    SUPPORTED_FORMATS,
    VLM_MODEL,
)


TRIAGE_PROMPT = """Look at this image of steel billets. I need to know if there are
any IDENTIFICATION NUMBERS visible on the billet end faces.

These numbers can be:
- White paint stenciled characters (most common in this dataset)
- Dot-matrix stamped text (small dots punched into steel)
- Any printed/marked numbers on the square cross-section faces

The numbers typically include heat numbers (4-6 digits) and sequence identifiers.

Ignore:
- Rust, scale, or oxide patterns that aren't text
- Structural features of the billets/equipment
- Scratches or tool marks

Respond with EXACTLY one JSON object:
{
    "has_stamp": true/false,
    "confidence": "high" or "medium" or "low",
    "description": "Brief description of what you see",
    "estimated_readability": "clear" or "partial" or "faint" or "none"
}"""


def triage_single_image(
    image_path: Path,
    model: str = VLM_MODEL,
    bbox: dict | None = None,
) -> dict:
    """Triage a single image for stamp visibility using VLM.

    Args:
        image_path: Path to the billet image.
        model: Claude model to use.
        bbox: Optional bounding box dict with x, y, width, height.
            If provided, crops to this region before sending to VLM.

    Returns:
        Dict with triage results including has_stamp, confidence, etc.
    """
    import cv2
    import numpy as np

    from src.ocr.vlm_reader import encode_image_to_base64

    # Load and optionally crop to bbox
    img = cv2.imread(str(image_path))
    if img is None:
        return {
            "image": image_path.name,
            "category": "error",
            "error": "Could not load image",
        }

    if bbox is not None:
        x, y, w, h = int(bbox["x"]), int(bbox["y"]), int(bbox["width"]), int(bbox["height"])
        # Add 10% padding
        pad_x, pad_y = int(w * 0.1), int(h * 0.1)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(img.shape[1], x + w + pad_x)
        y2 = min(img.shape[0], y + h + pad_y)
        img = img[y1:y2, x1:x2]

    # Encode for VLM
    b64_data, media_type = encode_image_to_base64(img)

    import anthropic

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=model,
            max_tokens=256,
            temperature=0.0,
            messages=[{
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
                    {"type": "text", "text": TRIAGE_PROMPT},
                ],
            }],
        )

        text = response.content[0].text.strip()

        # Parse JSON from response
        import re
        json_match = re.search(r"\{[^}]+\}", text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"has_stamp": False, "confidence": "low", "description": text}

        # Categorize
        has_stamp = result.get("has_stamp", False)
        confidence = result.get("confidence", "low")
        readability = result.get("estimated_readability", "none")

        if has_stamp and confidence in ("high", "medium"):
            category = "has_stamp"
        elif not has_stamp and confidence in ("high", "medium"):
            category = "no_stamp"
        else:
            category = "unclear"

        return {
            "image": image_path.name,
            "category": category,
            "has_stamp": has_stamp,
            "confidence": confidence,
            "readability": readability,
            "description": result.get("description", ""),
            "used_bbox": bbox is not None,
        }

    except Exception as e:
        logger.error("VLM error for {}: {}", image_path.name, e)
        return {
            "image": image_path.name,
            "category": "error",
            "error": str(e),
        }


def triage_dataset(
    image_dir: Path = RAW_DIR,
    max_images: int = 50,
    shuffle: bool = True,
    model: str = VLM_MODEL,
    bbox_path: Path | None = None,
    skip_existing: bool = True,
    output_path: Path = ANNOTATED_DIR / "triage.json",
) -> list[dict]:
    """Triage a batch of images for stamp visibility.

    Args:
        image_dir: Directory containing billet images.
        max_images: Maximum number of images to triage.
        shuffle: Whether to shuffle image order (for random sampling).
        model: Claude model to use.
        bbox_path: Path to Roboflow bbox annotations JSON. If provided,
            crops images to annotated bounding boxes before VLM scan.
        skip_existing: Skip images already triaged in previous runs.
        output_path: Path to save triage results.

    Returns:
        List of triage result dicts.
    """
    # Collect image paths
    paths = []
    for fmt in SUPPORTED_FORMATS:
        paths.extend(image_dir.glob(f"*{fmt}"))
    paths = sorted(set(paths), key=lambda p: p.name)

    if shuffle:
        random.shuffle(paths)

    # Load existing triage results
    existing: dict[str, dict] = {}
    if skip_existing and output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            for entry in json.load(f):
                existing[entry["image"]] = entry
        logger.info("Loaded {} existing triage entries", len(existing))

    # Load bboxes if available
    bboxes: dict[str, list[dict]] = {}
    if bbox_path and bbox_path.exists():
        with open(bbox_path, encoding="utf-8") as f:
            bboxes = json.load(f)
        logger.info("Loaded bboxes for {} images", len(bboxes))

    # Filter to un-triaged images
    if skip_existing:
        paths = [p for p in paths if p.name not in existing]

    paths = paths[:max_images]
    logger.info("Triaging {} images (max={})", len(paths), max_images)

    results = []
    start = time.perf_counter()

    for i, img_path in enumerate(paths, 1):
        logger.info("[{}/{}] Triaging: {}", i, len(paths), img_path.name)

        # Use first bbox if available
        bbox = None
        if img_path.name in bboxes:
            bbox = bboxes[img_path.name][0]  # Use first/largest bbox

        result = triage_single_image(img_path, model=model, bbox=bbox)
        results.append(result)
        existing[result["image"]] = result

        logger.info(
            "  -> {} (confidence={}, readability={})",
            result.get("category", "error"),
            result.get("confidence", "N/A"),
            result.get("readability", "N/A"),
        )

    elapsed = time.perf_counter() - start
    logger.info("Triaged {} images in {:.1f}s", len(results), elapsed)

    # Save merged results
    all_entries = sorted(existing.values(), key=lambda x: x["image"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)
    logger.info("Saved triage results to {}", output_path)

    # Print summary
    categories = {}
    for entry in all_entries:
        cat = entry.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    logger.info("=== Triage Summary ===")
    for cat, count in sorted(categories.items()):
        logger.info("  {}: {} images", cat, count)

    return results


def main() -> None:
    """CLI entry point for dataset triage."""
    parser = argparse.ArgumentParser(
        description="Triage billet images for stamp visibility using VLM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max-images", type=int, default=50,
        help="Maximum number of images to triage",
    )
    parser.add_argument(
        "--no-shuffle", action="store_true",
        help="Process images in sorted order instead of random",
    )
    parser.add_argument(
        "--model", default=VLM_MODEL,
        help="Claude model for triage",
    )
    parser.add_argument(
        "--use-bbox", action="store_true",
        help="Crop to Roboflow bounding boxes before VLM scan",
    )
    parser.add_argument(
        "--no-skip-existing", action="store_true",
        help="Re-triage images even if already in results",
    )
    parser.add_argument(
        "--output", default=str(ANNOTATED_DIR / "triage.json"),
        help="Output JSON path for triage results",
    )
    parser.add_argument(
        "--image-dir", default=str(RAW_DIR),
        help="Directory containing billet images",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    bbox_path = BBOX_ANNOTATIONS_PATH if args.use_bbox else None

    triage_dataset(
        image_dir=Path(args.image_dir),
        max_images=args.max_images,
        shuffle=not args.no_shuffle,
        model=args.model,
        bbox_path=bbox_path,
        skip_existing=not args.no_skip_existing,
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
