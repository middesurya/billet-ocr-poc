# Billet OCR POC -- Project Understanding

## Project Overview

**Goal**: Read dot-matrix stamped identification codes from steel billet end-face photos.

Steel billets are semi-finished products in steelmaking. After casting and cooling, each billet is stamped on its end face with identification codes using pin-marking machines. These codes contain:

- **Heat numbers** (5-7 digits) -- uniquely identify the melt/cast batch (e.g., "184767", "60008")
- **Strand identifiers** -- single digit indicating which continuous casting strand produced the billet
- **Sequence numbers** -- 2-4 digit position in the casting sequence (e.g., "09", "5383")

### Why This Is Hard

| Challenge | Description |
|-----------|-------------|
| Low contrast | Dot-matrix stamps on oxidized/scaled steel surfaces with minimal visual distinction |
| Variable lighting | Indoor warehouse, outdoor yard, shadows, mixed artificial and natural light |
| Visual noise | Yellow paint markings on billet faces add confounding visual elements |
| Partial occlusion | Codes sometimes worn, covered by scale, or partially obscured |
| Camera angle variation | Photos not always perpendicular to billet face; perspective distortion |
| Small targets | In multi-billet surveillance frames, each billet face is only ~50-100 pixels |

---

## Architecture

### Two-Stage Pipeline: Preprocessing -> OCR Engine -> Post-processing

The project uses a two-stage approach (detection then recognition) rather than end-to-end VLM because:

1. **PaddleOCR is 10-50x faster** than VLMs for inference
2. **PaddleOCR can run offline** on edge devices (NVIDIA Jetson Orin)
3. **VLM serves as intelligent fallback** for hard cases only
4. Research validation: Wei & Zhou (Feb 2025) achieved 91-94% weekly accuracy with DBNet+SVTR on this exact problem domain

### Pipeline Flow

```
Input Image
    |
    v
[Preprocessing]
    |- Bilateral filter (smooth noise, preserve edges)
    |- CLAHE on LAB L-channel (enhance contrast)
    |- ROI detection (4 strategies: Roboflow bbox / edge quad / largest contour / center crop)
    |
    v
[Primary OCR: PaddleOCR PP-OCRv5]
    |- DBNet++ for text detection
    |- SVTR for text recognition
    |- Confidence score per detection
    |
    v
[Confidence Check]
    |- >= 0.85 --> Accept result
    |- < 0.85 --> VLM Fallback
    |
    v
[VLM Fallback: Claude Vision API]
    |- Chain-of-thought prompt (V3: flexible format)
    |- Structured output via Pydantic + Anthropic SDK
    |
    v
[Post-processing]
    |- Character confusion correction (B->8, O->0, I->1, S->5, etc.)
    |- Format validation (heat number length, digit-only checks)
    |
    v
Output: BilletReading (heat_number, strand, sequence, confidence, method)
```

### OCR Engine Options

| Engine | Type | Params | Speed | Offline | Notes |
|--------|------|--------|-------|---------|-------|
| PaddleOCR PP-OCRv5 | Traditional OCR | ~12M | Fast | Yes | Primary engine, DBNet++ + SVTR |
| Claude Vision | Cloud VLM | N/A | Slow | No | Best accuracy, API cost |
| Florence-2 | Local VLM | 0.23B | Medium | Yes | Supports LoRA fine-tuning, edge deploy candidate |
| EasyOCR | Traditional OCR | ~10M | Fast | Yes | Poor on industrial stamps |
| TrOCR | Transformer OCR | ~334M | Medium | Yes | Recognition only (no detection) |
| docTR | Traditional OCR | ~25M | Fast | Yes | DBNet + CRNN |

### Preprocessing Details

The preprocessing pipeline is the single most impactful software intervention:

1. **Bilateral filter** (d=9, sigmaColor=75, sigmaSpace=75) -- smooths noise while preserving edges. Applied BEFORE CLAHE.
2. **CLAHE** (clipLimit=3.0, tileGridSize=8x8) on LAB color space L-channel only -- adaptive contrast enhancement. This is the most important step.
3. **ROI detection** with 4 strategies (in priority order):
   - Strategy 0: Roboflow bounding box (when annotations available)
   - Strategy 1: Edge-based quadrilateral detection
   - Strategy 2: Largest contour detection
   - Strategy 3: Center crop fallback (always works)

**Important**: Do NOT use adaptive thresholding with neural network OCR engines. Do NOT apply CLAHE when sending images to VLMs (it degrades VLM performance).

---

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11.9 | Runtime |
| OpenCV | 4.10.0 | Image preprocessing (pinned by PaddleX) |
| PaddleOCR | 3.4.0 (v3.x) | Primary OCR engine |
| PaddlePaddle | 3.3.0 | Deep learning framework for PaddleOCR |
| Florence-2 | 0.23B | Local VLM via HuggingFace transformers + PyTorch |
| Anthropic SDK | 0.83.0 | Claude Vision API (supports `messages.parse()` with Pydantic) |
| FastAPI | latest | REST API server |
| pytest | latest | Testing framework |
| Roboflow SDK | latest | Dataset download and management |

### Environment

- Virtual environment at `.venv/`, activate with `.venv/Scripts/activate`
- Run scripts with `.venv/Scripts/python.exe`
- Set `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` to skip PaddleOCR connectivity check
- Roboflow API key stored in `.env` as `ROBOFLOW_API_KEY`
- Anthropic API key stored in `.env` as `ANTHROPIC_API_KEY`

---

## Datasets

### Original Dataset (5 images)

- Hand-collected billet end-face photos
- **Stamp type**: Dot-matrix pin-marked stamps
- **Format**: 6-digit heat number + strand + sequence (e.g., "184767 / 3 09 1")
- **Location**: `data/raw_original/`
- **File naming**: Files have spaces in names (e.g., "Image (1).jpg") -- always use `pathlib.Path`

### Roboflow Dataset (ztai/steel-billet v7)

- **Total images**: 1783 (1638 train + 145 valid), 3x augmented from ~602 originals
- **Resolution**: Resized to 640x640 by Roboflow preprocessing (with static crop)
- **Stamp type**: White paint stenciled numbers (NOT dot-matrix like original images)
- **Format**: 5-digit heat number (top line) + 4-digit sequence (bottom line), e.g., "60008 / 5383"
- **Density**: Average ~9 billets per frame; each billet face is only ~50-100px in the 640x640 image
- **Annotations**: 15,998 bounding boxes across 1,780 images (COCO format, category: "batch")
- **Ground truth**: Extracted via Claude Vision API for 30 images (expandable)
- **Location**: `data/raw/` (images), `data/annotated/roboflow_bboxes.json` (bounding boxes)

### Roboflow Dataset Pipeline

1. `scripts/download_roboflow_dataset.py` -- Downloads dataset. **CRITICAL**: Must use `overwrite=True` in `ds.download()` because the SDK silently skips if directory exists.
2. `scripts/parse_roboflow_annotations.py` -- Extracts COCO bounding boxes into `data/annotated/roboflow_bboxes.json`
3. `scripts/triage_dataset.py` -- VLM scan to categorize images (has_stamp / no_stamp / unclear)
4. `scripts/extract_ground_truth.py` -- VLM ground truth extraction with `--max-images`, `--skip-existing`, `--use-bbox`

---

## Benchmark Results (Current State)

### Original 5 Images

| Method | Char Accuracy | Word Accuracy |
|--------|:---:|:---:|
| PaddleOCR Raw | ~20% | ~0% |
| PaddleOCR + CLAHE | ~40% | ~0% |
| Claude Vision (center crop) | 66.7% | 20% |
| Florence-2 Raw | 31.4% | 0% |
| Florence-2 Crop | 53.8% | 20% |

### Roboflow 30 Images

| Method | Char Accuracy | Word Accuracy |
|--------|:---:|:---:|
| PaddleOCR Raw | 1.9% | 0% |
| Bbox Crop + CLAHE + PaddleOCR | 15.0% | 3.3% |
| Claude Vision Center Crop | 57.4% | 33.3% |
| Claude Vision Raw | 54.7% | 30.0% |
| Claude Vision Preprocessed | 46.8% | - |
| EasyOCR | 0% | 0% |
| Florence-2 Raw | Not yet tested | - |
| Florence-2 Crop | Not yet tested | - |

### Key Insights

1. **Traditional OCR fails on industrial stamps** -- PaddleOCR and EasyOCR perform badly, especially on small billet crops from surveillance-style images.
2. **CLAHE helps PaddleOCR but hurts VLMs** -- Preprocessing gives PaddleOCR an 8x improvement (1.9% to 15.0%) but degrades Claude Vision from 54.7% to 46.8%. Never preprocess images destined for VLMs.
3. **VLMs are the best overall** -- Claude Vision achieves 57.4% character accuracy, the highest of any method. However, it requires API calls, is expensive, and is too slow for real-time use.
4. **Bounding box cropping is critical** -- For multi-billet Roboflow frames, cropping individual billets before OCR is essential for any method to work.
5. **Florence-2 shows promise** -- On the original 5 images, Florence-2 with cropping (53.8%) approaches Claude Vision (66.7%) while being fully local. It needs Roboflow benchmarking and fine-tuning to be competitive.
6. **Image resolution matters** -- Individual billet crops at 640x640 are too small for traditional OCR engines. Super-resolution or higher-resolution capture would help.

---

## File Organization

```
billet-ocr-setup/
├── src/
│   ├── config.py              # Central configuration (CLAHE params, thresholds, prompts)
│   ├── models.py              # Pydantic data models (BilletReading, OCRMethod)
│   ├── ocr/
│   │   ├── paddle_ocr.py      # PaddleOCR integration (legacy ocr() + new predict() API)
│   │   ├── vlm_reader.py      # Claude Vision API integration (structured output)
│   │   ├── florence2_reader.py # Florence-2 local VLM (supports LoRA adapter loading)
│   │   ├── easyocr_reader.py  # EasyOCR alternative engine
│   │   ├── trocr_reader.py    # TrOCR alternative engine (recognition only)
│   │   ├── doctr_reader.py    # docTR alternative engine (DBNet + CRNN)
│   │   └── ensemble.py        # Ensemble pipeline (PaddleOCR -> VLM fallback)
│   ├── preprocessing/
│   │   └── pipeline.py        # Image preprocessing (CLAHE, bilateral, ROI, center crop)
│   ├── postprocess/
│   │   ├── char_replace.py    # Character confusion correction (B->8, O->0, I->1, S->5)
│   │   └── validator.py       # Format validation (heat number length, digit checks)
│   └── api/
│       └── main.py            # FastAPI REST API
├── scripts/
│   ├── benchmark.py           # Accuracy benchmark (all engines, --all-engines flag)
│   ├── download_roboflow_dataset.py  # Roboflow dataset download
│   ├── parse_roboflow_annotations.py # COCO bbox extraction
│   ├── triage_dataset.py             # VLM image categorization
│   ├── extract_ground_truth.py       # VLM ground truth extraction
│   ├── prepare_florence2_training.py  # Dataset prep for fine-tuning
│   └── finetune_florence2.py          # LoRA fine-tuning script
├── data/
│   ├── raw/                   # All billet images (Roboflow + original)
│   ├── raw_original/          # Original 5 images backup
│   ├── annotated/
│   │   ├── ground_truth.json  # Ground truth labels
│   │   └── roboflow_bboxes.json # Roboflow bounding box annotations
│   └── training/florence2/    # Fine-tuning dataset (HuggingFace format)
├── models/
│   └── florence2_billet_lora/  # Saved LoRA adapter weights
├── docs/                       # Benchmark reports, research, and project documentation
├── tests/                      # pytest test suites
├── .env                        # API keys (ROBOFLOW_API_KEY, ANTHROPIC_API_KEY)
├── CLAUDE.md                   # Project instructions for Claude Code
└── requirements.txt            # Python dependencies
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `python -m pytest tests/ -v` | Run all tests |
| `python scripts/benchmark.py` | Run accuracy benchmark (default engines) |
| `python scripts/benchmark.py --all-engines` | Run benchmark with all OCR engines |
| `python scripts/benchmark.py --max-images 10 --shuffle` | Benchmark on random subset |
| `python scripts/benchmark.py --bbox-crop` | Benchmark with Roboflow bbox cropping |
| `python -m uvicorn src.api.main:app --reload` | Start FastAPI server |
| `python scripts/download_roboflow_dataset.py` | Download Roboflow dataset |
| `python scripts/parse_roboflow_annotations.py` | Parse COCO annotations to bbox JSON |
| `python scripts/triage_dataset.py` | Categorize images via VLM scan |
| `python scripts/extract_ground_truth.py --max-images 30` | Extract ground truth labels |
| `python scripts/prepare_florence2_training.py` | Prepare Florence-2 training data |
| `python scripts/finetune_florence2.py` | Run Florence-2 LoRA fine-tuning |

---

## PaddleOCR API Notes

PaddleOCR 3.4.0 has two APIs:

- **Legacy `ocr.ocr()`**: Returns `[[[box_points], (text, confidence)], ...]`. Sometimes returns `None` for empty images -- always check.
- **New `ocr.predict()`**: Returns structured result objects with `.print()` and `.save_to_json()` methods.

First run downloads ~100MB of models. Use `show_log=False` to suppress verbose output.

---

## VLM Prompt Versions

| Version | Description | Use Case |
|---------|-------------|----------|
| V1 | Basic OCR for dot-matrix stamps | 6-digit heat + strand + sequence |
| V2 | Chain-of-thought with pin-matrix analysis steps | More detailed reasoning |
| V3 (current) | Flexible format (paint + dot-matrix, 5-6 digit heat, variable sequence) | Handles both original and Roboflow images |

Current version is set in `src/config.py` via `VLM_PROMPT_VERSION=3`.

---

## Roadmap: Florence-2 Fine-Tuning

The next major milestone is fine-tuning Florence-2 for billet stamp OCR to achieve API-free, edge-deployable performance:

1. **Baseline benchmarks** -- Run Florence-2 on Roboflow 30 images (raw + crop + bbox-crop) to establish zero-shot performance on the Roboflow dataset.
2. **Scale ground truth** -- Expand ground truth labels to 200+ images using Claude Vision API (`scripts/extract_ground_truth.py --max-images 200`).
3. **Prepare training data** -- Generate bbox-cropped billet images with labels in HuggingFace datasets format (`scripts/prepare_florence2_training.py`).
4. **LoRA fine-tuning** -- Train Florence-2 on billet crops using LoRA adapters, targeting 80%+ character accuracy (`scripts/finetune_florence2.py`).
5. **Integrate** -- Load LoRA adapter in `src/ocr/florence2_reader.py` and benchmark fine-tuned model against zero-shot baseline.
6. **Edge deployment** -- Deploy Florence-2 + LoRA on NVIDIA Jetson Orin for real-time, offline billet OCR with no API dependency.

---

## Research Reference

- **Wei & Zhou (Feb 2025)**: Validated DBNet+SVTR architecture for billet stamp OCR, achieving 91-94% weekly accuracy in production. Full analysis in `docs/RESEARCH.md`.
- **PaddleOCR PP-OCRv5**: The proven stack for industrial OCR -- DBNet++ for detection, SVTR for recognition.
- **Florence-2**: Microsoft's 0.23B parameter multimodal model. Supports LoRA fine-tuning, small enough for edge deployment on Jetson Orin.
- **Key hardware insight**: Multi-directional lighting matters as much as model choice. Controlled lighting at the capture point would dramatically improve all OCR methods.
- **Software insight**: Format validation + character confusion correction adds approximately 5% accuracy on top of raw OCR output.
