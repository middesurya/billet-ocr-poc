# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-25 01:10 UTC  
**Images evaluated:** 50  
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
| VLM Preprocessed | 43.3% | 22.0% | 2514ms |
| VLM Raw | 44.1% | 10.0% | 2628ms |
| VLM Center Crop | 44.3% | 12.0% | 2515ms |
| Florence-2 Raw | 21.4% | 0.0% | 869ms |
| Florence-2 Crop | 23.6% | 2.0% | 222ms |
| Florence-2 Bbox Crop | 13.4% | 2.1% | 95ms |
| F2 Bbox+SuperRes | 12.2% | 2.1% | 96ms |
| F2 Raw+Validated | 22.8% | 0.0% | - |
| EasyOCR | - | - | - |
| TrOCR | - | - | - |
| docTR | - | - | - |
| Ensemble | - | - | - |
| Ensemble V2 | 46.9% | 18.0% | 3059ms |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |
|-------|---------|------------------|---------|-----------------|--------|---------|---------|------------|------------|
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | 60008 (0%) | 674457 (50%) | 67467 (40%) | 5752555 (0%) | 6445764 (43%) | - (0%) | - (0%) | 5752555 (0%) |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | 60008 (100%) | 60008 (100%) | 60008 (100%) | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | 67108 (80%) | 67108 (80%) | 871188 (67%) | 6168616 (14%) | 6116686 (29%) | 6116852 (29%) | 6116852 (29%) | 6168616 (14%) |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | 60008 (0%) | 81023b (67%) | 81030 (60%) | 8182681 (43%) | 6108368 (43%) | 8409552 (14%) | 8409552 (14%) | 8182681 (43%) |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | 60008 (0%) | 3-479 (60%) | 87479 (80%) | 8479814 (43%) | 8147984 (57%) | - (0%) | - (0%) | 8479814 (43%) |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | 60008 (40%) | 050085 (17%) | U26705 (17%) | 6895689 (43%) | 6895689 (43%) | 6988559 (29%) | 5898553 (14%) | 6895689 (43%) |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | 60008 (20%) | 67221 (40%) | 87221 (60%) | 6221622 (29%) | 2215311 (29%) | - (0%) | - (0%) | 6221622 (29%) |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | 60008 (0%) | J05A0 (17%) | 06540 (33%) | 8654986 (14%) | 8654985 (14%) | - (0%) | - (0%) | 8654986 (14%) |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | 60008 (100%) | SM730 (0%) | GMP080 (33%) | 9998949 (0%) | - (0%) | - (0%) | - (0%) | 9998949 (0%) |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | 60008 (0%) | 08E76 (0%) | 08E70 (0%) | - (0%) | 18888 (20%) | - (0%) | - (0%) | 33293 (0%) |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | 60008 (40%) | 80824 (80%) | 80824 (80%) | 8862488 (29%) | 8062480 (43%) | 8062452 (43%) | 8682453 (43%) | 8862488 (29%) |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | 184767 (33%) | 32E70 (20%) | 03870 (20%) | - (0%) | - (0%) | - (0%) | - (0%) | 454545 (0%) |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | 60008 (40%) | TE3N8 (20%) | TE2003 (17%) | - (0%) | - (0%) | - (0%) | - (0%) | 45494 (0%) |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | 60875 (60%) | 80805 (40%) | 82605 (20%) | 8889558 (14%) | 8689580 (14%) | 8889553 (14%) | 8889553 (14%) | 8889558 (14%) |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | 60008 (20%) | 627105 (50%) | D87165 (50%) | 6876568 (29%) | 6765676 (0%) | 6676552 (14%) | 6676552 (14%) | 6876568 (29%) |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | 60008 (20%) | 802360 (50%) | 82P3A (20%) | 8823868 (43%) | 8023868 (57%) | - (0%) | - (0%) | 8823868 (43%) |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | 60008 (100%) | 24704 (20%) | 60008 (100%) | - (0%) | - (0%) | - (0%) | - (0%) | 8882886 (14%) |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | 184042 (33%) | 60402 (40%) | 69A02 (20%) | 8640286 (43%) | 6840268 (29%) | 5840253 (29%) | 5840253 (29%) | 8640286 (43%) |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | 06575 (0%) | 60535 (40%) | 60755 (40%) | 6855685 (29%) | 6655665 (14%) | 6055558 (43%) | 6055558 (43%) | 6855685 (29%) |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | A730N (20%) | 87394 (80%) | 87304 (60%) | 8139481 (71%) | 1394813 (43%) | 8139453 (71%) | 8139453 (71%) | 8139481 (71%) |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | 60008 (0%) | 60008 (0%) | 10006 (20%) | - (0%) | - (0%) | - (0%) | - (0%) | 5254524 (14%) |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | 60008 (100%) | 89913 (0%) | 389414 (0%) | 7685976 (14%) | 168984 (17%) | - (0%) | - (0%) | 7685976 (14%) |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | 60008 (40%) | 87113 (40%) | 87N18 (20%) | 8714871 (14%) | 8718873 (29%) | 81110 (20%) | - (0%) | 8714871 (14%) |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | 60008 (100%) | 184767 (0%) | 60008 (100%) | 8898888 (14%) | 8898888 (14%) | - (0%) | - (0%) | 8898888 (14%) |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | 30837 (60%) | 82887 (60%) | 82037 (60%) | 8868786 (43%) | 8268753 (43%) | 8866753 (29%) | 8866753 (29%) | 8868786 (43%) |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | 60008 (40%) | 20188 (20%) | 72103 (0%) | 2818682 (14%) | 2818928 (0%) | - (0%) | - (0%) | 2818682 (14%) |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | 60008 (100%) | 60008 (100%) | 60P8A (40%) | 6098609 (43%) | 6098609 (43%) | - (0%) | - (0%) | 6098609 (43%) |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | 60008 (17%) | JG2024 (17%) | 60424 (17%) | 8824682 (14%) | 8824882 (0%) | - (0%) | - (0%) | 8824682 (14%) |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | 21082 (80%) | 61092 (80%) | 61092 (80%) | 6192619 (29%) | 6189261 (43%) | 01892 (40%) | 01892 (40%) | 6192619 (29%) |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | 60008 (0%) | 032113 (50%) | 32043 (40%) | 6821368 (43%) | 8021380 (57%) | - (0%) | - (0%) | 6821368 (43%) |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | 60008 (80%) | 60008 (80%) | 86086 (40%) | 8888888 (29%) | 8888688 (29%) | 666000 (50%) | 6660006 (43%) | 8888888 (29%) |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | 37497 (20%) | 374497 (33%) | 874971 (33%) | 8149181 (29%) | 6149781 (14%) | 8149755 (29%) | 8149155 (29%) | 8149181 (29%) |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | 60008 (20%) | 67419 (40%) | 67419 (40%) | 6141961 (29%) | 6149614 (14%) | - (0%) | - (0%) | 6141961 (29%) |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | 60008 (100%) | 60008 (100%) | 00008 (80%) | 8395368 (14%) | 5852585 (14%) | - (0%) | - (0%) | 8395368 (14%) |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | 60008 (0%) | P2214 (60%) | 22210 (100%) | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | 60008 (0%) | 60C10 (0%) | 82G7A (20%) | 9868678 (29%) | 8457084 (14%) | - (0%) | - (0%) | 9868678 (29%) |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | 60008 (20%) | 61374 (100%) | 61374 (100%) | 6137461 (71%) | 6746137 (43%) | 61374 (100%) | 61374 (100%) | 6137461 (71%) |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | 87398 (40%) | 81308 (80%) | 815908 (50%) | 8139861 (43%) | 8139861 (43%) | 8139853 (43%) | 8139853 (43%) | 8139861 (43%) |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | 60008 (100%) | 88M13 (0%) | 83413 (0%) | - (0%) | 8841188 (14%) | - (0%) | - (0%) | 61868 (40%) |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | 60008 (0%) | 022713 (50%) | 022710 (50%) | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | 60008 (100%) | 60008 (100%) | 60093 (60%) | 8693358 (29%) | 6093609 (43%) | - (0%) | - (0%) | 8693358 (29%) |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | 60008 (100%) | 32055 (20%) | 82055 (20%) | 8895589 (14%) | 8295588 (14%) | 80955 (20%) | 880554 (17%) | 8895589 (14%) |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | 60008 (20%) | A05A0 (20%) | 60540 (20%) | 8549854 (29%) | 8054980 (43%) | 6549552 (14%) | - (0%) | 8549854 (29%) |
| image_25.png | 191078 | 910789 (67%) | 18167 (50%) | 60008 (33%) | - (0%) | - (0%) | - | - | - (0%) |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | 60008 (40%) | 67162 (40%) | 67062 (60%) | 6116261 (14%) | 6116261 (14%) | 5116253 (14%) | - (0%) | 6116261 (14%) |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | 60008 (100%) | 60005 (80%) | 60008 (100%) | 6895689 (29%) | 6885688 (29%) | - (0%) | - (0%) | 6895689 (29%) |
| image_23.png | 187612 | 18612 (83%) | 187812 (83%) | 187812 (83%) | 7612187 (29%) | 187612 (100%) | - | - | 7612187 (29%) |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | 60008 (33%) | J02008 (33%) | 60008 (33%) | 8888888 (0%) | 6888688 (14%) | - (0%) | - (0%) | 8888888 (0%) |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | 61582 (0%) | 67482 (0%) | 67480 (0%) | 6148681 (14%) | 6148064 (14%) | 01480 (0%) | 0148053 (14%) | 6148681 (14%) |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | 60008 (0%) | 60008 (0%) | 60008 (0%) | - (0%) | - (0%) | - (0%) | - (0%) | - (0%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | VLM Raw | 674457 | `XX.XX+` | 50.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | VLM Center Crop | 67467 | `XX.X.` | 40.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | Florence-2 Raw | 5752555 | `XXXXX++` | 0.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | Florence-2 Crop | 6445764 | `X..X.++` | 42.9% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | F2 Raw+Validated | 5752555 | `XXXXX++` | 0.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | F2 Raw+Validated | - | `-----` | 0.0% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | VLM Preprocessed | 67108 | `X....` | 80.0% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | VLM Raw | 67108 | `X....` | 80.0% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | VLM Center Crop | 871188 | `...X.+` | 66.7% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | Florence-2 Raw | 6168616 | `XXXXX++` | 14.3% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | Florence-2 Crop | 6116686 | `XX.XX++` | 28.6% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | Florence-2 Bbox Crop | 6116852 | `XX.X.++` | 28.6% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | F2 Bbox+SuperRes | 6116852 | `XX.X.++` | 28.6% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | F2 Raw+Validated | 6168616 | `XXXXX++` | 14.3% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | VLM Raw | 81023b | `..XXX+` | 66.7% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | VLM Center Crop | 81030 | `..X.X` | 60.0% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | Florence-2 Raw | 8182681 | `..XX.++` | 42.9% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | Florence-2 Crop | 6108368 | `X.XXX++` | 42.9% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | Florence-2 Bbox Crop | 8409552 | `.XXXX++` | 14.3% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | F2 Bbox+SuperRes | 8409552 | `.XXXX++` | 14.3% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | F2 Raw+Validated | 8182681 | `..XX.++` | 42.9% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | VLM Raw | 3-479 | `XX...` | 60.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | VLM Center Crop | 87479 | `.X...` | 80.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | Florence-2 Raw | 8479814 | `..XXX++` | 42.9% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | Florence-2 Crop | 8147984 | `.X...++` | 57.1% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | F2 Raw+Validated | 8479814 | `..XXX++` | 42.9% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | VLM Preprocessed | 60008 | `.XX.X` | 40.0% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | VLM Raw | 050085 | `XXX.X+` | 16.7% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | VLM Center Crop | U26705 | `XXXXX+` | 16.7% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | Florence-2 Raw | 6895689 | `.X.X.++` | 42.9% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | Florence-2 Crop | 6895689 | `.X.X.++` | 42.9% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | Florence-2 Bbox Crop | 6988559 | `..XXX++` | 28.6% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | F2 Bbox+SuperRes | 5898553 | `XX.XX++` | 14.3% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | F2 Raw+Validated | 6895689 | `.X.X.++` | 42.9% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | VLM Preprocessed | 60008 | `XXX.X` | 20.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | VLM Raw | 67221 | `XX.X.` | 40.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | VLM Center Crop | 87221 | `.X.X.` | 60.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | Florence-2 Raw | 6221622 | `X..XX++` | 28.6% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | Florence-2 Crop | 2215311 | `X.XXX++` | 28.6% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | F2 Raw+Validated | 6221622 | `X..XX++` | 28.6% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | VLM Preprocessed | 60008 | `XXXXX-` | 0.0% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | VLM Raw | J05A0 | `XXXXX-` | 16.7% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | VLM Center Crop | 06540 | `XXX.X-` | 33.3% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | Florence-2 Raw | 8654986 | `XXX.XX+` | 14.3% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | Florence-2 Crop | 8654985 | `XXX.XX+` | 14.3% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | Florence-2 Bbox Crop | - | `------` | 0.0% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | F2 Bbox+SuperRes | - | `------` | 0.0% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | F2 Raw+Validated | 8654986 | `XXX.XX+` | 14.3% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | VLM Raw | SM730 | `XXXXX` | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | VLM Center Crop | GMP080 | `XXX..+` | 33.3% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | Florence-2 Raw | 9998949 | `XXXXX++` | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | F2 Raw+Validated | 9998949 | `XXXXX++` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | VLM Raw | 08E76 | `XXXXX` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | VLM Center Crop | 08E70 | `XXXXX` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | Florence-2 Raw | - | `-----` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | Florence-2 Crop | 18888 | `.XXXX` | 20.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | F2 Raw+Validated | 33293 | `XXXXX` | 0.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Preprocessed | 60008 | `..XXX` | 40.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Raw | 80824 | `X....` | 80.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | VLM Center Crop | 80824 | `X....` | 80.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Raw | 8862488 | `XXX..++` | 28.6% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Crop | 8062480 | `X.X..++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | Florence-2 Bbox Crop | 8062452 | `X.X..++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | F2 Bbox+SuperRes | 8682453 | `XX...++` | 42.9% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | F2 Raw+Validated | 8862488 | `XXX..++` | 28.6% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | VLM Preprocessed | 184767 | `X.XXX+` | 33.3% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | VLM Raw | 32E70 | `XXXXX` | 20.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | VLM Center Crop | 03870 | `.XXXX` | 20.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | F2 Raw+Validated | 454545 | `XXXXX+` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | VLM Preprocessed | 60008 | `XX.X.` | 40.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | VLM Raw | TE3N8 | `XXXX.` | 20.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | VLM Center Crop | TE2003 | `XXXXX+` | 16.7% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | F2 Raw+Validated | 45494 | `XXXXX` | 0.0% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | VLM Preprocessed | 60875 | `..XX.` | 60.0% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | VLM Raw | 80805 | `X.XX.` | 40.0% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | VLM Center Crop | 82605 | `XXXX.` | 20.0% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | Florence-2 Raw | 8889558 | `XXXX.++` | 14.3% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | Florence-2 Crop | 8689580 | `XXXX.++` | 14.3% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | Florence-2 Bbox Crop | 8889553 | `XXXX.++` | 14.3% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | F2 Bbox+SuperRes | 8889553 | `XXXX.++` | 14.3% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | F2 Raw+Validated | 8889558 | `XXXX.++` | 14.3% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | VLM Preprocessed | 60008 | `XXX.X` | 20.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | VLM Raw | 627105 | `XXXXX+` | 50.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | VLM Center Crop | D87165 | `X.XXX+` | 50.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Raw | 6876568 | `X.XX.++` | 28.6% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Crop | 6765676 | `XXXXX++` | 0.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | Florence-2 Bbox Crop | 6676552 | `XXXX.++` | 14.3% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | F2 Bbox+SuperRes | 6676552 | `XXXX.++` | 14.3% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | F2 Raw+Validated | 6876568 | `X.XX.++` | 28.6% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | VLM Preprocessed | 60008 | `X.XXX` | 20.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | VLM Raw | 802360 | `..XX.+` | 50.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | VLM Center Crop | 82P3A | `.XXXX` | 20.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Raw | 8823868 | `.XXXX++` | 42.9% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Crop | 8023868 | `..XXX++` | 57.1% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | F2 Raw+Validated | 8823868 | `.XXXX++` | 42.9% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | VLM Raw | 24704 | `XXX.X` | 20.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | F2 Raw+Validated | 8882886 | `XXXX.++` | 14.3% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | VLM Preprocessed | 184042 | `XX.XX+` | 33.3% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | VLM Raw | 60402 | `XX.X.` | 40.0% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | VLM Center Crop | 69A02 | `XXXX.` | 20.0% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Raw | 8640286 | `.X.X.++` | 42.9% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Crop | 6840268 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | Florence-2 Bbox Crop | 5840253 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | F2 Bbox+SuperRes | 5840253 | `XX.X.++` | 28.6% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | F2 Raw+Validated | 8640286 | `.X.X.++` | 42.9% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | VLM Preprocessed | 06575 | `XXXXX` | 0.0% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | VLM Raw | 60535 | `..XXX` | 40.0% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | VLM Center Crop | 60755 | `..XXX` | 40.0% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | Florence-2 Raw | 6855685 | `.XXXX++` | 28.6% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | Florence-2 Crop | 6655665 | `.XXXX++` | 14.3% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | Florence-2 Bbox Crop | 6055558 | `..XXX++` | 42.9% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | F2 Bbox+SuperRes | 6055558 | `..XXX++` | 42.9% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | F2 Raw+Validated | 6855685 | `.XXXX++` | 28.6% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | VLM Preprocessed | A730N | `XX.XX` | 20.0% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | VLM Raw | 87394 | `.X...` | 80.0% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | VLM Center Crop | 87304 | `.X.X.` | 60.0% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Raw | 8139481 | `.....++` | 71.4% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Crop | 1394813 | `XXXXX++` | 42.9% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | Florence-2 Bbox Crop | 8139453 | `.....++` | 71.4% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | F2 Bbox+SuperRes | 8139453 | `.....++` | 71.4% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | F2 Raw+Validated | 8139481 | `.....++` | 71.4% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | VLM Raw | 60008 | `XXXXX` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | VLM Center Crop | 10006 | `.XXXX` | 20.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | F2 Raw+Validated | 5254524 | `XXXX.++` | 14.3% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | VLM Raw | 89913 | `XXXXX` | 0.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | VLM Center Crop | 389414 | `XXXXX+` | 0.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | Florence-2 Raw | 7685976 | `XXXXX++` | 14.3% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | Florence-2 Crop | 168984 | `XXXX.+` | 16.7% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | F2 Raw+Validated | 7685976 | `XXXXX++` | 14.3% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | VLM Preprocessed | 60008 | `XX..X` | 40.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | VLM Raw | 87113 | `.XXX.` | 40.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | VLM Center Crop | 87N18 | `.XXXX` | 20.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Raw | 8714871 | `.XXXX++` | 14.3% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Crop | 8718873 | `.XXXX++` | 28.6% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | Florence-2 Bbox Crop | 81110 | `.XXXX` | 20.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | F2 Raw+Validated | 8714871 | `.XXXX++` | 14.3% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | VLM Raw | 184767 | `XXXXX+` | 0.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | Florence-2 Raw | 8898888 | `XXXX.++` | 14.3% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | Florence-2 Crop | 8898888 | `XXXX.++` | 14.3% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | F2 Raw+Validated | 8898888 | `XXXX.++` | 14.3% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Preprocessed | 30837 | `XX...` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Raw | 82887 | `.X.X.` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | VLM Center Crop | 82037 | `.XX..` | 60.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Raw | 8868786 | `.XXX.++` | 42.9% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Crop | 8268753 | `.XXX.++` | 42.9% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | Florence-2 Bbox Crop | 8866753 | `.XXX.++` | 28.6% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | F2 Bbox+SuperRes | 8866753 | `.XXX.++` | 28.6% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | F2 Raw+Validated | 8868786 | `.XXX.++` | 42.9% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | VLM Preprocessed | 60008 | `..XXX` | 40.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | VLM Raw | 20188 | `X.XXX` | 20.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | VLM Center Crop | 72103 | `XXXXX` | 0.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | Florence-2 Raw | 2818682 | `XXXXX++` | 14.3% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | Florence-2 Crop | 2818928 | `XXXXX++` | 0.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | F2 Raw+Validated | 2818682 | `XXXXX++` | 14.3% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | VLM Center Crop | 60P8A | `..XXX` | 40.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | Florence-2 Raw | 6098609 | `..XXX++` | 42.9% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | Florence-2 Crop | 6098609 | `..XXX++` | 42.9% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | F2 Raw+Validated | 6098609 | `..XXX++` | 42.9% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | VLM Preprocessed | 60008 | `XXXXX-` | 16.7% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | VLM Raw | JG2024 | `XXXXX.` | 16.7% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | VLM Center Crop | 60424 | `XXXXX-` | 16.7% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Raw | 8824682 | `XXXXXX+` | 14.3% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Crop | 8824882 | `XXXXXX+` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | Florence-2 Bbox Crop | - | `------` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | F2 Bbox+SuperRes | - | `------` | 0.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | F2 Raw+Validated | 8824682 | `XXXXXX+` | 14.3% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | VLM Preprocessed | 21082 | `X....` | 80.0% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | VLM Raw | 61092 | `...X.` | 80.0% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | VLM Center Crop | 61092 | `...X.` | 80.0% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | Florence-2 Raw | 6192619 | `..XXX++` | 28.6% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | Florence-2 Crop | 6189261 | `..XX.++` | 42.9% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | Florence-2 Bbox Crop | 01892 | `X.XX.` | 40.0% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | F2 Bbox+SuperRes | 01892 | `X.XX.` | 40.0% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | F2 Raw+Validated | 6192619 | `..XXX++` | 28.6% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | VLM Raw | 032113 | `XX..X+` | 50.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | VLM Center Crop | 32043 | `X.XX.` | 40.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | Florence-2 Raw | 6821368 | `XX...++` | 42.9% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | Florence-2 Crop | 8021380 | `.X...++` | 57.1% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | F2 Raw+Validated | 6821368 | `XX...++` | 42.9% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | VLM Preprocessed | 60008 | `.X...` | 80.0% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | VLM Raw | 60008 | `.X...` | 80.0% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | VLM Center Crop | 86086 | `XX.XX` | 40.0% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | Florence-2 Raw | 8888888 | `X.XX.++` | 28.6% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | Florence-2 Crop | 8888688 | `X.XXX++` | 28.6% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | Florence-2 Bbox Crop | 666000 | `.XX.X+` | 50.0% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | F2 Bbox+SuperRes | 6660006 | `.XX.X++` | 42.9% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | F2 Raw+Validated | 8888888 | `X.XX.++` | 28.6% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | VLM Preprocessed | 37497 | `XXXX.` | 20.0% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | VLM Raw | 374497 | `XXXXX+` | 33.3% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | VLM Center Crop | 874971 | `.XXX.+` | 33.3% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | Florence-2 Raw | 8149181 | `.XXXX++` | 28.6% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | Florence-2 Crop | 6149781 | `XXXX.++` | 14.3% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | Florence-2 Bbox Crop | 8149755 | `.XXX.++` | 28.6% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | F2 Bbox+SuperRes | 8149155 | `.XXXX++` | 28.6% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | F2 Raw+Validated | 8149181 | `.XXXX++` | 28.6% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | VLM Preprocessed | 60008 | `XXX.X` | 20.0% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | VLM Raw | 67419 | `XX.X.` | 40.0% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | VLM Center Crop | 67419 | `XX.X.` | 40.0% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | Florence-2 Raw | 6141961 | `XX.X.++` | 28.6% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | Florence-2 Crop | 6149614 | `XX.XX++` | 14.3% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | F2 Raw+Validated | 6141961 | `XX.X.++` | 28.6% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | VLM Center Crop | 00008 | `X....` | 80.0% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | Florence-2 Raw | 8395368 | `XXXXX++` | 14.3% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | Florence-2 Crop | 5852585 | `XXXXX++` | 14.3% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | F2 Raw+Validated | 8395368 | `XXXXX++` | 14.3% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | VLM Raw | P2214 | `X...X` | 60.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | VLM Center Crop | 22210 | `.....` | 100.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | F2 Raw+Validated | - | `-----` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Raw | 60C10 | `XXXXX` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | VLM Center Crop | 82G7A | `.XXXX` | 20.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Raw | 9868678 | `XXXXX++` | 28.6% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Crop | 8457084 | `.XXXX++` | 14.3% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | F2 Raw+Validated | 9868678 | `XXXXX++` | 28.6% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Preprocessed | 60008 | `.XXXX` | 20.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Raw | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | VLM Center Crop | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Raw | 6137461 | `.....++` | 71.4% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Crop | 6746137 | `.XXXX++` | 42.9% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | Florence-2 Bbox Crop | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | F2 Bbox+SuperRes | 61374 | `.....` | 100.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | F2 Raw+Validated | 6137461 | `.....++` | 71.4% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Preprocessed | 87398 | `XX.X.` | 40.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Raw | 81308 | `X....` | 80.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | VLM Center Crop | 815908 | `X.XXX+` | 50.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Raw | 8139861 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Crop | 8139861 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | Florence-2 Bbox Crop | 8139853 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | F2 Bbox+SuperRes | 8139853 | `X..X.++` | 42.9% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | F2 Raw+Validated | 8139861 | `X..X.++` | 42.9% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | VLM Raw | 88M13 | `XXXXX` | 0.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | VLM Center Crop | 83413 | `XXXXX` | 0.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | Florence-2 Raw | - | `-----` | 0.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | Florence-2 Crop | 8841188 | `XXXXX++` | 14.3% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | F2 Raw+Validated | 61868 | `.XXX.` | 40.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | VLM Raw | 022713 | `...XX+` | 50.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | VLM Center Crop | 022710 | `...XX+` | 50.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | F2 Raw+Validated | - | `-----` | 0.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | VLM Raw | 60008 | `.....` | 100.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | VLM Center Crop | 60093 | `...XX` | 60.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | Florence-2 Raw | 8693358 | `XXXXX++` | 28.6% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | Florence-2 Crop | 6093609 | `..XXX++` | 42.9% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | F2 Raw+Validated | 8693358 | `XXXXX++` | 28.6% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | VLM Raw | 32055 | `XX.XX` | 20.0% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | VLM Center Crop | 82055 | `XX.XX` | 20.0% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | Florence-2 Raw | 8895589 | `XXXXX++` | 14.3% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | Florence-2 Crop | 8295588 | `XXXXX++` | 14.3% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | Florence-2 Bbox Crop | 80955 | `X.XXX` | 20.0% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | F2 Bbox+SuperRes | 880554 | `XX.XX+` | 16.7% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | F2 Raw+Validated | 8895589 | `XXXXX++` | 14.3% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | VLM Preprocessed | 60008 | `XXXX.` | 20.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | VLM Raw | A05A0 | `XXXXX` | 20.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | VLM Center Crop | 60540 | `XXXXX` | 20.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Raw | 8549854 | `X.XX.++` | 28.6% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Crop | 8054980 | `XXXXX++` | 42.9% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | Florence-2 Bbox Crop | 6549552 | `X.XXX++` | 14.3% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | F2 Raw+Validated | 8549854 | `X.XX.++` | 28.6% |
| image_25.png | 191078 | VLM Preprocessed | 910789 | `XXXXXX` | 66.7% |
| image_25.png | 191078 | VLM Raw | 18167 | `.X.X.-` | 50.0% |
| image_25.png | 191078 | VLM Center Crop | 60008 | `XXX.X-` | 33.3% |
| image_25.png | 191078 | Florence-2 Raw | - | `------` | 0.0% |
| image_25.png | 191078 | Florence-2 Crop | - | `------` | 0.0% |
| image_25.png | 191078 | F2 Raw+Validated | - | `------` | 0.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | VLM Preprocessed | 60008 | `.X.XX` | 40.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | VLM Raw | 67162 | `..XXX` | 40.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | VLM Center Crop | 67062 | `...XX` | 60.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | Florence-2 Raw | 6116261 | `.XXXX++` | 14.3% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | Florence-2 Crop | 6116261 | `.XXXX++` | 14.3% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | Florence-2 Bbox Crop | 5116253 | `XXXXX++` | 14.3% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | F2 Raw+Validated | 6116261 | `.XXXX++` | 14.3% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Preprocessed | 60008 | `.....` | 100.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Raw | 60005 | `....X` | 80.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | VLM Center Crop | 60008 | `.....` | 100.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Raw | 6895689 | `.XXXX++` | 28.6% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Crop | 6885688 | `.XXXX++` | 28.6% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | F2 Raw+Validated | 6895689 | `.XXXX++` | 28.6% |
| image_23.png | 187612 | VLM Preprocessed | 18612 | `..XXX-` | 83.3% |
| image_23.png | 187612 | VLM Raw | 187812 | `...X..` | 83.3% |
| image_23.png | 187612 | VLM Center Crop | 187812 | `...X..` | 83.3% |
| image_23.png | 187612 | Florence-2 Raw | 7612187 | `XXXX.X+` | 28.6% |
| image_23.png | 187612 | Florence-2 Crop | 187612 | `......` | 100.0% |
| image_23.png | 187612 | F2 Raw+Validated | 7612187 | `XXXX.X+` | 28.6% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | VLM Preprocessed | 60008 | `XX..X-` | 33.3% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | VLM Raw | J02008 | `XXX.XX` | 33.3% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | VLM Center Crop | 60008 | `XX..X-` | 33.3% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | Florence-2 Raw | 8888888 | `XXXXXX+` | 0.0% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | Florence-2 Crop | 6888688 | `XXXX.X+` | 14.3% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | Florence-2 Bbox Crop | - | `------` | 0.0% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | F2 Bbox+SuperRes | - | `------` | 0.0% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | F2 Raw+Validated | 8888888 | `XXXXXX+` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | VLM Preprocessed | 61582 | `XXXXX` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | VLM Raw | 67482 | `XXXXX` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | VLM Center Crop | 67480 | `XXXXX` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Raw | 6148681 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Crop | 6148064 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | Florence-2 Bbox Crop | 01480 | `XXXXX` | 0.0% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | F2 Bbox+SuperRes | 0148053 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | F2 Raw+Validated | 6148681 | `XXXXX++` | 14.3% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | VLM Preprocessed | 60008 | `XXXXX` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | VLM Raw | 60008 | `XXXXX` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | VLM Center Crop | 60008 | `XXXXX` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | Florence-2 Raw | - | `-----` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | Florence-2 Crop | - | `-----` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | F2 Raw+Validated | - | `-----` | 0.0% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 6 | 8 | 23 |
| 0 | 1 | 20 |
| 0 | 2 | 20 |
| 8 | 6 | 20 |
| 0 | 8 | 16 |
| 0 | 7 | 13 |
| 1 | 0 | 12 |
| 0 | 6 | 11 |
| 8 | 0 | 10 |
| 3 | 8 | 9 |
| 2 | 0 | 9 |
| 0 | 4 | 8 |
| 8 | 3 | 8 |
| 0 | 3 | 7 |
| 0 | 9 | 7 |
| 8 | 4 | 7 |
| 5 | 8 | 7 |
| 7 | 2 | 6 |
| 6 | 0 | 6 |
| 5 | 0 | 6 |
| 7 | 1 | 6 |
| 2 | 6 | 6 |
| 8 | 9 | 5 |
| 7 | 0 | 5 |
| 7 | 4 | 5 |
| 9 | 0 | 5 |
| 9 | 8 | 5 |
| 3 | 0 | 5 |
| 8 | 1 | 4 |
| 8 | 5 | 4 |
| 0 | 5 | 4 |
| 4 | 2 | 4 |
| 6 | 4 | 4 |
| 6 | 3 | 4 |
| 4 | 0 | 4 |
| 6 | 1 | 3 |
| 8 | 7 | 2 |
| A | 8 | 2 |
| 9 | 1 | 2 |
| 1 | 4 | 2 |
| 2 | 9 | 2 |
| M | 0 | 2 |
| E | 6 | 2 |
| 4 | 8 | 2 |
| 7 | 5 | 2 |
| 1 | 7 | 2 |
| 7 | 3 | 2 |
| 5 | 1 | 2 |
| A | 1 | 2 |
| 2 | 5 | 2 |
| 8 | 2 | 2 |
| 9 | 2 | 2 |
| 3 | 1 | 2 |
| 4 | 1 | 2 |
| 3 | 4 | 2 |
| 6 | 7 | 1 |
| N | 4 | 1 |
| 9 | 3 | 1 |
| 6 | 2 | 1 |
| 1 | 9 | 1 |
| 5 | 2 | 1 |
| - | 4 | 1 |
| S | 6 | 1 |
| 2 | 8 | 1 |
| E | 2 | 1 |
| T | 7 | 1 |
| E | 3 | 1 |
| N | 1 | 1 |
| J | 1 | 1 |
| G | 9 | 1 |
| 2 | 7 | 1 |
| P | 2 | 1 |
| C | 8 | 1 |
| 1 | 2 | 1 |
| 3 | 6 | 1 |
| A | 0 | 1 |
| J | 0 | 1 |
| P | 3 | 1 |
| 3 | 9 | 1 |
| A | 6 | 1 |
| A | 4 | 1 |
| 6 | 5 | 1 |
| N | 0 | 1 |
| 7 | 6 | 1 |
| P | 0 | 1 |
| 2 | 1 | 1 |
| G | 8 | 1 |
| 1 | 5 | 1 |
| 4 | 7 | 1 |
| 5 | 3 | 1 |

## Ensemble V2 Tier Breakdown

| Image | GT Heat | Predicted | Char Acc | Tier | Tier Label | VLM? | Time |
|-------|---------|-----------|----------|------|------------|------|------|
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg | 84437 | 67467 | 40.0% | 4 | vlm_fallback | Yes | 3341ms |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 2688ms |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg | 87108 | 67108 | 80.0% | 4 | vlm_fallback | Yes | 2702ms |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg | 81236 | 61036 | 60.0% | 4 | vlm_fallback | Yes | 2985ms |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg | 84479 | 57470 | 40.0% | 4 | vlm_fallback | Yes | 2805ms |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg | 69906 | 60005 | 40.0% | 4 | vlm_fallback | Yes | 3603ms |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg | 82201 | 67221 | 40.0% | 4 | vlm_fallback | Yes | 2989ms |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg | 487440 | Q25AO | 0.0% | 4 | vlm_fallback | Yes | 2605ms |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg | 60008 | SM2704 | 16.7% | 4 | vlm_fallback | Yes | 3256ms |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg | 14624 | 08E76 | 0.0% | 4 | vlm_fallback | Yes | 3804ms |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg | 60824 | 80624 | 60.0% | 4 | vlm_fallback | Yes | 2807ms |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg | 08217 | 32E70 | 20.0% | 4 | vlm_fallback | Yes | 3416ms |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg | 73018 | TE318 | 40.0% | 4 | vlm_fallback | Yes | 2723ms |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg | 60025 | 80805 | 40.0% | 4 | vlm_fallback | Yes | 3091ms |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg | 88105 | 687165 | 50.0% | 4 | vlm_fallback | Yes | 2716ms |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg | 80396 | 00290 | 40.0% | 4 | vlm_fallback | Yes | 3372ms |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg | 60008 | 24750 | 0.0% | 4 | vlm_fallback | Yes | 2363ms |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg | 82482 | 60402 | 40.0% | 4 | vlm_fallback | Yes | 2331ms |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg | 60008 | 60555 | 40.0% | 4 | vlm_fallback | Yes | 2330ms |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg | 81394 | 3T39H | 40.0% | 4 | vlm_fallback | Yes | 3583ms |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg | 18725 | 10003 | 20.0% | 4 | vlm_fallback | Yes | 3129ms |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg | 60008 | 89F13 | 0.0% | 4 | vlm_fallback | Yes | 2747ms |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg | 85003 | 87113 | 40.0% | 4 | vlm_fallback | Yes | 3059ms |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 3574ms |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg | 86837 | 82687 | 60.0% | 4 | vlm_fallback | Yes | 2554ms |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg | 60761 | 20130 | 20.0% | 4 | vlm_fallback | Yes | 2784ms |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 2668ms |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg | 197604 | 60404 | 33.3% | 4 | vlm_fallback | Yes | 2738ms |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg | 61082 | 61082 | 100.0% | 4 | vlm_fallback | Yes | 3309ms |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg | 82213 | 822B | 60.0% | 4 | vlm_fallback | Yes | 3496ms |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg | 68008 | 60008 | 80.0% | 4 | vlm_fallback | Yes | 2906ms |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg | 84237 | 874971 | 33.3% | 4 | vlm_fallback | Yes | 2914ms |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg | 43409 | 434109 | 83.3% | 4 | vlm_fallback | Yes | 3080ms |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 3745ms |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg | 22210 | P2214 | 60.0% | 4 | vlm_fallback | Yes | 3194ms |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg | 81821 | 60374 | 0.0% | 4 | vlm_fallback | Yes | 2525ms |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg | 61374 | 61374 | 100.0% | 4 | vlm_fallback | Yes | 2910ms |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg | 61308 | 61308 | 100.0% | 4 | vlm_fallback | Yes | 2572ms |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg | 60008 | 88M13 | 0.0% | 4 | vlm_fallback | Yes | 2961ms |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg | 02246 | K2270 | 40.0% | 4 | vlm_fallback | Yes | 2535ms |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 2662ms |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg | 60008 | 82055 | 20.0% | 4 | vlm_fallback | Yes | 2840ms |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg | 05118 | J0540 | 20.0% | 4 | vlm_fallback | Yes | 3489ms |
| image_25.png | 191078 | 76107 | 50.0% | 4 | vlm_fallback | Yes | 5058ms |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg | 67085 | 67162 | 40.0% | 4 | vlm_fallback | Yes | 3461ms |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg | 60008 | 60008 | 100.0% | 4 | vlm_fallback | Yes | 4065ms |
| image_23.png | 187612 | 18Y812 | 66.7% | 4 | vlm_fallback | Yes | 3804ms |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg | 070060 | J02008 | 33.3% | 4 | vlm_fallback | Yes | 2844ms |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg | 84239 | 67480 | 0.0% | 4 | vlm_fallback | Yes | 3215ms |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg | 31179 | 60008 | 0.0% | 4 | vlm_fallback | Yes | 2622ms |

**VLM fallback rate:** 50/50 (100%)

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val | Ensemble | Ens V2 |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|---------|------------|------------|----------|--------|
| 202504011019023734_jpg.rf.5f2bb575d4626375a043610f27ff8b93.jpg |  | 84437 | - | - | - | - | - | 0.0% | 50.0% | 40.0% | 0.0% | 42.9% | 0.0% | 0.0% | 0.0% | - | 40.0% |
| screenshot_2025-04-05_05-41-22_jpg.rf.ed63a86690ac0002a9337e98bc47f6a0.jpg |  | 60008 | - | - | - | - | - | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 100.0% |
| 202503300653584438_jpg.rf.e3119aee1e5190eeb273afa50a3c94bf.jpg |  | 87108 | - | - | - | - | - | 80.0% | 80.0% | 66.7% | 14.3% | 28.6% | 28.6% | 28.6% | 14.3% | - | 80.0% |
| 202503290627339235_jpg.rf.c122a4b43b38a924950192202e70ea98.jpg |  | 81236 | - | - | - | - | - | 0.0% | 66.7% | 60.0% | 42.9% | 42.9% | 14.3% | 14.3% | 42.9% | - | 60.0% |
| screenshot_2025-04-06_10-02-33_jpg.rf.f8c094f77a71c09c82efd7cb5b522834.jpg |  | 84479 | - | - | - | - | - | 0.0% | 60.0% | 80.0% | 42.9% | 57.1% | 0.0% | 0.0% | 42.9% | - | 40.0% |
| 202503281429397380_jpg.rf.ca174a83e7a44ac38b38260147f09c49.jpg |  | 69906 | - | - | - | - | - | 40.0% | 16.7% | 16.7% | 42.9% | 42.9% | 28.6% | 14.3% | 42.9% | - | 40.0% |
| 202503290101502540_jpg.rf.fd17eff8b53a5f11b818f75587faf2d8.jpg |  | 82201 | - | - | - | - | - | 20.0% | 40.0% | 60.0% | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - | 40.0% |
| 20250319093914_jpg.rf.efda675c0eefe8d5a473022d9f8d6982.jpg |  | 487440 | - | - | - | - | - | 0.0% | 16.7% | 33.3% | 14.3% | 14.3% | 0.0% | 0.0% | 14.3% | - | 0.0% |
| 202503292050181271_jpg.rf.0700665d8f574e696a9bda9be3c5ff91.jpg |  | 60008 | - | - | - | - | - | 100.0% | 0.0% | 33.3% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 16.7% |
| 202503292152184650_jpg.rf.13a2bf161c1f77cf8a879c77f682ddb9.jpg |  | 14624 | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | 0.0% |
| 20250317011538_jpg.rf.299b27e41810d3c0ab9841dd4af37530.jpg |  | 60824 | - | - | - | - | - | 40.0% | 80.0% | 80.0% | 28.6% | 42.9% | 42.9% | 42.9% | 28.6% | - | 60.0% |
| screenshot_2025-04-04_20-35-12_jpg.rf.fd98978aeb94563e233ff19e3decf037.jpg |  | 08217 | - | - | - | - | - | 33.3% | 20.0% | 20.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 20.0% |
| screenshot_2025-04-05_00-25-56_jpg.rf.b70271e9b59ca4d52f44b6ffea0695f2.jpg |  | 73018 | - | - | - | - | - | 40.0% | 20.0% | 16.7% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 40.0% |
| 20250321183545_jpg.rf.891f5945fbed8a2152040214914f4a8c.jpg |  | 60025 | - | - | - | - | - | 60.0% | 40.0% | 20.0% | 14.3% | 14.3% | 14.3% | 14.3% | 14.3% | - | 40.0% |
| 20250314105317_jpg.rf.e39101560082e3c741ec16a9dd749b67.jpg |  | 88105 | - | - | - | - | - | 20.0% | 50.0% | 50.0% | 28.6% | 0.0% | 14.3% | 14.3% | 28.6% | - | 50.0% |
| 20250318174457_jpg.rf.b45df2f8c49801512e7a2349ad8e802b.jpg |  | 80396 | - | - | - | - | - | 20.0% | 50.0% | 20.0% | 42.9% | 57.1% | 0.0% | 0.0% | 42.9% | - | 40.0% |
| 20250320014333_jpg.rf.675b10fd772aaf2707c59a029ba21f79.jpg |  | 60008 | - | - | - | - | - | 100.0% | 20.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 14.3% | - | 0.0% |
| screenshot_2025-04-06_00-40-22_jpg.rf.44aeaadfc9a3acf0a794edb77c864844.jpg |  | 82482 | - | - | - | - | - | 33.3% | 40.0% | 20.0% | 42.9% | 28.6% | 28.6% | 28.6% | 42.9% | - | 40.0% |
| 20250316214050_jpg.rf.90b1418c15b9576f97b9d3e83199c555.jpg |  | 60008 | - | - | - | - | - | 0.0% | 40.0% | 40.0% | 28.6% | 14.3% | 42.9% | 42.9% | 28.6% | - | 40.0% |
| 202503292244278012_jpg.rf.57a0ed79961cdd79c04ab71fc839d25e.jpg |  | 81394 | - | - | - | - | - | 20.0% | 80.0% | 60.0% | 71.4% | 42.9% | 71.4% | 71.4% | 71.4% | - | 40.0% |
| 20250320153627_jpg.rf.4d335596e747424cd4c65b298de175d0.jpg |  | 18725 | - | - | - | - | - | 0.0% | 0.0% | 20.0% | 0.0% | 0.0% | 0.0% | 0.0% | 14.3% | - | 20.0% |
| 202503310842170129_jpg.rf.32e1e20d6ba5153ddf1775d618d14512.jpg |  | 60008 | - | - | - | - | - | 100.0% | 0.0% | 0.0% | 14.3% | 16.7% | 0.0% | 0.0% | 14.3% | - | 0.0% |
| screenshot_2025-04-05_08-37-57_jpg.rf.970d61a190dfbfea4175e23e06f1ce3f.jpg |  | 85003 | - | - | - | - | - | 40.0% | 40.0% | 20.0% | 14.3% | 28.6% | 20.0% | 0.0% | 14.3% | - | 40.0% |
| 202503301053335654_jpg.rf.74e2f8ce6ae97032c60f0762a26986ae.jpg |  | 60008 | - | - | - | - | - | 100.0% | 0.0% | 100.0% | 14.3% | 14.3% | 0.0% | 0.0% | 14.3% | - | 100.0% |
| 20250316184022_jpg.rf.50b1fea536c575eb73f28884dc6a7795.jpg |  | 86837 | - | - | - | - | - | 60.0% | 60.0% | 60.0% | 42.9% | 42.9% | 28.6% | 28.6% | 42.9% | - | 60.0% |
| 20250319014537_jpg.rf.c0546be5ea7ed28227b39267f4209458.jpg |  | 60761 | - | - | - | - | - | 40.0% | 20.0% | 0.0% | 14.3% | 0.0% | 0.0% | 0.0% | 14.3% | - | 20.0% |
| 202504011241330667_jpg.rf.d7246f6ffc3ded9c2b7cd03fc434d5a0.jpg |  | 60008 | - | - | - | - | - | 100.0% | 100.0% | 40.0% | 42.9% | 42.9% | 0.0% | 0.0% | 42.9% | - | 100.0% |
| 20250320060414_jpg.rf.048074f1313fd0d6553e0f3bf997f7a1.jpg |  | 197604 | - | - | - | - | - | 16.7% | 16.7% | 16.7% | 14.3% | 0.0% | 0.0% | 0.0% | 14.3% | - | 33.3% |
| 202503281919417768_jpg.rf.af7795230bed9e1971678402d34efa53.jpg |  | 61082 | - | - | - | - | - | 80.0% | 80.0% | 80.0% | 28.6% | 42.9% | 40.0% | 40.0% | 28.6% | - | 100.0% |
| screenshot_2025-04-07_09-29-06_jpg.rf.1fe5e33292a8e3adb2fcfdf13758b307.jpg |  | 82213 | - | - | - | - | - | 0.0% | 50.0% | 40.0% | 42.9% | 57.1% | 0.0% | 0.0% | 42.9% | - | 60.0% |
| 202503301709527799_jpg.rf.4743d45348c532b6e200a861096cb753.jpg |  | 68008 | - | - | - | - | - | 80.0% | 80.0% | 40.0% | 28.6% | 28.6% | 50.0% | 42.9% | 28.6% | - | 80.0% |
| 202504020337408273_jpg.rf.e466b8a6564725c881b48e287c5c91c8.jpg |  | 84237 | - | - | - | - | - | 20.0% | 33.3% | 33.3% | 28.6% | 14.3% | 28.6% | 28.6% | 28.6% | - | 33.3% |
| 20250318052542_jpg.rf.fbdf42502e87ae3a2f176b9c6d7f710c.jpg |  | 43409 | - | - | - | - | - | 20.0% | 40.0% | 40.0% | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - | 83.3% |
| 20250321135059_jpg.rf.70d0b84f094f3a4560f98c3b65bae32d.jpg |  | 60008 | - | - | - | - | - | 100.0% | 100.0% | 80.0% | 14.3% | 14.3% | 0.0% | 0.0% | 14.3% | - | 100.0% |
| screenshot_2025-04-04_19-25-26_jpg.rf.07eb0428ced19d2db18f436781aaa917.jpg |  | 22210 | - | - | - | - | - | 0.0% | 60.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 60.0% |
| 202503290724084610_jpg.rf.f242f059955a1067a4b499ca050ebacc.jpg |  | 81821 | - | - | - | - | - | 0.0% | 0.0% | 20.0% | 28.6% | 14.3% | 0.0% | 0.0% | 28.6% | - | 0.0% |
| 202503302211263868_jpg.rf.4bbb4db66b4cbe04cd806516a5407e9e.jpg |  | 61374 | - | - | - | - | - | 20.0% | 100.0% | 100.0% | 71.4% | 42.9% | 100.0% | 100.0% | 71.4% | - | 100.0% |
| 202503300444408940_jpg.rf.b0738afe796670562b56c97a68854f6e.jpg |  | 61308 | - | - | - | - | - | 40.0% | 80.0% | 50.0% | 42.9% | 42.9% | 42.9% | 42.9% | 42.9% | - | 100.0% |
| 202504010847248040_jpg.rf.234ef276f0d87b2c5d3a365134cde5df.jpg |  | 60008 | - | - | - | - | - | 100.0% | 0.0% | 0.0% | 0.0% | 14.3% | 0.0% | 0.0% | 40.0% | - | 0.0% |
| screenshot_2025-04-04_22-16-35_jpg.rf.99b75e357cab934bd7164c4a0934851d.jpg |  | 02246 | - | - | - | - | - | 0.0% | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 40.0% |
| 20250322000708_jpg.rf.90c7720ad89c8385788afa33566234ee.jpg |  | 60008 | - | - | - | - | - | 100.0% | 100.0% | 60.0% | 28.6% | 42.9% | 0.0% | 0.0% | 28.6% | - | 100.0% |
| 202503282034408803_jpg.rf.445076cb6761baa4ddfb962931949ad5.jpg |  | 60008 | - | - | - | - | - | 100.0% | 20.0% | 20.0% | 14.3% | 14.3% | 20.0% | 16.7% | 14.3% | - | 20.0% |
| 20250320045606_jpg.rf.1c97781628cdb39a22502c64ece2a8a9.jpg |  | 05118 | - | - | - | - | - | 20.0% | 20.0% | 20.0% | 28.6% | 42.9% | 14.3% | 0.0% | 28.6% | - | 20.0% |
| image_25.png | very_hard | 191078 | - | - | - | - | - | 66.7% | 50.0% | 33.3% | 0.0% | 0.0% | - | - | 0.0% | - | 50.0% |
| screenshot_2025-04-06_06-33-49_jpg.rf.ee8a68ac36c6f68b4e40daacb5c75677.jpg |  | 67085 | - | - | - | - | - | 40.0% | 40.0% | 60.0% | 14.3% | 14.3% | 14.3% | 0.0% | 14.3% | - | 40.0% |
| 202503301318042741_jpg.rf.158e2359ad20afd2fa8e054e4ff46574.jpg |  | 60008 | - | - | - | - | - | 100.0% | 80.0% | 100.0% | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - | 100.0% |
| image_23.png | medium | 187612 | - | - | - | - | - | 83.3% | 83.3% | 83.3% | 28.6% | 100.0% | - | - | 28.6% | - | 66.7% |
| 20250318231400_jpg.rf.ae563902ce324ff8e4b32e2c43825812.jpg |  | 070060 | - | - | - | - | - | 33.3% | 33.3% | 33.3% | 0.0% | 14.3% | 0.0% | 0.0% | 0.0% | - | 33.3% |
| screenshot_2025-04-03_16-27-23_jpg.rf.4fdf21ec5c2054c95ea21510b6450b3c.jpg |  | 84239 | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 14.3% | 14.3% | 0.0% | 14.3% | 14.3% | - | 0.0% |
| 202504010938102828_jpg.rf.544a5af91b16c8d1c799dec896c02658.jpg |  | 31179 | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | 0.0% |

---
*Generated by `scripts/benchmark.py`.*