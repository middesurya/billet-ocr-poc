"""Prepare a HuggingFace-compatible dataset for Florence-2 LoRA fine-tuning.

Reads ground truth annotations and billet images, crops to regions of interest,
applies data augmentation, and outputs train/val splits with metadata.jsonl files
in the format expected by Florence-2 fine-tuning scripts.

Usage:
    python scripts/prepare_florence2_training.py
    python scripts/prepare_florence2_training.py --augment-factor 5 --target-size 768
    python scripts/prepare_florence2_training.py --seed 123 --output-dir data/training/florence2_v2/
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Path setup -- make the project root importable regardless of cwd.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import (
    ANNOTATED_DIR,
    BBOX_ANNOTATIONS_PATH,
    FLORENCE2_BBOX_PAD_RATIO,
    RAW_DIR,
    VLM_CROP_RATIO,
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_ground_truth(gt_path: Path) -> list[dict[str, Any]]:
    """Load and filter ground truth entries to those with valid heat numbers.

    Args:
        gt_path: Path to ground_truth.json.

    Returns:
        List of ground truth dicts with heat_number containing 5+ digits.
    """
    with open(gt_path, "r", encoding="utf-8") as f:
        entries: list[dict[str, Any]] = json.load(f)

    valid: list[dict[str, Any]] = []
    for entry in entries:
        hn = entry.get("heat_number")
        if hn is not None and isinstance(hn, str) and len(hn) >= 5 and hn.isdigit():
            valid.append(entry)

    return valid


def load_ground_truth_v2(gt_path: Path) -> list[dict[str, Any]]:
    """Load GT V2 entries filtered for training quality.

    Filters:
    - Must have bbox_index (per-billet entry)
    - Heat number: 5+ digits, all numeric
    - Sequence: if fully '????', include with sequence=None (heat-only label)
    - Sequence: if contains partial '?', SKIP (unreliable)
    - Sequence: if clean, include as-is (may contain J, Y — real characters)

    Args:
        gt_path: Path to ground_truth_v2.json.

    Returns:
        List of ground truth dicts suitable for training.
    """
    with open(gt_path, "r", encoding="utf-8") as f:
        entries: list[dict[str, Any]] = json.load(f)

    valid: list[dict[str, Any]] = []
    for entry in entries:
        hn = entry.get("heat_number", "")
        seq = entry.get("sequence", "") or ""

        if "bbox_index" not in entry:
            continue
        if not (isinstance(hn, str) and len(hn) >= 5 and hn.isdigit()):
            continue

        if seq == "????" or seq == "":
            # Heat-only entry — label will be just heat number
            entry = dict(entry)
            entry["sequence"] = None
            valid.append(entry)
        elif "?" in seq:
            # Partial ? (e.g., 3?54, 4J2??) — skip, unreliable
            continue
        else:
            # Fully clean sequence (may contain J, Y — real chars)
            valid.append(entry)

    return valid


def load_bboxes(bbox_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load Roboflow bounding box annotations.

    Args:
        bbox_path: Path to roboflow_bboxes.json.

    Returns:
        Dict mapping image filename to list of bbox dicts.
    """
    if not bbox_path.exists():
        return {}

    with open(bbox_path, "r", encoding="utf-8") as f:
        data: dict[str, list[dict[str, Any]]] = json.load(f)

    return data


# ---------------------------------------------------------------------------
# Image cropping
# ---------------------------------------------------------------------------


def crop_to_single_bbox(
    image: np.ndarray,
    bbox: dict[str, Any],
    pad_ratio: float = FLORENCE2_BBOX_PAD_RATIO,
) -> np.ndarray:
    """Crop image to a single bounding box with padding.

    Args:
        image: Input image as numpy array (H, W, C).
        bbox: Bbox dict with keys: x, y, width, height.
        pad_ratio: Fraction of bbox dimensions to add as padding on each side.

    Returns:
        Cropped image region as numpy array.
    """
    x = int(bbox["x"])
    y = int(bbox["y"])
    w = int(bbox["width"])
    h = int(bbox["height"])

    pad_x = int(w * pad_ratio)
    pad_y = int(h * pad_ratio)

    img_h, img_w = image.shape[:2]

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, y + h + pad_y)

    return image[y1:y2, x1:x2]


def crop_to_bbox(
    image: np.ndarray,
    bboxes: list[dict[str, Any]],
    pad_ratio: float = FLORENCE2_BBOX_PAD_RATIO,
) -> np.ndarray:
    """Crop image to the largest bounding box with padding (legacy).

    Selects the bbox with the largest area, then applies pad_ratio padding
    on each side (clamped to image boundaries).

    Args:
        image: Input image as numpy array (H, W, C).
        bboxes: List of bbox dicts with keys: x, y, width, height, area.
        pad_ratio: Fraction of bbox dimensions to add as padding on each side.

    Returns:
        Cropped image region as numpy array.
    """
    largest = max(bboxes, key=lambda b: b.get("area", 0))
    return crop_to_single_bbox(image, largest, pad_ratio)


def center_crop(image: np.ndarray, crop_ratio: float = VLM_CROP_RATIO) -> np.ndarray:
    """Crop center portion of the image.

    Args:
        image: Input image as numpy array (H, W, C).
        crop_ratio: Fraction of each dimension to keep (centered).

    Returns:
        Center-cropped image as numpy array.
    """
    img_h, img_w = image.shape[:2]
    margin_x = int(img_w * (1 - crop_ratio) / 2)
    margin_y = int(img_h * (1 - crop_ratio) / 2)

    x1 = margin_x
    y1 = margin_y
    x2 = img_w - margin_x
    y2 = img_h - margin_y

    return image[y1:y2, x1:x2]


def resize_image(image: np.ndarray, target_size: int) -> np.ndarray:
    """Resize image to target_size x target_size using Lanczos interpolation.

    Args:
        image: Input image as numpy array.
        target_size: Target width and height in pixels.

    Returns:
        Resized image as numpy array.
    """
    return cv2.resize(image, (target_size, target_size), interpolation=cv2.INTER_LANCZOS4)


# ---------------------------------------------------------------------------
# Label formatting
# ---------------------------------------------------------------------------


def format_label(entry: dict[str, Any]) -> str:
    """Create the Florence-2 OCR label from a ground truth entry.

    For original images (with strand): heat_number + newline + strand + space + sequence.
    For Roboflow images (no strand): heat_number + newline + sequence.

    Args:
        entry: Ground truth dict with heat_number, strand, sequence fields.

    Returns:
        Formatted label string (without the <OCR> prefix).
    """
    heat = entry["heat_number"]
    strand = entry.get("strand")
    sequence = entry.get("sequence")

    if sequence:
        if strand:
            return f"{heat}\n{strand} {sequence}"
        else:
            return f"{heat}\n{sequence}"
    else:
        return heat


# ---------------------------------------------------------------------------
# Data augmentation
# ---------------------------------------------------------------------------


def augment_image(
    image: np.ndarray,
    rng: np.random.RandomState,
    max_rotation: float = 10.0,
    brightness_range: float = 0.2,
    contrast_range: float = 0.2,
    min_crop_ratio: float = 0.95,
) -> np.ndarray:
    """Apply random augmentations to a training image.

    Augmentations applied (in order):
        1. Random rotation within [-max_rotation, +max_rotation] degrees
        2. Random brightness jitter within [-brightness_range, +brightness_range]
        3. Random contrast jitter within [1 - contrast_range, 1 + contrast_range]
        4. Random crop between [min_crop_ratio, 1.0] of each dimension

    Note: NO horizontal flip is applied (would reverse digit order).

    Args:
        image: Input image as numpy array (H, W, C).
        rng: NumPy RandomState for reproducible augmentation.
        max_rotation: Maximum rotation angle in degrees (symmetric).
        brightness_range: Brightness adjustment range as fraction.
        contrast_range: Contrast adjustment range as fraction.
        min_crop_ratio: Minimum fraction of image to keep when random-cropping.

    Returns:
        Augmented image as numpy array with same shape as input.
    """
    h, w = image.shape[:2]
    result = image.copy()

    # 1. Random rotation
    angle = rng.uniform(-max_rotation, max_rotation)
    center = (w / 2, h / 2)
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    result = cv2.warpAffine(
        result, rot_matrix, (w, h),
        borderMode=cv2.BORDER_REFLECT_101,
    )

    # 2. Brightness jitter
    brightness_delta = rng.uniform(-brightness_range, brightness_range) * 255
    result = result.astype(np.float32) + brightness_delta

    # 3. Contrast jitter
    contrast_factor = rng.uniform(1 - contrast_range, 1 + contrast_range)
    mean_val = np.mean(result)
    result = (result - mean_val) * contrast_factor + mean_val

    # Clip and convert back to uint8
    result = np.clip(result, 0, 255).astype(np.uint8)

    # 4. Random crop (95-100% of image, then resize back to original dimensions)
    crop_ratio = rng.uniform(min_crop_ratio, 1.0)
    crop_h = int(h * crop_ratio)
    crop_w = int(w * crop_ratio)

    top = rng.randint(0, h - crop_h + 1)
    left = rng.randint(0, w - crop_w + 1)

    result = result[top:top + crop_h, left:left + crop_w]
    result = cv2.resize(result, (w, h), interpolation=cv2.INTER_LANCZOS4)

    return result


# ---------------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------------


def prepare_dataset(
    gt_entries: list[dict[str, Any]],
    bboxes: dict[str, list[dict[str, Any]]],
    raw_dir: Path,
    output_dir: Path,
    target_size: int = 768,
    augment_factor: int = 3,
    seed: int = 42,
) -> dict[str, Any]:
    """Prepare the full Florence-2 training dataset.

    Supports both per-image GT (v1) and per-billet GT (v2) formats.
    V2 entries have a "bbox" field with the exact bounding box to crop.
    V1 entries iterate all bboxes for the image from the bboxes dict.

    Args:
        gt_entries: Filtered ground truth entries with valid heat numbers.
        bboxes: Dict mapping image filenames to bbox annotations.
        raw_dir: Directory containing raw images.
        output_dir: Root output directory for the dataset.
        target_size: Target resolution (square) for output images.
        augment_factor: Number of augmented copies per training image.
        seed: Random seed for reproducibility.

    Returns:
        Dict with summary statistics.
    """
    rng = np.random.RandomState(seed)
    random.seed(seed)

    # Prepare output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    # Collect valid (image, label) pairs
    samples: list[tuple[np.ndarray, str, str]] = []  # (image, label, source_name)
    skipped_missing = 0
    skipped_load_error = 0

    # Cache loaded images to avoid re-reading the same file for multiple bboxes
    _image_cache: dict[str, np.ndarray] = {}

    for entry in gt_entries:
        img_name = entry["image"]
        img_path = raw_dir / img_name

        if not img_path.exists():
            skipped_missing += 1
            continue

        if img_name not in _image_cache:
            loaded = cv2.imread(str(img_path))
            if loaded is None:
                skipped_load_error += 1
                continue
            _image_cache[img_name] = loaded
        image = _image_cache[img_name]

        # GT V2: entry has its own bbox (per-billet)
        if "bbox" in entry and entry["bbox"]:
            cropped = crop_to_single_bbox(image, entry["bbox"])
            source = f"{img_name}:bbox{entry.get('bbox_index', 0)}"
        elif img_name in bboxes and bboxes[img_name]:
            # GT V1: iterate ALL bboxes for this image
            for bbox_idx, bbox in enumerate(bboxes[img_name]):
                cropped_multi = crop_to_single_bbox(image, bbox)
                resized_multi = resize_image(cropped_multi, target_size)
                label_multi = format_label(entry)
                samples.append((resized_multi, label_multi, f"{img_name}:bbox{bbox_idx}"))
            continue  # Skip the single-crop path below
        else:
            # No bbox at all — center crop
            cropped = center_crop(image)
            source = img_name

        # Resize to target resolution
        resized = resize_image(cropped, target_size)

        # Format the label
        label = format_label(entry)

        samples.append((resized, label, source))

    if not samples:
        print("ERROR: No valid samples found. Check paths and ground truth.")
        return {"total": 0, "train": 0, "val": 0}

    # Image-level split 80/20 (prevents data leakage from same-image crops)
    from collections import defaultdict

    image_groups: defaultdict[str, list] = defaultdict(list)
    for sample in samples:
        source_img = sample[2].split(":")[0]  # "img.jpg:bbox5" → "img.jpg"
        image_groups[source_img].append(sample)

    image_keys = list(image_groups.keys())
    random.shuffle(image_keys)
    split_idx = max(1, int(len(image_keys) * 0.8))
    train_images = image_keys[:split_idx]
    val_images = image_keys[split_idx:]

    train_samples = [s for img in train_images for s in image_groups[img]]
    val_samples = [s for img in val_images for s in image_groups[img]]

    # Ensure at least 1 sample in each split
    if not train_samples:
        train_samples = samples[:1]
        val_samples = samples[1:]
    if not val_samples and len(samples) > 1:
        val_samples = [train_samples.pop()]

    # Write validation set (clean images, no augmentation)
    val_metadata: list[dict[str, str]] = []
    for idx, (image, label, _source) in enumerate(val_samples):
        fname = f"img_{idx:04d}.jpg"
        out_path = val_dir / fname
        cv2.imwrite(str(out_path), image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        val_metadata.append({
            "file_name": fname,
            "text": f"<OCR>{label}",
        })

    _write_metadata_jsonl(val_dir / "metadata.jsonl", val_metadata)

    # Write training set (original + augmented copies)
    train_metadata: list[dict[str, str]] = []
    img_counter = 0

    for image, label, _source in train_samples:
        # Save original (clean) image
        fname = f"img_{img_counter:04d}.jpg"
        out_path = train_dir / fname
        cv2.imwrite(str(out_path), image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        train_metadata.append({
            "file_name": fname,
            "text": f"<OCR>{label}",
        })
        img_counter += 1

        # Save augmented copies
        for aug_idx in range(augment_factor):
            aug_image = augment_image(image, rng)
            fname = f"img_{img_counter:04d}.jpg"
            out_path = train_dir / fname
            cv2.imwrite(str(out_path), aug_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            train_metadata.append({
                "file_name": fname,
                "text": f"<OCR>{label}",
            })
            img_counter += 1

    _write_metadata_jsonl(train_dir / "metadata.jsonl", train_metadata)

    stats = {
        "total_gt_entries": len(gt_entries),
        "valid_samples": len(samples),
        "skipped_missing": skipped_missing,
        "skipped_load_error": skipped_load_error,
        "train_originals": len(train_samples),
        "val_originals": len(val_samples),
        "augment_factor": augment_factor,
        "train_total": len(train_metadata),
        "val_total": len(val_metadata),
        "target_size": target_size,
        "output_dir": str(output_dir),
    }

    return stats


def _write_metadata_jsonl(path: Path, records: list[dict[str, str]]) -> None:
    """Write a list of dicts as a JSONL file (one JSON object per line).

    Args:
        path: Output file path.
        records: List of dicts to serialize.
    """
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Prepare Florence-2 LoRA fine-tuning dataset from billet OCR ground truth.",
    )
    parser.add_argument(
        "--augment-factor",
        type=int,
        default=3,
        help="Number of augmented copies per training image (default: 3).",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=768,
        help="Target image resolution in pixels, square (default: 768).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/training/florence2/).",
    )
    parser.add_argument(
        "--gt-v2",
        action="store_true",
        default=False,
        help="Use per-billet ground truth (ground_truth_v2.json).",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: load data, prepare dataset, print summary."""
    args = parse_args()

    gt_path = (
        ANNOTATED_DIR / "ground_truth_v2.json" if args.gt_v2
        else ANNOTATED_DIR / "ground_truth.json"
    )
    bbox_path = BBOX_ANNOTATIONS_PATH
    raw_dir = RAW_DIR

    output_dir: Path
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = _PROJECT_ROOT / output_dir
    else:
        output_dir = _PROJECT_ROOT / "data" / "training" / "florence2"

    print("=" * 60)
    print("Florence-2 Training Dataset Preparation")
    print("=" * 60)
    print(f"  Ground truth:    {gt_path}")
    print(f"  Bboxes:          {bbox_path}")
    print(f"  Raw images:      {raw_dir}")
    print(f"  Output dir:      {output_dir}")
    print(f"  Target size:     {args.target_size}x{args.target_size}")
    print(f"  Augment factor:  {args.augment_factor}")
    print(f"  Seed:            {args.seed}")
    print("=" * 60)

    # Load data
    print("\nLoading ground truth...")
    if args.gt_v2:
        gt_entries = load_ground_truth_v2(gt_path)
        print(f"  Found {len(gt_entries)} training-quality entries (V2: valid heat, clean or heat-only seq).")
    else:
        gt_entries = load_ground_truth(gt_path)
        print(f"  Found {len(gt_entries)} entries with valid heat numbers (5+ digits).")

    print("Loading bounding box annotations...")
    bboxes = load_bboxes(bbox_path)
    print(f"  Found annotations for {len(bboxes)} images.")

    # Prepare dataset
    print("\nProcessing images...")
    stats = prepare_dataset(
        gt_entries=gt_entries,
        bboxes=bboxes,
        raw_dir=raw_dir,
        output_dir=output_dir,
        target_size=args.target_size,
        augment_factor=args.augment_factor,
        seed=args.seed,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Dataset Summary")
    print("=" * 60)
    print(f"  Ground truth entries (total):     {stats.get('total_gt_entries', 0)}")
    print(f"  Valid samples loaded:             {stats.get('valid_samples', 0)}")
    print(f"  Skipped (image not found):        {stats.get('skipped_missing', 0)}")
    print(f"  Skipped (load error):             {stats.get('skipped_load_error', 0)}")
    print(f"  ----")
    print(f"  Train originals:                  {stats.get('train_originals', 0)}")
    print(f"  Train total (with augmentation):  {stats.get('train_total', 0)}")
    print(f"  Val total:                        {stats.get('val_total', 0)}")
    print(f"  Augment factor:                   {stats.get('augment_factor', 0)}")
    print(f"  Target size:                      {stats.get('target_size', 0)}x{stats.get('target_size', 0)}")
    print(f"  Output directory:                 {stats.get('output_dir', '')}")
    print("=" * 60)

    train_meta = output_dir / "train" / "metadata.jsonl"
    val_meta = output_dir / "val" / "metadata.jsonl"
    if train_meta.exists():
        print(f"\n  Train metadata: {train_meta}")
    if val_meta.exists():
        print(f"  Val metadata:   {val_meta}")

    print("\nDone.")


if __name__ == "__main__":
    main()
