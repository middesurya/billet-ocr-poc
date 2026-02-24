# Billet OCR POC

A proof-of-concept system for reading dot-matrix stamped identification codes from steel billet end-face photos. Billets are stamped with heat numbers, strand IDs, and sequence numbers via pin-marking machines -- this project automates reading those codes under challenging industrial conditions.

## The Problem

Steel billet stamps are hard to read because of:

- Low-contrast dot-matrix impressions on oxidized/scaled steel surfaces
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Yellow paint markings adding visual noise
- Partial obscuring from wear, scale buildup, or camera angle

## Architecture

Two-stage pipeline: **Preprocessing** + **OCR** with intelligent fallback.

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
  |-- confidence < 0.85 --> VLM Fallback (Claude Vision API)
  |                              |
  |                              v
  |                           Result
  |
  v
Post-processing (character confusion correction + format validation)
```

### Why Two Stages?

- PaddleOCR is 10-50x faster than VLMs and runs offline on edge devices (Jetson Orin)
- VLM serves as intelligent fallback for hard cases only (~$0.01/image)
- Validated by research: Wei & Zhou (Feb 2025) achieved 91-94% weekly accuracy on billet stamps with DBNet+SVTR

## OCR Engines

| Engine | Type | Speed | Accuracy | Cost |
|--------|------|-------|----------|------|
| PaddleOCR PP-OCRv5 | Local | ~100ms | Primary engine | Free |
| Claude Vision (Sonnet) | Cloud API | ~3.5s | 66.7% char avg | ~$0.01/image |
| Florence-2 (0.23B) | Local GPU | ~126ms | 53.8% char avg | Free |

## Benchmark Results

Evaluated on 5 images graded easy to extreme difficulty:

| Method | Avg Char Accuracy | Avg Word Accuracy | Avg Time |
|--------|:-:|:-:|:-:|
| Ensemble (Paddle+VLM) | 66.7% | 20.0% | 22678ms |
| VLM Raw (Claude) | 66.7% | 20.0% | 3302ms |
| VLM Center Crop | 63.3% | 20.0% | 3095ms |
| VLM Preprocessed | 56.7% | 20.0% | 3046ms |
| VLM Fallback | 56.7% | 20.0% | 3297ms |
| Florence-2 Crop | 53.8% | 20.0% | 194ms |
| Florence-2 Raw | 31.4% | 0.0% | 4966ms |
| PaddleOCR Raw | 3.3% | 0.0% | 72159ms |
| CLAHE + Correction | 2.0% | 0.0% | - |
| PaddleOCR + CLAHE | 0.0% | 0.0% | 50930ms |
| ROI + CLAHE | 0.0% | 0.0% | 15056ms |

> **Note:** PaddleOCR's default PP-OCRv5 models are trained on clean document text, not industrial dot-matrix stamps. Fine-tuning on billet-specific data would be needed for production use. VLM Raw (unprocessed photos sent to Claude) currently gives the best accuracy.

Full reports in [`docs/`](docs/).

## Project Structure

```
billet-ocr-setup/
|-- src/
|   |-- config.py                  # Central configuration
|   |-- models.py                  # Shared data models (BilletReading, OCRMethod)
|   |-- preprocessing/
|   |   |-- pipeline.py            # CLAHE + bilateral filter pipeline
|   |   |-- roi_detector.py        # Billet face ROI detection
|   |   |-- perspective.py         # Perspective correction
|   |-- ocr/
|   |   |-- paddle_ocr.py          # PaddleOCR integration
|   |   |-- vlm_reader.py          # Claude Vision API reader
|   |   |-- florence2_reader.py     # Florence-2 local VLM reader
|   |   |-- ensemble.py            # PaddleOCR + VLM fallback pipeline
|   |-- postprocess/
|       |-- validator.py           # Format validation + character confusion map
|       |-- char_replace.py        # Character replacement with confidence scoring
|-- scripts/
|   |-- benchmark.py               # Accuracy benchmark suite
|   |-- extract_ground_truth.py    # Ground truth annotation helper
|-- tests/                         # 234 unit tests
|-- data/
|   |-- raw/                       # Billet photos (not committed)
|   |-- annotated/                 # Ground truth JSON
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

Create a `.env` file for VLM fallback:

```
ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Run the Benchmark

```bash
# Full benchmark (PaddleOCR + VLM)
python scripts/benchmark.py

# VLM-only comparison
python scripts/benchmark.py --vlm-only

# Include Florence-2 evaluation
python scripts/benchmark.py --vlm-only --florence2

# Output to specific file
python scripts/benchmark.py --output docs/results.md
```

### Run Tests

```bash
# All tests (234 tests)
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_florence2.py -v

# Skip accuracy benchmark (requires raw images)
python -m pytest tests/ -v --ignore=tests/test_accuracy_benchmark.py
```

## Billet Number Format

Stamps follow this pattern:

```
Line 1: 192435        (6-digit heat number)
Line 2: 3 09          (strand + sequence)
```

- Heat number: 5-7 digits
- Strand: single digit (1-9)
- Sequence: 1-3 digits

## Key Preprocessing Insights

- **Bilateral filter before CLAHE** -- smooth noise first, then enhance contrast
- **CLAHE on LAB color space** (L channel only) -- single most impactful intervention
- **Do NOT use adaptive thresholding** with neural network OCR engines
- **Center cropping** (60%) significantly improves VLM and Florence-2 accuracy by focusing on the stamp region

## Tech Stack

- **Python 3.11** with type hints throughout
- **OpenCV 4.x** for image preprocessing
- **PaddleOCR 3.x** (DBNet++ + SVTR) for primary OCR
- **Anthropic Claude API** for VLM fallback
- **Florence-2** (HuggingFace transformers) for local VLM evaluation
- **pytest** for testing (234 tests)
- **loguru** for structured logging

## License

MIT
