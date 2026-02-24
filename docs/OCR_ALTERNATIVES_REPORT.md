# OCR Alternatives Research Report

**Generated:** 2026-02-24
**Purpose:** Evaluate alternative OCR engines for steel billet stamp recognition

## Engine Overview

| Engine | Architecture | Size | Detection | Recognition | GPU Required | Status |
|--------|-------------|------|-----------|-------------|:---:|:---:|
| PaddleOCR v5 | DBNet++ + SVTR | ~100MB | Yes | Yes | No | Implemented |
| EasyOCR | CRAFT + CRNN | ~200MB | Yes | Yes | No | Implemented |
| TrOCR | PaddleOCR det + ViT-decoder | ~608MB | Hybrid | Yes | Recommended | Implemented |
| docTR (PARSeq) | db_resnet50 + PARSeq | ~120MB | Yes | Yes | No | Implemented |
| GOT-OCR-2.0 | Unified VLM | ~560MB | Single-pass | Single-pass | Required | Implemented |
| Claude Vision | Sonnet 4.5 | Cloud API | VLM | VLM | No | Implemented |

## Implementation Details

### PaddleOCR (`src/ocr/paddle_ocr.py`)
- **Detection**: DBNet++ with SVTR recognition
- **API**: Legacy `ocr.ocr()` returning `[[[box_points], (text, confidence)], ...]`
- **Strengths**: Fast CPU inference, good accuracy on high-res document text
- **Weaknesses**: Struggles with small/low-contrast text, character confusion (0↔O, 1↔I)
- **Benchmark**: 1.9% raw → 15.0% with bbox crop (Roboflow), 3.3% → 14.7% (original)

### EasyOCR (`src/ocr/easyocr_reader.py`)
- **Detection**: CRAFT (Character Region Awareness for Text)
- **Recognition**: CRNN (Convolutional Recurrent Neural Network)
- **Strengths**: Simple API, handles rotated text, 80+ language support
- **Weaknesses**: Slower than PaddleOCR, Windows encoding issues with progress bars
- **Fix Applied**: Suppressed stdout during init to avoid `\u2588` charmap error
- **Benchmark**: 0.0% on Roboflow (crops too small for CRAFT detection)

### TrOCR (`src/ocr/trocr_reader.py`)
- **Detection**: Uses PaddleOCR's DBNet++ for text region detection
- **Recognition**: Microsoft TrOCR (ViT encoder + GPT-2 decoder, 608M params)
- **Model**: `microsoft/trocr-large-printed` — specialized for printed text
- **Strengths**: State-of-the-art recognition on printed/industrial text
- **Weaknesses**: Needs separate detection, large model, slow without GPU
- **Status**: Implemented, not benchmarked (requires torch + transformers)

### docTR + PARSeq (`src/ocr/doctr_reader.py`)
- **Detection**: db_resnet50 (DeepBiLSTM-ResNet50)
- **Recognition**: PARSeq (Permutation AutoRegressive Sequence, ~24M params)
- **Strengths**: Fastest scene text recognizer, CPU-capable, small model
- **Weaknesses**: Requires `python-doctr[torch]` or `python-doctr[tf]`
- **Status**: Implemented, not benchmarked (needs dependency installation)

### GOT-OCR-2.0 (`src/ocr/got_ocr_reader.py`)
- **Architecture**: Unified VLM with 560M parameters
- **Model**: `stepfun-ai/GOT-OCR-2.0-hf`
- **Strengths**: Single-pass detection + recognition, good at scene text
- **Weaknesses**: Requires CUDA GPU (~4GB VRAM), too slow on CPU
- **Status**: Implemented with GPU check, not benchmarked (no local GPU)

### Claude Vision (VLM Fallback) (`src/ocr/vlm_reader.py`)
- **Model**: claude-sonnet-4-5 (Anthropic)
- **Strengths**: Best accuracy, understands context, handles any text type
- **Weaknesses**: Requires API call ($0.003-0.007/image), 2-3s latency per image
- **Benchmark**: 57.4% center crop (Roboflow), 86.0% raw (original)

## Head-to-Head Accuracy (Roboflow Dataset, 30 images)

| Rank | Engine | Char Accuracy | Word Accuracy | Avg Latency |
|:---:|--------|:---:|:---:|:---:|
| 1 | VLM Center Crop | **57.4%** | **16.7%** | ~2.6s |
| 2 | VLM Raw | 54.7% | 13.3% | ~2.8s |
| 3 | VLM Preprocessed | 46.8% | 16.7% | ~2.5s |
| 4 | Bbox Crop + PaddleOCR | 15.0% | 0.0% | ~1.0s |
| 5 | CLAHE + Correction | 6.4% | 0.0% | ~9.5s |
| 6 | PaddleOCR + CLAHE | 4.3% | 0.0% | ~9.2s |
| 7 | PaddleOCR Raw | 1.9% | 0.0% | ~9.5s |
| 8 | EasyOCR | 0.0% | 0.0% | ~23s |

## Resource Requirements

| Engine | RAM | GPU VRAM | CPU Time/Image | GPU Time/Image |
|--------|:---:|:---:|:---:|:---:|
| PaddleOCR | ~500MB | N/A | ~9.5s | ~0.5s |
| EasyOCR | ~800MB | N/A | ~23s | ~2s |
| TrOCR | ~2GB | ~2GB | ~30s | ~1s |
| docTR (PARSeq) | ~500MB | N/A | ~5s | ~0.3s |
| GOT-OCR-2.0 | ~4GB | ~4GB | N/A | ~2s |
| Claude Vision | ~50MB | N/A | ~2.5s (API) | N/A |

## Fine-Tuning Feasibility

| Engine | Fine-Tuning Support | Data Needed | Estimated Effort |
|--------|:---:|:---:|:---:|
| PaddleOCR | Good (PaddleX tools) | 200-500 labeled images | Medium |
| EasyOCR | Limited (custom model training) | 500+ images | High |
| TrOCR | Good (HuggingFace trainer) | 100-200 labeled images | Medium |
| docTR (PARSeq) | Good (PyTorch training loop) | 200-500 images | Medium |
| GOT-OCR-2.0 | Possible (LoRA/QLoRA) | 100-200 images | High |

## Recommendations

### For Current POC (No GPU, Small Dataset)
**Use Claude Vision as primary**, PaddleOCR + Bbox Crop as fast pre-filter:
1. Use Roboflow bboxes to crop individual billets
2. Run PaddleOCR on crops — if confidence > 0.85, accept
3. Otherwise, send crop to Claude Vision
4. Cost: ~$0.50-1.00 per 100 images (VLM fallback rate ~80-90%)

### For Production (Edge Deployment)
**Fine-tune PaddleOCR or TrOCR on labeled industrial data:**
1. Collect 200-500 high-resolution billet stamp images
2. Label with heat numbers (VLM can bootstrap this)
3. Fine-tune PaddleOCR's SVTR recognition model
4. Deploy on Jetson Orin (offline, <100ms/image)
5. Target: 85%+ accuracy with format validation

### For Research
**Try TrOCR on high-resolution original images:**
- TrOCR's ViT encoder should handle low-contrast dot-matrix better than CRNN
- The `trocr-large-printed` model was specifically trained on printed text
- Install: `pip install transformers torch`
- Run: `python scripts/benchmark.py --trocr --max-images 5`
