# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-24 00:01 UTC  
**Images evaluated:** 5  
**VLM model:** `claude-sonnet-4-5-20250929`  
**Prompt version:** V2  
**VLM crop ratio:** 0.6  

## Configuration

| Parameter | Value |
|-----------|-------|
| CLAHE clip limit | 3.0 |
| CLAHE tile grid | (8, 8) |
| Bilateral d | 9 |
| Bilateral sigma color | 75 |
| Bilateral sigma space | 75 |
| OCR confidence threshold | 0.85 |
| VLM model | `claude-sonnet-4-5-20250929` |
| VLM prompt version | 2 |
| VLM crop ratio | 0.6 |

## Summary

| Method | Avg Char Accuracy | Avg Word Accuracy | Avg Time |
|--------|-------------------|-------------------|----------|
| PaddleOCR Raw | 3.3% | 0.0% | 72159ms |
| PaddleOCR + CLAHE | 0.0% | 0.0% | 50930ms |
| ROI + CLAHE | 0.0% | 0.0% | 15056ms |
| CLAHE + Correction | 2.0% | 0.0% | - |
| VLM Fallback | 56.7% | 20.0% | 3297ms |
| VLM Preprocessed | 56.7% | 20.0% | 3046ms |
| VLM Raw | 66.7% | 20.0% | 3302ms |
| VLM Center Crop | 63.3% | 20.0% | 3095ms |
| Florence-2 Raw | 31.4% | 0.0% | 4966ms |
| Florence-2 Crop | 53.8% | 20.0% | 194ms |
| Ensemble | 66.7% | 20.0% | 22678ms |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | Florence-2 Raw | Florence-2 Crop |
|-------|---------|------------------|---------|-----------------|----------------|-----------------|
| image_22.png | 192435 | 192435 (100%) | 192435 (100%) | 192435 (100%) | 1924319 (71%) | 1924351 (86%) |
| image_23.png | 187612 | 183812 (67%) | 187812 (83%) | 187812 (83%) | 7612187 (29%) | 187612 (100%) |
| image_24.png | 185903 | 192435 (17%) | 185918 (67%) | 185935 (67%) | 1859912 (57%) | 185902 (83%) |
| image_25.png | 191078 | 910789 (67%) | 180743 (33%) | 192435 (33%) | - (0%) | - (0%) |
| image_26.png | 186241 | 189317 (33%) | 192471 (50%) | 192435 (33%) | - (0%) | - (0%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| image_22.png | 192435 | VLM Preprocessed | 192435 | `......` | 100.0% |
| image_22.png | 192435 | VLM Raw | 192435 | `......` | 100.0% |
| image_22.png | 192435 | VLM Center Crop | 192435 | `......` | 100.0% |
| image_22.png | 192435 | Florence-2 Raw | 1924319 | `.....X+` | 71.4% |
| image_22.png | 192435 | Florence-2 Crop | 1924351 | `......+` | 85.7% |
| image_23.png | 187612 | VLM Preprocessed | 183812 | `..XX..` | 66.7% |
| image_23.png | 187612 | VLM Raw | 187812 | `...X..` | 83.3% |
| image_23.png | 187612 | VLM Center Crop | 187812 | `...X..` | 83.3% |
| image_23.png | 187612 | Florence-2 Raw | 7612187 | `XXXX.X+` | 28.6% |
| image_23.png | 187612 | Florence-2 Crop | 187612 | `......` | 100.0% |
| image_24.png | 185903 | VLM Preprocessed | 192435 | `.XXXXX` | 16.7% |
| image_24.png | 185903 | VLM Raw | 185918 | `....XX` | 66.7% |
| image_24.png | 185903 | VLM Center Crop | 185935 | `....XX` | 66.7% |
| image_24.png | 185903 | Florence-2 Raw | 1859912 | `....XX+` | 57.1% |
| image_24.png | 185903 | Florence-2 Crop | 185902 | `.....X` | 83.3% |
| image_25.png | 191078 | VLM Preprocessed | 910789 | `XXXXXX` | 66.7% |
| image_25.png | 191078 | VLM Raw | 180743 | `.XXXXX` | 33.3% |
| image_25.png | 191078 | VLM Center Crop | 192435 | `..XXXX` | 33.3% |
| image_25.png | 191078 | Florence-2 Raw | - | `------` | 0.0% |
| image_25.png | 191078 | Florence-2 Crop | - | `------` | 0.0% |
| image_26.png | 186241 | VLM Preprocessed | 189317 | `..XXXX` | 33.3% |
| image_26.png | 186241 | VLM Raw | 192471 | `.XXXX.` | 50.0% |
| image_26.png | 186241 | VLM Center Crop | 192435 | `.XXXXX` | 33.3% |
| image_26.png | 186241 | Florence-2 Raw | - | `------` | 0.0% |
| image_26.png | 186241 | Florence-2 Crop | - | `------` | 0.0% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 9 | 8 | 4 |
| 8 | 6 | 3 |
| 3 | 7 | 2 |
| 3 | 0 | 2 |
| 5 | 3 | 2 |
| 0 | 1 | 2 |
| 7 | 0 | 2 |
| 2 | 6 | 2 |
| 4 | 2 | 2 |
| 2 | 5 | 1 |
| 4 | 9 | 1 |
| 9 | 1 | 1 |
| 1 | 9 | 1 |
| 8 | 7 | 1 |
| 9 | 6 | 1 |
| 3 | 2 | 1 |
| 1 | 4 | 1 |
| 7 | 1 | 1 |
| 1 | 0 | 1 |
| 8 | 3 | 1 |
| 8 | 9 | 1 |
| 4 | 7 | 1 |
| 3 | 8 | 1 |
| 7 | 4 | 1 |
| 2 | 1 | 1 |
| 4 | 0 | 1 |
| 5 | 8 | 1 |
| 3 | 4 | 1 |
| 5 | 1 | 1 |
| 2 | 3 | 1 |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | Ensemble |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|----------|
| image_22.png | easy | 192435 | 16.7% | 0.0% | 0.0% | 10.0% | 100.0% | 100.0% | 100.0% | 100.0% | 71.4% | 85.7% | 100.0% |
| image_23.png | medium | 187612 | 0.0% | 0.0% | 0.0% | 0.0% | 66.7% | 66.7% | 83.3% | 83.3% | 28.6% | 100.0% | 83.3% |
| image_24.png | hard | 185903 | 0.0% | 0.0% | 0.0% | 0.0% | 16.7% | 16.7% | 66.7% | 66.7% | 57.1% | 83.3% | 66.7% |
| image_25.png | very_hard | 191078 | 0.0% | 0.0% | 0.0% | 0.0% | 66.7% | 66.7% | 33.3% | 33.3% | 0.0% | 0.0% | 33.3% |
| image_26.png | extreme | 186241 | 0.0% | 0.0% | 0.0% | 0.0% | 33.3% | 33.3% | 50.0% | 33.3% | 0.0% | 0.0% | 50.0% |

---
*Generated by `scripts/benchmark.py`.*