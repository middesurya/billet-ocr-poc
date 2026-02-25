# Billet OCR POC

A proof-of-concept system for reading stamped/painted identification codes from steel billet end-face photos. Billets are marked with heat numbers and sequence IDs — this project automates reading those codes under challenging industrial conditions using local VLMs and cloud VLM fallback.

## The Problem

Steel billet stamps are hard to read because of:

- Low-contrast dot-matrix impressions or faded paint on oxidized/scaled steel
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Paint markings and surface noise
- Multiple billets per frame in surveillance camera views (~9 billets/frame)
- Small text regions (~100-200px) in wide-angle shots

## Architecture

Florence-2 primary OCR with Claude Vision as intelligent fallback:

```
Surveillance Image (1280x640)
  |
  v
Roboflow Bounding Boxes (per-billet isolation)
  |
  v
Florence-2 (local, 126ms/image)
  |
  |-- confidence >= 0.85 --> Result
  |
  |-- confidence < 0.85 --> Claude Vision Fallback
  |                              |
  |                              v
  |                           Result
  |
  v
Post-processing (character confusion correction + format validation)
```

### Why Florence-2?
- Achieves 86-100% accuracy on high-res billet images
- Runs locally on GPU — no API costs for primary inference
- 126ms per image — viable for edge deployment (NVIDIA Jetson)
- Claude Vision serves as fallback only for low-confidence cases

### Why Not PaddleOCR?
PaddleOCR was the original architecture choice but benchmarking showed only 1.8-17.6% accuracy on surveillance images. It remains in the codebase for potential future use on high-res single-billet images.

## OCR Engines

| Engine | Type | Speed | Best Accuracy | Cost | Status |
|--------|------|:-----:|:------------:|:----:|:------:|
| **Florence-2 (0.23B)** | Local VLM | **126ms** | **86-100%** (high-res) | Free | **Primary** |
| **Claude Vision (Sonnet 4.5)** | Cloud VLM | ~3s | **66.7%** char | ~$0.005/img | Fallback |
| PaddleOCR PP-OCRv5 | Local OCR | ~100ms | 15.0% char | Free | Secondary |

Previously evaluated but removed: EasyOCR, TrOCR, docTR, GOT-OCR-2.0 (all underperformed on this dataset).

## Benchmark Results

### Original Images (5 high-res close-up photos)

| Method | Avg Char Accuracy | Avg Word Accuracy | Avg Time |
|--------|:-:|:-:|:-:|
| **VLM Raw (Claude)** | **66.7%** | 20.0% | 3302ms |
| VLM Center Crop | 63.3% | 20.0% | 3095ms |
| VLM Preprocessed | 56.7% | 20.0% | 3046ms |
| **Florence-2 Crop** | **53.8%** | **20.0%** | **126ms** |
| Florence-2 Raw | 31.4% | 0.0% | 4966ms |
| PaddleOCR Raw | 3.3% | 0.0% | 72159ms |

### Roboflow Dataset (30 surveillance camera images, 640x640)

| Method | Avg Char Accuracy | Avg Word Accuracy |
|--------|:-:|:-:|
| **VLM Center Crop** | **57.4%** | 16.7% |
| VLM Raw | 54.7% | 13.3% |
| VLM Preprocessed | 46.8% | 16.7% |
| Bbox Crop + PaddleOCR | 15.0% | 0.0% |
| PaddleOCR Raw | 1.9% | 0.0% |

> **Key Insight:** VLMs significantly outperform traditional OCR on industrial stamp reading. Florence-2 runs locally for free at 126ms/image — viable for edge deployment. CLAHE preprocessing helps PaddleOCR but actually *hurts* VLM performance on paint-stenciled text.

Full reports in [`docs/`](docs/).

## Multi-Billet Pipeline (V2)

Each surveillance image contains ~9 billets. The V2 pipeline processes **all** bounding boxes per image:

- Per-billet ground truth with `BilletGroundTruth` dataclass (bbox_index + coordinates)
- `read_all_billets()` production API for NVIDIA Jetson deployment
- Exact bbox matching between GT and benchmark (no more bbox selection mismatch)
- Crop images generated at `data/gt_review/` for human verification

```bash
# Multi-billet GT extraction (V2)
python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30

# Per-billet benchmark (V2)
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2
```

## Roboflow Dataset

Integrated the [ztai/steel-billet](https://universe.roboflow.com/ztai/steel-billet) dataset (v9):

- **1,551 unique images** at 1280x640 resolution (upgraded from 640x640 v7)
- **~13,929 bounding boxes** (COCO format) marking individual billet faces
- White paint-stenciled numbers: 5-digit heat number + 4-digit sequence
- Avg 9 billets per surveillance camera frame
- 5 high-res reference images preserved in `data/raw_original/`

```bash
# Download dataset (requires ROBOFLOW_API_KEY in .env)
python scripts/download_roboflow_dataset.py --copy-to-raw --clear-raw

# Parse COCO annotations to bbox JSON
python scripts/parse_roboflow_annotations.py

# Extract ground truth using VLM
python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30 --skip-existing
```

## Project Structure

```
billet-ocr-setup/
|-- src/
|   |-- config.py                  # Central configuration
|   |-- models.py                  # Shared data models (BilletReading, OCRMethod)
|   |-- preprocessing/
|   |   |-- pipeline.py            # CLAHE + bilateral filter pipeline
|   |   |-- roi_detector.py        # Billet face ROI detection (4 strategies)
|   |   |-- perspective.py         # Perspective correction
|   |-- ocr/
|   |   |-- paddle_ocr.py          # PaddleOCR PP-OCRv5 integration
|   |   |-- vlm_reader.py          # Claude Vision API reader
|   |   |-- florence2_reader.py    # Florence-2 local VLM reader
|   |   |-- ensemble.py            # Florence-2 + VLM fallback pipeline
|   |-- postprocess/
|       |-- validator.py           # Format validation + character confusion map
|       |-- char_replace.py        # Character replacement with confidence scoring
|-- scripts/
|   |-- benchmark.py               # Multi-engine accuracy benchmark suite
|   |-- extract_ground_truth.py    # VLM-powered ground truth extraction (V2 multi-billet)
|   |-- download_roboflow_dataset.py  # Roboflow dataset downloader
|   |-- parse_roboflow_annotations.py # COCO annotation parser
|-- tests/                         # Unit tests
|-- data/
|   |-- raw/                       # Billet photos
|   |-- raw_original/              # 5 high-res reference images
|   |-- annotated/                 # Ground truth + bbox annotations
|   |-- gt_review/                 # Per-billet crop images for human review
|-- docs/                          # Benchmark reports + research notes
```

## Setup

### Prerequisites

- Python 3.11+
- CUDA-capable GPU recommended (for Florence-2 and PaddlePaddle)

### Installation

```bash
# Clone
git clone https://github.com/middesurya/billet-ocr-poc.git
cd billet-ocr-poc

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# For GPU (PyTorch with CUDA)
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

### Environment Variables

Create a `.env` file:

```
ANTHROPIC_API_KEY=your-key-here
ROBOFLOW_API_KEY=your-key-here    # Optional, for dataset download
```

## Usage

### Run the Benchmark

```bash
# Per-billet benchmark with Florence-2 (V2, recommended)
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2

# Florence-2 + VLM fallback benchmark
python scripts/benchmark.py --florence2 --bbox-crop --gt-v2

# Quick test (30 images)
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2 --max-images 30

# Legacy per-image benchmark
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm
```

### Run Tests

```bash
python -m pytest tests/ -v

# Skip accuracy benchmark (requires raw images)
python -m pytest tests/ -v --ignore=tests/test_accuracy_benchmark.py
```

## Billet Number Formats

Two formats encountered across datasets:

**Original dataset (dot-matrix stamps):**
```
Line 1: 192435        (6-digit heat number)
Line 2: 3 09          (strand + sequence)
```

**Roboflow dataset (paint-stenciled):**
```
Line 1: 60008         (5-digit heat number)
Line 2: 5383          (4-digit sequence)
```

## Key Findings

1. **VLMs beat traditional OCR** for industrial stamp reading — Florence-2 at 86-100% (high-res) vs PaddleOCR at 3-15%
2. **Florence-2 is the edge deployment candidate** — 126ms, free, local, no API needed
3. **Resolution is the #1 bottleneck** — 640x640 with ~50px billet faces is too small; 1280x640 with ~100-200px crops works
4. **CLAHE helps PaddleOCR but hurts VLMs** on paint-stenciled text
5. **Bounding box isolation** is critical for multi-billet surveillance frames
6. **Data quality > model complexity** — fine-tuning on noisy VLM-generated labels caused catastrophic forgetting

## Tech Stack

- **Python 3.11** with type hints throughout
- **OpenCV 4.x** for image preprocessing
- **Florence-2** (HuggingFace transformers) for primary OCR
- **Anthropic Claude API** (Sonnet 4.5) for VLM fallback
- **PaddleOCR 3.x** (DBNet++ + SVTR) retained as secondary
- **Roboflow** for dataset management + bounding boxes
- **pytest** for testing
- **loguru** for structured logging

## License

MIT
