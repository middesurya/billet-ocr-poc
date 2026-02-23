# Billet OCR POC — Project Instructions

## Project Overview
We are building a POC to read dot-matrix stamped identification codes from steel billet end-face photos. The codes contain heat numbers (e.g., "184767"), strand identifiers, and sequence numbers. These are stamped via pin-marking machines onto cooled billets in a steel mill.

## The Problem
- Stamps are low-contrast dot-matrix on oxidized/scaled steel surfaces
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Yellow paint markings add visual noise
- Some codes are partially obscured, worn, or covered by scale
- Camera angles vary (not always perpendicular to billet face)

## Architecture Decision: Two-Stage Pipeline
We use a two-stage approach (detection → recognition) rather than end-to-end VLM because:
1. PaddleOCR is 10-50x faster than VLMs for inference
2. PaddleOCR can run offline on edge devices (Jetson Orin)
3. VLM serves as intelligent fallback for hard cases only
4. Research paper (Wei & Zhou, Feb 2025) validated DBNet+SVTR on this exact problem

## Tech Stack
- Python 3.11+ (use type hints everywhere)
- OpenCV 4.x for preprocessing
- PaddleOCR PP-OCRv5 for primary OCR
- Anthropic Claude API / Qwen3-VL for VLM fallback
- FastAPI for REST API
- pytest for testing
- React + Tailwind for frontend (Phase 2)

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
- SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".bmp"]

## Billet Number Format
Based on the reference images, stamps follow these patterns:
- Line 1: 6-digit heat number (e.g., "184767", "184844")
- Line 2: Single digit strand + space + 2-digit sequence (e.g., "3 09 1")
- Characters: digits 0-9, occasionally letters. Dot-matrix style.
- Always on the billet END FACE (square cross-section face)

## Testing Requirements
- Every module must have unit tests
- Accuracy benchmark suite in tests/test_accuracy_benchmark.py
- Ground truth stored as JSON: {"image": "path", "heat_number": "184767", "strand": "3", "sequence": "09"}
- Run benchmarks with: pytest tests/test_accuracy_benchmark.py -v

## File Organization
- Raw billet photos → data/raw/
- Annotated ground truth → data/annotated/
- Synthetic training data → data/synthetic/
- All source code → src/
- API server → src/api/main.py

## Commands
- `python -m pytest tests/ -v` → run all tests
- `python scripts/benchmark.py` → run accuracy benchmark
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
- PaddleOCR PP-OCRv5 with DBNet++ detection + SVTR recognition is the proven stack
- CLAHE preprocessing is the single most impactful software intervention
- Multi-directional lighting matters as much as model choice (hardware insight)
- Wei & Zhou (Feb 2025) achieved 91-94% weekly accuracy on billet stamps
- Format validation + character confusion correction adds ~5% accuracy
