# BASELINE_RESULTS — first honest 10-item calibration baseline (B123)

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
