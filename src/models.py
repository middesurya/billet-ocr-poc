"""Shared data models for the Billet OCR pipeline."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class OCRMethod(str, Enum):
    """Method used to produce the OCR reading."""
    PADDLE_RAW = "paddle_raw"
    PADDLE_PREPROCESSED = "paddle_preprocessed"
    PADDLE_BBOX_CROP = "paddle_bbox_crop"
    VLM_CLAUDE = "vlm_claude"
    VLM_FLORENCE2 = "vlm_florence2"
    ENSEMBLE = "ensemble"
    ENSEMBLE_V2 = "ensemble_v2"
    MANUAL = "manual"


@dataclass
class BoundingBox:
    """Bounding box for a detected text region.

    Attributes:
        points: List of 4 (x, y) corner points in clockwise order.
    """
    points: list[tuple[float, float]]


@dataclass
class BilletROI:
    """Detected billet end face region of interest.

    Attributes:
        corners: 4 corner points in order: TL, TR, BR, BL.
        bounding_rect: Axis-aligned bounding rectangle (x, y, w, h).
        area: Contour area in pixels.
        confidence: Detection confidence 0.0-1.0.
        contour: Raw OpenCV contour array (optional).
    """
    corners: list[tuple[float, float]]
    bounding_rect: tuple[int, int, int, int]
    area: float
    confidence: float
    contour: Optional[np.ndarray] = None


@dataclass
class OCRResult:
    """Single text detection + recognition result from OCR engine.

    Attributes:
        text: Recognized text string.
        confidence: Recognition confidence score (0.0 to 1.0).
        bbox: Bounding box of the detected text region.
    """
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None


@dataclass
class BilletReading:
    """Structured reading extracted from a billet end face.

    Attributes:
        heat_number: 5-7 digit heat number (e.g., "184767").
        strand: Single digit strand identifier (e.g., "3").
        sequence: 1-3 digit sequence number (e.g., "09").
        confidence: Overall confidence score for this reading (0.0 to 1.0).
        method: Which OCR method produced this reading.
        raw_texts: Original unprocessed text lines from OCR.
    """
    heat_number: Optional[str] = None
    strand: Optional[str] = None
    sequence: Optional[str] = None
    confidence: float = 0.0
    method: OCRMethod = OCRMethod.PADDLE_RAW
    raw_texts: list[str] = field(default_factory=list)


@dataclass
class GroundTruth:
    """Ground truth annotation for a single billet image.

    Attributes:
        image: Filename of the image (relative to data/raw/).
        heat_number: Correct heat number.
        strand: Correct strand identifier.
        sequence: Correct sequence number.
        notes: Optional human notes about image quality/difficulty.
    """
    image: str
    heat_number: str
    strand: Optional[str] = None
    sequence: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BilletGroundTruth:
    """Ground truth for a SINGLE billet within a multi-billet image.

    Each surveillance image has ~9 billets. This stores GT per billet,
    with an explicit bbox_index and bbox coordinates so that benchmarking
    uses the exact same crop that was labeled.

    Attributes:
        image: Original image filename (relative to data/raw/).
        bbox_index: Which bbox in roboflow_bboxes.json (0-indexed).
        bbox: Bounding box dict with x, y, width, height keys.
        heat_number: Correct heat number (e.g., "60731").
        sequence: Correct sequence number (e.g., "5282").
        strand: Correct strand identifier.
        all_text: All text lines read from the billet face.
        vlm_confidence: VLM confidence when GT was extracted.
        verified: True after human review of the crop image.
        notes: Optional human notes about this billet.
    """
    image: str
    bbox_index: int
    bbox: dict
    heat_number: str
    sequence: Optional[str] = None
    strand: Optional[str] = None
    all_text: list[str] = field(default_factory=list)
    vlm_confidence: float = 0.0
    verified: bool = False
    notes: str = ""


@dataclass
class ImageBenchmarkResult:
    """Benchmark result for a single image across all methods.

    Attributes:
        image: Filename of the image.
        ground_truth: The ground truth annotation.
        readings: Dict mapping OCRMethod to the BilletReading result.
        char_accuracies: Dict mapping OCRMethod to character-level accuracy.
        word_accuracies: Dict mapping OCRMethod to word-level (exact match) accuracy.
        preprocessing_time_ms: Time spent on preprocessing in milliseconds.
        ocr_time_ms: Dict mapping OCRMethod to OCR inference time in ms.
    """
    image: str
    ground_truth: GroundTruth
    readings: dict[OCRMethod, BilletReading] = field(default_factory=dict)
    char_accuracies: dict[OCRMethod, float] = field(default_factory=dict)
    word_accuracies: dict[OCRMethod, float] = field(default_factory=dict)
    preprocessing_time_ms: float = 0.0
    ocr_time_ms: dict[OCRMethod, float] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """Aggregate benchmark report across all images.

    Attributes:
        results: Per-image benchmark results.
        avg_char_accuracy: Average character accuracy per method.
        avg_word_accuracy: Average word (exact match) accuracy per method.
        avg_time_ms: Average total processing time per method.
        total_images: Number of images benchmarked.
        timestamp: ISO format timestamp of when the benchmark was run.
    """
    results: list[ImageBenchmarkResult] = field(default_factory=list)
    avg_char_accuracy: dict[OCRMethod, float] = field(default_factory=dict)
    avg_word_accuracy: dict[OCRMethod, float] = field(default_factory=dict)
    avg_time_ms: dict[OCRMethod, float] = field(default_factory=dict)
    total_images: int = 0
    timestamp: str = ""
