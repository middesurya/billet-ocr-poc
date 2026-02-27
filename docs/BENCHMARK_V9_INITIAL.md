# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-25 03:32 UTC  
**Images evaluated:** 30  
**VLM model:** `claude-sonnet-4-5-20250929`  
**Prompt version:** V3  
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
| VLM prompt version | 3 |
| VLM crop ratio | 0.6 |

## Summary

| Method | Avg Char Accuracy | Avg Word Accuracy | Avg Time |
|--------|-------------------|-------------------|----------|
| PaddleOCR Raw | - | - | - |
| PaddleOCR + CLAHE | - | - | - |
| ROI + CLAHE | - | - | - |
| CLAHE + Correction | - | - | - |
| Bbox Crop + CLAHE | - | - | - |
| VLM Fallback | - | - | - |
| VLM Preprocessed | - | - | - |
| VLM Raw | - | - | - |
| VLM Center Crop | - | - | - |
| Florence-2 Raw | 37.6% | 0.0% | 700ms |
| Florence-2 Crop | 40.0% | 0.0% | 269ms |
| Florence-2 Bbox Crop | 53.5% | 0.0% | 94ms |
| F2 Bbox+SuperRes | 54.9% | 0.0% | 93ms |
| F2 Raw+Validated | 37.6% | 0.0% | - |
| Ensemble | - | - | - |
| Ensemble V2 | - | - | - |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |
|-------|---------|------------------|---------|-----------------|--------|---------|---------|------------|------------|
| 20250316051248_jpg.rf.4aeecc54ae1dc3a5e2d8d8351afe420f.jpg | SSE13 | - | - | - | - (0%) | - (0%) | - | - | 5555555 (0%) |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | - | - | - | 8228782 (43%) | 8028780 (57%) | 60287 (60%) | 80287 (80%) | 8228782 (43%) |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | - | - | - | 8054980 (57%) | 6054960 (71%) | 6054953 (71%) | 6054953 (71%) | 8054980 (57%) |
| 20250320065550_jpg.rf.7284f13303bd5fb4c6af4f555db404c3.jpg | X0E19 | - | - | - | 8654380 (0%) | 8054380 (14%) | - | - | 8654380 (0%) |
| 202503290307049445_jpg.rf.53c20a8b2443dfe033db7c768beae4db.jpg | 60008 | - | - | - | 6838868 (29%) | 6398869 (29%) | - | - | 6838868 (29%) |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | - | - | - | 8105281 (71%) | 8105281 (71%) | 8105253 (71%) | 8105253 (71%) | 8105281 (71%) |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | - | - | - | 6157615 (29%) | 6125753 (43%) | 6125753 (43%) | 6125753 (43%) | 6157615 (29%) |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | - | - | - | 1256124 (43%) | 2456124 (43%) | 6124553 (57%) | 6124553 (57%) | 1256124 (43%) |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | - | - | - | 6817486 (57%) | 6047486 (57%) | 6074853 (57%) | 6074853 (57%) | 6817486 (57%) |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | - | - | - | 8896889 (43%) | 8096880 (29%) | 8098865 (29%) | 8098653 (29%) | 8896889 (43%) |
| 202503301404576048_jpg.rf.7656e27e83761791753403fb127a97e3.jpg | 60008 | - | - | - | 6078687 (43%) | 5878687 (14%) | - | - | 6078687 (43%) |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | - | - | - | 2333232 (57%) | 2383238 (57%) | 2353151 (43%) | 2353151 (43%) | 2333232 (57%) |
| 202503301909102764_jpg.rf.88f0aad9f0fada933fca3bb1cf7f6595.jpg | 67468 | - | - | - | 6148646 (43%) | 4686146 (29%) | - | - | 6148646 (43%) |
| 202503301909102764_jpg.rf.f861b6e5f8c875f716328c32000dfba5.jpg | 67468 | - | - | - | 6148646 (43%) | 4686146 (29%) | - | - | 6148646 (43%) |
| 202503302318206024_jpg.rf.bfa3e95c0a5efebec7d1d8e1340027d0.jpg | 60088 | - | - | - | 6868886 (43%) | 6868685 (43%) | - | - | 6868886 (43%) |
| 202504010810261480_jpg.rf.048e9919ed0494dee86f151f3e08f482.jpg | 30551 | - | - | - | 8855885 (29%) | 8855786 (29%) | - | - | 8855885 (29%) |
| 202504011049280601_jpg.rf.52fb6672fd8a308513c1a0b9263ef397.jpg | 87467 | - | - | - | 6147674 (43%) | 6146764 (43%) | - | - | 6147674 (43%) |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | - | - | - | 6148261 (71%) | 6148261 (71%) | 6148253 (71%) | 6148253 (71%) | 6148261 (71%) |
| screenshot_2025-04-02_14-19-39_jpg.rf.8ed2e1f914f5dc521be1b38cb67aed02.jpg | 60008 | - | - | - | 6895689 (29%) | 8580958 (29%) | - | - | 6895689 (29%) |
| screenshot_2025-04-03_19-07-27_jpg.rf.a4fb1ae2213e38619a6b749fd37c49b0.jpg | 00092 | - | - | - | 6892609 (14%) | 6093226 (29%) | - | - | 6892609 (14%) |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | - | - | - | 285285 (0%) | 2085202 (14%) | - (0%) | - (0%) | 285285 (0%) |
| screenshot_2025-04-03_19-47-30_jpg.rf.5deee694ccec3c0c25296751f59c5392.jpg | 23710 | - | - | - | - (0%) | - (0%) | - | - | - (0%) |
| screenshot_2025-04-04_04-20-54_jpg.rf.373639a2bd9ac6adc97a256a7999f4e6.jpg | 080012 | - | - | - | 8881288 (29%) | 6831268 (29%) | - | - | 8881288 (29%) |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | - | - | - | 8141781 (57%) | 8141788 (57%) | 8141753 (57%) | 8141753 (57%) | 8141781 (57%) |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | - | - | - | 8184467 (43%) | 6134461 (71%) | 6134453 (71%) | 6134453 (71%) | 8184467 (43%) |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg | 67652 | - | - | - | 6152525 (43%) | 6125261 (43%) | - | - | 6152525 (43%) |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | - | - | - | 8140861 (43%) | 6414061 (43%) | 6140053 (57%) | 6140053 (57%) | 8140861 (43%) |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | - | - | - | 8694889 (43%) | 5094860 (43%) | 6094853 (57%) | 6094853 (57%) | 8694889 (43%) |
| screenshot_2025-04-06_10-02-33_jpg.rf.e607e2aebca50504d24b905b7f48b098.jpg | 84479 | - | - | - | 8479814 (43%) | 8147984 (57%) | - | - | 8479814 (43%) |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | - | - | - | 8288188 (43%) | 8008180 (57%) | 8008154 (57%) | 8000815 (57%) | 8288188 (43%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| 20250316051248_jpg.rf.4aeecc54ae1dc3a5e2d8d8351afe420f.jpg | SSE13 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250316051248_jpg.rf.4aeecc54ae1dc3a5e2d8d8351afe420f.jpg | SSE13 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250316051248_jpg.rf.4aeecc54ae1dc3a5e2d8d8351afe420f.jpg | SSE13 | F2 Raw+Validated | 5555555 | `XXXXX++` | 0.0% |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | Florence-2 Raw | 8228782 | `.X..+++` | 42.9% |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | Florence-2 Crop | 8028780 | `....+++` | 57.1% |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | Florence-2 Bbox Crop | 60287 | `X...+` | 60.0% |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | F2 Bbox+SuperRes | 80287 | `....+` | 80.0% |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg | 8028 | F2 Raw+Validated | 8228782 | `.X..+++` | 42.9% |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | Florence-2 Raw | 8054980 | `X....++` | 57.1% |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | Florence-2 Crop | 6054960 | `.....++` | 71.4% |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | Florence-2 Bbox Crop | 6054953 | `.....++` | 71.4% |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | F2 Bbox+SuperRes | 6054953 | `.....++` | 71.4% |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg | 60549 | F2 Raw+Validated | 8054980 | `X....++` | 57.1% |
| 20250320065550_jpg.rf.7284f13303bd5fb4c6af4f555db404c3.jpg | X0E19 | Florence-2 Raw | 8654380 | `XXXXX++` | 0.0% |
| 20250320065550_jpg.rf.7284f13303bd5fb4c6af4f555db404c3.jpg | X0E19 | Florence-2 Crop | 8054380 | `X.XXX++` | 14.3% |
| 20250320065550_jpg.rf.7284f13303bd5fb4c6af4f555db404c3.jpg | X0E19 | F2 Raw+Validated | 8654380 | `XXXXX++` | 0.0% |
| 202503290307049445_jpg.rf.53c20a8b2443dfe033db7c768beae4db.jpg | 60008 | Florence-2 Raw | 6838868 | `.XXX.++` | 28.6% |
| 202503290307049445_jpg.rf.53c20a8b2443dfe033db7c768beae4db.jpg | 60008 | Florence-2 Crop | 6398869 | `.XXX.++` | 28.6% |
| 202503290307049445_jpg.rf.53c20a8b2443dfe033db7c768beae4db.jpg | 60008 | F2 Raw+Validated | 6838868 | `.XXX.++` | 28.6% |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | Florence-2 Raw | 8105281 | `.....++` | 71.4% |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | Florence-2 Crop | 8105281 | `.....++` | 71.4% |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | Florence-2 Bbox Crop | 8105253 | `.....++` | 71.4% |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | F2 Bbox+SuperRes | 8105253 | `.....++` | 71.4% |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg | 81052 | F2 Raw+Validated | 8105281 | `.....++` | 71.4% |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | Florence-2 Raw | 6157615 | `XX..+++` | 28.6% |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | Florence-2 Crop | 6125753 | `XXXX+++` | 42.9% |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | Florence-2 Bbox Crop | 6125753 | `XXXX+++` | 42.9% |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | F2 Bbox+SuperRes | 6125753 | `XXXX+++` | 42.9% |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg | 5257 | F2 Raw+Validated | 6157615 | `XX..+++` | 28.6% |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | Florence-2 Raw | 1256124 | `XXXXX++` | 42.9% |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | Florence-2 Crop | 2456124 | `XXXXX++` | 42.9% |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | Florence-2 Bbox Crop | 6124553 | `X....++` | 57.1% |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | F2 Bbox+SuperRes | 6124553 | `X....++` | 57.1% |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg | 51245 | F2 Raw+Validated | 1256124 | `XXXXX++` | 42.9% |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | Florence-2 Raw | 6817486 | `.X.XX++` | 57.1% |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | Florence-2 Crop | 6047486 | `..XXX++` | 57.1% |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | Florence-2 Bbox Crop | 6074853 | `..X..++` | 57.1% |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | F2 Bbox+SuperRes | 6074853 | `..X..++` | 57.1% |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg | 60148 | F2 Raw+Validated | 6817486 | `.X.XX++` | 57.1% |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | Florence-2 Raw | 8896889 | `..XX.++` | 42.9% |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | Florence-2 Crop | 8096880 | `.XXX.++` | 28.6% |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | Florence-2 Bbox Crop | 8098865 | `.XXX.++` | 28.6% |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | F2 Bbox+SuperRes | 8098653 | `.XXXX++` | 28.6% |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg | 88798 | F2 Raw+Validated | 8896889 | `..XX.++` | 42.9% |
| 202503301404576048_jpg.rf.7656e27e83761791753403fb127a97e3.jpg | 60008 | Florence-2 Raw | 6078687 | `..XXX++` | 42.9% |
| 202503301404576048_jpg.rf.7656e27e83761791753403fb127a97e3.jpg | 60008 | Florence-2 Crop | 5878687 | `XXXXX++` | 14.3% |
| 202503301404576048_jpg.rf.7656e27e83761791753403fb127a97e3.jpg | 60008 | F2 Raw+Validated | 6078687 | `..XXX++` | 42.9% |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | Florence-2 Raw | 2333232 | `....+++` | 57.1% |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | Florence-2 Crop | 2383238 | `..X.+++` | 57.1% |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | Florence-2 Bbox Crop | 2353151 | `..X.+++` | 42.9% |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | F2 Bbox+SuperRes | 2353151 | `..X.+++` | 42.9% |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg | 2333 | F2 Raw+Validated | 2333232 | `....+++` | 57.1% |
| 202503301909102764_jpg.rf.88f0aad9f0fada933fca3bb1cf7f6595.jpg | 67468 | Florence-2 Raw | 6148646 | `.X.XX++` | 42.9% |
| 202503301909102764_jpg.rf.88f0aad9f0fada933fca3bb1cf7f6595.jpg | 67468 | Florence-2 Crop | 4686146 | `XXX.X++` | 28.6% |
| 202503301909102764_jpg.rf.88f0aad9f0fada933fca3bb1cf7f6595.jpg | 67468 | F2 Raw+Validated | 6148646 | `.X.XX++` | 42.9% |
| 202503301909102764_jpg.rf.f861b6e5f8c875f716328c32000dfba5.jpg | 67468 | Florence-2 Raw | 6148646 | `.X.XX++` | 42.9% |
| 202503301909102764_jpg.rf.f861b6e5f8c875f716328c32000dfba5.jpg | 67468 | Florence-2 Crop | 4686146 | `XXX.X++` | 28.6% |
| 202503301909102764_jpg.rf.f861b6e5f8c875f716328c32000dfba5.jpg | 67468 | F2 Raw+Validated | 6148646 | `.X.XX++` | 42.9% |
| 202503302318206024_jpg.rf.bfa3e95c0a5efebec7d1d8e1340027d0.jpg | 60088 | Florence-2 Raw | 6868886 | `.XX..++` | 42.9% |
| 202503302318206024_jpg.rf.bfa3e95c0a5efebec7d1d8e1340027d0.jpg | 60088 | Florence-2 Crop | 6868685 | `.XX.X++` | 42.9% |
| 202503302318206024_jpg.rf.bfa3e95c0a5efebec7d1d8e1340027d0.jpg | 60088 | F2 Raw+Validated | 6868886 | `.XX..++` | 42.9% |
| 202504010810261480_jpg.rf.048e9919ed0494dee86f151f3e08f482.jpg | 30551 | Florence-2 Raw | 8855885 | `XX..X++` | 28.6% |
| 202504010810261480_jpg.rf.048e9919ed0494dee86f151f3e08f482.jpg | 30551 | Florence-2 Crop | 8855786 | `XX..X++` | 28.6% |
| 202504010810261480_jpg.rf.048e9919ed0494dee86f151f3e08f482.jpg | 30551 | F2 Raw+Validated | 8855885 | `XX..X++` | 28.6% |
| 202504011049280601_jpg.rf.52fb6672fd8a308513c1a0b9263ef397.jpg | 87467 | Florence-2 Raw | 6147674 | `XX.XX++` | 42.9% |
| 202504011049280601_jpg.rf.52fb6672fd8a308513c1a0b9263ef397.jpg | 87467 | Florence-2 Crop | 6146764 | `XX...++` | 42.9% |
| 202504011049280601_jpg.rf.52fb6672fd8a308513c1a0b9263ef397.jpg | 87467 | F2 Raw+Validated | 6147674 | `XX.XX++` | 42.9% |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | Florence-2 Raw | 6148261 | `.....++` | 71.4% |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | Florence-2 Crop | 6148261 | `.....++` | 71.4% |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | Florence-2 Bbox Crop | 6148253 | `.....++` | 71.4% |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | F2 Bbox+SuperRes | 6148253 | `.....++` | 71.4% |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg | 61482 | F2 Raw+Validated | 6148261 | `.....++` | 71.4% |
| screenshot_2025-04-02_14-19-39_jpg.rf.8ed2e1f914f5dc521be1b38cb67aed02.jpg | 60008 | Florence-2 Raw | 6895689 | `.XXXX++` | 28.6% |
| screenshot_2025-04-02_14-19-39_jpg.rf.8ed2e1f914f5dc521be1b38cb67aed02.jpg | 60008 | Florence-2 Crop | 8580958 | `XXX.X++` | 28.6% |
| screenshot_2025-04-02_14-19-39_jpg.rf.8ed2e1f914f5dc521be1b38cb67aed02.jpg | 60008 | F2 Raw+Validated | 6895689 | `.XXXX++` | 28.6% |
| screenshot_2025-04-03_19-07-27_jpg.rf.a4fb1ae2213e38619a6b749fd37c49b0.jpg | 00092 | Florence-2 Raw | 6892609 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_19-07-27_jpg.rf.a4fb1ae2213e38619a6b749fd37c49b0.jpg | 00092 | Florence-2 Crop | 6093226 | `X.XX.++` | 28.6% |
| screenshot_2025-04-03_19-07-27_jpg.rf.a4fb1ae2213e38619a6b749fd37c49b0.jpg | 00092 | F2 Raw+Validated | 6892609 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | Florence-2 Raw | 285285 | `XXXXX+` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | Florence-2 Crop | 2085202 | `X.XXX++` | 14.3% |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg | 50619 | F2 Raw+Validated | 285285 | `XXXXX+` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.5deee694ccec3c0c25296751f59c5392.jpg | 23710 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.5deee694ccec3c0c25296751f59c5392.jpg | 23710 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-03_19-47-30_jpg.rf.5deee694ccec3c0c25296751f59c5392.jpg | 23710 | F2 Raw+Validated | - | `-----` | 0.0% |
| screenshot_2025-04-04_04-20-54_jpg.rf.373639a2bd9ac6adc97a256a7999f4e6.jpg | 080012 | Florence-2 Raw | 8881288 | `X.XXXX+` | 28.6% |
| screenshot_2025-04-04_04-20-54_jpg.rf.373639a2bd9ac6adc97a256a7999f4e6.jpg | 080012 | Florence-2 Crop | 6831268 | `X.XXXX+` | 28.6% |
| screenshot_2025-04-04_04-20-54_jpg.rf.373639a2bd9ac6adc97a256a7999f4e6.jpg | 080012 | F2 Raw+Validated | 8881288 | `X.XXXX+` | 28.6% |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | Florence-2 Raw | 8141781 | `...X.++` | 57.1% |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | Florence-2 Crop | 8141788 | `...X.++` | 57.1% |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | Florence-2 Bbox Crop | 8141753 | `...X.++` | 57.1% |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | F2 Bbox+SuperRes | 8141753 | `...X.++` | 57.1% |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg | 81447 | F2 Raw+Validated | 8141781 | `...X.++` | 57.1% |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | Florence-2 Raw | 8184467 | `X.X..++` | 42.9% |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | Florence-2 Crop | 6134461 | `.....++` | 71.4% |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | Florence-2 Bbox Crop | 6134453 | `.....++` | 71.4% |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | F2 Bbox+SuperRes | 6134453 | `.....++` | 71.4% |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg | 61344 | F2 Raw+Validated | 8184467 | `X.X..++` | 42.9% |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg | 67652 | Florence-2 Raw | 6152525 | `.XXXX++` | 42.9% |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg | 67652 | Florence-2 Crop | 6125261 | `.XX..++` | 42.9% |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg | 67652 | F2 Raw+Validated | 6152525 | `.XXXX++` | 42.9% |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | Florence-2 Raw | 8140861 | `X..XX++` | 42.9% |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | Florence-2 Crop | 6414061 | `.XXX.++` | 42.9% |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | Florence-2 Bbox Crop | 6140053 | `...X.++` | 57.1% |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | F2 Bbox+SuperRes | 6140053 | `...X.++` | 57.1% |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg | 61480 | F2 Raw+Validated | 8140861 | `X..XX++` | 42.9% |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | Florence-2 Raw | 8694889 | `XXX..++` | 42.9% |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | Florence-2 Crop | 5094860 | `X.X..++` | 42.9% |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | Florence-2 Bbox Crop | 6094853 | `..X..++` | 57.1% |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | F2 Bbox+SuperRes | 6094853 | `..X..++` | 57.1% |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg | 60448 | F2 Raw+Validated | 8694889 | `XXX..++` | 42.9% |
| screenshot_2025-04-06_10-02-33_jpg.rf.e607e2aebca50504d24b905b7f48b098.jpg | 84479 | Florence-2 Raw | 8479814 | `..XXX++` | 42.9% |
| screenshot_2025-04-06_10-02-33_jpg.rf.e607e2aebca50504d24b905b7f48b098.jpg | 84479 | Florence-2 Crop | 8147984 | `.X...++` | 57.1% |
| screenshot_2025-04-06_10-02-33_jpg.rf.e607e2aebca50504d24b905b7f48b098.jpg | 84479 | F2 Raw+Validated | 8479814 | `..XXX++` | 42.9% |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | Florence-2 Raw | 8288188 | `.XX..++` | 42.9% |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | Florence-2 Crop | 8008180 | `.X...++` | 57.1% |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | Florence-2 Bbox Crop | 8008154 | `.X...++` | 57.1% |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | F2 Bbox+SuperRes | 8000815 | `.X.XX++` | 57.1% |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg | 88081 | F2 Raw+Validated | 8288188 | `.XX..++` | 42.9% |

## Character Confusions (VLM)

No character-level confusions detected (lengths may differ).

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val | Ensemble | Ens V2 |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|---------|------------|------------|----------|--------|
| 20250316051248_jpg.rf.4aeecc54ae1dc3a5e2d8d8351afe420f.jpg |  | SSE13 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - | - |
| 20250318042301_jpg.rf.1335820152ec89087f830ef770acb4b0.jpg |  | 8028 | - | - | - | - | - | - | - | - | 42.9% | 57.1% | 60.0% | 80.0% | 42.9% | - | - |
| 20250319093914_jpg.rf.dc0ba7a65da808c4637460664da0f659.jpg |  | 60549 | - | - | - | - | - | - | - | - | 57.1% | 71.4% | 71.4% | 71.4% | 57.1% | - | - |
| 20250320065550_jpg.rf.7284f13303bd5fb4c6af4f555db404c3.jpg |  | X0E19 | - | - | - | - | - | - | - | - | 0.0% | 14.3% | - | - | 0.0% | - | - |
| 202503290307049445_jpg.rf.53c20a8b2443dfe033db7c768beae4db.jpg |  | 60008 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | - | - | 28.6% | - | - |
| 202503290412492969_jpg.rf.08f3d182eafd2114fdeb3ff60ac9cfda.jpg |  | 81052 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | 71.4% | 71.4% | 71.4% | - | - |
| 202503290940284673_jpg.rf.611295fa25993fde06e85e20e688bd0f.jpg |  | 5257 | - | - | - | - | - | - | - | - | 28.6% | 42.9% | 42.9% | 42.9% | 28.6% | - | - |
| 202503291037550517_jpg.rf.c931be384808c5cb78f5473c7913d05f.jpg |  | 51245 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | 57.1% | 57.1% | 42.9% | - | - |
| 202503292130419271_jpg.rf.f88f7ebd5bc21bf37a4e4ab90b10ab44.jpg |  | 60148 | - | - | - | - | - | - | - | - | 57.1% | 57.1% | 57.1% | 57.1% | 57.1% | - | - |
| 202503301010426208_jpg.rf.e057373d9618efffed859c79d0322e18.jpg |  | 88798 | - | - | - | - | - | - | - | - | 42.9% | 28.6% | 28.6% | 28.6% | 42.9% | - | - |
| 202503301404576048_jpg.rf.7656e27e83761791753403fb127a97e3.jpg |  | 60008 | - | - | - | - | - | - | - | - | 42.9% | 14.3% | - | - | 42.9% | - | - |
| 202503301805467743_jpg.rf.c0f2844f04e4097ff7ec19a736873f6f.jpg |  | 2333 | - | - | - | - | - | - | - | - | 57.1% | 57.1% | 42.9% | 42.9% | 57.1% | - | - |
| 202503301909102764_jpg.rf.88f0aad9f0fada933fca3bb1cf7f6595.jpg |  | 67468 | - | - | - | - | - | - | - | - | 42.9% | 28.6% | - | - | 42.9% | - | - |
| 202503301909102764_jpg.rf.f861b6e5f8c875f716328c32000dfba5.jpg |  | 67468 | - | - | - | - | - | - | - | - | 42.9% | 28.6% | - | - | 42.9% | - | - |
| 202503302318206024_jpg.rf.bfa3e95c0a5efebec7d1d8e1340027d0.jpg |  | 60088 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | - | - | 42.9% | - | - |
| 202504010810261480_jpg.rf.048e9919ed0494dee86f151f3e08f482.jpg |  | 30551 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | - | - | 28.6% | - | - |
| 202504011049280601_jpg.rf.52fb6672fd8a308513c1a0b9263ef397.jpg |  | 87467 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | - | - | 42.9% | - | - |
| screenshot_2025-04-02_08-13-42_jpg.rf.7fbeb69058f16e508b8b639c6e6d0eb2.jpg |  | 61482 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | 71.4% | 71.4% | 71.4% | - | - |
| screenshot_2025-04-02_14-19-39_jpg.rf.8ed2e1f914f5dc521be1b38cb67aed02.jpg |  | 60008 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | - | - | 28.6% | - | - |
| screenshot_2025-04-03_19-07-27_jpg.rf.a4fb1ae2213e38619a6b749fd37c49b0.jpg |  | 00092 | - | - | - | - | - | - | - | - | 14.3% | 28.6% | - | - | 14.3% | - | - |
| screenshot_2025-04-03_19-47-30_jpg.rf.0d35c792f6116c556a04f731563dd4f9.jpg |  | 50619 | - | - | - | - | - | - | - | - | 0.0% | 14.3% | 0.0% | 0.0% | 0.0% | - | - |
| screenshot_2025-04-03_19-47-30_jpg.rf.5deee694ccec3c0c25296751f59c5392.jpg |  | 23710 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - | - |
| screenshot_2025-04-04_04-20-54_jpg.rf.373639a2bd9ac6adc97a256a7999f4e6.jpg |  | 080012 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | - | - | 28.6% | - | - |
| screenshot_2025-04-04_09-24-59_jpg.rf.d91f4aa6c4c35fe332cf51605e58cce6.jpg |  | 81447 | - | - | - | - | - | - | - | - | 57.1% | 57.1% | 57.1% | 57.1% | 57.1% | - | - |
| screenshot_2025-04-04_11-14-50_jpg.rf.8d978bf62b084638d4ed71e5df620c0d.jpg |  | 61344 | - | - | - | - | - | - | - | - | 42.9% | 71.4% | 71.4% | 71.4% | 42.9% | - | - |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg |  | 67652 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | - | - | 42.9% | - | - |
| screenshot_2025-04-05_02-38-46_jpg.rf.9888e37606dacdc2b1f49443c1c377bf.jpg |  | 61480 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | 57.1% | 57.1% | 42.9% | - | - |
| screenshot_2025-04-05_17-14-02_jpg.rf.956b217f09a486b73c8cf6059018b2ed.jpg |  | 60448 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | 57.1% | 57.1% | 42.9% | - | - |
| screenshot_2025-04-06_10-02-33_jpg.rf.e607e2aebca50504d24b905b7f48b098.jpg |  | 84479 | - | - | - | - | - | - | - | - | 42.9% | 57.1% | - | - | 42.9% | - | - |
| screenshot_2025-04-06_14-43-26_jpg.rf.58b5f4c96538f18c5b4b296d6ffd67f3.jpg |  | 88081 | - | - | - | - | - | - | - | - | 42.9% | 57.1% | 57.1% | 57.1% | 42.9% | - | - |

---
*Generated by `scripts/benchmark.py`.*