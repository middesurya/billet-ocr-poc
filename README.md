# Billet OCR POC

A proof-of-concept system for reading stamped/painted identification codes from steel billet end-face photos. Billets are marked with heat numbers and sequence IDs — this project automates reading those codes under challenging industrial conditions using OCR and Vision Language Models (VLMs).

## The Problem

Steel billet stamps are hard to read because of:

- Low-contrast dot-matrix impressions or faded paint on oxidized/scaled steel
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Paint markings and surface noise
- Multiple billets per frame in surveillance camera views
- Small text regions (~50-100px) in wide-angle shots

## Architecture

Multi-engine pipeline with VLM fallback:

```
Image
  |
  v
Preprocessing (bilateral filter -> CLAHE on LAB color space)
  |
  v
PaddleOCR (DBNet++ detection + SVTR recognition)
  |
  |-- confidence >= 0.85 --> Result
  |
  |-- confidence < 0.85 --> VLM Fallback (Claude Vision / Florence-2)
  |                              |
  |                              v
  |                           Result
  |
  v
Post-processing (character confusion correction + format validation)
```

## OCR Engines Evaluated

| Engine | Type | Speed | Best Accuracy | Cost | Status |
|--------|------|:-----:|:------------:|:----:|:------:|
| **Claude Vision (Sonnet 4.5)** | Cloud VLM | ~3s | **66.7%** char | ~$0.005/img | Primary |
| **Florence-2 (0.23B)** | Local VLM | **126ms** | **53.8%** char | Free | Recommended for edge |
| PaddleOCR PP-OCRv5 | Local OCR | ~100ms | 15.0% char | Free | With bbox crop |
| EasyOCR | Local OCR | ~23s | 0% | Free | Tested, poor results |
| TrOCR | Local hybrid | ~30s | - | Free | Implemented |
| docTR (PARSeq) | Local OCR | ~5s | - | Free | Implemented |
| GOT-OCR-2.0 | Local VLM | ~2s | - | Free | Needs CUDA GPU |

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
| EasyOCR | 0.0% | 0.0% |

> **Key Insight:** VLMs significantly outperform traditional OCR on industrial stamp reading. Florence-2 runs locally for free and gets near-VLM accuracy at 126ms/image — making it viable for edge deployment. CLAHE preprocessing actually *hurts* VLM performance on paint-stenciled text.

Full reports in [`docs/`](docs/).

## Roboflow Dataset Integration

Integrated the [ztai/steel-billet](https://universe.roboflow.com/ztai/steel-billet) dataset from Roboflow Universe:

- **1,783 images** (1638 train + 145 valid) at 640x640 resolution
- **15,998 bounding boxes** (COCO format) marking individual billet faces
- White paint-stenciled numbers: 5-digit heat number + 4-digit sequence
- Avg 9 billets per surveillance camera frame

```bash
# Download dataset (requires ROBOFLOW_API_KEY in .env)
python scripts/download_roboflow_dataset.py --copy-to-raw

# Parse COCO annotations to bbox JSON
python scripts/parse_roboflow_annotations.py

# Triage images for stamp visibility
python scripts/triage_dataset.py --max-images 50 --use-bbox

# Extract ground truth using VLM
python scripts/extract_ground_truth.py --max-images 50 --use-bbox --skip-existing
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
|   |   |-- vlm_reader.py          # Claude Vision API reader (3 prompt versions)
|   |   |-- florence2_reader.py    # Florence-2 local VLM reader
|   |   |-- easyocr_reader.py      # EasyOCR wrapper
|   |   |-- trocr_reader.py        # TrOCR (PaddleOCR det + ViT recognition)
|   |   |-- doctr_reader.py        # docTR with PARSeq recognition
|   |   |-- got_ocr_reader.py      # GOT-OCR-2.0 (GPU-only)
|   |   |-- ensemble.py            # PaddleOCR + VLM fallback pipeline
|   |-- postprocess/
|       |-- validator.py           # Format validation + character confusion map
|       |-- char_replace.py        # Character replacement with confidence scoring
|-- scripts/
|   |-- benchmark.py               # Multi-engine accuracy benchmark suite
|   |-- extract_ground_truth.py    # VLM-powered ground truth extraction
|   |-- download_roboflow_dataset.py  # Roboflow dataset downloader
|   |-- parse_roboflow_annotations.py # COCO annotation parser
|   |-- triage_dataset.py          # VLM-based image triage
|-- tests/                         # 195+ unit tests
|-- data/
|   |-- raw/                       # Billet photos (not committed)
|   |-- annotated/                 # Ground truth + bbox annotations
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
# Full benchmark (PaddleOCR + VLM + all methods)
python scripts/benchmark.py

# VLM-only comparison
python scripts/benchmark.py --vlm-only

# Include Florence-2
python scripts/benchmark.py --florence2

# Include alternative engines + bbox cropping
python scripts/benchmark.py --all-engines --bbox-crop

# Limit to N images (useful for large datasets)
python scripts/benchmark.py --max-images 30 --shuffle

# No VLM (fast, PaddleOCR only)
python scripts/benchmark.py --no-vlm --bbox-crop
```

### Run Tests

```bash
# All tests (195+ tests)
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

1. **VLMs are the best approach** for industrial stamp reading — Claude Vision at 67% and Florence-2 at 54% vs. PaddleOCR at 3-15%
2. **Florence-2 is the edge deployment candidate** — 126ms, free, local, no API needed
3. **CLAHE preprocessing helps PaddleOCR** but **hurts VLM performance** on paint-stenciled text
4. **Bounding box cropping** is the single biggest PaddleOCR improvement (1.9% -> 15.0%)
5. **Fine-tuning on labeled data** is the recommended next step for production accuracy

## Tech Stack

- **Python 3.11** with type hints throughout
- **OpenCV 4.x** for image preprocessing
- **PaddleOCR 3.x** (DBNet++ + SVTR) for primary OCR
- **Anthropic Claude API** (Sonnet 4.5) for VLM fallback
- **Florence-2** (HuggingFace transformers) for local VLM
- **EasyOCR, TrOCR, docTR** as alternative engines
- **Roboflow** for dataset management
- **pytest** for testing (195+ tests)
- **loguru** for structured logging

## License

MIT
