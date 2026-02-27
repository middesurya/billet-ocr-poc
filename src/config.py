"""Central configuration for the Billet OCR POC."""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_ORIGINAL_DIR = DATA_DIR / "raw_original"
ANNOTATED_DIR = DATA_DIR / "annotated"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
DEBUG_DIR = DATA_DIR / "debug"

# Roboflow dataset
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
ROBOFLOW_WORKSPACE = "ztai"
ROBOFLOW_PROJECT = "steel-billet"
ROBOFLOW_VERSION = 9  # v9: 1280x640, 1551 images (was v7: 640x640, 1783 images)
ROBOFLOW_DOWNLOAD_DIR = DATA_DIR / "roboflow_download"
BBOX_ANNOTATIONS_PATH = ANNOTATED_DIR / "roboflow_bboxes.json"
ROBOFLOW_CONFIDENCE_THRESHOLD = 0.25  # Min confidence for bbox detection (0-1)
ROBOFLOW_OVERLAP_THRESHOLD = 0.30     # NMS overlap threshold (0-1)

# Preprocessing parameters
CLAHE_CLIP_LIMIT = 3.0
CLAHE_TILE_GRID = (8, 8)
BILATERAL_D = 9
BILATERAL_SIGMA_COLOR = 75
BILATERAL_SIGMA_SPACE = 75

# OCR configuration
OCR_CONFIDENCE_THRESHOLD = 0.85  # Below this → VLM fallback
PADDLEOCR_LANG = "en"
PADDLEOCR_USE_ANGLE_CLS = True
PADDLEOCR_USE_GPU = False  # Set True if GPU available
PADDLEOCR_MAX_SIDE_LEN = 1280  # Resize images so longest side <= this before OCR

# VLM configuration
VLM_TEMPERATURE = 0.0
VLM_MAX_TOKENS = 256
VLM_MODEL = "claude-opus-4-6"
VLM_PROMPT_VERSION = 4  # 1 = original, 2 = chain-of-thought, 3 = flexible format, 4 = single-billet crop
VLM_CROP_RATIO = 0.6  # Crop center 60% of image for VLM (stamps are centered)

# Florence-2 configuration
FLORENCE2_MODEL_ID = "florence-community/Florence-2-base"  # base (0.23B) — large (0.77B) tested but hurts ensemble
FLORENCE2_TASK = "<OCR>"                    # or "<OCR_WITH_REGION>"
FLORENCE2_MAX_NEW_TOKENS = 100
# Note: Florence-2 defaults to num_beams=3 internally — do NOT override to 1 (causes regression)
FLORENCE2_DEVICE = "cuda"                  # "cpu" if no GPU available
FLORENCE2_LORA_PATH: Optional[str] = None  # Path to LoRA adapter weights (None = zero-shot)
# V2 LoRA at models/florence2_billet_lora_v2/best — no improvement over zero-shot (69 entries too small)
# V1 LoRA regressed due to low-res 640x640 images + noisy VLM-generated labels
FLORENCE2_BBOX_PAD_RATIO = 0.25            # 25% padding around bbox crop for Florence-2

# Multi-orientation: try these rotations when reading billets (0° = normal, 180° = upside-down)
MULTI_ORIENT_ANGLES: list[int] = [0, 180]

# Cross-validation: combine F2 + PaddleOCR results for higher accuracy
CROSS_VALIDATE_ENGINES = True

# Multi-billet GT configuration
GT_BBOX_PAD_RATIO = 0.10                   # 10% padding around bbox for GT crop
MIN_BBOX_SIZE = 30                          # Skip bboxes smaller than 30px on shortest side
GT_OUTPUT_PATH = ANNOTATED_DIR / "ground_truth_v2.json"
GT_REVIEW_DIR = DATA_DIR / "gt_review"           # Root review directory
GT_REVIEW_SOURCES_DIR = GT_REVIEW_DIR / "sources"  # Full source images for reference
GT_REVIEW_CROPS_DIR = GT_REVIEW_DIR / "crops"      # Per-billet crop images for review

# Visual inference review
INFERENCE_REVIEW_DIR = DATA_DIR / "inference_review"
INFERENCE_REVIEW_SOURCES_DIR = INFERENCE_REVIEW_DIR / "sources"
INFERENCE_REVIEW_CROPS_DIR = INFERENCE_REVIEW_DIR / "crops"
INFERENCE_REVIEW_ANNOTATED_DIR = INFERENCE_REVIEW_DIR / "annotated"
INFERENCE_REVIEW_LIVE_DIR = INFERENCE_REVIEW_DIR / "live"

# Super-resolution configuration
SUPERRES_MODEL_NAME = "espcn"                                     # ESPCN is fastest (~50ms)
SUPERRES_SCALE = 4                                                # Upscale factor
SUPERRES_MODEL_PATH = PROJECT_ROOT / "models" / "ESPCN_x4.pb"   # Pre-trained model file
SUPERRES_MIN_SIZE = 300                                           # Upscale if shortest side < this (was 200)
SUPERRES_TARGET_SIZE = 600                                        # Target shortest side after upscale (was 400)

# Supported image formats
SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".bmp"]

# ROI detection
ROI_CANNY_THRESHOLD1 = 30
ROI_CANNY_THRESHOLD2 = 100
ROI_MIN_AREA_RATIO = 0.005   # Min 0.5% of image area
ROI_MAX_AREA_RATIO = 0.95    # Max 95% of image area
ROI_ASPECT_RATIO_RANGE = (0.4, 2.5)  # width/height acceptable range
ROI_APPROX_EPSILON = 0.02    # cv2.approxPolyDP tolerance
ROI_BLUR_KERNEL = (5, 5)
ROI_DILATE_KERNEL = (3, 3)
ROI_DILATE_ITERATIONS = 2

# Perspective correction
PERSPECTIVE_TARGET_SIZE = 512
PERSPECTIVE_BORDER_PERCENT = 0.05

# Billet number format patterns
HEAT_NUMBER_PATTERN = r"^\d{5,7}$"  # 5-7 digits
STRAND_PATTERN = r"^\d$"  # Single digit
SEQUENCE_PATTERN = r"^\d{1,4}$"  # 1-4 digits (Roboflow: 4-digit sequences like "5383")

# YOLOv8 billet detector
YOLO_MODEL_PATH = PROJECT_ROOT / "models" / "yolo_billet_detector" / "best.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.25
YOLO_IOU_THRESHOLD = 0.45

# Ensure directories exist
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
GT_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
GT_REVIEW_SOURCES_DIR.mkdir(parents=True, exist_ok=True)
GT_REVIEW_CROPS_DIR.mkdir(parents=True, exist_ok=True)
INFERENCE_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
INFERENCE_REVIEW_SOURCES_DIR.mkdir(parents=True, exist_ok=True)
INFERENCE_REVIEW_CROPS_DIR.mkdir(parents=True, exist_ok=True)
INFERENCE_REVIEW_ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
INFERENCE_REVIEW_LIVE_DIR.mkdir(parents=True, exist_ok=True)
