# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-24 02:13 UTC  
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
| PaddleOCR Raw | 1.9% | 0.0% | 9500ms |
| PaddleOCR + CLAHE | 4.3% | 0.0% | 9158ms |
| ROI + CLAHE | 3.1% | 0.0% | 5416ms |
| CLAHE + Correction | 6.4% | 0.0% | - |
| Bbox Crop + CLAHE | 15.0% | 0.0% | 1002ms |
| VLM Fallback | 48.0% | 17.9% | 2940ms |
| VLM Preprocessed | 46.8% | 16.7% | 2517ms |
| VLM Raw | 54.7% | 13.3% | 2755ms |
| VLM Center Crop | 57.4% | 16.7% | 2627ms |
| Florence-2 Raw | - | - | - |
| Florence-2 Crop | - | - | - |
| EasyOCR | 0.0% | 0.0% | - |
| TrOCR | - | - | - |
| docTR | - | - | - |
| Ensemble | 54.3% | 13.3% | 8183ms |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop |
|-------|---------|------------------|---------|-----------------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | 14 (0%) | 68227 (60%) | 60276 (80%) |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | 60524 (80%) | 60521 (60%) | 60521 (60%) |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | 60041 (60%) | 60041 (60%) | 60841 (60%) |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | 30837 (60%) | 82887 (60%) | 82037 (60%) |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | 60034 (60%) | 80824 (80%) | 80824 (80%) |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | 0C300 (40%) | 82E80 (40%) | 8E603 (40%) |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | 60008 (100%) | 67100 (40%) | 60008 (100%) |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg | M162 | 60008 (0%) | 60008 (0%) | 60008 (0%) |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | 60008 (20%) | 36224 (40%) | 30224 (60%) |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | 60008 (0%) | 60008 (0%) | 82437 (60%) |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | 60008 (100%) | 60008 (100%) | 06200 (40%) |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | 60745 (80%) | 087145 (50%) | 02745 (40%) |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | 60075 (60%) | 609175 (33%) | 060175 (33%) |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | 60008 (0%) | 60CT0 (0%) | 82G7A (20%) |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | 18916 (0%) | K2816 (0%) | K28176 (0%) |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | 87398 (40%) | 81308 (80%) | 815908 (50%) |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | 60008 (100%) | 60008 (100%) | 30008 (80%) |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | 60008 (100%) | 60005 (80%) | 60008 (100%) |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg | M7PU | N5670 (0%) | M7030 (40%) | AS1738 (17%) |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | 60008 (20%) | 61374 (100%) | 61374 (100%) |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | 21414 (80%) | 67414 (80%) | 61414 (100%) |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | 21414 (0%) | 67444 (20%) | 61414 (20%) |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | 60008 (17%) | D87042 (33%) | 087022 (50%) |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | X857 (20%) | 80551 (80%) | 80557 (60%) |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | 60008 (100%) | C2025 (20%) | 00008 (80%) |
| image_22.png | 192435 | 18248 (50%) | 192435 (100%) | 192435 (100%) |
| image_23.png | 187612 | 18612 (83%) | 187812 (83%) | 187812 (83%) |
| image_24.png | 185903 | 60008 (17%) | 18590 (83%) | 185935 (67%) |
| image_25.png | 191078 | 910789 (67%) | 18167 (50%) | 60008 (33%) |
| image_26.png | 186241 | 189311 (50%) | 19621 (67%) | 18?2? (50%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | VLM Preprocessed | 14 | `XX---` | 0.0% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | VLM Raw | 68227 | `.X..X` | 60.0% |
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg | 60226 | VLM Center Crop | 60276 | `...X.` | 80.0% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | VLM Preprocessed | 60524 | `.X...` | 80.0% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | VLM Raw | 60521 | `.X..X` | 60.0% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg | 66524 | VLM Center Crop | 60521 | `.X..X` | 60.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | VLM Preprocessed | 60041 | `XX...` | 60.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | VLM Raw | 60041 | `XX...` | 60.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 86041 | VLM Center Crop | 60841 | `XXX..` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Preprocessed | 30837 | `XX...` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Raw | 82887 | `.X.X.` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Center Crop | 82037 | `.XX..` | 60.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Preprocessed | 60034 | `..XX.` | 60.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Raw | 80824 | `X....` | 80.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Center Crop | 80824 | `X....` | 80.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | VLM Preprocessed | 0C300 | `XXX..` | 40.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | VLM Raw | 82E80 | `.XXX.` | 40.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg | 86200 | VLM Center Crop | 8E603 | `.XX.X` | 40.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | VLM Raw | 67100 | `.XX.X` | 40.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg | M162 | VLM Preprocessed | 60008 | `XXXX+` | 0.0% |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg | M162 | VLM Raw | 60008 | `XXXX+` | 0.0% |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg | M162 | VLM Center Crop | 60008 | `XXXX+` | 0.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | VLM Preprocessed | 60008 | `X.XXX` | 20.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | VLM Raw | 36224 | `XX..X` | 40.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg | 70227 | VLM Center Crop | 30224 | `X...X` | 60.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | VLM Raw | 60008 | `XXXXX` | 0.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg | 82371 | VLM Center Crop | 82437 | `..XXX` | 60.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg | 60008 | VLM Center Crop | 06200 | `XXX.X` | 40.0% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | VLM Preprocessed | 60745 | `..X..` | 80.0% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | VLM Raw | 087145 | `XXXXX+` | 50.0% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg | 60145 | VLM Center Crop | 02745 | `XXX..` | 40.0% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | VLM Preprocessed | 60075 | `...XX` | 60.0% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | VLM Raw | 609175 | `..XXX+` | 33.3% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg | 60008 | VLM Center Crop | 060175 | `XX.XX+` | 33.3% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Raw | 60CT0 | `XXXXX` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Center Crop | 82G7A | `.XXXX` | 20.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | VLM Preprocessed | 18916 | `XXXXX` | 0.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | VLM Raw | K2816 | `XXXXX` | 0.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg | 60008 | VLM Center Crop | K28176 | `XXXXX+` | 0.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Preprocessed | 87398 | `XX.X.` | 40.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Raw | 81308 | `X....` | 80.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Center Crop | 815908 | `X.XXX+` | 50.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg | 60008 | VLM Center Crop | 30008 | `X....` | 80.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Raw | 60005 | `....X` | 80.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg | M7PU | VLM Preprocessed | N5670 | `XXXX+` | 0.0% |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg | M7PU | VLM Raw | M7030 | `..XX+` | 40.0% |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg | M7PU | VLM Center Crop | AS1738 | `XXXX++` | 16.7% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Preprocessed | 60008 | `.XXXX` | 20.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Raw | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Center Crop | 61374 | `.....` | 100.0% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | VLM Preprocessed | 21414 | `X....` | 80.0% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | VLM Raw | 67414 | `.X...` | 80.0% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg | 61414 | VLM Center Crop | 61414 | `.....` | 100.0% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | VLM Preprocessed | 21414 | `XXXXX` | 0.0% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | VLM Raw | 67444 | `.XXXX` | 20.0% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg | 60008 | VLM Center Crop | 61414 | `.XXXX` | 20.0% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | VLM Preprocessed | 60008 | `XXXXX-` | 16.7% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | VLM Raw | D87042 | `XX.XX.` | 33.3% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg | 167122 | VLM Center Crop | 087022 | `XX.X..` | 50.0% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | VLM Preprocessed | X857 | `XX.X-` | 20.0% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | VLM Raw | 80551 | `.X...` | 80.0% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg | 82551 | VLM Center Crop | 80557 | `.X..X` | 60.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | VLM Raw | C2025 | `XX.XX` | 20.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg | 60008 | VLM Center Crop | 00008 | `X....` | 80.0% |
| image_22.png | 192435 | VLM Preprocessed | 18248 | `.X..X-` | 50.0% |
| image_22.png | 192435 | VLM Raw | 192435 | `......` | 100.0% |
| image_22.png | 192435 | VLM Center Crop | 192435 | `......` | 100.0% |
| image_23.png | 187612 | VLM Preprocessed | 18612 | `..XXX-` | 83.3% |
| image_23.png | 187612 | VLM Raw | 187812 | `...X..` | 83.3% |
| image_23.png | 187612 | VLM Center Crop | 187812 | `...X..` | 83.3% |
| image_24.png | 185903 | VLM Preprocessed | 60008 | `XXXXX-` | 16.7% |
| image_24.png | 185903 | VLM Raw | 18590 | `.....-` | 83.3% |
| image_24.png | 185903 | VLM Center Crop | 185935 | `....XX` | 66.7% |
| image_25.png | 191078 | VLM Preprocessed | 910789 | `XXXXXX` | 66.7% |
| image_25.png | 191078 | VLM Raw | 18167 | `.X.X.-` | 50.0% |
| image_25.png | 191078 | VLM Center Crop | 60008 | `XXX.X-` | 33.3% |
| image_26.png | 186241 | VLM Preprocessed | 189311 | `..XXX.` | 50.0% |
| image_26.png | 186241 | VLM Raw | 19621 | `.X..X-` | 66.7% |
| image_26.png | 186241 | VLM Center Crop | 18?2? | `..X.X-` | 50.0% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 0 | 6 | 10 |
| 6 | 8 | 9 |
| 0 | 1 | 8 |
| 8 | 6 | 8 |
| 0 | 2 | 7 |
| 1 | 0 | 7 |
| 0 | 8 | 6 |
| 7 | 1 | 6 |
| 8 | 0 | 5 |
| 2 | 6 | 5 |
| 2 | 0 | 5 |
| 7 | 0 | 4 |
| 4 | 0 | 4 |
| 3 | 2 | 3 |
| 0 | 3 | 3 |
| 0 | 7 | 3 |
| 8 | 1 | 3 |
| 5 | 8 | 3 |
| 4 | 8 | 3 |
| 1 | 4 | 3 |
| 3 | 7 | 3 |
| C | 6 | 2 |
| 8 | 7 | 2 |
| 9 | 0 | 2 |
| 6 | 0 | 2 |
| 4 | 7 | 2 |
| 7 | 2 | 2 |
| 3 | 0 | 2 |
| 3 | 8 | 1 |
| 6 | 7 | 1 |
| 1 | 6 | 1 |
| 8 | 4 | 1 |
| 9 | 1 | 1 |
| 1 | 9 | 1 |
| 9 | 8 | 1 |
| 9 | 6 | 1 |
| 7 | 6 | 1 |
| 8 | 3 | 1 |
| E | 2 | 1 |
| C | 8 | 1 |
| T | 2 | 1 |
| K | 6 | 1 |
| D | 1 | 1 |
| 4 | 2 | 1 |
| E | 6 | 1 |
| 6 | 2 | 1 |
| 4 | 3 | 1 |
| 2 | 1 | 1 |
| G | 8 | 1 |
| A | 1 | 1 |
| 3 | 6 | 1 |
| 5 | 3 | 1 |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | Ensemble |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|----------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg |  | 60226 | 8.9% | 8.9% | 0.0% | 8.9% | - | 0.0% | 60.0% | 80.0% | 60.0% |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg |  | 66524 | 0.0% | 0.0% | 16.0% | 20.0% | 80.0% | 80.0% | 60.0% | 60.0% | 16.0% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg |  | 86041 | 0.0% | 0.0% | 9.3% | 0.0% | - | 60.0% | 60.0% | 60.0% | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg |  | 86837 | 0.0% | 12.5% | 20.0% | 12.8% | 60.0% | 60.0% | 60.0% | 60.0% | 60.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg |  | 60824 | 0.0% | 0.0% | 0.0% | 0.0% | 60.0% | 60.0% | 80.0% | 80.0% | 80.0% |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg |  | 86200 | 4.8% | 6.8% | 0.0% | 6.8% | 40.0% | 40.0% | 40.0% | 40.0% | 40.0% |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg |  | 60008 | 11.1% | 14.3% | 12.5% | 14.8% | 100.0% | 100.0% | 40.0% | 100.0% | 60.0% |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg |  | M162 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg |  | 70227 | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 20.0% | 40.0% | 60.0% | 40.0% |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg |  | 82371 | 7.1% | 15.0% | 0.0% | 15.0% | 0.0% | 0.0% | 0.0% | 60.0% | 0.0% |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 100.0% | 40.0% | 100.0% |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg |  | 60145 | 0.0% | 0.0% | 0.0% | 0.0% | 80.0% | 80.0% | 50.0% | 40.0% | 50.0% |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg |  | 60008 | 9.1% | 16.0% | 3.6% | 16.0% | 60.0% | 60.0% | 33.3% | 33.3% | 33.3% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg |  | 81821 | 0.0% | 0.0% | 10.5% | 12.5% | 0.0% | 0.0% | 0.0% | 20.0% | 0.0% |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg |  | 60008 | 0.0% | 2.0% | 2.4% | 2.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg |  | 61308 | 0.0% | 0.0% | 0.0% | 20.0% | 40.0% | 40.0% | 80.0% | 50.0% | 60.0% |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg |  | 60008 | 0.0% | 28.6% | 0.0% | 28.6% | 100.0% | 100.0% | 100.0% | 80.0% | 100.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 80.0% | 100.0% | 80.0% |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg |  | M7PU | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 40.0% | 16.7% | 40.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg |  | 61374 | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 20.0% | 100.0% | 100.0% | 100.0% |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg |  | 61414 | 0.0% | 0.0% | 0.0% | 0.0% | 80.0% | 80.0% | 80.0% | 100.0% | 80.0% |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 20.0% | 20.0% |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg |  | 167122 | 0.0% | 9.4% | 0.0% | 9.8% | 16.7% | 16.7% | 33.3% | 50.0% | 66.7% |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg |  | 82551 | 0.0% | 16.0% | 20.0% | 16.0% | 20.0% | 20.0% | 80.0% | 60.0% | 80.0% |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% | 20.0% | 80.0% | 20.0% |
| image_22.png | easy | 192435 | 16.7% | 0.0% | 0.0% | 10.0% | 50.0% | 50.0% | 100.0% | 100.0% | 100.0% |
| image_23.png | medium | 187612 | 0.0% | 0.0% | 0.0% | 0.0% | 83.3% | 83.3% | 83.3% | 83.3% | 83.3% |
| image_24.png | hard | 185903 | 0.0% | 0.0% | 0.0% | 0.0% | 16.7% | 16.7% | 83.3% | 66.7% | 83.3% |
| image_25.png | very_hard | 191078 | 0.0% | 0.0% | 0.0% | 0.0% | 66.7% | 66.7% | 50.0% | 33.3% | 50.0% |
| image_26.png | extreme | 186241 | 0.0% | 0.0% | 0.0% | 0.0% | 50.0% | 50.0% | 66.7% | 50.0% | 66.7% |

## Errors

- **20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **image_22.png**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **image_23.png**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **image_24.png**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **image_25.png**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>
- **image_26.png**: EasyOCR error: 'charmap' codec can't encode character '\u2588' in position 12: character maps to <undefined>

---
*Generated by `scripts/benchmark.py`.*