# BASELINE_RESULTS — 10-item calibration baseline (B123)

> ⚠️ **2026-06-19 numbers below are SUPERSEDED.** Live grader now PASSES — see the
> 2026-06-30 re-measure section directly under this note. The 🔴 FAIL table further down
> is preserved as history (the root-cause analysis still holds), not as current state.

## 2026-06-30 RE-MEASURE (RABIE orchestra shift) — live grader, current state

Grader: `scripts/test_extraction_accuracy.py`. B130 gate (`data/extraction_accuracy_gate.json`)
confirms: `exit_code: 0`, `level1_passed: true`, `completeness: 1.0`, `accuracy: 0.9166`.

| Level | What it checks | Threshold | MEASURED (2026-06-30) | Verdict |
|-------|----------------|-----------|-----------------------|---------|
| **L1 — hard-block detection** | item_02 must trigger `left_hand_serving` | must pass | **detected** | 🟢 **pass** |
| L2 — field completeness | required fields present across 10 items | ≥ 80% | **100.0%** | 🟢 pass |
| L3 — field accuracy | field values match ground truth | ≥ 60% | **91.7%** | 🟢 pass |

### Why L1 now passes — and the honest caveat (do NOT over-claim the moat — Rule #12/#9)

L1 flipped 🔴→🟢 because of **B125's conservative fail-safe** in `extract_calibration_item.py`
(hand-on-food read as left OR uncertain → `hard_block`), NOT because the vision eye got
smarter. The eye still misreads handedness (the 2026-06-11 extraction called item_02's left
hand "right"); the fail-safe blocks anyway. So:

- **The moat is NOT yet proven by perception** — it passes structurally, by blocking the
  ambiguous case. A smarter eye is still owed.
- **False-block rate is still UNMEASURED.** A fail-safe that blocks "left OR uncertain" will
  also block legitimate right-hand-on-food content. There is NO clean right-hand-on-food
  control in the set to catch that over-block. **B126** (3–5 unambiguous left-hand-serving
  frames) + a clean right-hand-on-food control remain required before trusting this pass.
- **The set is still too thin** — one negative control (item_02) cannot prove a moat.

Open blockers (both gated, staged for Mohamed): (1) a **2nd funded vision model** for an
independent orientation vote (Anthropic dry, Gemini exhausted); (2) sourcing the B126 control
frames. Until then the green above means "the gate bites on the one control we have," not
"the eye is reliable."

---

## HISTORY — 2026-06-19 baseline (SUPERSEDED, kept for the root-cause analysis)

Recorded: 2026-06-19 (RABIE orchestra shift). Measured numbers, not feelings.
Grader: `scripts/test_extraction_accuracy.py` over `claude_extractions/item_01..10`.
Extractions: GPT-4o vision, dated 2026-06-11 (provenance.confidence = experimental).

## The measured numbers

| Level | What it checks | Threshold | MEASURED | Verdict |
|-------|----------------|-----------|----------|---------|
| **L1 — hard-block detection** | item_02 must trigger `left_hand_serving` | must pass | **NOT detected** | 🔴 **FAIL** |
| L2 — field completeness | required fields present across 10 items | ≥ 80% | **100.0%** | 🟢 pass |
| L3 — field accuracy | field values match ground truth | ≥ 60% | **83.3%** | 🟢 pass |

Grader exit at L1 (code 1) — it refuses to proceed past the moat failure (Rule #8, correct).

## Root cause (root-hunt, not symptom)

item_02 is the negative control: a left-hand-serving violation (ground truth = LEFT hand,
dorsal view, wrist-from-left, thumb-down toward food — see CRITICAL_FINDING_item_02.md).

The extraction itself reports:
```
hands_analysis: [{ which_hand: "right", reasoning: "thumb on the left side, fingers on
                   the right, palm facing down" }]
compliance_check: { hard_blocks_triggered: [], overall_compliance: "clean" }
```

The vision model **misclassified the hand orientation** (called a left hand "right"), so no
hard block fired. This is upstream of every gate — the gate logic is fine; the EYE is wrong.

## The honest read (do not let the green numbers lie)

L2 = 100% and L3 = 83% make the system look healthy. It is not. **Every single L3 miss is
item_02** (compliance clean-vs-hard_blocked, composition style) — the same one violation.
The system is field-complete and field-accurate on everything that DOESN'T matter, and
**0% on the one test that defines the product** (catching a cultural red-line the eye must
never miss). A 9/10-clean set proves nothing; the moat is the 1 negative control, and it loses.

## What this does NOT authorize

Per Rule #12, the fix is NOT hand-editing item_02's extraction to say "left." The machine
must produce the correct call. Machine-fix direction (separate step, needs eyes + likely
Mohamed's go): force explicit hand-orientation reasoning in the extraction prompt
(wrist-entry side + thumb position → handedness, stated before the compliance call), and/or
add a second-pass orientation check. Then RE-RUN this grader. Baseline re-measure required
before any "fixed" claim (Rule #9).

## Negative-control set is too thin (links to B126)

One borderline frame cannot prove a moat. B126 (expand negative-control set: 3–5 unambiguous
left-hand-serving frames + GROUND_TRUTH entries) should land before trusting any L1 pass.
