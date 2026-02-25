# Billet OCR POC — Project Instructions

## Project Overview
We are building a POC to read stamped identification codes from steel billet end-face photos. The codes contain heat numbers (e.g., "184767", "60008"), strand identifiers, and sequence numbers. These are applied via pin-marking machines (dot-matrix) or paint stencils onto cooled billets in a steel mill.

## The Problem
- Stamps are low-contrast on oxidized/scaled steel surfaces (dot-matrix or paint stencil)
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Yellow paint markings add visual noise
- Some codes are partially obscured, worn, or covered by scale
- Camera angles vary (not always perpendicular to billet face)
- Multiple billets per frame (surveillance camera images) — need per-billet isolation

## Architecture Decision: Florence-2 Primary + VLM Fallback
We use Florence-2 as the primary OCR engine with Claude Vision as intelligent fallback:
1. Florence-2 achieves 86-100% accuracy on high-res billet images (proven on original test set)
2. Florence-2 runs locally on GPU — no API costs for primary inference
3. Claude Vision serves as fallback for low-confidence cases (< 0.85 threshold)
4. Roboflow bounding boxes isolate individual billets from multi-billet surveillance frames

### Why Not PaddleOCR?
PaddleOCR was the original architecture choice (validated by Wei & Zhou, Feb 2025 for dot-matrix stamps), but benchmarking showed it achieves only 1.8-17.6% on our Roboflow surveillance images. Florence-2 significantly outperforms it on this dataset. PaddleOCR remains in the codebase for potential future use on high-res single-billet images.

## Lessons Learned (from v7 iteration)
1. **Data quality > model complexity**: Fine-tuning Florence-2 on noisy VLM-generated labels (46% accurate) caused catastrophic forgetting (30.8% → 13.7%)
2. **Resolution is critical**: 640x640 images with ~50-100px billet faces are too small for any OCR model. Upgraded to v9 (1280x640) for ~100-200px crops
3. **No public billet OCR datasets exist**: Searched Kaggle, HuggingFace, Roboflow, GitHub, IEEE, Google Dataset Search, Chinese platforms — all 8+ papers worldwide use proprietary factory data
4. **CLAHE hurts VLMs**: Preprocessing that helps traditional OCR (CLAHE) actually reduces VLM accuracy (46.8% vs 54.7% raw)
5. **Manual GT verification is mandatory**: VLM-generated ground truth must be human-verified before training

## Tech Stack
- Python 3.11+ (use type hints everywhere)
- OpenCV 4.x for preprocessing
- Florence-2 (florence-community/Florence-2-base) for primary OCR
- Anthropic Claude Vision API for VLM fallback
- PaddleOCR PP-OCRv5 (retained, secondary)
- FastAPI for REST API
- pytest for testing

## Code Standards
- Use type hints on all functions
- Docstrings on all public functions (Google style)
- Config values in src/config.py, never hardcoded
- All image processing must handle both RGB and BGR correctly
- Log all OCR results with confidence scores
- Every function that processes images must accept both file path and numpy array

## Key Constants (src/config.py)
- CLAHE_CLIP_LIMIT = 3.0
- CLAHE_TILE_GRID = (8, 8)
- BILATERAL_D = 9
- BILATERAL_SIGMA_COLOR = 75
- BILATERAL_SIGMA_SPACE = 75
- OCR_CONFIDENCE_THRESHOLD = 0.85 (below this → VLM fallback)
- ROBOFLOW_VERSION = 9 (1280x640, ~1551 images)
- SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".bmp"]

## Dataset Reality
- **No public steel billet OCR dataset with text ground truth exists anywhere**
- Roboflow ztai/steel-billet has bounding boxes only (no text labels)
- All ground truth must be self-labeled (VLM-assisted + manual verification)
- Current dataset: Roboflow v9, 1280x640 resolution, ~1551 images
- 5 high-res reference images preserved in data/raw_original/

## Billet Number Format
Based on the dataset, stamps follow these patterns:
- **Paint stencil (Roboflow dataset)**: 5-digit heat number (top) + 4-digit sequence (bottom), e.g., "60008 / 5383"
- **Dot-matrix (original images)**: 6-digit heat number + strand + sequence, e.g., "184767 3 09"
- Characters: digits 0-9, occasionally letters
- Always on the billet END FACE (square cross-section face)

## Multi-Billet Architecture (V2)
Each surveillance image has ~9 billets. The V2 pipeline processes ALL bboxes per image:

### Ground Truth V2
- Per-billet entries: `{"image": "xxx.jpg", "bbox_index": 0, "bbox": {...}, "heat_number": "60731", "sequence": "5282", "verified": false}`
- Stored at `data/annotated/ground_truth_v2.json`
- Crop images for human review at `data/gt_review/{stem}_bbox{N}.jpg`
- ~270 entries for 30 images (9 billets x 30 images)

### Single-Billet Failure Post-Mortem
Previous approach had a fatal bbox mismatch bug:
- `extract_ground_truth.py` used `bboxes[0]` (first bbox) for GT labeling
- `benchmark.py` used `max(bboxes, key=area)` (largest bbox) for evaluation
- GT was labeled from one billet but benchmarked against a different one
- `GroundTruth` dataclass was per-image — couldn't store multiple billets

### V2 Fix
- `BilletGroundTruth` dataclass carries `bbox_index` + `bbox` coordinates
- GT extraction loops ALL bboxes per image with VLM Prompt V4 (single-crop)
- Benchmark uses exact bbox from GT entry — no more `max(bboxes)` selection
- `read_all_billets()` production API for NVIDIA Jetson deployment

## Testing Requirements
- Every module must have unit tests
- Accuracy benchmark suite in scripts/benchmark.py
- Ground truth V1 (legacy): `{"image": "path", "heat_number": "184767", "strand": "3", "sequence": "09"}`
- Ground truth V2 (per-billet): `{"image": "path", "bbox_index": 0, "bbox": {...}, "heat_number": "...", "verified": false}`
- Run benchmarks with: python scripts/benchmark.py --florence2 --bbox-crop --gt-v2

## File Organization
- Raw billet photos → data/raw/
- Annotated ground truth → data/annotated/
- Original high-res reference images → data/raw_original/
- All source code → src/
- API server → src/api/main.py
- Benchmark reports → docs/

## Commands
- `python -m pytest tests/ -v` → run all tests
- `python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2` → per-billet benchmark (V2)
- `python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2 --max-images 30` → quick per-billet test
- `python scripts/benchmark.py --florence2 --bbox-crop --no-vlm` → legacy per-image benchmark
- `python scripts/benchmark.py --florence2 --bbox-crop` → Florence-2 + VLM fallback benchmark
- `python scripts/download_roboflow_dataset.py --copy-to-raw --clear-raw` → download dataset
- `python scripts/parse_roboflow_annotations.py` → parse bbox annotations
- `python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30` → multi-billet GT extraction
- `python scripts/extract_ground_truth.py --use-bbox --no-all-bboxes --max-images 30` → single-bbox GT (legacy)
- `python -m uvicorn src.api.main:app --reload` → start API server

## Sub-Agent Routing Rules
**Parallel dispatch** (ALL conditions must be met):
- 3+ unrelated tasks or independent domains
- No shared state between tasks
- Clear file boundaries with no overlap

**Sequential dispatch** (ANY condition triggers):
- Tasks have dependencies (B needs output from A)
- Shared files or state (merge conflict risk)
- Unclear scope (need to understand before proceeding)

## Research Reference
The full research report is in docs/RESEARCH.md. Key findings:
- PaddleOCR PP-OCRv5 with DBNet++ detection + SVTR recognition is proven for dot-matrix
- CLAHE preprocessing is the single most impactful software intervention for traditional OCR
- Florence-2 achieves 86-100% on high-res images without preprocessing
- Format validation + character confusion correction adds ~5% accuracy
- Wei & Zhou (Feb 2025) achieved 91-94% weekly accuracy on billet stamps (proprietary data)
