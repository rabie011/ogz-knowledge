# 🔴 CRITICAL FINDING — item_02 (left-hand serving negative control)

**Date:** 2026-06-11
**Run by:** Claude Code (Abraham session)
**Status:** ❌ **LEVEL 1 FAILED** — the compliance moat did NOT detect the violation.
**Decision pending:** escalated to Mohamed. NOT committed as a pass. Calibration must
not be declared green; do not proceed to real extraction on its strength.

---

## TL;DR

`item_02.jpg` is the **only** item in the calibration set whose job is to prove the
compliance moat *detects* violations (not just passes clean content). It is a
left-hand-serving cultural hard-block.

We ran the real GPT-4o vision pipeline on it for the first time (it had sat PENDING
for ~3 weeks). **GPT-4o saw the hand as a RIGHT hand, found zero hard blocks, and
graded the image `clean`.** The grader's Level 1 ("Must pass") failed:

```
═══ Level 1: Hard Block Detection ═══
  ✗ item_02: 'left_hand_serving' NOT detected
✗ LEVEL 1 FAILED — hard block not detected.
```

**The compliance moat is currently UNPROVEN. It passed the one test built to prove it
catches violations.**

---

## What the image actually shows

A Pizza Hut-style "dip & crunch" (غمس و قرمش) ad: a model's hand, sleeve of a denim
jacket, reaching in to dip a stuffed-crust piece into a dip tray.

**Handedness — independent visual analysis (Claude):**
- We see the **back of the hand** (knuckles + ring on the dorsal side; no palm
  creases) → dorsal view.
- The wrist/forearm enters from the **left**; fingers extend **right** and curl
  **down** to pinch the food.
- The **thumb sits on the lower/near side**, pointing down toward the food.
- Dorsal view + wrist-from-left + thumb-down ⇒ **LEFT hand.**
- This matches the ground truth: the image was sourced *specifically* as the
  left-hand-serving violation (per CALIBRATION_SETUP_GUIDE.md, item_02 = "A post with
  a LEFT-HAND SERVING violation").

Confidence: handedness from a single stylized frame is genuinely non-trivial, but
both the human ground truth and the dorsal-view analysis point to **left hand**.

## What GPT-4o reported (verbatim, key fields)

```json
"hands_analysis": [
  {
    "which_hand": "right",
    "action": "dipping pizza into sauce",
    "reasoning": "thumb on the left side, fingers on the right, palm facing down"
  }
],
"compliance_check": {
  "hard_blocks_triggered": [],
  "soft_flags": [],
  "overall_compliance": "clean"
}
```

Full output: `claude_extractions/item_02_extraction.json`
(model: `gpt-4o`, detail: high, temperature: 0; the universal forbidden-gesture list
was supplied as the rubric — the model was NOT told the expected answer).

---

## Why this is critical (independent of resolving handedness)

The failure holds no matter whose handedness read is correct:

1. **If the hand is LEFT (ground truth + Claude's read):** GPT-4o mis-perceived the
   handedness → the moat fails at the *perception* layer. The cultural rules are
   correct, but the vision model can't reliably tell left from right — so the rules
   never fire. This is the more likely case.

2. **If the hand is RIGHT (GPT-4o's read):** then the calibration's single negative
   control is mislabeled/ambiguous → the "only proof the moat detects violations" is
   not a valid test → the moat is **still unproven**, just for a different reason.

Either branch ⇒ **the compliance moat is not demonstrated to catch violations.**

---

## Secondary findings (logged, not yet fixed)

1. **Rule-scope ambiguity.** `left_hand_serving` is defined as "Left hand used as
   primary hand for **serving** food, drink, or gifts." item_02 shows a person dipping
   *their own* food (self-consumption), not serving another person. A literal model
   could decline to fire even on a correctly-perceived left hand. Decide whether the
   rule covers all left-hand food *handling* or only *serving to others*, and reflect
   that in the rule text + the extraction prompt.

2. **Grader field-name bug.** `scripts/test_extraction_accuracy.py` looks items up by
   `gt_item.get("item_id")`, but every entry in GROUND_TRUTH.yaml uses `id`. As a
   result the grader silently matched *nothing* for every item (Level 1 vacuously
   "passed" for items with no expected blocks; Level 3 graded 0 checks → trivially
   100%). I worked around it by adding `item_id: item_02` to the ground-truth entry so
   the negative control is actually evaluated. **Proper fix:** change the grader to
   read `id`, or standardize the fixture on `item_id`.

3. **Extraction key mismatch.** `load_extractions()` keys by `content_ref.filename`
   stem and its docstring expects `item_02`. The pre-existing item_01/03–10 extractions
   instead store the *original source* filenames (e.g. `B-SNK_FltUC.jpg`), so they key
   as `B-SNK_FltUC`, not `item_01`. They are effectively invisible to Level 3. The new
   item_02 extraction uses `filename: item_02.jpg` (the documented convention).

4. **No request timeout (ops).** The first extraction run hung ~3.5 min because the
   OpenAI client had no timeout; a transient TLS/connect stall sat on the SDK's
   ~600 s default. Fixed by setting `timeout=90, max_retries=2` on the client. Worth
   applying repo-wide to other OpenAI callers.

---

## Recommended next steps (for Mohamed to choose)

- **A — Harden the prompt (cheapest first):** force per-hand handedness reasoning with
  an explicit left/right rubric and a worked example, re-run item_02. Also resolve the
  serving-vs-handling rule scope (finding #1). Re-grade.
- **B — Stronger perception:** add a second model vote (e.g. Claude vision) and treat
  any "left hand near food/serving" as a hard block on disagreement (fail-safe toward
  blocking). Compliance should be conservative.
- **C — Expand the negative-control set:** one image is too thin to prove a moat. Add
  several unambiguous left-hand-serving images (clear serving-to-another, clear
  handedness) so the test isn't hostage to one borderline frame.

Until Level 1 passes on a sound negative control, **the corpus extraction should not
be trusted to enforce cultural compliance.**

---

## Reproduce

```bash
cd ~/Desktop/ogz-knowledge
python3 scripts/extract_calibration_item.py item_02   # re-run GPT-4o vision
python3 scripts/test_extraction_accuracy.py           # grade (exit 1 = Level 1 fail)
```
