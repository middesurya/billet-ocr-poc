"""Test the full inference pipeline on validation images WITHOUT annotation lookup.

Loads images from the Roboflow validation set and runs them through the
detection + OCR pipeline as if they were brand-new uploads. This tests:
1. YOLO detector (if trained) or edge detection fallback
2. Sequence number extraction fix
3. Full V11 ensemble pipeline

Usage:
    python scripts/test_yolo_inference.py
    python scripts/test_yolo_inference.py --max-images 5
    python scripts/test_yolo_inference.py --save-annotated
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    FLORENCE2_BBOX_PAD_RATIO,
    INFERENCE_REVIEW_LIVE_DIR,
    ROBOFLOW_DOWNLOAD_DIR,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test pipeline on validation images (no annotations)")
    parser.add_argument("--max-images", type=int, default=5, help="Max images to process")
    parser.add_argument("--save-annotated", action="store_true", help="Save annotated images")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for image selection")
    return parser.parse_args()


def detect_without_annotations(image: np.ndarray) -> tuple[list[dict], str]:
    """Detect billets WITHOUT Roboflow annotation lookup.

    Only uses YOLO detector → edge detection fallback.

    Args:
        image: BGR numpy array.

    Returns:
        Tuple of (bboxes, bbox_source).
    """
    # Tier 1: YOLO detector
    from src.preprocessing.yolo_detector import detect_billets_yolo

    yolo_bboxes = detect_billets_yolo(image)
    if yolo_bboxes is not None and len(yolo_bboxes) > 0:
        return yolo_bboxes, "yolo_detector"

    # Tier 2: Edge detection fallback
    from src.preprocessing.roi_detector import detect_billet_faces

    rois = detect_billet_faces(image, max_faces=20)
    bboxes: list[dict] = []
    for roi in rois:
        x, y, w, h = roi.bounding_rect
        bboxes.append({"x": x, "y": y, "width": w, "height": h})
    return bboxes, "edge_detection"


def main() -> None:
    args = parse_args()

    valid_dir = ROBOFLOW_DOWNLOAD_DIR / "valid"
    if not valid_dir.exists():
        print(f"ERROR: Validation directory not found: {valid_dir}")
        sys.exit(1)

    # Get all images (exclude annotation files)
    image_files = sorted([
        f for f in valid_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")
    ])

    # Seed & select
    rng = np.random.RandomState(args.seed)
    indices = rng.permutation(len(image_files))[:args.max_images]
    selected = [image_files[i] for i in indices]

    print("=" * 70)
    print(f"Testing pipeline on {len(selected)} validation images (NO annotations)")
    print("=" * 70)

    all_results: list[dict] = []

    for img_idx, img_path in enumerate(selected):
        print(f"\n--- Image {img_idx + 1}/{len(selected)}: {img_path.name} ---")
        t0 = time.perf_counter()

        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  SKIP: failed to load")
            continue

        # Detect billets WITHOUT annotation lookup
        bboxes, bbox_source = detect_without_annotations(image)
        print(f"  Detection: {bbox_source} → {len(bboxes)} billets")

        if not bboxes:
            print(f"  WARNING: No billets detected!")
            all_results.append({
                "image": img_path.name,
                "bbox_source": bbox_source,
                "num_billets": 0,
                "billets": [],
            })
            continue

        # Run inference on each billet
        from src.ocr.inference import crop_to_bbox, draw_annotated_image, run_billet_inference

        predictions: list[dict] = []
        for bbox_idx, bbox in enumerate(bboxes):
            bbox_crop = crop_to_bbox(image, bbox, pad_ratio=FLORENCE2_BBOX_PAD_RATIO)
            pred = run_billet_inference(bbox_crop)
            predictions.append(pred)

            ens = pred.get("ensemble", {})
            heat = ens.get("heat_number") or "???"
            seq = ens.get("sequence") or "—"
            conf = ens.get("confidence", 0.0)
            decision = ens.get("decision", "?")
            print(f"  [{bbox_idx}] heat={heat:>6s}  seq={seq:>5s}  conf={conf:.0%}  [{decision}]")

        elapsed = time.perf_counter() - t0

        # Save annotated image
        if args.save_annotated:
            annotated = draw_annotated_image(image, bboxes, predictions)
            out_path = INFERENCE_REVIEW_LIVE_DIR / f"test_{img_path.stem}_annotated.jpg"
            cv2.imwrite(str(out_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"  Saved: {out_path.name}")

        all_results.append({
            "image": img_path.name,
            "bbox_source": bbox_source,
            "num_billets": len(bboxes),
            "elapsed_s": round(elapsed, 1),
            "billets": [
                {
                    "bbox_index": i,
                    "heat_number": p.get("ensemble", {}).get("heat_number"),
                    "sequence": p.get("ensemble", {}).get("sequence"),
                    "confidence": p.get("ensemble", {}).get("confidence", 0.0),
                    "decision": p.get("ensemble", {}).get("decision", "ERROR"),
                }
                for i, p in enumerate(predictions)
            ],
        })

        print(f"  Time: {elapsed:.1f}s")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_billets = sum(r["num_billets"] for r in all_results)
    yolo_images = sum(1 for r in all_results if r["bbox_source"] == "yolo_detector")
    edge_images = sum(1 for r in all_results if r["bbox_source"] == "edge_detection")

    billets_with_heat = 0
    billets_with_seq = 0
    for r in all_results:
        for b in r.get("billets", []):
            if b.get("heat_number"):
                billets_with_heat += 1
            if b.get("sequence"):
                billets_with_seq += 1

    print(f"  Images processed:  {len(all_results)}")
    print(f"  Detection method:  YOLO={yolo_images}, Edge={edge_images}")
    print(f"  Total billets:     {total_billets}")
    print(f"  With heat number:  {billets_with_heat}/{total_billets}")
    print(f"  With sequence:     {billets_with_seq}/{total_billets}")

    # Save results
    results_path = INFERENCE_REVIEW_LIVE_DIR / "test_yolo_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to: {results_path}")


if __name__ == "__main__":
    main()
