"""Convert COCO annotations from Roboflow to YOLOv8 format for training.

Reads the COCO-format annotation files from the Roboflow download directory
and creates a YOLO-format dataset with label text files and a dataset.yaml.

Usage:
    python scripts/prepare_yolo_training.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ROBOFLOW_DOWNLOAD_DIR

YOLO_DATASET_DIR = PROJECT_ROOT / "data" / "yolo_dataset"
CLASS_NAME = "billet"


def convert_coco_to_yolo(split: str) -> int:
    """Convert COCO annotations for one split to YOLO format.

    COCO bbox format: [x, y, width, height] (absolute pixels, top-left origin)
    YOLO format: [class x_center y_center width height] (normalized 0-1)

    Args:
        split: Either "train" or "valid".

    Returns:
        Number of images processed.
    """
    yolo_split = "val" if split == "valid" else split
    src_dir = ROBOFLOW_DOWNLOAD_DIR / split
    ann_path = src_dir / "_annotations.coco.json"

    if not ann_path.exists():
        print(f"  [SKIP] No annotations at {ann_path}")
        return 0

    with open(ann_path, encoding="utf-8") as f:
        coco = json.load(f)

    # Build image ID → image info lookup
    images_by_id: dict[int, dict] = {img["id"]: img for img in coco["images"]}

    # Build image ID → annotations lookup
    anns_by_image: dict[int, list[dict]] = {}
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        anns_by_image.setdefault(img_id, []).append(ann)

    # Create output directories
    img_out_dir = YOLO_DATASET_DIR / "images" / yolo_split
    lbl_out_dir = YOLO_DATASET_DIR / "labels" / yolo_split
    img_out_dir.mkdir(parents=True, exist_ok=True)
    lbl_out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for img_id, img_info in images_by_id.items():
        filename = img_info["file_name"]
        img_w = img_info["width"]
        img_h = img_info["height"]

        # Copy image file
        src_img = src_dir / filename
        if not src_img.exists():
            continue

        dst_img = img_out_dir / filename
        if not dst_img.exists():
            shutil.copy2(src_img, dst_img)

        # Write YOLO label file
        stem = Path(filename).stem
        label_path = lbl_out_dir / f"{stem}.txt"

        annotations = anns_by_image.get(img_id, [])
        lines: list[str] = []
        for ann in annotations:
            x, y, w, h = ann["bbox"]  # COCO: top-left x, y, width, height

            # Convert to YOLO: center x, center y, width, height (all normalized)
            x_center = (x + w / 2) / img_w
            y_center = (y + h / 2) / img_h
            w_norm = w / img_w
            h_norm = h / img_h

            # Clamp to [0, 1]
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            w_norm = max(0.0, min(1.0, w_norm))
            h_norm = max(0.0, min(1.0, h_norm))

            lines.append(f"0 {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

        with open(label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        count += 1

    return count


def write_dataset_yaml() -> None:
    """Write the dataset.yaml config file for YOLOv8 training."""
    yaml_content = f"""# YOLOv8 billet detection dataset
# Auto-generated from Roboflow COCO annotations

path: {YOLO_DATASET_DIR.as_posix()}
train: images/train
val: images/val

nc: 1
names:
  0: {CLASS_NAME}
"""
    yaml_path = YOLO_DATASET_DIR / "dataset.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"  Written: {yaml_path}")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Preparing YOLOv8 training dataset from Roboflow COCO annotations")
    print("=" * 60)

    if not ROBOFLOW_DOWNLOAD_DIR.exists():
        print(f"ERROR: Roboflow download directory not found: {ROBOFLOW_DOWNLOAD_DIR}")
        print("Run: python scripts/download_roboflow_dataset.py --copy-to-raw --clear-raw")
        sys.exit(1)

    YOLO_DATASET_DIR.mkdir(parents=True, exist_ok=True)

    for split in ("train", "valid"):
        print(f"\nProcessing {split} split...")
        count = convert_coco_to_yolo(split)
        print(f"  Converted {count} images to YOLO format")

    write_dataset_yaml()

    # Print summary
    train_labels = list((YOLO_DATASET_DIR / "labels" / "train").glob("*.txt"))
    val_labels = list((YOLO_DATASET_DIR / "labels" / "val").glob("*.txt"))
    print(f"\nDataset ready at: {YOLO_DATASET_DIR}")
    print(f"  Train: {len(train_labels)} images")
    print(f"  Val:   {len(val_labels)} images")
    print(f"\nNext: python scripts/train_yolo_detector.py")


if __name__ == "__main__":
    main()
