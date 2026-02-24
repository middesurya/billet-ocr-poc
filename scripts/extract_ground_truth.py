"""Extract ground truth annotations from billet images using Claude Vision API.

Usage:
    python scripts/extract_ground_truth.py
    python scripts/extract_ground_truth.py --image "Image (1).jpg"
    python scripts/extract_ground_truth.py --max-images 50 --skip-existing
    python scripts/extract_ground_truth.py --use-bbox --max-images 30

Processes all images in data/raw/ (or a specific image) using Claude Vision
to extract billet stamp readings. Results are saved to
data/annotated/ground_truth.json for manual verification.

The output JSON includes VLM confidence and notes so the human reviewer
can focus verification effort on low-confidence readings.

New flags (v2):
    --max-images N    Process at most N images
    --skip-existing   Skip images already in ground truth file
    --batch-size N    Save after every N images (for long runs)
    --use-bbox        Crop to Roboflow bounding boxes before VLM extraction
    --triage-filter   Only process images marked 'has_stamp' in triage results
    --shuffle         Randomize processing order
"""
import argparse
import json
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.config import (
    ANNOTATED_DIR,
    BBOX_ANNOTATIONS_PATH,
    RAW_DIR,
    SUPPORTED_FORMATS,
)
from src.models import GroundTruth
from src.preprocessing.pipeline import preprocess_billet_image
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


def _crop_to_bbox(image_path: Path, bbox: dict) -> "np.ndarray":
    """Crop an image to a bounding box with padding.

    Args:
        image_path: Path to the image file.
        bbox: Dict with x, y, width, height keys.

    Returns:
        Cropped numpy array.
    """
    import cv2

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    x, y, w, h = int(bbox["x"]), int(bbox["y"]), int(bbox["width"]), int(bbox["height"])
    # Add 10% padding
    pad_x, pad_y = int(w * 0.1), int(h * 0.1)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img.shape[1], x + w + pad_x)
    y2 = min(img.shape[0], y + h + pad_y)

    return img[y1:y2, x1:x2]


def extract_ground_truth_for_image(
    image_path: Path,
    bbox: dict | None = None,
) -> dict:
    """Extract ground truth for a single image using VLM.

    Preprocesses the image with CLAHE first for better VLM reading,
    then sends to Claude Vision.

    Args:
        image_path: Path to the raw billet image.
        bbox: Optional bounding box to crop to before preprocessing.

    Returns:
        Dict with image filename and VLM reading results.
    """
    logger.info(f"Processing: {image_path.name}")

    # If bbox provided, crop first then preprocess
    if bbox is not None:
        cropped = _crop_to_bbox(image_path, bbox)
        preprocessed, timing = preprocess_billet_image(cropped)
        logger.info(f"  Bbox-cropped + preprocessing took {timing['total_ms']:.0f}ms")
    else:
        preprocessed, timing = preprocess_billet_image(image_path)
        logger.info(f"  Preprocessing took {timing['total_ms']:.0f}ms")

    # Send preprocessed image to VLM
    result = read_billet_with_vlm_for_ground_truth(preprocessed)

    entry = {
        "image": image_path.name,
        "heat_number": result.get("heat_number", ""),
        "strand": result.get("strand"),
        "sequence": result.get("sequence"),
        "notes": result.get("notes", ""),
        "vlm_confidence": result.get("confidence", "unknown"),
        "all_text": result.get("all_text", []),
    }

    if bbox is not None:
        entry["bbox_used"] = True

    logger.info(
        f"  Result: heat={entry['heat_number']}, "
        f"strand={entry['strand']}, seq={entry['sequence']}, "
        f"confidence={entry['vlm_confidence']}"
    )
    return entry


def extract_all_ground_truth(
    image_dir: Path = RAW_DIR,
    output_path: Path = ANNOTATED_DIR / "ground_truth.json",
    specific_image: str | None = None,
    max_images: int = 0,
    skip_existing: bool = False,
    batch_size: int = 0,
    shuffle: bool = False,
    bbox_path: Path | None = None,
    triage_path: Path | None = None,
) -> list[dict]:
    """Extract ground truth from all images using VLM.

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

    Returns:
        List of ground truth dicts (one per image).
    """
    image_paths = get_image_paths(image_dir, specific_image)

    # Load existing ground truth to merge with
    existing = {}
    if output_path.exists():
        with open(output_path, "r") as f:
            for entry in json.load(f):
                existing[entry["image"]] = entry
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

    # Skip existing
    if skip_existing:
        before = len(image_paths)
        image_paths = [p for p in image_paths if p.name not in existing]
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

    results = []
    total_start = time.perf_counter()

    for i, image_path in enumerate(image_paths, 1):
        logger.info(f"[{i}/{len(image_paths)}] {image_path.name}")

        # Get bbox if available
        bbox = None
        if image_path.name in bboxes:
            bbox = bboxes[image_path.name][0]  # Use first bbox

        try:
            entry = extract_ground_truth_for_image(image_path, bbox=bbox)
            existing[entry["image"]] = entry
            results.append(entry)
        except Exception as e:
            logger.error(f"  Failed: {e}")
            results.append({
                "image": image_path.name,
                "heat_number": "",
                "strand": None,
                "sequence": None,
                "notes": f"VLM extraction failed: {e}",
                "vlm_confidence": "failed",
                "all_text": [],
            })

        # Periodic save
        if batch_size > 0 and i % batch_size == 0:
            all_entries = sorted(existing.values(), key=lambda x: x["image"])
            save_ground_truth(all_entries, output_path)
            logger.info(f"  Batch save at {i}/{len(image_paths)}")

    elapsed = time.perf_counter() - total_start
    logger.info(f"Processed {len(results)} images in {elapsed:.1f}s")

    # Save merged results
    all_entries = sorted(existing.values(), key=lambda x: x["image"])
    save_ground_truth(all_entries, output_path)

    return results


def save_ground_truth(
    results: list[dict],
    output_path: Path = ANNOTATED_DIR / "ground_truth.json",
) -> Path:
    """Save ground truth results to JSON file.

    Args:
        results: List of ground truth dicts.
        output_path: Path to save JSON file.

    Returns:
        Path to the saved file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved ground truth to {output_path}")
    logger.info(f"  {len(results)} entries total")
    logger.info(f"  REVIEW THIS FILE and correct any errors before benchmarking!")
    return output_path


def main() -> None:
    """Main entry point for ground truth extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract ground truth from billet images using Claude Vision"
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
        default=str(ANNOTATED_DIR / "ground_truth.json"),
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
        "--triage-filter",
        action="store_true",
        help="Only process images marked 'has_stamp' in triage results",
    )
    args = parser.parse_args()

    logger.info("=== Billet OCR Ground Truth Extraction ===")
    logger.info(f"Image directory: {RAW_DIR}")
    logger.info(f"Output: {args.output}")
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
    )

    logger.info("=== Done! ===")
    logger.info("Next step: Review data/annotated/ground_truth.json and correct any errors.")


if __name__ == "__main__":
    main()
