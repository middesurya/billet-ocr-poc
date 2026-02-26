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

Florence-2 + PaddleOCR cross-validation ensemble with Claude Vision fallback:

```
Surveillance Image (1280x640)
  |
  v
Roboflow Bounding Boxes (per-billet isolation)
  |
  v
+------ Bbox Crop + Padding ------+
|                                  |
v                                  v
Florence-2 (0° + 180°)      PaddleOCR + CLAHE
+ Format Validation          (angle classifier)
|                                  |
+---------> Cross-Validate <-------+
                 |
    Agree? ----> High confidence result (77% accuracy)
    Disagree? -> Prefer PaddleOCR
    Neither? --> Claude Vision Fallback
```

### Why This Architecture?
- **Florence-2 + PaddleOCR ensemble achieves 77.0% heat char accuracy** — exceeding either engine alone
- Florence-2 and PaddleOCR fail on *different* images — cross-validation catches complementary failures
- Multi-orientation (0°/180°) handles upside-down billets in surveillance feeds
- Format validation extracts 5-digit heat numbers from noisy F2 output (+11% accuracy alone)
- Claude Vision serves as fallback only for genuinely hard cases

## OCR Engines

| Engine | Type | Speed | Best Accuracy | Cost | Status |
|--------|------|:-----:|:------------:|:----:|:------:|
| **F2+Paddle Ensemble** | Local | **~1.7s** | **77.0%** char | Free | **Primary** |
| **Florence-2 (0.23B)** | Local VLM | ~200ms | 69.9% char | Free | Ensemble component |
| **PaddleOCR PP-OCRv5** | Local OCR | ~100ms | 65.2% char | Free | Ensemble component |
| **Claude Vision** | Cloud VLM | ~3s | 66.7% char | ~$0.005/img | Fallback |

Previously evaluated but removed: EasyOCR, TrOCR, docTR, GOT-OCR-2.0 (all underperformed on this dataset).

## Benchmark Results

### Latest: V10 Per-Billet (73 billets across 14 images, v9 1280x640)

| Method | Avg Heat Char Acc | Avg Heat Exact Match |
|--------|:-:|:-:|
| **F2+Paddle Ensemble** | **77.0%** | **68.5%** |
| F2 Multi-Orient (0°+180°) | 69.9% | 60.3% |
| PaddleOCR Bbox+CLAHE | 65.2% | 56.2% |
| F2 Bbox Crop (format fix) | 60.8% | 52.1% |
| F2 Bbox+SuperRes | 60.3% | 49.3% |

### Accuracy Improvement History

| Version | Best Method | Heat Char Acc | Key Change |
|---------|-------------|:------------:|------------|
| V7 baseline | VLM Center Crop | 57.4% | Initial benchmarks |
| V9 zero-shot | PaddleOCR+CLAHE | 65.2% | Higher-res dataset (1280x640) |
| **V10 ensemble** | **F2+Paddle** | **77.0%** | **Format fix + multi-orient + cross-validation** |

> **Key Insights:**
> - **Post-processing > model improvements**: Format validator fix alone = +11.2% accuracy (more than any model change)
> - **Complementary engines beat individual**: F2+PaddleOCR (77%) > PaddleOCR (65%) > F2 (61%) because they fail differently
> - **Multi-orientation is critical**: 10% of billets are upside-down; 180° rotation adds +9% to F2 accuracy

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
|   |   |-- super_resolution.py    # ESPCN x4 super-resolution for tiny crops
|   |-- ocr/
|   |   |-- paddle_ocr.py          # PaddleOCR PP-OCRv5 integration
|   |   |-- vlm_reader.py          # Claude Vision API reader
|   |   |-- florence2_reader.py    # Florence-2 local VLM + multi-orientation
|   |   |-- ensemble.py            # F2+PaddleOCR cross-validation + VLM fallback
|   |-- postprocess/
|       |-- validator.py           # Format validation + character confusion map
|       |-- format_validator.py    # Florence-2 output format extraction (5-digit heat)
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

1. **Cross-engine ensemble beats any single engine** — F2+PaddleOCR (77%) > PaddleOCR (65%) > Florence-2 (61%)
2. **Post-processing gives the biggest ROI** — format validator fix = +11.2% accuracy, more than any model change
3. **Multi-orientation is essential** — 10% of surveillance images have upside-down billets; 0°/180° adds +9%
4. **Resolution is the #1 bottleneck** — 640x640 with ~50px billet faces is too small; 1280x640 with ~100-200px crops works
5. **CLAHE helps PaddleOCR but hurts VLMs** on paint-stenciled text
6. **Bounding box isolation** is critical for multi-billet surveillance frames
7. **Data quality > model complexity** — fine-tuning on noisy VLM-generated labels caused catastrophic forgetting

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
