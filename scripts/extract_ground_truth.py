"""Extract ground truth annotations from billet images using Claude Vision API.

V2: Multi-billet support — processes ALL bboxes per image, not just the first/largest.

Usage:
    python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30
    python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30 --shuffle
    python scripts/extract_ground_truth.py --use-bbox --max-images 30  # single-bbox legacy mode
    python scripts/extract_ground_truth.py --image "Image (1).jpg"

Each surveillance image has ~9 billets. In --all-bboxes mode (default when --use-bbox),
this script loops over ALL bounding boxes per image, crops each one, sends to VLM,
and creates a per-billet GT entry with bbox_index + bbox coordinates.

Output: ground_truth_v2.json with entries like:
    {"image": "xxx.jpg", "bbox_index": 0, "bbox": {...}, "heat_number": "60731", ...}

Per-billet crop images saved to data/gt_review/ for human verification.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.config import (
    ANNOTATED_DIR,
    BBOX_ANNOTATIONS_PATH,
    GT_BBOX_PAD_RATIO,
    GT_OUTPUT_PATH,
    GT_REVIEW_CROPS_DIR,
    GT_REVIEW_DIR,
    GT_REVIEW_SOURCES_DIR,
    MIN_BBOX_SIZE,
    RAW_DIR,
    SUPPORTED_FORMATS,
)
from src.ocr.vlm_reader import read_billet_with_vlm_for_ground_truth


def get_image_paths(image_dir: Path = RAW_DIR, specific_image: str | None = None) -> list[Path]:
    """Get list of image paths to process.

    Args:
        image_dir: Directory containing raw billet images.
        specific_image: Optional specific image filename to process.

    Returns:
        Sorted list of image paths.
    """
    if specific_image:
        path = image_dir / specific_image
        if not path.exists():
            logger.error(f"Image not found: {path}")
            sys.exit(1)
        return [path]

    paths = []
    for fmt in SUPPORTED_FORMATS:
        paths.extend(image_dir.glob(f"*{fmt}"))
    paths = sorted(set(paths), key=lambda p: p.name)
    logger.info(f"Found {len(paths)} images in {image_dir}")
    return paths


def _crop_to_bbox(
    image: np.ndarray,
    bbox: dict,
    pad_ratio: float = GT_BBOX_PAD_RATIO,
) -> np.ndarray:
    """Crop an image to a bounding box with padding.

    Args:
        image: Loaded BGR image array.
        bbox: Dict with x, y, width, height keys.
        pad_ratio: Padding fraction on each side.

    Returns:
        Cropped numpy array.
    """
    x, y, w, h = int(bbox["x"]), int(bbox["y"]), int(bbox["width"]), int(bbox["height"])
    pad_x, pad_y = int(w * pad_ratio), int(h * pad_ratio)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(image.shape[1], x + w + pad_x)
    y2 = min(image.shape[0], y + h + pad_y)

    return image[y1:y2, x1:x2]


def _save_crop_image(
    crop: np.ndarray,
    image_stem: str,
    bbox_index: int,
    output_dir: Path = GT_REVIEW_CROPS_DIR,
) -> Path:
    """Save a per-billet crop image for human review.

    Args:
        crop: Cropped BGR image array.
        image_stem: Base name of the source image (without extension).
        bbox_index: Bounding box index within the image.
        output_dir: Directory to save crop images.

    Returns:
        Path to the saved crop image.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # Truncate long filenames for readability
    short_stem = image_stem[:60] if len(image_stem) > 60 else image_stem
    out_path = output_dir / f"{short_stem}_bbox{bbox_index}.jpg"
    cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out_path


def _save_source_image(image_path: Path) -> None:
    """Copy the full source image to the sources review folder.

    Only copies if not already present, to avoid redundant writes.
    """
    dest = GT_REVIEW_SOURCES_DIR / image_path.name
    if not dest.exists():
        import shutil
        GT_REVIEW_SOURCES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(image_path), str(dest))


def extract_gt_for_single_billet(
    image: np.ndarray,
    image_name: str,
    bbox: dict,
    bbox_index: int,
) -> dict:
    """Extract ground truth for a single billet crop using VLM.

    Sends the raw cropped image to Claude Vision with Prompt V4
    (designed for pre-cropped single-billet images).

    Args:
        image: Loaded BGR image of the full surveillance frame.
        image_name: Original image filename.
        bbox: Bounding box dict for this billet.
        bbox_index: Index of this bbox within the image's bbox list.

    Returns:
        Per-billet ground truth dict.
    """
    cropped = _crop_to_bbox(image, bbox)

    # Save crop for human review
    stem = Path(image_name).stem
    crop_path = _save_crop_image(cropped, stem, bbox_index)

    # Send raw crop to VLM (no CLAHE — hurts VLM accuracy)
    result = read_billet_with_vlm_for_ground_truth(cropped, prompt_version=4)

    confidence_raw = result.get("confidence", 0.0)
    if isinstance(confidence_raw, str):
        try:
            confidence_raw = float(confidence_raw)
        except ValueError:
            confidence_raw = 0.0

    entry = {
        "image": image_name,
        "bbox_index": bbox_index,
        "bbox": {
            "x": int(bbox["x"]),
            "y": int(bbox["y"]),
            "width": int(bbox["width"]),
            "height": int(bbox["height"]),
        },
        "heat_number": result.get("heat_number", ""),
        "sequence": result.get("sequence"),
        "strand": result.get("strand"),
        "all_text": result.get("all_text", []),
        "vlm_confidence": confidence_raw,
        "verified": False,
        "notes": "",
        "crop_path": f"crops/{crop_path.name}",
    }

    logger.info(
        f"    bbox[{bbox_index}] heat={entry['heat_number']}, "
        f"seq={entry['sequence']}, conf={confidence_raw:.2f}, "
        f"crop={crop_path.name}"
    )
    return entry


def extract_gt_for_image_all_bboxes(
    image_path: Path,
    bboxes: list[dict],
) -> list[dict]:
    """Extract ground truth for ALL bboxes in one image.

    Args:
        image_path: Path to the raw billet image.
        bboxes: List of bbox dicts from roboflow_bboxes.json.

    Returns:
        List of per-billet GT dicts (one per valid bbox).
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Save source image to sources/ for side-by-side review
    _save_source_image(image_path)

    entries = []
    skipped = 0

    for bbox_idx, bbox in enumerate(bboxes):
        w, h = int(bbox.get("width", 0)), int(bbox.get("height", 0))
        if min(w, h) < MIN_BBOX_SIZE:
            skipped += 1
            continue

        try:
            entry = extract_gt_for_single_billet(
                image, image_path.name, bbox, bbox_idx,
            )
            entries.append(entry)
        except Exception as e:
            logger.error(f"    bbox[{bbox_idx}] FAILED: {e}")
            entries.append({
                "image": image_path.name,
                "bbox_index": bbox_idx,
                "bbox": {
                    "x": int(bbox.get("x", 0)),
                    "y": int(bbox.get("y", 0)),
                    "width": w,
                    "height": h,
                },
                "heat_number": "",
                "sequence": None,
                "strand": None,
                "all_text": [],
                "vlm_confidence": 0.0,
                "verified": False,
                "notes": f"VLM extraction failed: {e}",
            })

    if skipped:
        logger.info(f"    Skipped {skipped} tiny bboxes (< {MIN_BBOX_SIZE}px)")

    return entries


def extract_gt_for_image_single_bbox(
    image_path: Path,
    bbox: dict | None = None,
) -> dict:
    """Extract ground truth for a single image/bbox (legacy mode).

    Falls back to full-image VLM when no bbox is provided.

    Args:
        image_path: Path to the raw billet image.
        bbox: Optional bounding box to crop to.

    Returns:
        Single ground truth dict.
    """
    if bbox is not None:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        cropped = _crop_to_bbox(image, bbox)
        result = read_billet_with_vlm_for_ground_truth(cropped, prompt_version=4)
    else:
        result = read_billet_with_vlm_for_ground_truth(image_path, prompt_version=3)

    return {
        "image": image_path.name,
        "heat_number": result.get("heat_number", ""),
        "strand": result.get("strand"),
        "sequence": result.get("sequence"),
        "notes": result.get("notes", ""),
        "vlm_confidence": result.get("confidence", "unknown"),
        "all_text": result.get("all_text", []),
    }


def extract_all_ground_truth(
    image_dir: Path = RAW_DIR,
    output_path: Path = GT_OUTPUT_PATH,
    specific_image: str | None = None,
    max_images: int = 0,
    skip_existing: bool = False,
    batch_size: int = 10,
    shuffle: bool = False,
    bbox_path: Path | None = None,
    triage_path: Path | None = None,
    all_bboxes: bool = True,
) -> list[dict]:
    """Extract ground truth from all images using VLM.

    In all_bboxes mode (default), iterates ALL bboxes per image, producing
    ~9 GT entries per image. Otherwise, uses only the first bbox per image.

    Args:
        image_dir: Directory containing raw billet images.
        output_path: Path to save the ground truth JSON.
        specific_image: Optional specific image filename.
        max_images: Maximum images to process (0 = all).
        skip_existing: Skip images already in ground truth.
        batch_size: Save after every N images (0 = save only at end).
        shuffle: Randomize processing order.
        bbox_path: Path to Roboflow bbox annotations for cropping.
        triage_path: Path to triage results; only process 'has_stamp' images.
        all_bboxes: If True, process ALL bboxes per image (multi-billet mode).

    Returns:
        List of ground truth dicts (one per billet, not per image).
    """
    image_paths = get_image_paths(image_dir, specific_image)

    # Load existing ground truth to merge with (keyed by image+bbox_index)
    existing: list[dict] = []
    existing_keys: set[str] = set()
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        for entry in existing:
            key = f"{entry['image']}:{entry.get('bbox_index', 0)}"
            existing_keys.add(key)
        logger.info(f"Loaded {len(existing)} existing entries from {output_path}")

    # Filter by triage results if specified
    if triage_path and triage_path.exists():
        with open(triage_path, encoding="utf-8") as f:
            triage_data = json.load(f)
        stamp_images = {
            entry["image"] for entry in triage_data
            if entry.get("category") == "has_stamp"
        }
        before = len(image_paths)
        image_paths = [p for p in image_paths if p.name in stamp_images]
        logger.info(
            f"Triage filter: {before} -> {len(image_paths)} images (has_stamp only)"
        )

    # Skip existing images (if all bboxes for that image already exist)
    if skip_existing:
        before = len(image_paths)
        existing_images = {e["image"] for e in existing}
        image_paths = [p for p in image_paths if p.name not in existing_images]
        logger.info(f"Skip existing: {before} -> {len(image_paths)} new images")

    # Shuffle
    if shuffle:
        random.shuffle(image_paths)

    # Limit
    if max_images > 0:
        image_paths = image_paths[:max_images]
        logger.info(f"Limited to {max_images} images")

    # Load bboxes
    bboxes: dict[str, list[dict]] = {}
    if bbox_path and bbox_path.exists():
        with open(bbox_path, encoding="utf-8") as f:
            bboxes = json.load(f)
        logger.info(f"Loaded bboxes for {len(bboxes)} images")

    new_entries: list[dict] = []
    total_start = time.perf_counter()
    total_billets = 0

    for i, image_path in enumerate(image_paths, 1):
        img_name = image_path.name
        img_bboxes = bboxes.get(img_name, [])
        logger.info(
            f"[{i}/{len(image_paths)}] {img_name} — "
            f"{len(img_bboxes)} bboxes"
        )

        if all_bboxes and img_bboxes:
            # Multi-billet mode: process ALL bboxes
            try:
                entries = extract_gt_for_image_all_bboxes(image_path, img_bboxes)
                new_entries.extend(entries)
                total_billets += len(entries)
            except Exception as e:
                logger.error(f"  Image-level failure: {e}")
        elif img_bboxes:
            # Legacy mode: first bbox only
            try:
                entry = extract_gt_for_image_single_bbox(
                    image_path, bbox=img_bboxes[0],
                )
                new_entries.append(entry)
                total_billets += 1
            except Exception as e:
                logger.error(f"  Failed: {e}")
        else:
            # No bboxes: full-image mode
            try:
                entry = extract_gt_for_image_single_bbox(image_path)
                new_entries.append(entry)
                total_billets += 1
            except Exception as e:
                logger.error(f"  Failed: {e}")

        # Periodic save
        if batch_size > 0 and i % batch_size == 0:
            merged = existing + new_entries
            save_ground_truth(merged, output_path)
            logger.info(f"  Batch save at {i}/{len(image_paths)} ({total_billets} billets)")

    elapsed = time.perf_counter() - total_start
    logger.info(
        f"Processed {len(image_paths)} images → {total_billets} billet entries "
        f"in {elapsed:.1f}s"
    )

    # Save merged results
    merged = existing + new_entries
    save_ground_truth(merged, output_path)

    return new_entries


def save_ground_truth(
    results: list[dict],
    output_path: Path = GT_OUTPUT_PATH,
) -> Path:
    """Save ground truth results to JSON file.

    Args:
        results: List of ground truth dicts.
        output_path: Path to save JSON file.

    Returns:
        Path to the saved file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved ground truth to {output_path}")
    logger.info(f"  {len(results)} entries total")
    logger.info(f"  REVIEW crops in {GT_REVIEW_DIR} and set verified=true!")
    return output_path


def main() -> None:
    """Main entry point for ground truth extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract ground truth from billet images using Claude Vision (multi-billet)"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help='Specific image filename to process (e.g., "Image (1).jpg")',
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(GT_OUTPUT_PATH),
        help="Output JSON path",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Maximum number of images to process (0 = all)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images already in the ground truth file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Save after every N images (0 = only at end)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Randomize processing order",
    )
    parser.add_argument(
        "--use-bbox",
        action="store_true",
        help="Crop to Roboflow bounding boxes before VLM extraction",
    )
    parser.add_argument(
        "--all-bboxes",
        action="store_true",
        default=True,
        help="Process ALL bboxes per image (default: True). Use --no-all-bboxes for legacy mode.",
    )
    parser.add_argument(
        "--no-all-bboxes",
        action="store_true",
        help="Only process first bbox per image (legacy single-billet mode).",
    )
    parser.add_argument(
        "--triage-filter",
        action="store_true",
        help="Only process images marked 'has_stamp' in triage results",
    )
    args = parser.parse_args()

    all_bboxes = args.all_bboxes and not args.no_all_bboxes

    logger.info("=== Billet OCR Ground Truth Extraction (V2 Multi-Billet) ===")
    logger.info(f"Image directory: {RAW_DIR}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Mode: {'ALL bboxes per image' if all_bboxes else 'Single bbox per image'}")
    if args.max_images > 0:
        logger.info(f"Max images: {args.max_images}")
    if args.skip_existing:
        logger.info("Skipping existing entries")
    if args.use_bbox:
        logger.info(f"Using bbox annotations from {BBOX_ANNOTATIONS_PATH}")

    bbox_path = BBOX_ANNOTATIONS_PATH if args.use_bbox else None
    triage_path = ANNOTATED_DIR / "triage.json" if args.triage_filter else None

    extract_all_ground_truth(
        image_dir=RAW_DIR,
        output_path=Path(args.output),
        specific_image=args.image,
        max_images=args.max_images,
        skip_existing=args.skip_existing,
        batch_size=args.batch_size,
        shuffle=args.shuffle,
        bbox_path=bbox_path,
        triage_path=triage_path,
        all_bboxes=all_bboxes,
    )

    logger.info("=== Done! ===")
    logger.info(f"Next: Review crop images in {GT_REVIEW_DIR}")
    logger.info(f"       Compare with {args.output} and set verified=true")


if __name__ == "__main__":
    main()
