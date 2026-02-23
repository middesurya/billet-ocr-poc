"""Extract ground truth annotations from billet images using Claude Vision API.

Usage:
    python scripts/extract_ground_truth.py
    python scripts/extract_ground_truth.py --image "Image (1).jpg"

Processes all images in data/raw/ (or a specific image) using Claude Vision
to extract billet stamp readings. Results are saved to
data/annotated/ground_truth.json for manual verification.

The output JSON includes VLM confidence and notes so the human reviewer
can focus verification effort on low-confidence readings.
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.config import RAW_DIR, ANNOTATED_DIR, SUPPORTED_FORMATS
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


def extract_ground_truth_for_image(image_path: Path) -> dict:
    """Extract ground truth for a single image using VLM.

    Preprocesses the image with CLAHE first for better VLM reading,
    then sends to Claude Vision.

    Args:
        image_path: Path to the raw billet image.

    Returns:
        Dict with image filename and VLM reading results.
    """
    logger.info(f"Processing: {image_path.name}")

    # Preprocess for better VLM reading
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
) -> list[dict]:
    """Extract ground truth from all images using VLM.

    Args:
        image_dir: Directory containing raw billet images.
        output_path: Path to save the ground truth JSON.
        specific_image: Optional specific image filename.

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

    results = []
    total_start = time.perf_counter()

    for i, image_path in enumerate(image_paths, 1):
        logger.info(f"[{i}/{len(image_paths)}] {image_path.name}")
        try:
            entry = extract_ground_truth_for_image(image_path)
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
    args = parser.parse_args()

    logger.info("=== Billet OCR Ground Truth Extraction ===")
    logger.info(f"Image directory: {RAW_DIR}")
    logger.info(f"Output: {args.output}")

    extract_all_ground_truth(
        image_dir=RAW_DIR,
        output_path=Path(args.output),
        specific_image=args.image,
    )

    logger.info("=== Done! ===")
    logger.info("Next step: Review data/annotated/ground_truth.json and correct any errors.")


if __name__ == "__main__":
    main()
