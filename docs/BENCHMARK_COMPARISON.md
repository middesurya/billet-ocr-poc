# Billet OCR Benchmark Comparison Report

**Generated:** 2026-02-24
**Dataset:** ztai/steel-billet v7 from Roboflow Universe (30 images with ground truth)
**Original baseline:** 5 hand-labeled billet images

## Dataset Comparison

| Property | Original (5 images) | Roboflow (30 images) |
|----------|:---:|:---:|
| Stamp type | Dot-matrix pin marks | White paint stencil |
| Image resolution | 1536x2752+ (high-res) | 640x640 (pre-resized) |
| Number format | 6-digit heat + strand + seq | 5-digit heat + 4-digit seq |
| Billets per frame | 1 (close-up) | ~9 (surveillance view) |
| Source | Hand-photographed | Surveillance camera |
| Bounding boxes | None | COCO annotations (15,998 bboxes) |

## Accuracy Comparison

### PaddleOCR Methods

| Method | Original 5 | Roboflow 30 | Change |
|--------|:---:|:---:|:---:|
| PaddleOCR Raw | 3.3% | 1.9% | -1.4% |
| PaddleOCR + CLAHE | 10.0% | 4.3% | -5.7% |
| ROI + CLAHE | 10.6% | 3.1% | -7.5% |
| CLAHE + Correction | 14.7% | 6.4% | -8.3% |
| **Bbox Crop + CLAHE** | N/A | **15.0%** | (new) |

### VLM Methods

| Method | Original 5 | Roboflow 30 | Change |
|--------|:---:|:---:|:---:|
| VLM Preprocessed | 76.7% | 46.8% | -29.9% |
| VLM Raw | 86.0% | 54.7% | -31.3% |
| VLM Center Crop | 80.0% | 57.4% | -22.6% |
| Ensemble | 86.0% | 54.3% | -31.7% |

### Alternative OCR Engines

| Method | Roboflow 30 | Notes |
|--------|:---:|:---|
| EasyOCR | 0.0% | Windows encoding fix applied; crops too small |
| TrOCR | Not run | Requires GPU or slow CPU inference |
| docTR | Not run | Requires separate installation |
| GOT-OCR | Not run | Requires CUDA GPU |

## Key Findings

### 1. Image Resolution is Critical
The Roboflow images are pre-resized to 640x640 by Roboflow's preprocessing. With ~9 billets per frame, each individual billet face is only **50-100 pixels** wide. This is below the minimum effective resolution for PaddleOCR's DBNet++ detection network (typically needs 100+ pixels per character).

### 2. VLM Dominance
Claude Vision remains the only viable approach for these surveillance images:
- **VLM Center Crop (57.4%)** is the best method — 4x better than Bbox Crop PaddleOCR (15.0%)
- VLM handles small text and variable angles much better than traditional OCR
- However, VLM accuracy dropped ~25-30% vs original high-res images

### 3. CLAHE Hurts VLM Performance
On the Roboflow dataset, CLAHE preprocessing **reduced** VLM accuracy:
- VLM Raw: 54.7% vs VLM Preprocessed: 46.8% (-7.9%)
- CLAHE may wash out the white paint stencil contrast on these images
- For paint-stenciled text, raw images may be preferable

### 4. Bbox Crop is the Biggest PaddleOCR Win
Using Roboflow bounding boxes to crop individual billets before OCR:
- Raw → Bbox Crop: 1.9% → 15.0% (8x improvement)
- This confirms that detection (finding the billet) is a bigger problem than recognition

### 5. Multi-Billet Frame Challenge
The surveillance images show multiple billets. The current pipeline reads all text in the frame and picks the first line, which often picks up wrong billets or non-stamp text.

## Failure Mode Analysis

### Why PaddleOCR Fails
1. **Full frame**: Text from railings, equipment, and watermarks overwhelms the billet stamps
2. **Low resolution**: 50-100px billet faces are too small for character detection
3. **Multiple text sources**: 9 billets × 2 lines = 18 text regions competing for "heat number"
4. **Character confusion**: PaddleOCR reads digits as letters (0→O, 1→I, 5→S, 8→B)

### Why VLM is Better but Not Perfect
1. **Spatial reasoning**: VLM can understand which text belongs to which billet
2. **Context**: VLM knows "steel billet numbers" and reads accordingly
3. **Small text handling**: Better at upscaling and reading tiny characters
4. **Failures**: Still confused by augmented images (brightness, flip) and distant billets

## Recommendations

1. **Get higher-resolution images**: The 640x640 Roboflow preprocessing is destructive. Original surveillance frames are likely 1920x1080+. Re-downloading at native resolution would dramatically improve all methods.

2. **Focus VLM on bbox crops**: Crop individual billets using COCO bounding boxes, upscale to 256x256+, then send to VLM. This combines precise detection with superior recognition.

3. **Skip CLAHE for paint-stenciled text**: White paint on steel has good inherent contrast. CLAHE can reduce this contrast, hurting both VLM and OCR.

4. **Consider fine-tuning PaddleOCR**: The current general-purpose model struggles with industrial stamps. A model fine-tuned on billet stamp images (even 100-200 labeled examples) could improve dramatically.

5. **Multi-billet parsing**: Update `extract_billet_info()` to handle images with multiple billets — pick the largest/most-confident single reading rather than concatenating all text.
