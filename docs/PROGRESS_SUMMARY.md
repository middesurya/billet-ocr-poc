# Billet OCR POC — Progress Summary

## Timeline & Attempts

### Phase 1: PaddleOCR Baseline (Initial)
- **Approach**: PaddleOCR PP-OCRv5 (DBNet++ + SVTR) with CLAHE preprocessing
- **Dataset**: Roboflow v7 (640x640, 1783 images) + 5 high-res originals
- **Results**:
  - PaddleOCR Raw: **1.8%** char accuracy
  - PaddleOCR + Bbox Crop + CLAHE: **17.6%** char accuracy
- **Conclusion**: PaddleOCR cannot handle low-res surveillance camera crops

### Phase 2: Multi-Engine Exploration
- **Approach**: Added EasyOCR, TrOCR, docTR, GOT-OCR as alternative engines
- **Results**: None significantly outperformed PaddleOCR on 640x640 crops
- **Conclusion**: The bottleneck is image resolution, not the OCR model

### Phase 3: Florence-2 + VLM
- **Approach**: Florence-2 zero-shot + Claude Vision VLM fallback
- **Results**:
  - Florence-2 Raw: **30.8%** char accuracy (Roboflow v7)
  - Florence-2 on high-res originals: **86-100%** char accuracy
  - VLM Center Crop: **57.4%** (best single method on Roboflow)
- **Key insight**: Florence-2 works excellently on high-res images — resolution is the bottleneck

### Phase 4: Florence-2 Fine-Tuning (FAILED)
- **Approach**: LoRA fine-tuning (r=8, alpha=32) on VLM-generated ground truth
- **Training**: 185 labels (158 valid), 20 epochs, best val_char_acc 38.57% at epoch 4
- **Results**: **13.7%** char accuracy — WORSE than zero-shot (30.8%)
- **Failure analysis**:
  1. Ground truth was only ~46% accurate (VLM hallucinations on tiny crops)
  2. Training images too low-res (640x640, ~50-100px per billet)
  3. Model overfit to noise, catastrophic forgetting of general OCR ability
  4. Output degenerated to repeated "383" patterns
- **Conclusion**: Data quality problem, not model architecture problem

### Phase 5: Ensemble V2
- **Approach**: 4-tier cascade: F2 bbox → F2 crop → cross-validate → VLM fallback
- **Results**: **~45% char / ~17% word** accuracy (100% VLM fallback rate)
- **Conclusion**: Florence-2 never passes 0.80 threshold on v7 crops

### Phase 6: Super-Resolution + Format Validation
- **Approach**: Bicubic upscaling + format-aware output validation
- **Results**: Marginal improvement, still limited by source resolution
- **Conclusion**: Cannot upscale detail that doesn't exist in the source image

### Phase 7: Single-Billet GT Failure (v9)
- **Approach**: Upgraded to v9 (1280x640) + Florence-2 benchmark
- **Results**: F2 Raw 37.6%, F2 Bbox Crop 53.5% on v9
- **Fatal bug discovered**:
  - `extract_ground_truth.py` used `bboxes[0]` (first bbox) for labeling
  - `benchmark.py` used `max(bboxes, key=area)` (largest bbox) for eval
  - GT was labeled from a DIFFERENT billet than what was benchmarked
  - `GroundTruth` dataclass was per-image — couldn't store ~9 billets/image
- **Conclusion**: Single-billet-per-image architecture was fundamentally wrong

### Phase 8: Multi-Billet Architecture (V2)
- **Approach**: Per-billet GT with explicit bbox coordinates carried through pipeline
- **Key changes**:
  1. `BilletGroundTruth` dataclass with `bbox_index`, `bbox`, `verified` fields
  2. GT extraction loops ALL bboxes per image (not just first/largest)
  3. Benchmark uses EXACT bbox from GT entry (no more `max(bboxes)`)
  4. VLM Prompt V4 designed for pre-cropped single-billet images
  5. `read_all_billets()` production API for Jetson deployment
  6. Per-billet crop images saved to `data/gt_review/` for human review
- **Result**: 130 labels for 30 images (14 with per-billet crops, 16 without)

### Phase 9: Option C — Clean GT + Fine-tune + Benchmark (Current)
- **GT cleanup**: Removed 16 no-crop entries → 114 per-billet entries across 14 images
- **Human review**: 130 entries verified (VLM-assisted + manual corrections for J chars, upside-down images)
  - 53 fully clean, 4 partial seq, 16 heat-only, 41 unreadable
- **Benchmark fix**: Skips `?????`-heat entries (73 benchmarked, not 114); seq accuracy only on clean entries
- **Training data**: 69 clean entries (53 full + 16 heat-only), 3x augment, image-level split (57 train / 12 val)
- **LoRA config**: r=16, alpha=32, lr=5e-5, 20 epochs (best at epoch 2, overfitting)
- **Results (v9 per-billet, 73 billets)**:
  | Method | Heat Char Acc | Heat Exact | N |
  |--------|-------------|------------|---|
  | Florence-2 Bbox Crop (zero-shot) | 49.6% | 6.8% | 73 |
  | Florence-2 Bbox+SR (zero-shot) | 49.2% | 8.2% | 73 |
  | **PaddleOCR Bbox+CLAHE** | **65.2%** | **56.2%** | 73 |
  | Florence-2 Bbox Crop (LoRA v2) | 48.0% | 9.6% | 73 |
  | Florence-2 Bbox+SR (LoRA v2) | 46.2% | 8.2% | 73 |
- **Key findings**:
  1. PaddleOCR+CLAHE is the strongest method on v9 bbox crops (65.2% vs F2's 49.6%)
  2. LoRA fine-tuning had no meaningful effect (69 entries too small, best epoch 2/20)
  3. Resolution remains the primary bottleneck — all methods struggle on ~50-100px crops
  4. Image-level train/val split confirmed zero leakage between splits

---

## Current Direction: v9 Multi-Billet Pipeline

### What Changed
1. **Dataset**: Roboflow v9 (1280x640) — 2x width vs v7 (640x640)
2. **OCR Engine**: Florence-2 only (removed EasyOCR, TrOCR, docTR, GOT-OCR)
3. **Ground Truth**: Per-billet V2 format with bbox coordinates and verification status
4. **Codebase**: Multi-billet architecture across GT, benchmark, and production API
5. **Training**: ~9x more labeled data (per-billet crops instead of per-image)

### Actual vs Expected Accuracy
```
v7 single-billet (wrong bbox):   ~35-54% char (noisy, mismatched)       [as expected]
v9 per-billet F2 zero-shot:       49.6% char / 6.8% exact               [within range]
v9 per-billet F2 LoRA:            48.0% char / 9.6% exact               [no improvement]
v9 per-billet PaddleOCR+CLAHE:    65.2% char / 56.2% exact              [surprise winner]
Next: VLM fallback on F2 failures → expected ~70-80% combined
```

---

## Dataset Search Results

**Conclusion: No public steel billet OCR dataset with text ground truth exists.**

### Sources Searched
| Source | Result |
|--------|--------|
| Kaggle | No billet OCR datasets |
| HuggingFace Datasets | No billet OCR datasets |
| Roboflow Universe | ztai/steel-billet has bboxes only, no text labels |
| GitHub | Repos reference private factory data |
| IEEE / Springer / arXiv | All 8+ papers use proprietary data |
| Google Dataset Search | No relevant results |
| Chinese platforms (CSDN, Baidu) | References to private datasets |

### Academic Papers (All Private Data)
- Wei & Zhou (Feb 2025) — Chinese steel mill, proprietary
- Multiple Chinese patents — factory-specific systems
- All papers achieve 91-94% but on their own private datasets

---

## Benchmark History (All on 32 v7 images)

| Method | Char Acc | Word Acc | Notes |
|--------|----------|----------|-------|
| PaddleOCR Raw | 1.8% | 0.0% | Baseline |
| PaddleOCR + CLAHE | 5.4% | 0.0% | Preprocessing helps slightly |
| PaddleOCR + Bbox Crop + CLAHE | 17.6% | 3.1% | Cropping helps more |
| Florence-2 Raw | 30.8% | 6.3% | Best local model |
| Florence-2 Bbox Crop | 17.7% | 3.1% | Crops too small |
| Florence-2 Fine-tuned | 13.7% | 0.0% | REGRESSED |
| VLM Preprocessed (CLAHE) | 46.8% | 12.5% | CLAHE hurts VLM |
| VLM Raw | 54.7% | 15.6% | Better without CLAHE |
| VLM Center Crop | 57.4% | 18.8% | Best single method |
| Ensemble V2 | 45.0% | 17.0% | 100% VLM fallback |
| Florence-2 on original high-res | 86-100% | — | Proves model works |

---

## Key Lessons

1. **Resolution trumps everything**: The single most important factor is per-billet pixel count
2. **Clean labels are non-negotiable**: Training on noisy labels is worse than no training
3. **Simpler is better**: One good engine (Florence-2) beats an ensemble of mediocre ones
4. **Verify ground truth manually**: Automated GT generation creates a garbage-in-garbage-out loop
5. **Test on real conditions first**: High-res success doesn't predict low-res performance
