"""Pydantic response models for the Billet OCR API."""

from __future__ import annotations

from pydantic import BaseModel


class BilletPrediction(BaseModel):
    """Per-billet prediction from the V11 ensemble pipeline."""

    bbox_index: int
    bbox: dict
    crop_url: str
    f2_orient: dict  # {heat_number, sequence, confidence, raw_texts}
    paddle: dict  # {heat_number, sequence, confidence}
    ensemble: dict  # {heat_number, sequence, confidence, decision}


class ImageResult(BaseModel):
    """Summary of all billets detected in a single image."""

    friendly_name: str
    source_url: str
    annotated_url: str
    num_billets: int
    billets: list[BilletPrediction]
    confidence_summary: dict  # {high, medium, low}
    distinct_heats: list[str]


class ImageListItem(BaseModel):
    """Compact summary for the browse sidebar."""

    friendly_name: str
    num_billets: int
    confidence_summary: dict
    distinct_heats: list[str]
    is_consistent: bool  # True if all billets share one heat number


class BrowseStatsResponse(BaseModel):
    """Aggregate stats across all pre-computed inference results."""

    total_images: int
    total_billets: int
    pipeline: str
    confidence_distribution: dict  # {high, medium, low}
    decision_distribution: dict  # {AGREE: N, DISAGREE_PADDLE: N, ...}
    consistency: dict  # {consistent, inconsistent}


class HealthResponse(BaseModel):
    """Basic health check."""

    status: str
    pipeline: str
    browse_images: int
    models_loaded: bool


class InferenceResponse(BaseModel):
    """Response from live inference on an uploaded image."""

    source_url: str
    annotated_url: str
    num_billets: int
    billets: list[BilletPrediction]
    elapsed_ms: float
    bbox_source: str  # "roboflow_api", "edge_detection", or "roboflow_annotations"
