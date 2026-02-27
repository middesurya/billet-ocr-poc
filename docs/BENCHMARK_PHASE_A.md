# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-24 22:41 UTC  
**Images evaluated:** 32  
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
| PaddleOCR Raw | 1.8% | 0.0% | 22440ms |
| PaddleOCR + CLAHE | 4.5% | 0.0% | 22545ms |
| ROI + CLAHE | 3.6% | 0.0% | 12809ms |
| CLAHE + Correction | 6.5% | 0.0% | - |
| Bbox Crop + CLAHE | 10.3% | 0.0% | 1628ms |
| VLM Fallback | - | - | - |
| VLM Preprocessed | - | - | - |
| VLM Raw | - | - | - |
| VLM Center Crop | - | - | - |
| Florence-2 Raw | 30.8% | 0.0% | 1446ms |
| Florence-2 Crop | 31.6% | 3.1% | 303ms |
| Florence-2 Bbox Crop | 21.9% | 3.7% | 131ms |
| F2 Bbox+SuperRes | 21.9% | 3.7% | 133ms |
| F2 Raw+Validated | 30.8% | 0.0% | - |
| EasyOCR | - | - | - |
| TrOCR | - | - | - |
| docTR | - | - | - |
| Ensemble | - | - | - |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |
|-------|---------|------------------|---------|-----------------|--------|---------|---------|------------|------------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | - | - | - | 6827168 (43%) | 6027653 (57%) | 2576555 (0%) | 2276555 (14%) | 6827168 (43%) |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | - | - | - | 6521652 (43%) | 6521652 (43%) | 6052153 (43%) | 6521538 (29%) | 6521652 (43%) |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | - | - | - | 6864168 (43%) | 6864186 (43%) | 66641 (60%) | 66641 (60%) | 6864168 (43%) |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | - | - | - | 8868786 (43%) | 8268753 (43%) | 8866753 (29%) | 8866753 (29%) | 8868786 (43%) |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | - | - | - | 8862488 (29%) | 8062480 (43%) | 8062452 (43%) | 8682453 (43%) | 8862488 (29%) |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | - | - | - | 8688888 (29%) | - (0%) | 888888 (17%) | 888888 (17%) | 8688888 (29%) |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | - | - | - | 8622186 (29%) | 8822188 (29%) | - (0%) | - (0%) | 8622186 (29%) |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | - | - | - | 8686788 (29%) | 6867686 (14%) | - (0%) | - (0%) | 8686788 (29%) |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | - | - | - | 8014580 (57%) | 5607456 (57%) | 6074554 (57%) | 6074554 (57%) | 8014580 (57%) |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | - | - | - | 8875887 (14%) | 8097568 (29%) | - (0%) | - (0%) | 8875887 (14%) |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | - | - | - | 9868678 (29%) | 8457084 (14%) | - (0%) | - (0%) | 9868678 (29%) |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | - | - | - | 1616181 (29%) | 1848181 (14%) | - (0%) | - (0%) | 1616181 (29%) |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | - | - | - | 8139861 (43%) | 8139861 (43%) | 8139853 (43%) | 8139853 (43%) | 8139861 (43%) |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | - | - | - | 8896889 (14%) | 8096809 (29%) | 5896556 (0%) | - (0%) | 8896889 (14%) |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | - | - | - | 6895689 (29%) | 6885688 (29%) | - (0%) | - (0%) | 6895689 (29%) |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | - | - | - | 6137461 (71%) | 6746137 (43%) | 61374 (100%) | 61374 (100%) | 6137461 (71%) |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | - | - | - | 6144641 (57%) | 6414674 (57%) | 6141458 (71%) | 6141456 (71%) | 6144641 (57%) |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | - | - | - | 6144641 (14%) | 6414641 (14%) | 6141458 (29%) | 6141458 (29%) | 6144641 (14%) |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | - | - | - | 6810268 (29%) | 8702871 (14%) | - (0%) | - (0%) | 6810268 (29%) |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | - | - | - | 8855788 (43%) | 8055708 (43%) | 6055553 (29%) | 6055553 (29%) | 8855788 (43%) |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | - | - | - | 8688368 (29%) | 6068636 (29%) | - (0%) | - (0%) | 8688368 (29%) |
| image_22.png | 192435 | - | - | - | 1924319 (71%) | 1924351 (86%) | - | - | 1924319 (71%) |
| image_23.png | 187612 | - | - | - | 7612187 (29%) | 187612 (100%) | - | - | 7612187 (29%) |
| image_24.png | 185903 | - | - | - | 1859912 (57%) | 185902 (83%) | - | - | 1859912 (57%) |
| image_25.png | 191078 | - | - | - | - (0%) | - (0%) | - | - | - (0%) |
| image_26.png | 186241 | - | - | - | - (0%) | - (0%) | - | - | - (0%) |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | - | - | - | 7141871 (14%) | - (0%) | - (0%) | - (0%) | 7141871 (14%) |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | - | - | - | 27373 (0%) | - (0%) | - (0%) | - (0%) | 27373 (0%) |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | - | - | - | 6155661 (29%) | 6155661 (29%) | 6155058 (43%) | 6155058 (43%) | 6155661 (29%) |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | - | - | - | 8640286 (43%) | 6840268 (29%) | 5840253 (29%) | 5840253 (29%) | 8640286 (43%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | Florence-2 Raw | 6827168 | `.X.XX++` | 42.9% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | Florence-2 Crop | 6027653 | `...X.++` | 57.1% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | Florence-2 Bbox Crop | 2576555 | `XXXXX++` | 0.0% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | F2 Bbox+SuperRes | 2276555 | `XXXXX++` | 14.3% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | F2 Raw+Validated | 6827168 | `.X.XX++` | 42.9% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | Florence-2 Raw | 6521652 | `.XXXX++` | 42.9% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | Florence-2 Crop | 6521652 | `.XXXX++` | 42.9% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | Florence-2 Bbox Crop | 6052153 | `.X..X++` | 42.9% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | F2 Bbox+SuperRes | 6521538 | `.XXXX++` | 28.6% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | F2 Raw+Validated | 6521652 | `.XXXX++` | 42.9% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | Florence-2 Raw | 6864168 | `XXX..++` | 42.9% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | Florence-2 Crop | 6864186 | `XXX..++` | 42.9% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | Florence-2 Bbox Crop | 66641 | `X.X..` | 60.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | F2 Bbox+SuperRes | 66641 | `X.X..` | 60.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | F2 Raw+Validated | 6864168 | `XXX..++` | 42.9% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Raw | 8868786 | `.XXX.++` | 42.9% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Crop | 8268753 | `.XXX.++` | 42.9% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Bbox Crop | 8866753 | `.XXX.++` | 28.6% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | F2 Bbox+SuperRes | 8866753 | `.XXX.++` | 28.6% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | F2 Raw+Validated | 8868786 | `.XXX.++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Raw | 8862488 | `XXX..++` | 28.6% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Crop | 8062480 | `X.X..++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Bbox Crop | 8062452 | `X.X..++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | F2 Bbox+SuperRes | 8682453 | `XX...++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | F2 Raw+Validated | 8862488 | `XXX..++` | 28.6% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Raw | 8688888 | `..XXX++` | 28.6% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | Florence-2 Bbox Crop | 888888 | `.XXXX+` | 16.7% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | F2 Bbox+SuperRes | 888888 | `.XXXX+` | 16.7% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | F2 Raw+Validated | 8688888 | `..XXX++` | 28.6% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | F2 Raw+Validated | - | `-----` | 0.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | Florence-2 Raw | 8622186 | `XX..X++` | 28.6% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | Florence-2 Crop | 8822188 | `XX..X++` | 28.6% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | F2 Raw+Validated | 8622186 | `XX..X++` | 28.6% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | Florence-2 Raw | 8686788 | `.XXXX++` | 28.6% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | Florence-2 Crop | 6867686 | `XXX.X++` | 14.3% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | F2 Raw+Validated | 8686788 | `.XXXX++` | 28.6% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | F2 Raw+Validated | - | `-----` | 0.0% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | Florence-2 Raw | 8014580 | `X....++` | 57.1% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | Florence-2 Crop | 5607456 | `XXXXX++` | 57.1% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | Florence-2 Bbox Crop | 6074554 | `..X..++` | 57.1% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | F2 Bbox+SuperRes | 6074554 | `..X..++` | 57.1% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | F2 Raw+Validated | 8014580 | `X....++` | 57.1% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | Florence-2 Raw | 8875887 | `XXXX.++` | 14.3% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | Florence-2 Crop | 8097568 | `X.XXX++` | 28.6% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | F2 Raw+Validated | 8875887 | `XXXX.++` | 14.3% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Raw | 9868678 | `XXXXX++` | 28.6% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Crop | 8457084 | `.XXXX++` | 14.3% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | F2 Raw+Validated | 9868678 | `XXXXX++` | 28.6% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | Florence-2 Raw | 1616181 | `XXXXX++` | 28.6% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | Florence-2 Crop | 1848181 | `XXXXX++` | 14.3% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | F2 Raw+Validated | 1616181 | `XXXXX++` | 28.6% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Raw | 8139861 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Crop | 8139861 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Bbox Crop | 8139853 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | F2 Bbox+SuperRes | 8139853 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | F2 Raw+Validated | 8139861 | `X..X.++` | 42.9% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | Florence-2 Raw | 8896889 | `XXXX.++` | 14.3% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | Florence-2 Crop | 8096809 | `X.XX.++` | 28.6% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | Florence-2 Bbox Crop | 5896556 | `XXXXX++` | 0.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | F2 Raw+Validated | 8896889 | `XXXX.++` | 14.3% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Raw | 6895689 | `.XXXX++` | 28.6% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Crop | 6885688 | `.XXXX++` | 28.6% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | F2 Raw+Validated | 6895689 | `.XXXX++` | 28.6% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Raw | 6137461 | `.....++` | 71.4% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Crop | 6746137 | `.XXXX++` | 42.9% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Bbox Crop | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | F2 Bbox+SuperRes | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | F2 Raw+Validated | 6137461 | `.....++` | 71.4% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | Florence-2 Raw | 6144641 | `...XX++` | 57.1% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | Florence-2 Crop | 6414674 | `.XXXX++` | 57.1% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | Florence-2 Bbox Crop | 6141458 | `.....++` | 71.4% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | F2 Bbox+SuperRes | 6141456 | `.....++` | 71.4% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | F2 Raw+Validated | 6144641 | `...XX++` | 57.1% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | Florence-2 Raw | 6144641 | `.XXXX++` | 14.3% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | Florence-2 Crop | 6414641 | `.XXXX++` | 14.3% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | Florence-2 Bbox Crop | 6141458 | `.XXXX++` | 28.6% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | F2 Bbox+SuperRes | 6141458 | `.XXXX++` | 28.6% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | F2 Raw+Validated | 6144641 | `.XXXX++` | 14.3% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | Florence-2 Raw | 6810268 | `XXXX.X+` | 28.6% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | Florence-2 Crop | 8702871 | `XXXXXX+` | 14.3% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | Florence-2 Bbox Crop | - | `------` | 0.0% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | F2 Bbox+SuperRes | - | `------` | 0.0% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | F2 Raw+Validated | 6810268 | `XXXX.X+` | 28.6% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | Florence-2 Raw | 8855788 | `.X..X++` | 42.9% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | Florence-2 Crop | 8055708 | `.X..X++` | 42.9% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | Florence-2 Bbox Crop | 6055553 | `XX..X++` | 28.6% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | F2 Bbox+SuperRes | 6055553 | `XX..X++` | 28.6% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | F2 Raw+Validated | 8855788 | `.X..X++` | 42.9% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | Florence-2 Raw | 8688368 | `XXXXX++` | 28.6% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | Florence-2 Crop | 6068636 | `..XXX++` | 28.6% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | F2 Raw+Validated | 8688368 | `XXXXX++` | 28.6% |
| image_22.png | 192435 | Florence-2 Raw | 1924319 | `.....X+` | 71.4% |
| image_22.png | 192435 | Florence-2 Crop | 1924351 | `......+` | 85.7% |
| image_22.png | 192435 | F2 Raw+Validated | 1924319 | `.....X+` | 71.4% |
| image_23.png | 187612 | Florence-2 Raw | 7612187 | `XXXX.X+` | 28.6% |
| image_23.png | 187612 | Florence-2 Crop | 187612 | `......` | 100.0% |
| image_23.png | 187612 | F2 Raw+Validated | 7612187 | `XXXX.X+` | 28.6% |
| image_24.png | 185903 | Florence-2 Raw | 1859912 | `....XX+` | 57.1% |
| image_24.png | 185903 | Florence-2 Crop | 185902 | `.....X` | 83.3% |
| image_24.png | 185903 | F2 Raw+Validated | 1859912 | `....XX+` | 57.1% |
| image_25.png | 191078 | Florence-2 Raw | - | `------` | 0.0% |
| image_25.png | 191078 | Florence-2 Crop | - | `------` | 0.0% |
| image_25.png | 191078 | F2 Raw+Validated | - | `------` | 0.0% |
| image_26.png | 186241 | Florence-2 Raw | - | `------` | 0.0% |
| image_26.png | 186241 | Florence-2 Crop | - | `------` | 0.0% |
| image_26.png | 186241 | F2 Raw+Validated | - | `------` | 0.0% |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | Florence-2 Raw | 7141871 | `XXXX.++` | 14.3% |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg | 60008 | F2 Raw+Validated | 7141871 | `XXXX.++` | 14.3% |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | Florence-2 Raw | 27373 | `XXXXX` | 0.0% |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg | 60008 | F2 Raw+Validated | 27373 | `XXXXX` | 0.0% |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | Florence-2 Raw | 6155661 | `XX..X++` | 28.6% |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | Florence-2 Crop | 6155661 | `XX..X++` | 28.6% |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | Florence-2 Bbox Crop | 6155058 | `XX..X++` | 42.9% |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | F2 Bbox+SuperRes | 6155058 | `XX..X++` | 42.9% |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg | 87558 | F2 Raw+Validated | 6155661 | `XX..X++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Raw | 8640286 | `.X.X.++` | 42.9% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Crop | 6840268 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Bbox Crop | 5840253 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | F2 Bbox+SuperRes | 5840253 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | F2 Raw+Validated | 8640286 | `.X.X.++` | 42.9% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 7 | 0 | 4 |
| 2 | 6 | 2 |
| 3 | 0 | 2 |
| 3 | 8 | 2 |
| 6 | 8 | 2 |
| 6 | 0 | 2 |
| 2 | 3 | 1 |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val | Ensemble |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|---------|------------|------------|----------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg |  | 60226 | 8.9% | 8.9% | 0.0% | 8.9% | - | - | - | - | 42.9% | 57.1% | 0.0% | 14.3% | 42.9% | - |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg |  | 66524 | 0.0% | 0.0% | 16.0% | 20.0% | - | - | - | - | 42.9% | 42.9% | 42.9% | 28.6% | 42.9% | - |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg |  | 86041 | 0.0% | 0.0% | 9.3% | 0.0% | - | - | - | - | 42.9% | 42.9% | 60.0% | 60.0% | 42.9% | - |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg |  | 86837 | 0.0% | 12.5% | 20.0% | 12.8% | - | - | - | - | 42.9% | 42.9% | 28.6% | 28.6% | 42.9% | - |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg |  | 60824 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 28.6% | 42.9% | 42.9% | 42.9% | 28.6% | - |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg |  | 86200 | 4.8% | 6.8% | 0.0% | 6.8% | - | - | - | - | 28.6% | 0.0% | 16.7% | 16.7% | 28.6% | - |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg |  | 60008 | 11.1% | 14.3% | 12.5% | 14.8% | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg |  | 70227 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg |  | 82371 | 7.1% | 15.0% | 0.0% | 15.0% | - | - | - | - | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg |  | 60145 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 57.1% | 57.1% | 57.1% | 57.1% | 57.1% | - |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg |  | 60008 | 9.1% | 16.0% | 3.6% | 16.0% | - | - | - | - | 14.3% | 28.6% | 0.0% | 0.0% | 14.3% | - |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg |  | 81821 | 0.0% | 0.0% | 10.5% | 12.5% | - | - | - | - | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg |  | 60008 | 0.0% | 2.0% | 2.4% | 2.0% | - | - | - | - | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg |  | 61308 | 0.0% | 0.0% | 0.0% | 20.0% | - | - | - | - | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% | - |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg |  | 60008 | 0.0% | 28.6% | 0.0% | 28.6% | - | - | - | - | 14.3% | 28.6% | 0.0% | 0.0% | 14.3% | - |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg |  | 61374 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 71.4% | 42.9% | 100.0% | 100.0% | 71.4% | - |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg |  | 61414 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 57.1% | 57.1% | 71.4% | 71.4% | 57.1% | - |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 14.3% | 14.3% | 28.6% | 28.6% | 14.3% | - |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg |  | 167122 | 0.0% | 9.4% | 0.0% | 9.8% | - | - | - | - | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg |  | 82551 | 0.0% | 16.0% | 20.0% | 16.0% | - | - | - | - | 42.9% | 42.9% | 28.6% | 28.6% | 42.9% | - |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - |
| image_22.png | easy | 192435 | 16.7% | 0.0% | 0.0% | 10.0% | - | - | - | - | 71.4% | 85.7% | - | - | 71.4% | - |
| image_23.png | medium | 187612 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 28.6% | 100.0% | - | - | 28.6% | - |
| image_24.png | hard | 185903 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 57.1% | 83.3% | - | - | 57.1% | - |
| image_25.png | very_hard | 191078 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - |
| image_26.png | extreme | 186241 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 0.0% | 0.0% | - | - | 0.0% | - |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg |  | 60008 | 0.0% | 4.8% | 0.0% | 4.8% | - | - | - | - | 14.3% | 0.0% | 0.0% | 0.0% | 14.3% | - |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg |  | 87558 | 0.0% | 8.7% | 0.0% | 8.7% | - | - | - | - | 28.6% | 28.6% | 42.9% | 42.9% | 28.6% | - |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg |  | 82482 | 0.0% | 0.0% | 20.0% | 0.0% | - | - | - | - | 42.9% | 28.6% | 28.6% | 28.6% | 42.9% | - |

---
*Generated by `scripts/benchmark.py`.*