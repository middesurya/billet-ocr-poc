# Billet OCR POC -- Status and Roadmap

**Date:** 2026-02-26
**Pipeline Version:** V11 Ensemble (Florence-2 + PaddleOCR + VLM Fallback)
**Current Accuracy:** 77.3% heat char accuracy, 68.5% exact match (73-billet GT V2 benchmark)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [What Was Accomplished](#what-was-accomplished)
3. [Architecture](#architecture)
4. [Accuracy Results](#accuracy-results)
5. [Key Files Modified](#key-files-modified)
6. [Known Limitations](#known-limitations)
7. [Dot-Matrix Support Roadmap](#dot-matrix-support-roadmap)
8. [Commands Reference](#commands-reference)
9. [Lessons Learned](#lessons-learned)

---

## Project Overview

This POC reads stamped identification codes from steel billet end-face photos. The codes contain 5-digit heat numbers and 3-4 digit sequence numbers applied via paint stencils onto cooled billets in a steel mill. Surveillance cameras capture multiple billets per frame (typically 8-12), and the pipeline must isolate and read each one independently.

### The Challenge

- White paint stencils on oxidized/scaled steel surfaces
- Variable lighting (indoor warehouse, outdoor yard, shadows)
- Yellow paint markings add visual noise
- Partially obscured, worn, or scale-covered codes
- Non-perpendicular camera angles
- Multiple billets per surveillance frame requiring per-billet isolation
- Billet crops as small as 53-75 pixels on the shortest side

### Billet Number Format (Paint Stencil -- Roboflow Dataset)

```
Line 1:  60008      (5-digit heat number)
Line 2:  5383       (3-4 digit sequence number)
```

---

## What Was Accomplished

### Part 1: Sequence Number Recovery

Prior to this work, the pipeline extracted heat numbers but returned 0% sequence numbers. Three independent fixes were needed across different OCR engines:

**1. Config fix** (`src/config.py`):

```python
# Before: only accepted 1-3 digit sequences
SEQUENCE_PATTERN = r"^\d{1,3}$"

# After: accepts 1-4 digit sequences (Roboflow uses 4-digit)
SEQUENCE_PATTERN = r"^\d{1,4}$"
```

**2. PaddleOCR paint-stencil parsing** (`src/ocr/paddle_ocr.py`):

PaddleOCR's `extract_billet_info()` now correctly handles the paint-stencil format where line 2 is a single 3-4 digit sequence token (no strand prefix), distinct from the dot-matrix format where line 2 contains "strand sequence":

```python
# Paint-stencil: line 2 IS the full sequence (e.g., "5383")
if len(parts) == 1 and re.match(r"^\d{3,4}$", parts[0]):
    sequence = parts[0].strip()
# Dot-matrix: line 2 is "[strand] [sequence]" with space
elif len(parts) >= 1:
    strand = parts[0].strip()
    if len(parts) >= 2:
        sequence = "".join(parts[1:]).strip()
```

**3. Florence-2 concatenated output splitting** (`src/ocr/florence2_reader.py`):

Florence-2 concatenates all visible text into a single blob (e.g., `"612535383"` instead of `"61253\n5383"`). Added logic to split at position 5:

```python
# 8-10 digits: first 5 = heat, rest = sequence
if heat_number and len(heat_number) >= 8 and sequence is None:
    sequence = heat_number[5:]
    heat_number = heat_number[:5]
# 6-7 digits: prefix = heat, suffix = partial sequence
elif heat_number and len(heat_number) in (6, 7) and sequence is None:
    suffix = heat_number[5:]
    heat_number = heat_number[:5]
    if suffix:
        sequence = suffix
```

**4. Format validator sequence extraction** (`src/postprocess/format_validator.py`):

Added `extract_heat_and_sequence()` to recover sequences from raw OCR text, handling both concatenated and space-separated formats:

```python
def extract_heat_and_sequence(raw_text: str) -> tuple[Optional[str], Optional[str]]:
    # Case 1: "612535383" -> heat="61253", seq="5383"
    # Case 2: "60008 5383" -> heat="60008", seq="5383"
```

**5. Inference pipeline wiring** (`src/ocr/inference.py`):

`run_billet_inference()` now calls `extract_heat_and_sequence()` on F2 raw text when the initial parse returns no sequence.

**Result:** Sequences went from 0% populated to 95.7% (268/280 billets across 30 test images).

---

### Part 2: YOLOv8 Billet Detector

Previously, billet detection relied entirely on pre-computed Roboflow annotations. New images (not in the Roboflow dataset) had no detection capability. A YOLOv8n detector was trained to fill this gap.

**Training setup:**

| Parameter | Value |
|-----------|-------|
| Model | YOLOv8n (nano, 3.2M params) |
| Dataset | 1,424 train + 127 val images |
| Classes | 1 ("billet") |
| Image size | 1280px |
| Epochs | 50 |
| Batch size | 4 |

**Training metrics (epoch 50):**

| Metric | Value |
|--------|-------|
| mAP@0.5 | 99.5% |
| mAP@0.5:0.95 | 92.1% |
| Precision | 99.0% |
| Recall | 99.3% |
| Model size | 6.3 MB |

**Three-tier detection chain** (`src/api/main.py`):

```
1. Roboflow annotations  -->  Known dataset images (exact bboxes)
       |
       v (not found)
2. YOLOv8 detector  -->  Any new image (trained model)
       |
       v (model not available)
3. Edge detection  -->  Last resort fallback
```

In testing on 5 images not in the annotation cache, all used YOLO detection successfully (zero edge fallback needed), detecting 8-12 billets per image.

**Key files:**

| File | Purpose |
|------|---------|
| `scripts/prepare_yolo_training.py` | Converts COCO annotations to YOLO format |
| `scripts/train_yolo_detector.py` | YOLOv8 training script |
| `scripts/test_yolo_inference.py` | End-to-end pipeline test on unannotated images |
| `src/preprocessing/yolo_detector.py` | Singleton YOLO model with `detect_billets_yolo()` |
| `models/yolo_billet_detector/best.pt` | Trained weights (6.3 MB) |

---

### Part 3: Ensemble Sequence Selection Fix

The cross-validation ensemble (`src/ocr/ensemble.py`) previously discarded PaddleOCR's sequence when the AGREE or F2_ONLY decision paths were taken. This was a problem because:

- PaddleOCR reads line-by-line (DBNet++ finds each text line separately), producing full 3-4 digit sequences
- Florence-2 concatenates everything into one blob, and the splitter often truncates to 1-2 digits

**Fix: `_pick_best_sequence()` added to `ensemble.py`:**

```python
def _pick_best_sequence(f2_seq, paddle_seq) -> Optional[str]:
    """Prefer the longer sequence (3-4 digits over 1-2 digits).
    Same length: prefer PaddleOCR (reads sequences line-by-line)."""
    if len(paddle_seq) > len(f2_seq):
        return paddle_seq
    if len(f2_seq) > len(paddle_seq):
        return f2_seq
    return paddle_seq  # same length -> prefer Paddle
```

This function is now called in both decision paths:

- **AGREE path:** Picks longer sequence instead of defaulting to F2's truncated version
- **F2_ONLY path:** Checks PaddleOCR's sequence even when Paddle's heat number is invalid

**Example fix (Billet #7):**

| | Before | After |
|---|--------|-------|
| Heat | 80622 | 80622 |
| Sequence | 55 (truncated) | 5353 (correct) |
| Source | F2 only | F2 heat + Paddle sequence |

---

## Architecture

```
                    +-------------------+
                    |  Surveillance      |
                    |  Camera Image      |
                    +--------+----------+
                             |
                    +--------v----------+
                    |  Billet Detection  |
                    |  (3-tier chain)    |
                    |                   |
                    | 1. Roboflow annot.|
                    | 2. YOLOv8n (6MB)  |
                    | 3. Edge detection  |
                    +--------+----------+
                             |
                    Per-billet bbox crops
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+       +-----------v-----------+
    |  Florence-2       |       |  PaddleOCR            |
    |  Multi-Orient     |       |  + CLAHE preprocessing|
    |  (0 + 180 deg)    |       |  + Char correction    |
    |  + Format valid.  |       |  + Line-by-line read  |
    +---------+---------+       +-----------+-----------+
              |                             |
              +-------------+---------------+
                            |
                  +---------v---------+
                  | Cross-Validation  |
                  | Ensemble          |
                  |                   |
                  | AGREE: boost conf |
                  | DISAGREE: Paddle  |
                  | F2_ONLY: F2 heat  |
                  |   + Paddle seq    |
                  | NEITHER: VLM      |
                  +---------+---------+
                            |
              (low confidence / neither valid)
                            |
                  +---------v---------+
                  |  Claude Vision    |
                  |  VLM Fallback     |
                  |  (API call)       |
                  +-------------------+
```

### Why PaddleOCR Outperforms Florence-2 on Sequences

| Aspect | Florence-2 | PaddleOCR |
|--------|-----------|-----------|
| Text detection | Single blob OCR task | DBNet++ finds each line separately |
| Output format | Concatenated: `"612535383"` | Line 1: `"61253"`, Line 2: `"5383"` |
| Sequence quality | Often truncated (1-2 digits) | Full 3-4 digits |
| Heat number | Better at multi-orientation | Good but no rotation handling |
| Preprocessing | No preprocessing needed | CLAHE enhances white paint contrast |
| Speed | ~200ms per crop (GPU) | ~300ms per crop (CPU) |

### Cross-Validation Decision Rules

| Scenario | Rule | Rationale |
|----------|------|-----------|
| Both valid, same heat | **AGREE** -- boost confidence +0.2 | High reliability when engines agree |
| Both valid, different heat | **DISAGREE** -- prefer PaddleOCR | Simpson's Paradox: F2 has more "confident errors" on the disagree subset |
| Only F2 valid | **F2_ONLY** -- F2 heat + pick best sequence | PaddleOCR may still have correct sequence |
| Only Paddle valid | **PADDLE_ONLY** -- use Paddle | Straightforward |
| Neither valid | **NEITHER** -- VLM fallback, then best partial | Highest value from VLM on hard cases |

---

## Accuracy Results

### Browse Data Results (30 images, 280 billets)

| Metric | Result |
|--------|--------|
| Heat numbers populated | 98.6% (276/280) |
| Sequences populated | 95.7% (268/280) |
| AGREE decisions | 66.4% |
| F2_ONLY decisions | 15.7% |
| DISAGREE_PADDLE decisions | 12.5% |
| PADDLE_ONLY decisions | 3.6% |
| NEITHER_VALID decisions | 1.8% |

### Benchmark History (73-billet GT V2 Dataset)

| Version | Method | Heat Char Acc | Exact Match |
|---------|--------|:------------:|:-----------:|
| V9 | PaddleOCR + CLAHE (standalone) | 65.2% | 56.2% |
| V9 | Florence-2 zero-shot | 49.6% | 6.8% |
| V10 | F2 + format validator fix | 60.8% | 52.1% |
| V10 | F2 multi-orient (0 + 180 deg) | 69.9% | 60.3% |
| **V10** | **F2 + PaddleOCR ensemble** | **77.0%** | **68.5%** |
| **V11** | **Ensemble + Paddle char correction** | **77.3%** | **68.5%** |
| V11+ | Ensemble + VLM fallback | >80% (projected, untested) |

### Mathematical Ceiling Analysis

The benchmark contains 15 billets from `billet_05` (one surveillance image) with 53-75px crops of embossed stamps. These are below the information-theoretic floor for any OCR engine:

| Metric | Value |
|--------|-------|
| Total billets | 73 |
| Reachable billets | 58 |
| Unreachable (billet_05) | 15 (20.5% of benchmark) |
| Ensemble on reachable | **96.9%** char accuracy |
| Ensemble overall | 77.3% (dragged down by billet_05) |
| **Max possible without VLM** | **79.7%** |

---

## Key Files Modified

| File | Changes |
|------|---------|
| `src/config.py` | `SEQUENCE_PATTERN` widened to `r"^\d{1,4}$"`, YOLO config constants added (`YOLO_MODEL_PATH`, `YOLO_CONFIDENCE_THRESHOLD`, `YOLO_IOU_THRESHOLD`) |
| `src/ocr/paddle_ocr.py` | `extract_billet_info()` updated for paint-stencil format (single 3-4 digit token on line 2 = sequence, no strand) |
| `src/ocr/florence2_reader.py` | `_parse_florence2_output()` splits 6-10 digit concatenated outputs at position 5 into heat + sequence |
| `src/postprocess/format_validator.py` | New `extract_heat_and_sequence()` function for recovering sequences from raw OCR text |
| `src/ocr/inference.py` | `run_billet_inference()` wired to call `extract_heat_and_sequence()` for F2 sequence recovery |
| `src/ocr/ensemble.py` | New `_pick_best_sequence()` function; AGREE and F2_ONLY paths now select the longer/better sequence from either engine |
| `src/preprocessing/yolo_detector.py` | **New file:** YOLOv8 singleton model loader + `detect_billets_yolo()` detection function |
| `src/api/main.py` | Three-tier detection chain (Roboflow -> YOLO -> Edge) in `_run_inference_sync()` |
| `frontend/index.html` | Added `"yolo_detector"` to `bbox_source` display map |
| `scripts/prepare_yolo_training.py` | **New file:** COCO-to-YOLO annotation converter |
| `scripts/train_yolo_detector.py` | **New file:** YOLOv8 training script with CLI arguments |
| `scripts/test_yolo_inference.py` | **New file:** End-to-end pipeline test without pre-computed annotations |

---

## Known Limitations

1. **Dot-matrix pin-marking stamps are NOT supported yet.** The format validator rejects 6-digit heat numbers, and the concatenated output splitter assumes a 5-digit heat prefix. See [Dot-Matrix Support Roadmap](#dot-matrix-support-roadmap).

2. **VLM fallback is untested.** The Anthropic API rate limit was hit on 2026-02-25 and resets on 2026-03-01. The `NEITHER_VALID` path (5.4% of billets) would benefit most from VLM. Projected accuracy with VLM: >80%.

3. **Mathematical ceiling of 79.7% without VLM.** The 15 billet_05 billets (20.5% of the benchmark) have 53-75px embossed stamp crops that are below the resolution floor of every OCR engine tested. No preprocessing (CLAHE, unsharp mask, bilateral filter) helps.

4. **YOLO detector trained only on paint-stencil surveillance images.** The 1,424 training images are all from the Roboflow dataset (white paint on steel, surveillance camera perspective). Performance on dot-matrix close-up photos is unknown -- edge detection fallback handles those cases today.

5. **Florence-2 sequence truncation persists for some billets.** The concatenated output splitter assumes the heat is always at positions 0-4. If Florence-2 reads noise before the heat number, the split point is wrong. PaddleOCR sequence selection mitigates this for 66.4% (AGREE) + 15.7% (F2_ONLY) of cases.

6. **69 ground-truth entries is too few for meaningful fine-tuning.** LoRA fine-tuning (V2) showed no improvement over zero-shot. Expanding the labeled dataset is a prerequisite for any model training approach.

---

## Dot-Matrix Support Roadmap

The current POC is optimized for the Roboflow paint-stencil format. Dot-matrix pin-marking stamps (the original use case from the 5 reference images) have fundamentally different characteristics:

### Format Comparison

| Feature | Paint Stencil (current) | Dot-Matrix (future) |
|---------|------------------------|---------------------|
| Heat digits | 5-digit (e.g., `60008`) | 6-digit (e.g., `184767`) |
| Line 2 format | Single 4-digit sequence (e.g., `5383`) | Strand + Sequence (e.g., `3 09`) |
| Contrast | High (white paint on steel) | Very low (embossed dots on oxidized surface) |
| Camera distance | Far (surveillance, 8-12 billets/frame) | Close-up (single billet, high-res) |
| Resolution per billet | 80-150px crops | 500-2000px crops |
| CLAHE impact | Moderate improvement | Significant improvement |

### Changes Required

1. **Heat validation** -- Accept 5 OR 6 digit heat numbers:
   ```python
   # src/config.py
   HEAT_NUMBER_PATTERN = r"^\d{5,7}$"  # Already accepts 5-7 digits
   ```
   The pattern already allows 6 digits, but `_is_valid_5digit_heat()` in `ensemble.py` explicitly checks for exactly 5 digits. This function needs a configurable length:
   ```python
   # New: accept 5 or 6 digit heats based on context
   HEAT_NUMBER_DIGITS = [5, 6]
   ```

2. **Format validator** -- Handle 6-digit heat extraction in `extract_best_heat_number()`:
   ```python
   # Currently: 5-digit candidates score 1.0, 6-digit score 0.4
   # Needed: context-aware scoring (factory config determines expected length)
   ```

3. **Concatenated output splitter** -- Try 6-digit split before 5-digit:
   ```python
   # Current: always splits at position 5
   # Needed: try position 6 first if configured for dot-matrix
   ```

4. **Ensemble cross-validation** -- Update `_is_valid_5digit_heat()` to `_is_valid_heat()` in decision logic:
   ```python
   # Use the configurable validator instead of hardcoded 5-digit check
   ```

5. **YOLO detector** -- Either retrain with dot-matrix images or accept edge detection fallback for close-up billet photos (which work well at high resolution).

### What Already Works for Dot-Matrix

- PaddleOCR `extract_billet_info()` handles "strand sequence" format (e.g., `"3 09"`)
- CLAHE preprocessing significantly enhances low-contrast embossed dots
- Florence-2 achieved 86-100% accuracy on the original 5 high-res dot-matrix images
- Edge detection fallback works well for close-up single-billet photos
- The `HEAT_NUMBER_PATTERN` regex already accepts 5-7 digit numbers

### Estimated Effort

| Task | Complexity | Files |
|------|-----------|-------|
| Configurable heat length | Low | `config.py`, `ensemble.py` |
| Format validator updates | Medium | `format_validator.py` |
| Concatenated splitter | Low | `florence2_reader.py` |
| Testing with dot-matrix images | Medium | New ground truth needed |
| YOLO retraining (optional) | High | Training data collection |

---

## Commands Reference

### Inference and Demo

```bash
# Start the API server (serves frontend + live inference)
python -m uvicorn src.api.main:app --port 8001

# Regenerate browse data (30 images, pre-computed)
python scripts/visual_inference.py --max-images 30 --seed 42

# Quick smoke test (5 images)
python scripts/visual_inference.py --max-images 5 --seed 42
```

### Benchmarking

```bash
# Full V11 ensemble benchmark (73 billets, no VLM)
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2

# Quick subset benchmark
python scripts/benchmark.py --florence2 --bbox-crop --no-vlm --gt-v2 --max-images 30

# With VLM fallback (requires Anthropic API key)
python scripts/benchmark.py --florence2 --bbox-crop --gt-v2
```

### YOLO Detector

```bash
# Step 1: Convert COCO annotations to YOLO format
python scripts/prepare_yolo_training.py

# Step 2: Train YOLOv8n (50 epochs, GPU)
python scripts/train_yolo_detector.py --epochs 50 --batch 4 --workers 0

# Step 3: Test pipeline on images without pre-computed annotations
python scripts/test_yolo_inference.py --max-images 5 --save-annotated
```

### Dataset and Ground Truth

```bash
# Download Roboflow dataset
python scripts/download_roboflow_dataset.py --copy-to-raw --clear-raw

# Parse bounding box annotations
python scripts/parse_roboflow_annotations.py

# Extract ground truth (multi-billet, all bboxes)
python scripts/extract_ground_truth.py --use-bbox --all-bboxes --max-images 30

# Prepare Florence-2 fine-tuning data
python scripts/prepare_florence2_training.py --gt-v2 --augment-factor 3 --target-size 768 --seed 42
```

### Testing

```bash
# Run all unit tests
python -m pytest tests/ -v
```

---

## Lessons Learned

These are the most impactful lessons from building this POC, in order of practical value:

1. **Post-processing beats model improvements.** The format validator fix alone gave +11.2% accuracy (49.6% to 60.8%) -- more impact than any model change, fine-tuning attempt, or preprocessing technique.

2. **Complementary engines beat individual ones.** The F2+PaddleOCR ensemble (77.0%) exceeds both F2 alone (60.8%) and PaddleOCR alone (65.2%) because they fail on different images with different error patterns.

3. **Simpson's Paradox applies to ensemble decisions.** F2 Orient has higher overall accuracy (69.9%) than PaddleOCR (65.2%), but on the disagree subset, PaddleOCR wins. Switching to prefer-F2 dropped the ensemble from 77.0% to 72.1%.

4. **Resolution is the primary bottleneck.** 53-75px billet crops are below the information-theoretic floor for any OCR engine. No amount of preprocessing, model selection, or ensembling can recover information that was never captured.

5. **Each OCR engine has structural strengths.** PaddleOCR's DBNet++ text detector reads line-by-line (better sequences). Florence-2's multi-orientation handles upside-down billets. Using each for what it does best yields the highest accuracy.

6. **Do not override model defaults without benchmarking.** Florence-2 internally defaults to `num_beams=3`. Setting `num_beams=1` caused a -4.4% regression. Setting `num_beams=3` explicitly had no effect (it was already the default).

7. **Larger models can hurt ensembles.** Florence-2-large (0.77B) improved individual F2 accuracy by +1.1% but reduced ensemble accuracy by -2.2% because it changed the error distribution that the cross-validation logic was optimized for.

8. **Data quality matters more than data quantity for fine-tuning.** Fine-tuning on 46%-accurate VLM-generated labels caused catastrophic forgetting (30.8% to 13.7%). Even with clean labels, 69 samples was too few for meaningful LoRA improvement.

9. **CLAHE helps traditional OCR but hurts VLMs.** CLAHE preprocessing improved PaddleOCR accuracy but reduced Claude Vision accuracy (46.8% vs 54.7% on raw images). Each engine has its own optimal input.

10. **Three-tier detection (annotations -> YOLO -> edge) provides graceful degradation.** Known dataset images get exact bounding boxes. New images get YOLO detection (99.5% mAP). If YOLO weights are missing, edge detection still works.
