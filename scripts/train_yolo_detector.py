"""Train YOLOv8n to detect billets in surveillance images.

Uses the YOLO-format dataset prepared by prepare_yolo_training.py.
Single-class detection ("billet") — YOLOv8n (nano) is sufficient.

Usage:
    python scripts/train_yolo_detector.py
    python scripts/train_yolo_detector.py --epochs 100 --imgsz 1280 --batch 4
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

YOLO_DATASET_DIR = PROJECT_ROOT / "data" / "yolo_dataset"
OUTPUT_DIR = PROJECT_ROOT / "models" / "yolo_billet_detector"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Train YOLOv8 billet detector")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model (default: yolov8n.pt)")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs (default: 50)")
    parser.add_argument("--imgsz", type=int, default=1280, help="Image size (default: 1280)")
    parser.add_argument("--batch", type=int, default=4, help="Batch size (default: 4)")
    parser.add_argument("--device", default="0", help="Device: '0' for GPU, 'cpu' for CPU")
    parser.add_argument("--workers", type=int, default=0, help="Dataloader workers (default: 0 for Windows)")
    return parser.parse_args()


def main() -> None:
    """Train the YOLOv8 billet detector."""
    args = parse_args()

    dataset_yaml = YOLO_DATASET_DIR / "dataset.yaml"
    if not dataset_yaml.exists():
        print(f"ERROR: dataset.yaml not found at {dataset_yaml}")
        print("Run: python scripts/prepare_yolo_training.py")
        sys.exit(1)

    print("=" * 60)
    print("Training YOLOv8 billet detector")
    print(f"  Model:   {args.model}")
    print(f"  Epochs:  {args.epochs}")
    print(f"  ImgSize: {args.imgsz}")
    print(f"  Batch:   {args.batch}")
    print(f"  Device:  {args.device}")
    print(f"  Workers: {args.workers}")
    print(f"  Dataset: {dataset_yaml}")
    print("=" * 60)

    from ultralytics import YOLO

    model = YOLO(args.model)

    results = model.train(
        data=str(dataset_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=str(OUTPUT_DIR.parent),
        name=OUTPUT_DIR.name,
        exist_ok=True,
        verbose=True,
    )

    # Copy best weights to the expected location
    train_dir = Path(results.save_dir) if hasattr(results, "save_dir") else OUTPUT_DIR
    best_src = train_dir / "weights" / "best.pt"

    if best_src.exists():
        best_dst = OUTPUT_DIR / "best.pt"
        best_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_src, best_dst)
        print(f"\nBest weights saved to: {best_dst}")
    else:
        print(f"\nWARNING: best.pt not found at {best_src}")
        print("Check the training output directory for weights.")

    print("\nTraining complete!")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
