"""Visual inference on held-out validation images for manual inspection.

Runs the full V11 ensemble pipeline (F2 Multi-Orient + PaddleOCR+CLAHE +
cross-validation) on new images that were NOT part of the 73-billet GT set.
Produces annotated images, per-billet crops, and a structured results JSON
for human review.

Usage:
    python scripts/visual_inference.py                        # 30 images, seed=42
    python scripts/visual_inference.py --max-images 5         # quick smoke test
    python scripts/visual_inference.py --max-images 30 --seed 99  # different selection
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Path setup — make the project root importable regardless of cwd
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import (
    BBOX_ANNOTATIONS_PATH,
    FLORENCE2_BBOX_PAD_RATIO,
    GT_BBOX_PAD_RATIO,
    GT_OUTPUT_PATH,
    INFERENCE_REVIEW_ANNOTATED_DIR,
    INFERENCE_REVIEW_CROPS_DIR,
    INFERENCE_REVIEW_DIR,
    INFERENCE_REVIEW_SOURCES_DIR,
    RAW_DIR,
    ROBOFLOW_DOWNLOAD_DIR,
)
from src.models import BilletReading, OCRMethod
from src.ocr.inference import (
    crop_to_bbox as _crop_to_bbox,
    draw_annotated_image,
    infer_decision as _infer_decision,
    is_valid_5digit as _is_valid_5digit,
    run_billet_inference,
)


# ---------------------------------------------------------------------------
# GT exclusion set — base timestamps of the 14 images used for GT V2
# ---------------------------------------------------------------------------
GT_BASE_TIMESTAMPS: set[str] = {
    "20250318004238",
    "20250318052542",
    "20250318100749",
    "20250319024651",
    "20250319130327",
    "20250319133306",
    "20250319225731",
    "202503281156009789",
    "202503281651353652",
    "202503291555003304",
    "202503300011415199",
    "202503300022275249",
    "screenshot_2025-04-05_03-06-20",
    "screenshot_2025-04-05_19-05-59",
}


# ---------------------------------------------------------------------------
# Image selection
# ---------------------------------------------------------------------------


def _extract_base_timestamp(filename: str) -> str:
    """Extract the base timestamp from a Roboflow-augmented filename.

    Args:
        filename: e.g. '20250313171154_jpg.rf.4de7b6648952f10ff8d860d3c8fb9428.jpg'

    Returns:
        Base timestamp, e.g. '20250313171154'.
    """
    if "_jpg.rf." in filename:
        return filename.split("_jpg.rf.")[0]
    return filename


def select_inference_images(
    max_images: int = 30,
    seed: int = 42,
) -> list[str]:
    """Select held-out validation images that are NOT in the GT set.

    Picks one variant per base timestamp from the validation split that has
    bbox annotations. Excludes the 14 GT images.

    Args:
        max_images: Maximum number of images to select.
        seed: Random seed for reproducibility.

    Returns:
        List of image filenames (as they appear in roboflow_bboxes.json).
    """
    # Load bbox annotations
    with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as f:
        all_bboxes: dict[str, list[dict]] = json.load(f)

    # List validation images
    valid_dir = ROBOFLOW_DOWNLOAD_DIR / "valid"
    valid_files = {f.name for f in valid_dir.glob("*.jpg")}

    # Group valid images with bboxes by base timestamp
    base_to_files: dict[str, list[str]] = defaultdict(list)
    for fname in sorted(valid_files):
        if fname in all_bboxes:
            base = _extract_base_timestamp(fname)
            base_to_files[base].append(fname)

    # Filter out GT images
    eligible: list[str] = []
    for base, files in sorted(base_to_files.items()):
        if base not in GT_BASE_TIMESTAMPS:
            # Pick first variant (deterministic before random sampling)
            eligible.append(files[0])

    # Random sample
    rng = random.Random(seed)
    if len(eligible) <= max_images:
        selected = eligible
    else:
        selected = rng.sample(eligible, max_images)

    return sorted(selected)


# ---------------------------------------------------------------------------
# Per-billet inference + visual annotation: imported from src.ocr.inference
# ---------------------------------------------------------------------------
# Functions imported at top: _crop_to_bbox, run_billet_inference,
# _infer_decision, _is_valid_5digit, draw_annotated_image


# ---------------------------------------------------------------------------
# Output saving
# ---------------------------------------------------------------------------


def save_outputs(
    image_idx: int,
    source_filename: str,
    raw_img: np.ndarray,
    bboxes: list[dict],
    predictions: list[dict],
) -> dict:
    """Save source, crops, and annotated image for one inference image.

    Args:
        image_idx: 1-based index for naming.
        source_filename: Original Roboflow filename.
        raw_img: BGR source image.
        bboxes: List of bbox dicts.
        predictions: List of per-billet prediction dicts.

    Returns:
        Image result dict for results.json.
    """
    friendly = f"infer_{image_idx:02d}"

    # Source image
    src_path = INFERENCE_REVIEW_SOURCES_DIR / f"{friendly}.jpg"
    cv2.imwrite(str(src_path), raw_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # Per-billet crops (10% padding for review)
    billet_results: list[dict] = []
    for bbox_idx, (bbox, pred) in enumerate(zip(bboxes, predictions)):
        crop = _crop_to_bbox(raw_img, bbox, pad_ratio=GT_BBOX_PAD_RATIO)
        crop_name = f"{friendly}_bbox{bbox_idx:02d}.jpg"
        crop_path = INFERENCE_REVIEW_CROPS_DIR / crop_name
        cv2.imwrite(str(crop_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])

        billet_results.append({
            "bbox_index": bbox_idx,
            "bbox": {
                "x": bbox["x"],
                "y": bbox["y"],
                "width": bbox["width"],
                "height": bbox["height"],
            },
            "crop_path": f"crops/{crop_name}",
            "predictions": pred,
        })

    # Annotated image
    annotated = draw_annotated_image(raw_img, bboxes, predictions)
    ann_path = INFERENCE_REVIEW_ANNOTATED_DIR / f"{friendly}_annotated.jpg"
    cv2.imwrite(str(ann_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])

    return {
        "source_image": source_filename,
        "friendly_name": friendly,
        "num_bboxes": len(bboxes),
        "billets": billet_results,
    }


# ---------------------------------------------------------------------------
# Summary report generation
# ---------------------------------------------------------------------------


def generate_summary(results: dict) -> str:
    """Generate a Markdown summary report from inference results.

    Args:
        results: Full results dict with metadata and images.

    Returns:
        Markdown string.
    """
    lines: list[str] = []
    lines.append("# Visual Inference Report\n")
    lines.append(f"**Generated:** {results['metadata']['timestamp']}\n")
    lines.append(f"**Pipeline:** {results['metadata']['pipeline']}\n")
    lines.append(
        f"**Images:** {results['metadata']['total_images']} | "
        f"**Billets:** {results['metadata']['total_billets']} | "
        f"**Seed:** {results['metadata']['seed']}\n"
    )

    # Collect all ensemble results
    all_billets: list[dict] = []
    for img in results["images"]:
        for b in img["billets"]:
            all_billets.append({**b, "image": img["friendly_name"]})

    # Confidence distribution
    conf_high = sum(
        1 for b in all_billets if b["predictions"]["ensemble"]["confidence"] >= 0.80
    )
    conf_med = sum(
        1
        for b in all_billets
        if 0.50 <= b["predictions"]["ensemble"]["confidence"] < 0.80
    )
    conf_low = sum(
        1 for b in all_billets if b["predictions"]["ensemble"]["confidence"] < 0.50
    )
    total = len(all_billets) or 1

    lines.append("## Confidence Distribution\n")
    lines.append("| Level | Count | % |")
    lines.append("|-------|------:|--:|")
    lines.append(f"| High (>=80%) | {conf_high} | {conf_high/total:.0%} |")
    lines.append(f"| Medium (50-79%) | {conf_med} | {conf_med/total:.0%} |")
    lines.append(f"| Low (<50%) | {conf_low} | {conf_low/total:.0%} |")
    lines.append(f"| **Total** | **{total}** | **100%** |")
    lines.append("")

    # Decision distribution
    decision_counts: Counter[str] = Counter()
    for b in all_billets:
        decision_counts[b["predictions"]["ensemble"].get("decision", "ERROR")] += 1

    lines.append("## Ensemble Decision Distribution\n")
    lines.append("| Decision | Count | % |")
    lines.append("|----------|------:|--:|")
    for decision in ["AGREE", "DISAGREE_PADDLE", "F2_ONLY", "PADDLE_ONLY", "NEITHER_VALID", "ERROR"]:
        cnt = decision_counts.get(decision, 0)
        if cnt > 0:
            lines.append(f"| {decision} | {cnt} | {cnt/total:.0%} |")
    lines.append("")

    # Per-image table
    lines.append("## Per-Image Summary\n")
    lines.append("| Image | Billets | High | Med | Low | Predicted Heats |")
    lines.append("|-------|--------:|-----:|----:|----:|-----------------|")

    for img in results["images"]:
        billets = img["billets"]
        n = len(billets)
        h = sum(
            1
            for b in billets
            if b["predictions"]["ensemble"]["confidence"] >= 0.80
        )
        m = sum(
            1
            for b in billets
            if 0.50 <= b["predictions"]["ensemble"]["confidence"] < 0.80
        )
        lo = sum(
            1
            for b in billets
            if b["predictions"]["ensemble"]["confidence"] < 0.50
        )
        # Collect unique predicted heats
        heats = set()
        for b in billets:
            ht = b["predictions"]["ensemble"].get("heat_number")
            if ht and _is_valid_5digit(ht):
                heats.add(ht)
        heat_str = ", ".join(sorted(heats)) if heats else "—"
        lines.append(
            f"| {img['friendly_name']} | {n} | {h} | {m} | {lo} | {heat_str} |"
        )

    lines.append("")

    # Cross-billet consistency
    lines.append("## Cross-Billet Consistency\n")
    lines.append(
        "Billets from the same image should share one heat number. "
        "Images with multiple distinct predicted heats may indicate errors.\n"
    )

    inconsistent = 0
    for img in results["images"]:
        heats = set()
        for b in img["billets"]:
            ht = b["predictions"]["ensemble"].get("heat_number")
            if ht and _is_valid_5digit(ht):
                heats.add(ht)
        if len(heats) > 1:
            inconsistent += 1
            lines.append(
                f"- **{img['friendly_name']}**: {len(heats)} distinct heats — {sorted(heats)}"
            )

    if inconsistent == 0:
        lines.append("All images with valid predictions show single-heat consistency.")
    else:
        lines.append(
            f"\n**{inconsistent}/{results['metadata']['total_images']}** images "
            f"have multiple distinct predicted heats."
        )

    lines.append("")
    lines.append(
        "*Generated by `scripts/visual_inference.py`. "
        "Review annotated images in `data/inference_review/annotated/`.*"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def main() -> None:
    """Run visual inference on held-out validation images."""
    parser = argparse.ArgumentParser(
        description="Visual inference on held-out validation images"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=30,
        help="Number of images to process (default: 30)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for image selection (default: 42)",
    )
    parser.add_argument(
        "--no-vlm",
        action="store_true",
        default=True,
        help="Skip VLM fallback (default: True — no API calls)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Visual Inference — Held-Out Validation Images")
    print("=" * 60)

    # Select images
    selected = select_inference_images(
        max_images=args.max_images,
        seed=args.seed,
    )
    print(f"\nSelected {len(selected)} images (seed={args.seed})")

    # Verify no GT contamination
    for fname in selected:
        base = _extract_base_timestamp(fname)
        assert base not in GT_BASE_TIMESTAMPS, (
            f"GT contamination: {fname} has base {base}"
        )

    # Load bbox annotations
    with open(BBOX_ANNOTATIONS_PATH, encoding="utf-8") as f:
        all_bboxes: dict[str, list[dict]] = json.load(f)

    # Clear previous outputs
    for subdir in [
        INFERENCE_REVIEW_SOURCES_DIR,
        INFERENCE_REVIEW_CROPS_DIR,
        INFERENCE_REVIEW_ANNOTATED_DIR,
    ]:
        for old_file in subdir.glob("*"):
            old_file.unlink()

    # Process each image
    image_results: list[dict] = []
    total_billets = 0
    t_start = time.perf_counter()

    for img_idx, fname in enumerate(selected, start=1):
        img_path = RAW_DIR / fname
        bboxes = all_bboxes.get(fname, [])
        # Sort by area descending (consistent with benchmark)
        bboxes = sorted(
            bboxes,
            key=lambda b: b.get("width", 0) * b.get("height", 0),
            reverse=True,
        )
        n_bboxes = len(bboxes)
        total_billets += n_bboxes

        print(f"\n[{img_idx}/{len(selected)}] {fname} — {n_bboxes} bboxes")

        # Load image
        raw_img = cv2.imread(str(img_path))
        if raw_img is None:
            print(f"  ERROR: Failed to load {img_path}")
            continue

        # Run inference on each billet
        predictions: list[dict] = []
        for bbox_idx, bbox in enumerate(bboxes):
            bbox_crop = _crop_to_bbox(raw_img, bbox, pad_ratio=FLORENCE2_BBOX_PAD_RATIO)

            pred = run_billet_inference(bbox_crop)
            predictions.append(pred)

            ens = pred["ensemble"]
            heat = ens.get("heat_number") or "???"
            conf = ens.get("confidence", 0.0)
            decision = ens.get("decision", "?")
            print(
                f"  bbox[{bbox_idx}] {heat} ({conf:.0%}) [{decision}]"
            )

        # Save outputs
        img_result = save_outputs(img_idx, fname, raw_img, bboxes, predictions)
        image_results.append(img_result)

    elapsed = time.perf_counter() - t_start

    # Build results JSON
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = {
        "metadata": {
            "timestamp": timestamp,
            "total_images": len(image_results),
            "total_billets": total_billets,
            "seed": args.seed,
            "vlm_enabled": not args.no_vlm,
            "pipeline": "F2 Orient + PaddleOCR + Ensemble V11",
            "elapsed_seconds": round(elapsed, 1),
        },
        "images": image_results,
    }

    # Write results JSON
    results_path = INFERENCE_REVIEW_DIR / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {results_path}")

    # Generate and write summary
    summary_md = generate_summary(results)
    summary_path = INFERENCE_REVIEW_DIR / "summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    print(f"Summary saved to {summary_path}")

    # Print quick stats
    print(f"\n{'=' * 60}")
    print(f"Completed in {elapsed:.1f}s")
    print(f"Images: {len(image_results)} | Billets: {total_billets}")
    print(f"Output: {INFERENCE_REVIEW_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
