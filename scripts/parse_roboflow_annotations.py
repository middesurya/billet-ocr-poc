"""Parse COCO annotations from Roboflow download into billet bounding boxes.

Extracts bounding boxes for the 'batch' class (billet locations) from COCO
format annotations and saves them in a simplified JSON format for use by
the ROI detector and benchmark pipeline.

Usage:
    python scripts/parse_roboflow_annotations.py
    python scripts/parse_roboflow_annotations.py --download-dir data/roboflow_download
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from loguru import logger

from src.config import BBOX_ANNOTATIONS_PATH, ROBOFLOW_DOWNLOAD_DIR


def parse_coco_annotations(
    download_dir: Path = ROBOFLOW_DOWNLOAD_DIR,
) -> dict[str, list[dict]]:
    """Parse COCO annotation files from all splits.

    COCO format structure:
        {
            "images": [{"id": 1, "file_name": "img.jpg", "width": W, "height": H}],
            "annotations": [{"image_id": 1, "bbox": [x, y, w, h], "category_id": 0}],
            "categories": [{"id": 0, "name": "batch"}]
        }

    Args:
        download_dir: Root of the Roboflow download containing train/valid/test
            subdirectories, each with an _annotations.coco.json file.

    Returns:
        Dict mapping image filename to list of bounding box dicts.
        Each bbox dict has keys: x, y, width, height, area, category, split.
    """
    all_bboxes: dict[str, list[dict]] = {}

    for split_dir in sorted(download_dir.iterdir()):
        if not split_dir.is_dir():
            continue

        ann_file = split_dir / "_annotations.coco.json"
        if not ann_file.exists():
            logger.warning("No annotations found in {}", split_dir)
            continue

        logger.info("Parsing annotations from {}", ann_file)

        with open(ann_file, encoding="utf-8") as f:
            coco = json.load(f)

        # Build lookup: image_id -> filename
        id_to_filename: dict[int, str] = {}
        id_to_dims: dict[int, tuple[int, int]] = {}
        for img_info in coco.get("images", []):
            img_id = img_info["id"]
            id_to_filename[img_id] = img_info["file_name"]
            id_to_dims[img_id] = (img_info["width"], img_info["height"])

        # Build lookup: category_id -> name
        id_to_category: dict[int, str] = {}
        for cat in coco.get("categories", []):
            id_to_category[cat["id"]] = cat["name"]

        # Extract bboxes
        split_name = split_dir.name
        for ann in coco.get("annotations", []):
            img_id = ann["image_id"]
            filename = id_to_filename.get(img_id)
            if filename is None:
                continue

            x, y, w, h = ann["bbox"]
            cat_id = ann.get("category_id", 0)
            category = id_to_category.get(cat_id, "unknown")
            img_w, img_h = id_to_dims.get(img_id, (0, 0))

            bbox_entry = {
                "x": round(x, 1),
                "y": round(y, 1),
                "width": round(w, 1),
                "height": round(h, 1),
                "area": round(ann.get("area", w * h), 1),
                "category": category,
                "split": split_name,
                "image_width": img_w,
                "image_height": img_h,
            }

            if filename not in all_bboxes:
                all_bboxes[filename] = []
            all_bboxes[filename].append(bbox_entry)

    return all_bboxes


def save_bbox_annotations(
    bboxes: dict[str, list[dict]],
    output_path: Path = BBOX_ANNOTATIONS_PATH,
) -> Path:
    """Save parsed bounding boxes to a JSON file.

    Args:
        bboxes: Dict mapping image filename to list of bbox dicts.
        output_path: Path to save the JSON file.

    Returns:
        Path to the saved file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bboxes, f, indent=2)

    total_images = len(bboxes)
    total_bboxes = sum(len(v) for v in bboxes.values())
    logger.info(
        "Saved {} bounding boxes for {} images to {}",
        total_bboxes, total_images, output_path,
    )
    return output_path


def print_stats(bboxes: dict[str, list[dict]]) -> None:
    """Print summary statistics about the parsed annotations.

    Args:
        bboxes: Dict mapping image filename to list of bbox dicts.
    """
    total_images = len(bboxes)
    total_bboxes = sum(len(v) for v in bboxes.values())
    categories = set()
    splits = set()
    for boxes in bboxes.values():
        for b in boxes:
            categories.add(b["category"])
            splits.add(b["split"])

    # Count bboxes per image
    bbox_counts = [len(v) for v in bboxes.values()]
    avg_bboxes = sum(bbox_counts) / len(bbox_counts) if bbox_counts else 0

    logger.info("=== Annotation Statistics ===")
    logger.info("  Images: {}", total_images)
    logger.info("  Total bounding boxes: {}", total_bboxes)
    logger.info("  Avg bboxes per image: {:.1f}", avg_bboxes)
    logger.info("  Categories: {}", sorted(categories))
    logger.info("  Splits: {}", sorted(splits))

    # Per-split counts
    split_counts: dict[str, int] = {}
    for boxes in bboxes.values():
        for b in boxes:
            split = b["split"]
            split_counts[split] = split_counts.get(split, 0) + 1
    for split in sorted(split_counts):
        logger.info("  {}: {} bboxes", split, split_counts[split])


def main() -> None:
    """CLI entry point for annotation parsing."""
    parser = argparse.ArgumentParser(
        description="Parse COCO annotations from Roboflow download",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--download-dir",
        default=str(ROBOFLOW_DOWNLOAD_DIR),
        help="Root directory of the Roboflow download",
    )
    parser.add_argument(
        "--output",
        default=str(BBOX_ANNOTATIONS_PATH),
        help="Output JSON path for parsed bounding boxes",
    )
    args = parser.parse_args()

    download_dir = Path(args.download_dir)
    output_path = Path(args.output)

    if not download_dir.exists():
        logger.error("Download directory not found: {}", download_dir)
        logger.error("Run scripts/download_roboflow_dataset.py first.")
        sys.exit(1)

    bboxes = parse_coco_annotations(download_dir)

    if not bboxes:
        logger.error("No annotations found. Check the download directory structure.")
        sys.exit(1)

    print_stats(bboxes)
    save_bbox_annotations(bboxes, output_path)

    logger.info("Done! Next step: python scripts/triage_dataset.py")


if __name__ == "__main__":
    main()
