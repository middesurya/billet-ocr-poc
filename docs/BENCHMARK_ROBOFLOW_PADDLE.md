# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-24 01:27 UTC  
**Images evaluated:** 35  
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
| PaddleOCR Raw | 1.4% | 0.0% | 8816ms |
| PaddleOCR + CLAHE | 4.8% | 0.0% | 7802ms |
| ROI + CLAHE | 3.8% | 0.0% | 5426ms |
| CLAHE + Correction | 6.6% | 0.0% | - |
| Bbox Crop + CLAHE | 16.2% | 0.0% | 999ms |
| VLM Fallback | - | - | - |
| VLM Preprocessed | - | - | - |
| VLM Raw | - | - | - |
| VLM Center Crop | - | - | - |
| Florence-2 Raw | - | - | - |
| Florence-2 Crop | - | - | - |
| EasyOCR | - | - | - |
| TrOCR | - | - | - |
| docTR | - | - | - |
| Ensemble | - | - | - |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | Ensemble |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|----------|
| 20250314122512_jpg.rf.d1dc11b738404bf3782db5a7934f0992.jpg |  | 60226 | 8.9% | 8.9% | 0.0% | 8.9% | - | - | - | - | - |
| 20250316144312_jpg.rf.0d90a90447309aa866ed4c2f5cdb2ad8.jpg |  | 66524 | 0.0% | 0.0% | 16.0% | 20.0% | - | - | - | - | - |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg |  | 86041 | 0.0% | 0.0% | 9.3% | 0.0% | - | - | - | - | - |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg |  | 86837 | 0.0% | 12.5% | 20.0% | 12.8% | - | - | - | - | - |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg |  | 60824 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 20250317082939_jpg.rf.53585de9df9bf549d2738fd796cf4624.jpg |  | 86200 | 4.8% | 6.8% | 0.0% | 6.8% | - | - | - | - | - |
| 20250317232807_jpg.rf.8e63e1abcbd5b8037379bd45210eb133.jpg |  | 60008 | 11.1% | 14.3% | 12.5% | 14.8% | - | - | - | - | - |
| 20250318122803_jpg.rf.75d953e1c40b86c448c5ee2dd7d83f3e.jpg |  | M162 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 20250319021642_jpg.rf.c4a7c7118703755e72bec4eab17f1541.jpg |  | 70227 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 20250319095628_jpg.rf.92db986fd409d4c0f1e84eb4969ed4d2.jpg |  | 82371 | 7.1% | 15.0% | 0.0% | 15.0% | - | - | - | - | - |
| 20250320050658_jpg.rf.787ad9a503c0aed193eacf02f8011a64.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 20250321125300_jpg.rf.f8fec1e3531303307c4e7138aaacd4e0.jpg |  | 60145 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503290441220175_jpg.rf.84d2d777cbe0ac6b68cb295f4ac4b167.jpg |  | 60008 | 9.1% | 16.0% | 3.6% | 16.0% | - | - | - | - | - |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg |  | 81821 | 0.0% | 0.0% | 10.5% | 12.5% | - | - | - | - | - |
| 202503292337161741_jpg.rf.d3d287781590a043805d3a2eb49b9376.jpg |  | 60008 | 0.0% | 2.0% | 2.4% | 2.0% | - | - | - | - | - |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg |  | 61308 | 0.0% | 0.0% | 0.0% | 20.0% | - | - | - | - | - |
| 202503301010426208_jpg.rf.f212f5b8d25f6f09be91dd8e098b2e5c.jpg |  | 60008 | 0.0% | 28.6% | 0.0% | 28.6% | - | - | - | - | - |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503301444517644_jpg.rf.28f7b309125bac3153c5f02c518bfef9.jpg |  | M7PU | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg |  | 61374 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503311848550698_jpg.rf.2ba245d291eec4e1efd98fe467309ffd.jpg |  | 61414 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503311848550698_jpg.rf.7333f9f6aabf0a0aa0985672a00deb7a.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| 202503312005360997_jpg.rf.8824ff165872e4af0a10bec475ae2526.jpg |  | 167122 | 0.0% | 9.4% | 0.0% | 9.8% | - | - | - | - | - |
| 202503312136148524_jpg.rf.1948d1e9e0c7e34afff76763f08301ec.jpg |  | 82551 | 0.0% | 16.0% | 20.0% | 16.0% | - | - | - | - | - |
| 202504020444158222_jpg.rf.41bf1d353ffe6bc81e5d94f1bfe96967.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| image_22.png | easy | 192435 | - | - | - | - | - | - | - | - | - |
| image_23.png | medium | 187612 | - | - | - | - | - | - | - | - | - |
| image_24.png | hard | 185903 | - | - | - | - | - | - | - | - | - |
| image_25.png | very_hard | 191078 | - | - | - | - | - | - | - | - | - |
| image_26.png | extreme | 186241 | - | - | - | - | - | - | - | - | - |
| screenshot_2025-04-04_09-24-59_jpg.rf.50141461fbed3b5f88ac20a54fcff749.jpg |  | 60008 | 0.0% | 4.8% | 0.0% | 4.8% | - | - | - | - | - |
| screenshot_2025-04-04_16-16-49_jpg.rf.02fce3b57bb5e5dd99113460ecd0387d.jpg |  | 60008 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| screenshot_2025-04-04_16-43-54_jpg.rf.1f42494a27d9f48a8a001bc1cd1c0d27.jpg |  | 75 | 0.0% | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| screenshot_2025-04-04_23-27-34_jpg.rf.6b13c2184c490c7b341f8ca01bb9b537.jpg |  | 87558 | 0.0% | 8.7% | 0.0% | 8.7% | - | - | - | - | - |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg |  | 82482 | 0.0% | 0.0% | 20.0% | 0.0% | - | - | - | - | - |

## Errors

- **image_22.png**: Image not found: C:\Users\surya\OneDrive\Desktop\work\projects\personal_proj\billet-ocr-poc-setup\billet-ocr-setup\data\raw\image_22.png
- **image_23.png**: Image not found: C:\Users\surya\OneDrive\Desktop\work\projects\personal_proj\billet-ocr-poc-setup\billet-ocr-setup\data\raw\image_23.png
- **image_24.png**: Image not found: C:\Users\surya\OneDrive\Desktop\work\projects\personal_proj\billet-ocr-poc-setup\billet-ocr-setup\data\raw\image_24.png
- **image_25.png**: Image not found: C:\Users\surya\OneDrive\Desktop\work\projects\personal_proj\billet-ocr-poc-setup\billet-ocr-setup\data\raw\image_25.png
- **image_26.png**: Image not found: C:\Users\surya\OneDrive\Desktop\work\projects\personal_proj\billet-ocr-poc-setup\billet-ocr-setup\data\raw\image_26.png

---
*Generated by `scripts/benchmark.py`.*