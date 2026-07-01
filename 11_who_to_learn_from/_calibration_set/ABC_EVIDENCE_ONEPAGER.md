# A/B/C COMPLIANCE OPTIONS — EVIDENCE ONE-PAGER (B127)

> **60-second gate for Mohamed's B128 decision.** Every number below is grep/test-verified
> against the live repo on **2026-07-01**. Where a number does not exist yet, this page says
> so with the hard fact (e.g. "0 live runs") — never "pending" (Rule #9, DeepSeek's B127 trap).

**The one question B128 answers:** which left-hand-serving compliance option does the brain
ship — **A**, **B**, **A+B**, or **C-expanded** — and does `left_hand_serving` cover ALL
left-hand food handling or only *serving-to-others*?

---

## THE OPTIONS

- **A** — single-model (GPT-4o) vision + a **conservative fail-safe**: hand read as *left OR
  uncertain* in contact with food → `hard_block`. **LIVE today.**
- **B** — an **independent Anthropic-vision second vote** layered on A. Escalate-only (can turn
  a "clean" into a block on disagreement; **never downgrades** a block). Fail-safe, not
  fail-open: if the 2nd model is unavailable it returns A unchanged. **Built + unit-tested;
  never run live** (Anthropic dry since 2026-06-12).
- **A+B** — both together (A's structural fail-safe + B's orientation vote).
- **C-expanded** — A (and/or B) **plus a widened calibration set** (B126): 3–5 unambiguous
  left-hand-serving frames **+ a clean right-hand-on-food control** — the only path that can
  finally *measure the false-block rate*. **Not built.**

---

## THE EVIDENCE TABLE

| Option | Detection (known control) | False-block rate | Cost / image | **Live runs** | Status |
|--------|---------------------------|------------------|--------------|---------------|--------|
| **A** | item_02 **caught** (L1 🟢); L2 completeness **100%**, L3 accuracy **91.7%** | **UNMEASURED** — no clean right-hand-on-food control exists | 1 GPT-4o vision call/img (single call, not separately metered) | **10-item set graded** (B130 gate: exit 0, L1 pass, completeness 1.0, accuracy 0.9166) | **LIVE** |
| **B** | **UNKNOWN** | **UNKNOWN** | +1 Anthropic vision call, escalate-path only (on top of A) | **0 live runs** — built, `reconcile()` **9/9 unit tests pass**, 0 production calls | **BUILT, not deployed** (Anthropic dry) |
| **A+B** | = A today (B contributes nothing until it runs) | **UNKNOWN** | A + B's escalate calls | **0** (B never ran) | **gated on B** |
| **C-expanded** | would add 3–5 hard controls | **would finally be measurable** | = chosen base option | **0** — set not built (B126) | **NOT built** |

---

## THE HONEST CAVEAT (do not over-claim the moat — Rule #12)

A's L1 green is **structural, not perceptual**. item_02 passes because the fail-safe blocks the
*ambiguous* case — **the eye still misread its handedness** (called the left hand "right" in the
2026-06-11 extraction). Consequences:

1. **The moat is not yet proven by perception.** A smarter/second eye (B) is still owed.
2. **False-block rate is UNMEASURED** for every option. A "left OR uncertain → block" fail-safe
   will also block legitimate *right*-hand-on-food content — and there is **no clean
   right-hand-on-food control** in the set to catch that over-block. Only **C-expanded** fixes this.
3. **One negative control (item_02) cannot prove a moat.** The set is still too thin.

---

## THE PAIR'S RECOMMENDATION (provisional — your eye rules)

- **Ship A now** (it's the only measurable option today and it bites on the one control we have).
- **Switch on B the moment Anthropic is funded** — it's built, free of new code, escalate-only,
  and gives the independent orientation vote perception is missing. **Zero risk** (fail-safe).
- **Do C-expanded regardless of A vs B** — it is the *only* way to ever quote a false-block rate
  and honestly prove the moat. This is the real unlock; A/B without it stay "passes on 1 control."

**Net:** **A now → A+B when funded → C-expanded to prove it.** Not mutually exclusive; a sequence.

### Second half of B128 — the cultural scope question (needs YOUR ruling, not ours)
Does `left_hand_serving` forbid **ALL** left-hand contact with food, or **only serving-to-others**
(offering food to another person with the left hand)? This is a taste/cultural call — it sets
whether a person eating with their own left hand trips the gate. It flows straight into
`universal_gestures_forbidden.yaml` (B129) once you rule.

---

*Sources (all in-repo, verified 2026-07-01): `BASELINE_RESULTS.md` (2026-06-30 re-measure),
`data/extraction_accuracy_gate.json` (B130), `scripts/vision_second_vote.py` +
`scripts/tests/test_vision_second_vote.py` (9/9 green), `GROUND_TRUTH.yaml` (10 items, 1 control),
`scripts/test_immune_system.py` (42/0). Built for B127 by the RABIE+DeepSeek orchestra.*
