# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-25 00:41 UTC  
**Images evaluated:** 20  
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
| Florence-2 Raw | 13.7% | 0.0% | 580ms |
| Florence-2 Crop | 5.8% | 0.0% | 105ms |
| Florence-2 Bbox Crop | 19.4% | 0.0% | 80ms |
| F2 Bbox+SuperRes | 21.8% | 0.0% | 81ms |
| F2 Raw+Validated | 25.2% | 0.0% | - |
| EasyOCR | - | - | - |
| TrOCR | - | - | - |
| docTR | - | - | - |
| Ensemble | - | - | - |
| Ensemble V2 | - | - | - |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |
|-------|---------|------------------|---------|-----------------|--------|---------|---------|------------|------------|
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | - | - | - | - (0%) | - (0%) | 88383 (20%) | 88383 (20%) | 8861461 (14%) |
| image_24.png | 185903 | - | - | - | - (0%) | - (0%) | - | - | - (0%) |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | - | - | - | 5383538 (14%) | 614555 (17%) | 84383 (33%) | 84383 (33%) | 5383538 (14%) |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | 6000383 (71%) |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | - | - | - | - (0%) | - (0%) | 24383 (0%) | 24383 (0%) | 8243833 (0%) |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | 383383 (17%) |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | - | - | - | 8394813 (43%) | 1394819 (43%) | - (0%) | - (0%) | 8394813 (43%) |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | - | - | - | 8383383 (29%) | - (0%) | 6000383 (29%) | 6000383 (29%) | 8383383 (29%) |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | - | - | - | 383383 (17%) | - (0%) | - (0%) | 383383 (17%) | 383383 (17%) |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | - | - | - | - (0%) | - (0%) | 82383 (20%) | 82383 (20%) | 8423833 (14%) |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | - | - | - | - (0%) | - (0%) | 6000383 (29%) | 6000383 (29%) | 8283833 (14%) |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | - | - | - | 3833833 (14%) | - (0%) | 849383 (17%) | 849383 (17%) | 3833833 (14%) |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | - | - | - | 8676587 (29%) | 8765676 (14%) | 86555 (40%) | 86555 (40%) | 8676587 (29%) |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | - | - | - | - (0%) | - (0%) | 6000383 (71%) | 6000383 (71%) | 6000383 (71%) |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | - | - | - | 8135835 (71%) | - (0%) | 15383 (40%) | 15383 (40%) | 8135835 (71%) |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | - | - | - | 6145383 (29%) | - (0%) | 814383 (17%) | 814383 (17%) | 6145383 (29%) |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | - | - | - | 3833833 (29%) | 8948945 (43%) | 894383 (33%) | 84383 (40%) | 3833833 (29%) |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | - | - | - | - (0%) | - (0%) | - (0%) | 11383 (20%) | 8113833 (29%) |
| image_26.png | 186241 | - | - | - | - (0%) | - (0%) | - | - | 24383 (0%) |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Bbox Crop | 88383 | `.XXXX` | 20.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | F2 Bbox+SuperRes | 88383 | `.XXXX` | 20.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | F2 Raw+Validated | 8861461 | `.XXXX++` | 14.3% |
| image_24.png | 185903 | Florence-2 Raw | - | `------` | 0.0% |
| image_24.png | 185903 | Florence-2 Crop | - | `------` | 0.0% |
| image_24.png | 185903 | F2 Raw+Validated | - | `------` | 0.0% |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | Florence-2 Raw | 5383538 | `XXXXXX+` | 14.3% |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | Florence-2 Crop | 614555 | `XX.XXX` | 16.7% |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | Florence-2 Bbox Crop | 84383 | `XXXXX-` | 33.3% |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | F2 Bbox+SuperRes | 84383 | `XXXXX-` | 33.3% |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg | 184767 | F2 Raw+Validated | 5383538 | `XXXXXX+` | 14.3% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | F2 Raw+Validated | 6000383 | `....X++` | 71.4% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Raw | - | `------` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Crop | - | `------` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Bbox Crop | 24383 | `XXXXX-` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | F2 Bbox+SuperRes | 24383 | `XXXXX-` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | F2 Raw+Validated | 8243833 | `XXXXXX+` | 0.0% |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | Florence-2 Raw | - | `------` | 0.0% |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | Florence-2 Crop | - | `------` | 0.0% |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | Florence-2 Bbox Crop | - | `------` | 0.0% |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | F2 Bbox+SuperRes | - | `------` | 0.0% |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg | 184767 | F2 Raw+Validated | 383383 | `X.XXXX` | 16.7% |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | Florence-2 Raw | 8394813 | `.XXXX++` | 42.9% |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | Florence-2 Crop | 1394819 | `XXXXX++` | 42.9% |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg | 81394 | F2 Raw+Validated | 8394813 | `.XXXX++` | 42.9% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Raw | 8383383 | `.XXXX++` | 28.6% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Bbox Crop | 6000383 | `X.XXX++` | 28.6% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | F2 Bbox+SuperRes | 6000383 | `X.XXX++` | 28.6% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | F2 Raw+Validated | 8383383 | `.XXXX++` | 28.6% |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | Florence-2 Raw | 383383 | `XX.XX+` | 16.7% |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | Florence-2 Crop | - | `-----` | 0.0% |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | F2 Bbox+SuperRes | 383383 | `XX.XX+` | 16.7% |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg | 61394 | F2 Raw+Validated | 383383 | `XX.XX+` | 16.7% |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | Florence-2 Bbox Crop | 82383 | `XXXX.` | 20.0% |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | F2 Bbox+SuperRes | 82383 | `XXXX.` | 20.0% |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg | 69003 | F2 Raw+Validated | 8423833 | `XXXXX++` | 14.3% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Bbox Crop | 6000383 | `XXX.X++` | 28.6% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | F2 Bbox+SuperRes | 6000383 | `XXX.X++` | 28.6% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | F2 Raw+Validated | 8283833 | `.XXXX++` | 14.3% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Raw | 3833833 | `XXXX.++` | 14.3% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Bbox Crop | 849383 | `XXXX.+` | 16.7% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | F2 Bbox+SuperRes | 849383 | `XXXX.+` | 16.7% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | F2 Raw+Validated | 3833833 | `XXXX.++` | 14.3% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Raw | 8676587 | `.XXX.++` | 28.6% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Crop | 8765676 | `.XXXX++` | 14.3% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Bbox Crop | 86555 | `.XXX.` | 40.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | F2 Bbox+SuperRes | 86555 | `.XXX.` | 40.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | F2 Raw+Validated | 8676587 | `.XXX.++` | 28.6% |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | Florence-2 Bbox Crop | 6000383 | `....X++` | 71.4% |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | F2 Bbox+SuperRes | 6000383 | `....X++` | 71.4% |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg | 60008 | F2 Raw+Validated | 6000383 | `....X++` | 71.4% |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | Florence-2 Raw | 8135835 | `...XX++` | 71.4% |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | Florence-2 Crop | - | `-----` | 0.0% |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | Florence-2 Bbox Crop | 15383 | `XX..X` | 40.0% |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | F2 Bbox+SuperRes | 15383 | `XX..X` | 40.0% |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg | 81385 | F2 Raw+Validated | 8135835 | `...XX++` | 71.4% |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | Florence-2 Raw | 6145383 | `.XXXX++` | 28.6% |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | Florence-2 Bbox Crop | 814383 | `XXXX.+` | 16.7% |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | F2 Bbox+SuperRes | 814383 | `XXXX.+` | 16.7% |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg | 60008 | F2 Raw+Validated | 6145383 | `.XXXX++` | 28.6% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Raw | 3833833 | `XX.XX++` | 28.6% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Crop | 8948945 | `.XXXX++` | 42.9% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Bbox Crop | 894383 | `.XXXX+` | 33.3% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | F2 Bbox+SuperRes | 84383 | `.X.XX` | 40.0% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | F2 Raw+Validated | 3833833 | `XX.XX++` | 28.6% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | F2 Bbox+SuperRes | 11383 | `XXXX.` | 20.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | F2 Raw+Validated | 8113833 | `.XXXX++` | 28.6% |
| image_26.png | 186241 | Florence-2 Raw | - | `------` | 0.0% |
| image_26.png | 186241 | Florence-2 Crop | - | `------` | 0.0% |
| image_26.png | 186241 | F2 Raw+Validated | 24383 | `XXXXX-` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | F2 Raw+Validated | - | `-----` | 0.0% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 1 | 8 | 4 |
| 5 | 1 | 4 |
| 8 | 6 | 3 |
| 3 | 0 | 3 |
| 8 | 0 | 3 |
| 5 | 7 | 2 |
| 8 | 4 | 2 |
| 3 | 2 | 2 |
| 8 | 3 | 2 |
| 3 | 9 | 2 |
| 2 | 9 | 2 |
| 6 | 8 | 2 |
| 5 | 0 | 2 |
| 3 | 5 | 2 |
| 3 | 4 | 2 |
| 3 | 7 | 2 |
| 6 | 1 | 1 |
| 5 | 6 | 1 |
| 4 | 1 | 1 |
| 8 | 9 | 1 |
| 1 | 5 | 1 |
| 3 | 1 | 1 |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val | Ensemble | Ens V2 |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|---------|------------|------------|----------|--------|
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg |  | 84239 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 20.0% | 20.0% | 14.3% | - | - |
| image_24.png | hard | 185903 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - | - |
| 20250320031700_jpg.rf.8e8da034e3217c6baee4d5b301bab340.jpg |  | 184767 | - | - | - | - | - | - | - | - | 14.3% | 16.7% | 33.3% | 33.3% | 14.3% | - | - |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg |  | 60008 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 71.4% | - | - |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg |  | 197604 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| 20250319091538_jpg.rf.f48d568ce70197d91355e0b74d75757b.jpg |  | 184767 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 16.7% | - | - |
| 202503300259020792_jpg.rf.8c73d48e712f8dda10ddcbf3087d9afd.jpg |  | 81394 | - | - | - | - | - | - | - | - | 42.9% | 42.9% | 0.0% | 0.0% | 42.9% | - | - |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg |  | 80396 | - | - | - | - | - | - | - | - | 28.6% | 0.0% | 28.6% | 28.6% | 28.6% | - | - |
| 202504010711224772_jpg.rf.cc8d64cbe026ac9afd11ca5654f649d5.jpg |  | 61394 | - | - | - | - | - | - | - | - | 16.7% | 0.0% | 0.0% | 16.7% | 16.7% | - | - |
| 20250320174342_jpg.rf.bf669548ba4ef53e8b84094db2495686.jpg |  | 69003 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 20.0% | 20.0% | 14.3% | - | - |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg |  | 86200 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 28.6% | 28.6% | 14.3% | - | - |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg |  | 05118 | - | - | - | - | - | - | - | - | 14.3% | 0.0% | 16.7% | 16.7% | 14.3% | - | - |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg |  | 88105 | - | - | - | - | - | - | - | - | 28.6% | 14.3% | 40.0% | 40.0% | 28.6% | - | - |
| 20250321233109_jpg.rf.e9490a0e6a2af327361c21fbf384d906.jpg |  | 60008 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 71.4% | 71.4% | 71.4% | - | - |
| 202503292015068923_jpg.rf.a7c90b38e9b24f454ae129419dc52d4a.jpg |  | 81385 | - | - | - | - | - | - | - | - | 71.4% | 0.0% | 40.0% | 40.0% | 71.4% | - | - |
| 202503311848550698_jpg.rf.225f4ab41090aa37f7514f217dd18fea.jpg |  | 60008 | - | - | - | - | - | - | - | - | 28.6% | 0.0% | 16.7% | 16.7% | 28.6% | - | - |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg |  | 81394 | - | - | - | - | - | - | - | - | 28.6% | 42.9% | 33.3% | 40.0% | 28.6% | - | - |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg |  | 85003 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 20.0% | 28.6% | - | - |
| image_26.png | extreme | 186241 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - | - |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg |  | 73018 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |

---
*Generated by `scripts/benchmark.py`.*