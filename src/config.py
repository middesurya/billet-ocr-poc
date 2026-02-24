"""Central configuration for the Billet OCR POC."""
import os
from pathlib import Path

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
ROBOFLOW_VERSION = 7
ROBOFLOW_DOWNLOAD_DIR = DATA_DIR / "roboflow_download"
BBOX_ANNOTATIONS_PATH = ANNOTATED_DIR / "roboflow_bboxes.json"

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
VLM_MODEL = "claude-sonnet-4-5-20250929"
VLM_PROMPT_VERSION = 3  # 1 = original, 2 = chain-of-thought, 3 = flexible format (paint + dot-matrix)
VLM_CROP_RATIO = 0.6  # Crop center 60% of image for VLM (stamps are centered)

# Florence-2 configuration
FLORENCE2_MODEL_ID = "florence-community/Florence-2-base"
FLORENCE2_TASK = "<OCR>"                    # or "<OCR_WITH_REGION>"
FLORENCE2_MAX_NEW_TOKENS = 100
FLORENCE2_DEVICE = "cuda"                  # "cpu" if no GPU available

# EasyOCR configuration
EASYOCR_LANGUAGES = ["en"]
EASYOCR_GPU = False  # Set True if GPU available

# TrOCR configuration
TROCR_MODEL_ID = "microsoft/trocr-large-printed"
TROCR_DEVICE = "cuda"  # "cpu" if no GPU available

# docTR configuration
DOCTR_DET_ARCH = "db_resnet50"
DOCTR_RECO_ARCH = "parseq"  # PARSeq recognizer (~24M params, CPU-capable)
DOCTR_DEVICE = "cpu"  # "cuda" if GPU available

# GOT-OCR configuration
GOT_OCR_MODEL_ID = "stepfun-ai/GOT-OCR-2.0-hf"
GOT_OCR_DEVICE = "cuda"  # Requires GPU — too slow on CPU

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
SEQUENCE_PATTERN = r"^\d{1,3}$"  # 1-3 digits

# Ensure directories exist
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
