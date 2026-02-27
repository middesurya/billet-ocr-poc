# Billet OCR Benchmark Report — V3

**Generated:** 2026-02-25 03:41 UTC  
**Images evaluated:** 30  
**VLM model:** `claude-opus-4-6`  
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
| VLM model | `claude-opus-4-6` |
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
| Florence-2 Raw | 35.4% | 0.0% | 1061ms |
| Florence-2 Crop | 36.2% | 0.0% | 544ms |
| Florence-2 Bbox Crop | 33.6% | 0.0% | 246ms |
| F2 Bbox+SuperRes | 36.8% | 0.0% | 210ms |
| F2 Raw+Validated | 38.8% | 0.0% | - |
| Ensemble | - | - | - |
| Ensemble V2 | - | - | - |

## VLM A/B Comparison

| Image | GT Heat | VLM Preprocessed | VLM Raw | VLM Center Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val |
|-------|---------|------------------|---------|-----------------|--------|---------|---------|------------|------------|
| 20250316151241_jpg.rf.4743ea9ebc9ba623f1bb3f86a7f82e0c.jpg | 60731 | - | - | - | 6873168 (57%) | 6073160 (71%) | - | - | 6873168 (57%) |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 68641 | - | - | - | 6864168 (71%) | 6864186 (71%) | - | - | 6864168 (71%) |
| 20250316194929_jpg.rf.dc9dd51ef2b4819b2740ee4cae9a378e.jpg | 61196 | - | - | - | 6119661 (71%) | 6119652 (71%) | - | - | 6119661 (71%) |
| 20250317141401_jpg.rf.12604c217d3b2d98432886dd6272ec94.jpg | 16T88 | - | - | - | 7864852 (29%) | - (0%) | - | - | 7864852 (29%) |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | - | - | - | 6000050 (57%) | 6000030 (71%) | 600003 (83%) | 600003 (83%) | 6000050 (57%) |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | - | - | - | - (0%) | 72019 (0%) | 525719 (17%) | 525719 (17%) | 917989 (17%) |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | - | - | - | 2333232 (57%) | 3323232 (29%) | - (0%) | 2357027 (14%) | 2333232 (57%) |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | - | - | - | - (0%) | - (0%) | 2256909 (29%) | 2256909 (29%) | 5599999 (29%) |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | - | - | - | 19094 (0%) | 19999 (20%) | - (0%) | - (0%) | 19094 (0%) |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | - | - | - | 2351238 (29%) | 2381238 (29%) | 2315008 (43%) | 2315008 (43%) | 2351238 (29%) |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | - | - | - | 84835 (0%) | 16645 (20%) | - (0%) | - (0%) | 84835 (0%) |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | - | - | - | 8457484 (29%) | 8457484 (29%) | - (0%) | - (0%) | 8457484 (29%) |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | - | - | - | 22019 (0%) | - (0%) | 1251219 (14%) | 1251219 (14%) | 22019 (0%) |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | - | - | - | 6121561 (71%) | 6121561 (71%) | 6121553 (71%) | 6121553 (71%) | 6121561 (71%) |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | - | - | - | 19989 (20%) | - (0%) | - (0%) | - (0%) | 19989 (20%) |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | - | - | - | 6159261 (71%) | 6159261 (71%) | 6159255 (71%) | 6159253 (71%) | 6159261 (71%) |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | - | - | - | 6749067 (43%) | 8614305 (71%) | 6143053 (71%) | 6143053 (71%) | 6749067 (43%) |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | - | - | - | 6147614 (57%) | 1457614 (29%) | 6146753 (71%) | 6146753 (71%) | 6147614 (57%) |
| screenshot_2025-04-02_17-06-26_jpg.rf.e0260f3c5493b3e03ef3a13e6006a154.jpg | 61482 | - | - | - | 4962559 (14%) | 14826 (60%) | - | - | 4962559 (14%) |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | - | - | - | - (0%) | - (0%) | - (0%) | - (0%) | 5051051 (29%) |
| screenshot_2025-04-03_19-40-58_jpg.rf.9640da77089a24983c9c16e089258eaa.jpg | 68931 | - | - | - | 6893168 (71%) | 6093160 (57%) | - | - | 6893168 (71%) |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | - | - | - | 5859585 (14%) | - (0%) | 000007 (17%) | 000007 (17%) | 5859585 (14%) |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | - | - | - | 9595095 (0%) | - (0%) | - (0%) | - (0%) | 9595095 (0%) |
| screenshot_2025-04-04_08-29-00_jpg.rf.80a924315f4041b18eec6437c45c61e9.jpg | 17418 | - | - | - | - (0%) | - (0%) | - | - | 7187871 (29%) |
| screenshot_2025-04-04_11-00-31_jpg.rf.f4066dc0086504ef3d4c23b70eb68752.jpg | 61344 | - | - | - | 8134613 (43%) | 6134461 (71%) | - | - | 8134613 (43%) |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | - | - | - | 8149981 (57%) | 1499811 (29%) | 8140095 (71%) | 8140095 (71%) | 8149981 (57%) |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | - | - | - | 6155861 (71%) | 6560655 (29%) | 6155053 (57%) | 6155053 (57%) | 6155861 (71%) |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | - | - | - | 8821788 (29%) | 6081760 (57%) | 175418 (17%) | 6001754 (71%) | 8821788 (29%) |
| screenshot_2025-04-07_05-45-21_jpg.rf.28492552d7f8ae9c7e81ea37472b68ee.jpg | 80876 | - | - | - | 8387688 (57%) | 8007680 (57%) | - | - | 8387688 (57%) |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | - | - | - | 6212682 (43%) | 6021260 (71%) | 6021254 (71%) | 6021254 (71%) | 6212682 (43%) |

## VLM Diagnostic Diffs

Character-level comparison: `.` = match, `X` = mismatch, `+` = extra, `-` = missing

| Image | GT Heat | Method | Predicted | Diff | Char Acc |
|-------|---------|--------|-----------|------|----------|
| 20250316151241_jpg.rf.4743ea9ebc9ba623f1bb3f86a7f82e0c.jpg | 60731 | Florence-2 Raw | 6873168 | `.X...++` | 57.1% |
| 20250316151241_jpg.rf.4743ea9ebc9ba623f1bb3f86a7f82e0c.jpg | 60731 | Florence-2 Crop | 6073160 | `.....++` | 71.4% |
| 20250316151241_jpg.rf.4743ea9ebc9ba623f1bb3f86a7f82e0c.jpg | 60731 | F2 Raw+Validated | 6873168 | `.X...++` | 57.1% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 68641 | Florence-2 Raw | 6864168 | `.....++` | 71.4% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 68641 | Florence-2 Crop | 6864186 | `.....++` | 71.4% |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg | 68641 | F2 Raw+Validated | 6864168 | `.....++` | 71.4% |
| 20250316194929_jpg.rf.dc9dd51ef2b4819b2740ee4cae9a378e.jpg | 61196 | Florence-2 Raw | 6119661 | `.....++` | 71.4% |
| 20250316194929_jpg.rf.dc9dd51ef2b4819b2740ee4cae9a378e.jpg | 61196 | Florence-2 Crop | 6119652 | `.....++` | 71.4% |
| 20250316194929_jpg.rf.dc9dd51ef2b4819b2740ee4cae9a378e.jpg | 61196 | F2 Raw+Validated | 6119661 | `.....++` | 71.4% |
| 20250317141401_jpg.rf.12604c217d3b2d98432886dd6272ec94.jpg | 16T88 | Florence-2 Raw | 7864852 | `XXXX.++` | 28.6% |
| 20250317141401_jpg.rf.12604c217d3b2d98432886dd6272ec94.jpg | 16T88 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250317141401_jpg.rf.12604c217d3b2d98432886dd6272ec94.jpg | 16T88 | F2 Raw+Validated | 7864852 | `XXXX.++` | 28.6% |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | Florence-2 Raw | 6000050 | `....X++` | 57.1% |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | Florence-2 Crop | 6000030 | `....X++` | 71.4% |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | Florence-2 Bbox Crop | 600003 | `....X+` | 83.3% |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | F2 Bbox+SuperRes | 600003 | `....X+` | 83.3% |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg | 60003 | F2 Raw+Validated | 6000050 | `....X++` | 57.1% |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | Florence-2 Crop | 72019 | `XXXXX` | 0.0% |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | Florence-2 Bbox Crop | 525719 | `XXX.X+` | 16.7% |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | F2 Bbox+SuperRes | 525719 | `XXX.X+` | 16.7% |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg | 61473 | F2 Raw+Validated | 917989 | `X.XXX+` | 16.7% |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | Florence-2 Raw | 2333232 | `.X..X++` | 57.1% |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | Florence-2 Crop | 3323232 | `XXX.X++` | 28.6% |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | F2 Bbox+SuperRes | 2357027 | `.XXXX++` | 14.3% |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg | 28333 | F2 Raw+Validated | 2333232 | `.X..X++` | 57.1% |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | Florence-2 Raw | - | `-----` | 0.0% |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | Florence-2 Crop | - | `-----` | 0.0% |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | Florence-2 Bbox Crop | 2256909 | `XXXX.++` | 28.6% |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | F2 Bbox+SuperRes | 2256909 | `XXXX.++` | 28.6% |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg | 68989 | F2 Raw+Validated | 5599999 | `XX.X.++` | 28.6% |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | Florence-2 Raw | 19094 | `XXXXX` | 0.0% |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | Florence-2 Crop | 19999 | `XXXX.` | 20.0% |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg | 63769 | F2 Raw+Validated | 19094 | `XXXXX` | 0.0% |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | Florence-2 Raw | 2351238 | `..XX+++` | 28.6% |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | Florence-2 Crop | 2381238 | `..XX+++` | 28.6% |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | Florence-2 Bbox Crop | 2315008 | `..X.+++` | 42.9% |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | F2 Bbox+SuperRes | 2315008 | `..X.+++` | 42.9% |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg | 2345 | F2 Raw+Validated | 2351238 | `..XX+++` | 28.6% |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | Florence-2 Raw | 84835 | `XXXX+` | 0.0% |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | Florence-2 Crop | 16645 | `X.XX+` | 20.0% |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | Florence-2 Bbox Crop | - | `----` | 0.0% |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | F2 Bbox+SuperRes | - | `----` | 0.0% |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg | 26AM | F2 Raw+Validated | 84835 | `XXXX+` | 0.0% |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | Florence-2 Raw | 8457484 | `.XXXX++` | 28.6% |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | Florence-2 Crop | 8457484 | `.XXXX++` | 28.6% |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg | 86218 | F2 Raw+Validated | 8457484 | `.XXXX++` | 28.6% |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | Florence-2 Raw | 22019 | `XXXXX` | 0.0% |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | Florence-2 Crop | - | `-----` | 0.0% |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | Florence-2 Bbox Crop | 1251219 | `XXXXX++` | 14.3% |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | F2 Bbox+SuperRes | 1251219 | `XXXXX++` | 14.3% |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg | 85338 | F2 Raw+Validated | 22019 | `XXXXX` | 0.0% |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | Florence-2 Raw | 6121561 | `.....++` | 71.4% |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | Florence-2 Crop | 6121561 | `.....++` | 71.4% |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | Florence-2 Bbox Crop | 6121553 | `.....++` | 71.4% |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | F2 Bbox+SuperRes | 6121553 | `.....++` | 71.4% |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg | 61215 | F2 Raw+Validated | 6121561 | `.....++` | 71.4% |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | Florence-2 Raw | 19989 | `XX.XX` | 20.0% |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | Florence-2 Crop | - | `-----` | 0.0% |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg | 53934 | F2 Raw+Validated | 19989 | `XX.XX` | 20.0% |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | Florence-2 Raw | 6159261 | `.....++` | 71.4% |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | Florence-2 Crop | 6159261 | `.....++` | 71.4% |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | Florence-2 Bbox Crop | 6159255 | `.....++` | 71.4% |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | F2 Bbox+SuperRes | 6159253 | `.....++` | 71.4% |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg | 61592 | F2 Raw+Validated | 6159261 | `.....++` | 71.4% |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | Florence-2 Raw | 6749067 | `.X.X.++` | 42.9% |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | Florence-2 Crop | 8614305 | `XXXXX++` | 71.4% |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | Florence-2 Bbox Crop | 6143053 | `.....++` | 71.4% |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | F2 Bbox+SuperRes | 6143053 | `.....++` | 71.4% |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg | 61430 | F2 Raw+Validated | 6749067 | `.X.X.++` | 42.9% |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | Florence-2 Raw | 6147614 | `...XX++` | 57.1% |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | Florence-2 Crop | 1457614 | `XXXXX++` | 28.6% |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | Florence-2 Bbox Crop | 6146753 | `.....++` | 71.4% |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | F2 Bbox+SuperRes | 6146753 | `.....++` | 71.4% |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg | 61467 | F2 Raw+Validated | 6147614 | `...XX++` | 57.1% |
| screenshot_2025-04-02_17-06-26_jpg.rf.e0260f3c5493b3e03ef3a13e6006a154.jpg | 61482 | Florence-2 Raw | 4962559 | `XXXXX++` | 14.3% |
| screenshot_2025-04-02_17-06-26_jpg.rf.e0260f3c5493b3e03ef3a13e6006a154.jpg | 61482 | Florence-2 Crop | 14826 | `XXXXX` | 60.0% |
| screenshot_2025-04-02_17-06-26_jpg.rf.e0260f3c5493b3e03ef3a13e6006a154.jpg | 61482 | F2 Raw+Validated | 4962559 | `XXXXX++` | 14.3% |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg | 11165 | F2 Raw+Validated | 5051051 | `XXXXX++` | 28.6% |
| screenshot_2025-04-03_19-40-58_jpg.rf.9640da77089a24983c9c16e089258eaa.jpg | 68931 | Florence-2 Raw | 6893168 | `.....++` | 71.4% |
| screenshot_2025-04-03_19-40-58_jpg.rf.9640da77089a24983c9c16e089258eaa.jpg | 68931 | Florence-2 Crop | 6093160 | `.X...++` | 57.1% |
| screenshot_2025-04-03_19-40-58_jpg.rf.9640da77089a24983c9c16e089258eaa.jpg | 68931 | F2 Raw+Validated | 6893168 | `.....++` | 71.4% |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | Florence-2 Raw | 5859585 | `XXX.X++` | 14.3% |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | Florence-2 Bbox Crop | 000007 | `XXXX.+` | 16.7% |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | F2 Bbox+SuperRes | 000007 | `XXXX.+` | 16.7% |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg | 69490 | F2 Raw+Validated | 5859585 | `XXX.X++` | 14.3% |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | Florence-2 Raw | 9595095 | `XXXXX++` | 0.0% |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | Florence-2 Bbox Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | F2 Bbox+SuperRes | - | `-----` | 0.0% |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg | 23238 | F2 Raw+Validated | 9595095 | `XXXXX++` | 0.0% |
| screenshot_2025-04-04_08-29-00_jpg.rf.80a924315f4041b18eec6437c45c61e9.jpg | 17418 | Florence-2 Raw | - | `-----` | 0.0% |
| screenshot_2025-04-04_08-29-00_jpg.rf.80a924315f4041b18eec6437c45c61e9.jpg | 17418 | Florence-2 Crop | - | `-----` | 0.0% |
| screenshot_2025-04-04_08-29-00_jpg.rf.80a924315f4041b18eec6437c45c61e9.jpg | 17418 | F2 Raw+Validated | 7187871 | `XXXX.++` | 28.6% |
| screenshot_2025-04-04_11-00-31_jpg.rf.f4066dc0086504ef3d4c23b70eb68752.jpg | 61344 | Florence-2 Raw | 8134613 | `X...X++` | 42.9% |
| screenshot_2025-04-04_11-00-31_jpg.rf.f4066dc0086504ef3d4c23b70eb68752.jpg | 61344 | Florence-2 Crop | 6134461 | `.....++` | 71.4% |
| screenshot_2025-04-04_11-00-31_jpg.rf.f4066dc0086504ef3d4c23b70eb68752.jpg | 61344 | F2 Raw+Validated | 8134613 | `X...X++` | 42.9% |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | Florence-2 Raw | 8149981 | `...X.++` | 57.1% |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | Florence-2 Crop | 1499811 | `XXXXX++` | 28.6% |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | Florence-2 Bbox Crop | 8140095 | `....X++` | 71.4% |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | F2 Bbox+SuperRes | 8140095 | `....X++` | 71.4% |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg | 81409 | F2 Raw+Validated | 8149981 | `...X.++` | 57.1% |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | Florence-2 Raw | 6155861 | `.....++` | 71.4% |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | Florence-2 Crop | 6560655 | `.XXXX++` | 28.6% |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | Florence-2 Bbox Crop | 6155053 | `....X++` | 57.1% |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | F2 Bbox+SuperRes | 6155053 | `....X++` | 57.1% |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg | 61558 | F2 Raw+Validated | 6155861 | `.....++` | 71.4% |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | Florence-2 Raw | 8821788 | `XXX..++` | 28.6% |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | Florence-2 Crop | 6081760 | `..X..++` | 57.1% |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | Florence-2 Bbox Crop | 175418 | `XXXXX+` | 16.7% |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | F2 Bbox+SuperRes | 6001754 | `.....++` | 71.4% |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg | 60017 | F2 Raw+Validated | 8821788 | `XXX..++` | 28.6% |
| screenshot_2025-04-07_05-45-21_jpg.rf.28492552d7f8ae9c7e81ea37472b68ee.jpg | 80876 | Florence-2 Raw | 8387688 | `.X...++` | 57.1% |
| screenshot_2025-04-07_05-45-21_jpg.rf.28492552d7f8ae9c7e81ea37472b68ee.jpg | 80876 | Florence-2 Crop | 8007680 | `..X..++` | 57.1% |
| screenshot_2025-04-07_05-45-21_jpg.rf.28492552d7f8ae9c7e81ea37472b68ee.jpg | 80876 | F2 Raw+Validated | 8387688 | `.X...++` | 57.1% |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | Florence-2 Raw | 6212682 | `.XXXX++` | 42.9% |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | Florence-2 Crop | 6021260 | `.....++` | 71.4% |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | Florence-2 Bbox Crop | 6021254 | `.....++` | 71.4% |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | F2 Bbox+SuperRes | 6021254 | `.....++` | 71.4% |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg | 60212 | F2 Raw+Validated | 6212682 | `.XXXX++` | 42.9% |

## Character Confusions (VLM)

| Predicted | Actual | Count |
|-----------|--------|-------|
| 9 | 3 | 6 |
| 1 | 6 | 4 |
| 9 | 6 | 3 |
| 2 | 8 | 3 |
| 0 | 7 | 2 |
| 4 | 9 | 2 |
| 2 | 5 | 2 |
| 0 | 3 | 2 |
| 1 | 3 | 2 |
| 9 | 8 | 2 |
| 1 | 5 | 2 |
| 8 | 3 | 2 |
| 9 | 4 | 2 |
| 7 | 6 | 1 |
| 2 | 1 | 1 |
| 0 | 4 | 1 |
| 1 | 7 | 1 |
| 9 | 7 | 1 |
| 4 | 1 | 1 |
| 8 | 4 | 1 |
| 6 | 2 | 1 |

## Per-Image Breakdown

| Image | Difficulty | GT Heat | Raw Char | Pre Char | ROI Char | Post Char | VLM Char | VLM Pre | VLM Raw | VLM Crop | F2 Raw | F2 Crop | F2 Bbox | F2 Bbox+SR | F2 Raw+Val | Ensemble | Ens V2 |
|-------|------------|---------|----------|----------|----------|-----------|----------|---------|---------|----------|--------|---------|---------|------------|------------|----------|--------|
| 20250316151241_jpg.rf.4743ea9ebc9ba623f1bb3f86a7f82e0c.jpg |  | 60731 | - | - | - | - | - | - | - | - | 57.1% | 71.4% | - | - | 57.1% | - | - |
| 20250316165933_jpg.rf.5a25ded7cc7958384aad59cd625dadb2.jpg |  | 68641 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | - | - | 71.4% | - | - |
| 20250316194929_jpg.rf.dc9dd51ef2b4819b2740ee4cae9a378e.jpg |  | 61196 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | - | - | 71.4% | - | - |
| 20250317141401_jpg.rf.12604c217d3b2d98432886dd6272ec94.jpg |  | 16T88 | - | - | - | - | - | - | - | - | 28.6% | 0.0% | - | - | 28.6% | - | - |
| 20250318040532_jpg.rf.5a0d95c3ac90ccbbc6ac7c9410e160a9.jpg |  | 60003 | - | - | - | - | - | - | - | - | 57.1% | 71.4% | 83.3% | 83.3% | 57.1% | - | - |
| 20250319061732_jpg.rf.2d5837433375fa5b6aaa412648135a96.jpg |  | 61473 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 16.7% | 16.7% | 16.7% | - | - |
| 20250320045606_jpg.rf.6c031f71a2039b3dfbde5d294f4a1c42.jpg |  | 28333 | - | - | - | - | - | - | - | - | 57.1% | 28.6% | 0.0% | 14.3% | 57.1% | - | - |
| 20250320165326_jpg.rf.8236b4d1749df5f2fdf0eea81df0bb6f.jpg |  | 68989 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 28.6% | 28.6% | 28.6% | - | - |
| 20250321142707_jpg.rf.a37d6ce6712bcae3b16fa9777ab6029b.jpg |  | 63769 | - | - | - | - | - | - | - | - | 0.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| 202503281446340726_jpg.rf.a6e95c44ba1d6d1ce15461060e2eec1e.jpg |  | 2345 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | 42.9% | 42.9% | 28.6% | - | - |
| 202503281919417768_jpg.rf.6d9f43d892f0ebbc68214b4cf2b45fd4.jpg |  | 26AM | - | - | - | - | - | - | - | - | 0.0% | 20.0% | 0.0% | 0.0% | 0.0% | - | - |
| 202503290756039305_jpg.rf.e57c80c6527140cc64a21ee9573db2ed.jpg |  | 86218 | - | - | - | - | - | - | - | - | 28.6% | 28.6% | 0.0% | 0.0% | 28.6% | - | - |
| 202503300048465184_jpg.rf.b0c954ce701fd2d48a8c3c73e19a7536.jpg |  | 85338 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 14.3% | 14.3% | 0.0% | - | - |
| 202503300207515435_jpg.rf.a264e295527701f444c6a1682d2ff8f1.jpg |  | 61215 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | 71.4% | 71.4% | 71.4% | - | - |
| 202503312109477150_jpg.rf.3036b2a7284e3fdce90ee0668293d1bf.jpg |  | 53934 | - | - | - | - | - | - | - | - | 20.0% | 0.0% | 0.0% | 0.0% | 20.0% | - | - |
| 202504010149466243_jpg.rf.071f3435d7b34ecf8bab38bde9db89c7.jpg |  | 61592 | - | - | - | - | - | - | - | - | 71.4% | 71.4% | 71.4% | 71.4% | 71.4% | - | - |
| 202504010501322714_jpg.rf.b4ef69556ff49628c345e9666787970f.jpg |  | 61430 | - | - | - | - | - | - | - | - | 42.9% | 71.4% | 71.4% | 71.4% | 42.9% | - | - |
| 202504011107581787_jpg.rf.f22d0a70f552c2febbde741279e45fc3.jpg |  | 61467 | - | - | - | - | - | - | - | - | 57.1% | 28.6% | 71.4% | 71.4% | 57.1% | - | - |
| screenshot_2025-04-02_17-06-26_jpg.rf.e0260f3c5493b3e03ef3a13e6006a154.jpg |  | 61482 | - | - | - | - | - | - | - | - | 14.3% | 60.0% | - | - | 14.3% | - | - |
| screenshot_2025-04-03_14-40-30_jpg.rf.e786ec197c9e9c5fded9c1fc1915c685.jpg |  | 11165 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 28.6% | - | - |
| screenshot_2025-04-03_19-40-58_jpg.rf.9640da77089a24983c9c16e089258eaa.jpg |  | 68931 | - | - | - | - | - | - | - | - | 71.4% | 57.1% | - | - | 71.4% | - | - |
| screenshot_2025-04-04_05-33-54_jpg.rf.5de152bf6f68816e4fa593e672430bb7.jpg |  | 69490 | - | - | - | - | - | - | - | - | 14.3% | 0.0% | 16.7% | 16.7% | 14.3% | - | - |
| screenshot_2025-04-04_05-51-16_jpg.rf.e7b954733c55a7f44fa05646ea94fabc.jpg |  | 23238 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | - | - |
| screenshot_2025-04-04_08-29-00_jpg.rf.80a924315f4041b18eec6437c45c61e9.jpg |  | 17418 | - | - | - | - | - | - | - | - | 0.0% | 0.0% | - | - | 28.6% | - | - |
| screenshot_2025-04-04_11-00-31_jpg.rf.f4066dc0086504ef3d4c23b70eb68752.jpg |  | 61344 | - | - | - | - | - | - | - | - | 42.9% | 71.4% | - | - | 42.9% | - | - |
| screenshot_2025-04-04_11-55-00_jpg.rf.3040ce12d2073fcac126cfb636d186a5.jpg |  | 81409 | - | - | - | - | - | - | - | - | 57.1% | 28.6% | 71.4% | 71.4% | 57.1% | - | - |
| screenshot_2025-04-04_18-38-47_jpg.rf.0ec080c2b8aaae62f4fa928642467bc6.jpg |  | 61558 | - | - | - | - | - | - | - | - | 71.4% | 28.6% | 57.1% | 57.1% | 71.4% | - | - |
| screenshot_2025-04-06_02-41-38_jpg.rf.c8314992f06510da1ac3d19636011df2.jpg |  | 60017 | - | - | - | - | - | - | - | - | 28.6% | 57.1% | 16.7% | 71.4% | 28.6% | - | - |
| screenshot_2025-04-07_05-45-21_jpg.rf.28492552d7f8ae9c7e81ea37472b68ee.jpg |  | 80876 | - | - | - | - | - | - | - | - | 57.1% | 57.1% | - | - | 57.1% | - | - |
| screenshot_2025-04-07_07-31-20_jpg.rf.ad56d1fbcae227c65664ea68f24c53c1.jpg |  | 60212 | - | - | - | - | - | - | - | - | 42.9% | 71.4% | 71.4% | 71.4% | 42.9% | - | - |

---
*Generated by `scripts/benchmark.py`.*