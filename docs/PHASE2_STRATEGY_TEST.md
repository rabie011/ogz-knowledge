# PHASE 2 — THE 3-MONTH STRATEGY TEST (concrete design)
*Drafted 2026-06-13 00:58 (night shift, zero-LLM). Status: DESIGN — fires on key refill + Mohamed's go.*

## The one sentence
Run two real clients (eatjurisha + albaik) for 90 days on the full machine — minds
produce from confirmed truth, gates filter, Mohamed judges 20/batch, prompts re-version
from every batch — and prove with numbers that **the system learns his taste**.

## THE ONE METRIC (pass/fail)
**Rejection rate per batch must FALL.**
- Baseline: batch 1 rejection rate (whatever it is — honesty over vanity).
- PASS: by batch 6, rejection rate ≤ half of baseline, sustained for 2 consecutive batches.
- FAIL: flat or rising rejection rate after 6 batches → the loop is broken somewhere
  (prompts not absorbing verdicts, or the judging surface is hiding context again).
  A FAIL is a finding, not a shame — it points at the broken arc.

## Secondary numbers (tracked, never blended into one score)
| # | Number | Source | Healthy direction |
|---|---|---|---|
| 1 | Gold per batch (★4+) | gold_mint | rising |
| 2 | Corrections per batch (fix-box) | corrections.jsonl | falling after rise |
| 3 | Law violations caught at gate | caption_filter logs | falling at source |
| 4 | Median seconds per verdict | portal session log | stable ≤30s |
| 5 | Mind bench events | bench.json | zero after batch 3 |
| 6 | Recipe usage spread | attribution lineage | no recipe >30% of batch |

## Cadence (the weekly loop)
- **Sun:** render the week's batch (≤20 full posts/client) from year map + ratified
  recipes + gold few-shot. Gates run. Anything killed at gate is logged with its law.
- **Mon–Tue:** Mohamed's sitting(s) — full-post cards, 20 max per sitting (his law).
- **Wed:** verdict fold — gold minted, issues opened, corrections into the corpus,
  recipe/mind scorecards updated. **Prompt re-version**: every mind whose rejections
  cluster gets its methodology PR'd with the verbatim corrections (Mohamed-visible diff).
- **Thu:** regenerate next week's drafts WITH the new prompt versions. The A/B truth:
  every batch tagged with its prompt version — the rejection curve maps to versions.
- **Fri–Sat:** team lanes (Amira strategy review via her link), zoom-out ritual, receipt.

## Gates that must hold the whole 90 days (all already live)
verdicts_applied · gold_wire_e2e · law_registry · founder-words read-back ·
full-post-only judging surfaces · verified-live client identities · money law
(≈3¢/post-unit, zero image spend until the fal tap).

## What Mohamed does (and ONLY this)
- 1–2 sittings/week, ≤20 cards, ≤10 minutes each (measured median 22s/verdict).
- Rulings when law-vs-taste conflicts surface (the mint stages them).
- Nothing else. If the test needs more of him than this, the test has failed its
  own premise — flag it, don't stretch him.

## Start conditions (the checklist that fires it)
1. ☐ LLM key refilled (either OpenAI or Anthropic — minds + renderer run)
2. ☐ jurisha voice ruling (his «talk» — prep card staged)
3. ☐ taxonomy ruling for «evergreen» replacement (his words, twice — prep card staged)
4. ☐ Mohamed's go on this document (one card: «start the 90 days؟»)

When all four check, batch 1 renders the same day.
