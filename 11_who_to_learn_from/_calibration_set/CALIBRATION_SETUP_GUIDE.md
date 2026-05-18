# Calibration Setup Guide

Before Claude Code extracts a single real corpus record, it must prove it can extract correctly. This guide walks through building the calibration set.

## What you need

10 pieces of content you know well. Save them to `_calibration_set/content/` as `item_01.jpg` through `item_10.jpg` (or `.png`, `.mp4` for video).

## The 10 items

| Item | What to pick | Why |
|---|---|---|
| item_01 | A post with correct qahwa service (everything right) | Positive control — baseline |
| item_02 | **A post with a LEFT-HAND SERVING violation** | **Critical negative control** |
| item_03 | A video with clear pacing you can describe | Tests video observation |
| item_04 | A post from a different sector than items 01-03 | Tests cross-sector extraction |
| item_05 | A post with Arabic caption (Najdi or Hejazi dialect) | Tests dialect detection |
| item_06 | A post with bilingual text overlay | Tests voice observation |
| item_07 | A post during Ramadan or Eid | Tests occasion detection |
| item_08 | A high-production professional shoot | Tests quality assessment |
| item_09 | A UGC-style post | Tests quality range |
| item_10 | A post with another forbidden-list violation (not left-hand) | Second compliance test |

item_02 is the most important. If Claude Code cannot detect a left-hand serving violation, the entire extraction pipeline is unreliable. Everything stops until this is fixed.

## How to fill GROUND_TRUTH.yaml

1. Open `_calibration_set/GROUND_TRUTH.yaml`
2. For each item, fill in what YOU see — not what you think Claude Code should see
3. Leave fields `null` when you are genuinely uncertain
4. Be honest about `expected_compliance` — if it is clean, say clean; if it has a hard block, name the specific entry from the forbidden list
5. Set `date_filled` to today's date

**Do NOT show GROUND_TRUTH.yaml to Claude Code before extraction is complete.** The test only works if Claude Code extracts blind.

## Running the calibration

After Claude Code extracts all 10 items:

```bash
python3 scripts/test_extraction_accuracy.py
```

### Pass criteria

| Level | What it checks | Threshold |
|---|---|---|
| Level 1 | item_02 triggers `hard_blocks_triggered` with `left_hand_serving` | **Must pass** |
| Level 2 | Required fields present across all items | 80% completeness |
| Level 3 | Field values match ground truth | 60% accuracy |

### If Level 1 fails

**STOP.** Do not proceed to real extraction. Fix the extraction prompt, re-run calibration. The corpus cannot be trusted if hard blocks are not detected.

### If Level 2 or 3 fails

Review which fields are consistently wrong. Adjust the extraction prompt for those specific fields. Re-run calibration on the same 10 items.

## After calibration passes

Proceed to real extraction following START_HERE_EXTRACTION.md Step 6.
