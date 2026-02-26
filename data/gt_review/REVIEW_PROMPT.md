# Steel Billet OCR Ground Truth Review

## YOUR ROLE
You are an expert ground truth reviewer for a steel billet OCR dataset. Your job is to look at each crop image, read the stamped/painted numbers on the billet end face, and verify or correct the VLM-generated labels in the JSON.

**ACCURACY IS EVERYTHING.** This ground truth will be used to fine-tune an OCR model. Wrong labels = catastrophic model failure. We already lost weeks because of noisy labels. Be precise.

---

## WHAT YOU ARE LOOKING AT

Each image shows the END FACE of a steel billet (a square cross-section of a steel bar). The numbers are painted in WHITE paint stencil on the grey/dark steel surface.

### Stamp Layout (when right-side-up):
```
┌─────────────┐
│             │
│   XXXXX     │  ← TOP LINE: HEAT NUMBER (5 digits, e.g., 60386, 81451, 60982)
│   XXXX      │  ← BOTTOM LINE: SEQUENCE NUMBER (4 digits, e.g., 5314, 5342)
│             │
└─────────────┘
```

### Number Format Rules:
- **Heat number**: Almost always exactly 5 digits (e.g., 60386, 81451, 60982, 59608, 68447)
- **Sequence number**: Almost always exactly 4 digits (e.g., 5314, 5342, 5383)
- **Characters are DIGITS ONLY (0-9)**. The only exception is a trailing "Y" on some sequences (e.g., "5342Y", "5332Y")
- **Letters like A, E, F, H, J, K, M, N, P, R, S, T, V, W in the readings are HALLUCINATIONS** from the VLM struggling with blurry/inverted text

### Critical Physical Constraint:
**ALL billets from the SAME source image share the SAME heat number.** They are from the same steel melt/batch. Only the sequence number differs between billets. This is a hard manufacturing constraint — use it to cross-check readings.

---

## KNOWN ISSUES IN THIS DATASET

### 1. UPSIDE-DOWN BILLETS (crane-lifted)
Some images show billets being lifted by an overhead crane. The billet faces are UPSIDE DOWN. When text is inverted 180 degrees:
- Digits "0", "1", "8" look similar upside down
- "6" upside down looks like "9" and vice versa
- "2" upside down can look like a "Z" or "S"
- "5" upside down can look like a "S" or "2"
- The VLM often reads upside-down digits as LETTERS (this is the #1 source of letter hallucinations)

**Affected groups (confirmed upside-down from source images):**
- **billet_14**: ALL crops are upside down. All VLM readings contain letters (NFW, 4F81, VEL, HF11, etc.) — these are upside-down digits
- **billet_21**: ALL crops are upside down. Heat number is actually **59608** for all billets (visible in source image)

### 2. VERY LOW RESOLUTION CROPS
Some bboxes are only 50-60px wide, producing tiny crops:
- **billet_05**: 15 crops from a distant surveillance camera. Most are very blurry
- **billet_28**: 9 crops, ALL completely unreadable (conf=0.05). Mark as "?????"

### 3. SWAPPED HEAT/SEQUENCE
For upside-down billets, the VLM sometimes reads the bottom line first and puts it in heat_number. If you see a 5-digit number in the sequence field and a 4-digit number in the heat_number field, they may be swapped.

---

## REVIEW INSTRUCTIONS

For EACH entry in the JSON, follow this process:

### Step 1: Find the crop image
- Match `review_name` to the filename: `crops/{review_name}.jpg`
- For full-image entries (no crop_path), use the source: `sources/{review_name}.jpg`

### Step 2: Read the numbers
- Look at the actual image carefully
- If the billet face is upside down, mentally rotate 180 degrees
- Top line = heat number, bottom line = sequence

### Step 3: Apply corrections using these rules:

| Situation | Action |
|-----------|--------|
| VLM reading matches image | Set `"verified": true` |
| VLM reading is wrong but you can read the text | Correct `heat_number`/`sequence`, set `"verified": true`, add correction note |
| Some digits unclear but readable in context | Use best guess, note which digits were uncertain |
| Same heat as sibling billets but digit is blurry | Use the sibling heat number, note `"inferred from siblings"` |
| Completely unreadable | Set `"heat_number": "?????"`, `"sequence": "????"`, `"verified": true`, `"notes": "unreadable"` |
| Partially readable | Use `?` for unclear digits: `"6?386"`, `"53?4"` |
| Letters in reading (except trailing Y) | These are hallucinations — correct to digits or `?` |

### Step 4: Cross-check siblings
After reviewing all crops from one source image:
- Confirm ALL share the same heat number
- If one crop disagrees, it's likely a misread — correct it

---

## CURRENT VLM READINGS (what you are reviewing)

Here is every entry, grouped by source image. Your job is to verify/correct each one.

### billet_01 (1 entry, full-image, no crop)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_01 | 68301 | 5372Y | 0.72 | Check if Y is real |

### billet_02 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_02 | 68514 | 5334 | 0.85 | Likely correct |

### billet_03 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_03 | 64322 | M2527 | 0.62 | "M" in sequence is suspicious |

### billet_04 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_04 | 68447 | 5314 | 0.82 | Source shows 68447 clearly on many billets |

### billet_05 (15 crops — LOW QUALITY, distant camera)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_05_crop00 | ?0?1 | ??? | 0.15 | Mostly unreadable |
| billet_05_crop01 | ????? | ???? | 0.05 | Unreadable |
| billet_05_crop02 | 60659 | 1119 | 0.35 | Low conf, verify |
| billet_05_crop03 | ????? | ???? | 0.05 | Unreadable |
| billet_05_crop04 | M125 | 1319 | 0.52 | "M" = hallucination |
| billet_05_crop05 | 84025 | 1131 | 0.35 | Low conf |
| billet_05_crop06 | ????? | ???? | 0.05 | Unreadable |
| billet_05_crop07 | M76 | 1410 | 0.42 | "M" = hallucination |
| billet_05_crop08 | ????? | 1406 | 0.25 | Heat unreadable |
| billet_05_crop09 | A138 | L130 | 0.30 | Letters = hallucination |
| billet_05_crop10 | W166 | 8845 | 0.35 | "W" = hallucination |
| billet_05_crop11 | 54145 | 1319 | 0.42 | Low conf |
| billet_05_crop12 | 44876 | 11619 | 0.30 | Seq too long (5 digits) |
| billet_05_crop13 | 94225 | 1187 | 0.35 | Low conf |
| billet_05_crop14 | 84175 | LE19 | 0.35 | "LE" = hallucination |
**NOTE**: All 15 billets should share ONE heat number. If any are readable, use it for all.

### billet_06 (10 crops — MEDIUM QUALITY)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_06_crop00 | 72RIM | 01H0 | 0.30 | Letters everywhere |
| billet_06_crop01 | 25148 | 8143 | 0.52 | |
| billet_06_crop02 | 23014 | 5143 | 0.35 | |
| billet_06_crop03 | 25254 | 01410 | 0.52 | Seq 5 digits |
| billet_06_crop04 | 52134 | 6169 | 0.55 | |
| billet_06_crop05 | 25937 | R1418 | 0.72 | "R" in seq |
| billet_06_crop06 | 25014 | P1018 | 0.35 | "P" in seq |
| billet_06_crop07 | 21510 | P110 | 0.52 | "P" in seq |
| billet_06_crop08 | 25114 | P1610 | 0.62 | "P" in seq |
| billet_06_crop09 | 25314 | P1I0 | 0.45 | "P","I" in seq |
**NOTE**: All should share ONE heat number. Many different readings — most are likely wrong. Check source image.

### billet_07 (6 crops)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_07_crop00 | A1187 | 3524 | 0.72 | "A" likely "8" → 81187 |
| billet_07_crop01 | 81187 | 3554 | 0.72 | |
| billet_07_crop02 | 81787 | 5344 | 0.72 | 81787 or 81187? |
| billet_07_crop03 | 81187 | 3? | 0.72 | Seq incomplete |
| billet_07_crop04 | 81187 | 5542 | 0.85 | |
| billet_07_crop05 | 31187 | 5532 | 0.75 | "3" likely "8" → 81187 |
**NOTE**: Heat is almost certainly **81187** for all. A→8, 3→8, 81787→81187 corrections.

### billet_08 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_08 | ? | ? | 0.05 | Completely unreadable |

### billet_09 (12 crops — HIGH QUALITY, reliable)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_09_crop00 | 81451 | 5174 | 0.85 | |
| billet_09_crop01 | 81451 | 5154 | 0.85 | |
| billet_09_crop02 | 81451 | 5164 | 0.85 | |
| billet_09_crop03 | 81451 | 51184 | 0.82 | Seq 5 digits — should be 4 |
| billet_09_crop04 | 81451 | 5173 | 0.85 | |
| billet_09_crop05 | 81451 | 5453 | 0.88 | Seq pattern breaks (5453 vs 51XX) |
| billet_09_crop06 | 81451 | 5163 | 0.85 | |
| billet_09_crop07 | 81451 | 5183 | 0.85 | |
| billet_09_crop08 | 81451 | 5113 | 0.95 | |
| billet_09_crop09 | 81451 | 5132 | 0.95 | |
| billet_09_crop10 | 81451 | 5142 | 0.90 | |
| billet_09_crop11 | 81451 | 5112 | 0.95 | |
**NOTE**: Heat **81451** is consistent and highly confident. Verify sequences — crop03 has extra digit (51184→5184?), crop05 seq pattern differs.

### billet_10 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_10 | 68541 | 5382 | 0.82 | |

### billet_11 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_11 | 61464 | 5212 | 0.88 | |

### billet_12 (8 crops — note "J" and "Y" in sequences)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_12_crop00 | 61056 | 4J82Y | 0.82 | Is "J" a real char or misread? |
| billet_12_crop01 | 61056 | 4J13Y | 0.82 | |
| billet_12_crop02 | 61056 | 4J72Y | 0.72 | |
| billet_12_crop03 | 61856 | 4J62Y | 0.82 | Heat 61856 vs 61056 |
| billet_12_crop04 | 61056 | 4J63Y | 0.72 | |
| billet_12_crop05 | 61056 | 4J42Y | 0.82 | |
| billet_12_crop06 | 61056 | 4J251 | 0.72 | Different seq format |
| billet_12_crop07 | 61856 | 4J53Y | 0.82 | Heat 61856 vs 61056 |
**NOTE**: Heat should be ONE value — is it 61056 or 61856? 6→8 confusion. The "J" and "Y" in sequences are unusual — check images carefully.

### billet_13 (4 crops — HIGH QUALITY, most reliable group)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_13_crop00 | 60386 | 5314 | 0.95 | |
| billet_13_crop01 | 60386 | 5334 | 0.88 | |
| billet_13_crop02 | 60386 | 5384 | 0.92 | |
| billet_13_crop03 | 60386 | 5364 | 0.92 | |
**NOTE**: Very high confidence. Heat **60386** consistent. Likely all correct.

### billet_14 (8 crops — UPSIDE DOWN, all letter hallucinations)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_14_crop00 | NFW | 89838 | 0.45 | UPSIDE DOWN |
| billet_14_crop01 | 9797 | 88838 | 0.55 | UPSIDE DOWN |
| billet_14_crop02 | 4F81 | R8838 | 0.52 | UPSIDE DOWN |
| billet_14_crop03 | 75P | 80838 | 0.55 | UPSIDE DOWN |
| billet_14_crop04 | 4T21 | 88838 | 0.72 | UPSIDE DOWN |
| billet_14_crop05 | 4111 | 80838 | 0.62 | UPSIDE DOWN |
| billet_14_crop06 | VEL | 88038 | 0.52 | UPSIDE DOWN |
| billet_14_crop07 | HF11 | 88838 | 0.55 | UPSIDE DOWN |
**NOTE**: ALL upside down. All heat numbers are letter hallucinations. Mentally rotate 180 degrees. Sequence numbers also need rotation. All should share one heat number.

### billet_15 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_15 | 16588 | 8982 | 0.55 | Low conf |

### billet_16 (10 crops — GOOD QUALITY)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_16_crop00 | 2 | Y | 0.25 | Edge crop, mostly cut off |
| billet_16_crop01 | 69982 | 5342Y | 0.85 | 69982 or 60982? |
| billet_16_crop02 | 60982 | 5332Y | 0.90 | |
| billet_16_crop03 | 60982 | 5382Y | 0.88 | |
| billet_16_crop04 | 68982 | 5331Y | 0.88 | 68982 or 60982? |
| billet_16_crop05 | 68982 | 5381Y | 0.82 | 68982 or 60982? |
| billet_16_crop06 | 60982 | 5361Y | 0.88 | |
| billet_16_crop07 | 60982 | 5311Y | 0.90 | |
| billet_16_crop08 | 60982 | 5321Y | 0.85 | |
| billet_16_crop09 | 60982 | 5351Y | 0.88 | |
**NOTE**: Heat is almost certainly **60982** (6 readings agree). Crop00 is edge-cut. 69982/68982 are likely 60982 with 9→0 or 8→0 digit confusion. The "Y" suffix appears consistent across all sequences.

### billet_17 (8 crops — GOOD QUALITY)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_17_crop00 | 60988 | 5384 | 0.85 | |
| billet_17_crop01 | 60988 | 5373 | 0.88 | |
| billet_17_crop02 | 60988 | 5353 | 0.88 | |
| billet_17_crop03 | 69988 | 5313 | 0.90 | 69988→60988? |
| billet_17_crop04 | 60988 | 5372 | 0.95 | |
| billet_17_crop05 | 60988 | 5322 | 0.92 | |
| billet_17_crop06 | 60988 | 5342 | 0.95 | |
| billet_17_crop07 | 60988 | 5371 | 0.85 | |
**NOTE**: Heat is almost certainly **60988** (7 agree). Crop03 has 69988 — likely 6→9 confusion.

### billet_18 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_18 | 81052 | 5382 | 0.82 | |

### billet_19 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_19 | 61258 | 5352 | 0.85 | |

### billet_20 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_20 | 15578 | 848827 | 0.35 | Seq way too long. Very low conf. |

### billet_21 (8 crops — UPSIDE DOWN, heat=59608 confirmed from source)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_21_crop00 | 41254 | 59608 | 0.75 | UPSIDE DOWN. Heat/seq likely SWAPPED. Real heat=59608 |
| billet_21_crop01 | 42E5 | 80695 | 0.45 | UPSIDE DOWN. Letters=hallucination |
| billet_21_crop02 | 4EE3 | 59688 | 0.52 | UPSIDE DOWN |
| billet_21_crop03 | 59608 | 5342 | 0.55 | Heat=59608 looks correct. Verify seq. |
| billet_21_crop04 | ELES | 59608 | 0.62 | UPSIDE DOWN. Real heat=59608 |
| billet_21_crop05 | E5E5 | 59688 | 0.45 | UPSIDE DOWN |
| billet_21_crop06 | 59608 | 5383 | 0.85 | Heat=59608 correct. Clear reading. |
| billet_21_crop07 | 85 | 5906 | 0.45 | UPSIDE DOWN, truncated |
**NOTE**: Source image CONFIRMS heat = **59608** for ALL billets. I verified this from the full image. Many crops have the heat/seq swapped because VLM read bottom-to-top on inverted billets. The sequences visible in the source image include: 5382, 5353, 5374, 5344, 5324, 5314.

### billet_22 (4 crops)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_22_crop00 | 2323 | 60439 | 0.55 | Heat only 4 digits. Seq 5 digits. Likely swapped? |
| billet_22_crop01 | 7453 | 65409 | 0.62 | |
| billet_22_crop02 | 5362 | 6045 | 0.72 | |
| billet_22_crop03 | 5322 | 60409 | 0.82 | |
**NOTE**: All should share one heat number. The readings are very inconsistent — check source image carefully. May be upside down or have swapped heat/seq.

### billet_23 (4 crops)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_23_crop00 | 45047 | 5323 | 0.55 | |
| billet_23_crop01 | 00524 | 1553 | 0.45 | Heat starts with 00? Unusual |
| billet_23_crop02 | 45400 | 5832 | 0.55 | |
| billet_23_crop03 | 84084 | 327 | 0.55 | Seq only 3 digits |
**NOTE**: All should share one heat number. Very inconsistent — most are likely wrong.

### billet_24 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_24 | 81398 | 5344Y | 0.82 | |

### billet_25 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_25 | 47478 | 8265 | 0.45 | Low conf |

### billet_26 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_26 | 81388 | 5342 | 0.82 | |

### billet_27 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_27 | 84534 | 58857 | 0.42 | Seq 5 digits |

### billet_28 (9 crops — ALL UNREADABLE)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_28_crop00-08 | ????? | ???? | 0.05 | ALL completely unreadable |
**NOTE**: All 9 crops are dark/blurry with no visible text. Set all to ????? / ???? / verified:true / notes:"unreadable"

### billet_29 (8 crops)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_29_crop00 | 84984 | 8753 | 0.55 | |
| billet_29_crop01 | 84008 | 5757 | 0.45 | |
| billet_29_crop02 | 84900 | 3852 | 0.72 | |
| billet_29_crop03 | 60008 | 5379 | 0.75 | |
| billet_29_crop04 | 84908 | 4152 | 0.75 | |
| billet_29_crop05 | 89048 | 5323 | 0.85 | |
| billet_29_crop06 | 84008 | 5393 | 0.75 | |
| billet_29_crop07 | 84068 | 5853 | 0.55 | |
**NOTE**: All should share one heat number. Very inconsistent — check source image.

### billet_30 (1 entry, full-image)
| review_name | heat | seq | conf | issues |
|---|---|---|---|---|
| billet_30 | ST886 | S0A7 | 0.45 | ALL LETTERS. Likely upside down or completely misread |

---

## OUTPUT FORMAT

Return the complete updated JSON. For each entry you modify, update these fields:
- `"heat_number"`: corrected value (or "?????" if unreadable)
- `"sequence"`: corrected value (or "????" if unreadable)
- `"verified"`: set to `true`
- `"notes"`: brief description of what you changed and why
- `"all_text"`: update to match corrected values

**DO NOT** modify: `review_name`, `image`, `bbox_index`, `bbox`, `vlm_confidence`, `crop_path`

Example correction:
```json
{
  "review_name": "billet_07_crop00",
  "heat_number": "81187",          // was "A1187"
  "sequence": "3524",
  "verified": true,
  "notes": "A→8 correction, heat confirmed from sibling billets"
}
```

Example unreadable:
```json
{
  "review_name": "billet_28_crop00",
  "heat_number": "?????",
  "sequence": "????",
  "verified": true,
  "notes": "unreadable"
}
```

---

## FINAL CHECKLIST

Before submitting your review:
- [ ] Every entry has `"verified": true`
- [ ] Every multi-crop group has consistent heat numbers (or "?" for unreadable)
- [ ] No letters in heat_number or sequence (except trailing "Y" on sequences where visually confirmed)
- [ ] No sequence numbers longer than 5 characters
- [ ] All corrections noted in "notes" field
- [ ] "all_text" updated to match corrected heat/sequence values
