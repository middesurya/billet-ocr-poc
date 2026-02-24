"""Download the steel billet dataset from Roboflow Universe.

Downloads the ztai/steel-billet dataset in COCO format, which provides:
- ~602 surveillance camera images of steel billets
- COCO bounding box annotations for billet locations ('batch' class)

The images are surveillance camera screenshots — billets appear as
regions within the frame. Bounding boxes identify where billets are.

Usage:
    python scripts/download_roboflow_dataset.py
    python scripts/download_roboflow_dataset.py --copy-to-raw
    python scripts/download_roboflow_dataset.py --api-key rf_xxxxx
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from loguru import logger

from src.config import (
    RAW_DIR,
    ROBOFLOW_API_KEY,
    ROBOFLOW_DOWNLOAD_DIR,
    ROBOFLOW_PROJECT,
    ROBOFLOW_VERSION,
    ROBOFLOW_WORKSPACE,
    SUPPORTED_FORMATS,
)


def download_dataset(
    api_key: str,
    workspace: str = ROBOFLOW_WORKSPACE,
    project: str = ROBOFLOW_PROJECT,
    version: int = ROBOFLOW_VERSION,
    download_dir: Path = ROBOFLOW_DOWNLOAD_DIR,
    format: str = "coco",
) -> Path:
    """Download a Roboflow dataset in the specified format.

    Args:
        api_key: Roboflow API key (starts with 'rf_').
        workspace: Roboflow workspace name.
        project: Roboflow project name.
        version: Dataset version number.
        download_dir: Local directory to save the download.
        format: Export format ('coco', 'yolov8', 'voc', etc.).

    Returns:
        Path to the downloaded dataset directory.

    Raises:
        ImportError: If roboflow package is not installed.
        ValueError: If API key is empty.
    """
    if not api_key:
        raise ValueError(
            "Roboflow API key is required. Set ROBOFLOW_API_KEY in .env "
            "or pass --api-key. Get a free key at https://app.roboflow.com/"
        )

    try:
        from roboflow import Roboflow
    except ImportError:
        raise ImportError(
            "roboflow package not installed. Run: pip install roboflow"
        )

    logger.info(
        "Downloading dataset: {}/{} v{} in '{}' format",
        workspace, project, version, format,
    )
    logger.info("Download directory: {}", download_dir)

    rf = Roboflow(api_key=api_key)
    proj = rf.workspace(workspace).project(project)
    ds = proj.version(version)

    # Roboflow SDK skips download if location exists, so use overwrite=True
    download_dir.mkdir(parents=True, exist_ok=True)
    ds.download(format, location=str(download_dir), overwrite=True)

    logger.info("Download complete: {}", download_dir)
    return download_dir


def copy_images_to_raw(
    download_dir: Path = ROBOFLOW_DOWNLOAD_DIR,
    raw_dir: Path = RAW_DIR,
    clear_existing: bool = False,
) -> int:
    """Copy downloaded images from all splits into data/raw/.

    Args:
        download_dir: Root of the Roboflow download (contains train/valid/test).
        raw_dir: Target directory for raw images.
        clear_existing: If True, removes existing files in raw_dir first.

    Returns:
        Number of images copied.
    """
    if clear_existing:
        # Only remove image files, not the directory itself
        existing = list(raw_dir.glob("*"))
        for f in existing:
            if f.suffix.lower() in SUPPORTED_FORMATS:
                f.unlink()
        logger.info("Cleared {} existing images from {}", len(existing), raw_dir)

    raw_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    # Roboflow COCO downloads have train/valid/test subdirectories
    for split_dir in sorted(download_dir.iterdir()):
        if not split_dir.is_dir():
            continue
        for img_file in sorted(split_dir.iterdir()):
            if img_file.suffix.lower() in SUPPORTED_FORMATS:
                dest = raw_dir / img_file.name
                if not dest.exists():
                    shutil.copy2(img_file, dest)
                    copied += 1

    logger.info("Copied {} images to {}", copied, raw_dir)
    return copied


def count_dataset_images(download_dir: Path = ROBOFLOW_DOWNLOAD_DIR) -> dict[str, int]:
    """Count images per split in the downloaded dataset.

    Args:
        download_dir: Root of the Roboflow download.

    Returns:
        Dict mapping split name to image count.
    """
    counts: dict[str, int] = {}
    for split_dir in sorted(download_dir.iterdir()):
        if not split_dir.is_dir():
            continue
        n = sum(
            1 for f in split_dir.iterdir()
            if f.suffix.lower() in SUPPORTED_FORMATS
        )
        counts[split_dir.name] = n
    return counts


def main() -> None:
    """CLI entry point for dataset download."""
    parser = argparse.ArgumentParser(
        description="Download steel billet dataset from Roboflow Universe",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api-key",
        default=ROBOFLOW_API_KEY,
        help="Roboflow API key (or set ROBOFLOW_API_KEY in .env)",
    )
    parser.add_argument(
        "--copy-to-raw",
        action="store_true",
        help="Copy downloaded images into data/raw/ after download",
    )
    parser.add_argument(
        "--clear-raw",
        action="store_true",
        help="Clear existing images in data/raw/ before copying (use with --copy-to-raw)",
    )
    parser.add_argument(
        "--download-dir",
        default=str(ROBOFLOW_DOWNLOAD_DIR),
        help="Local directory for the download",
    )
    parser.add_argument(
        "--format",
        default="coco",
        choices=["coco", "yolov8", "voc", "darknet"],
        help="Export format for the dataset",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, only copy existing download to data/raw/",
    )
    args = parser.parse_args()

    download_dir = Path(args.download_dir)

    if not args.skip_download:
        download_dataset(
            api_key=args.api_key,
            download_dir=download_dir,
            format=args.format,
        )

    # Show download stats
    counts = count_dataset_images(download_dir)
    total = sum(counts.values())
    logger.info("Dataset statistics:")
    for split, count in counts.items():
        logger.info("  {}: {} images", split, count)
    logger.info("  Total: {} images", total)

    if args.copy_to_raw:
        copy_images_to_raw(
            download_dir=download_dir,
            clear_existing=args.clear_raw,
        )

    logger.info("Done! Next steps:")
    logger.info("  1. Run: python scripts/parse_roboflow_annotations.py")
    logger.info("  2. Run: python scripts/triage_dataset.py")
    logger.info("  3. Run: python scripts/extract_ground_truth.py --max-images 50")


if __name__ == "__main__":
    main()
