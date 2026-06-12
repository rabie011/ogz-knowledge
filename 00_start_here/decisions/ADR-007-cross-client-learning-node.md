# ADR-007 — The Cross-Client Learning Node (Crystallize Loop)
*Status: ACCEPTED (live since June 11; operational-scar input added June 12). Author: the pair (Claude + RABIE provisional). Ratifier: Mohamed (3 rules already minted permanent).*

## Context
Mohamed's Rule #4 step 7: every pain becomes a permanent rule ("scar → scar tissue").
Individually, each client's rejections are anecdotes; across clients they are PATTERNS.
The platform needed a mechanism that turns repeated pain into draft law WITHOUT letting
any AI write law on its own (the AI-judge scar: machines can't judge Saudi creative).

## Decision
One loop (`scripts/crystallize_loop.py`), two evidence sources, one human gate:

1. **Client verdicts** — append-only event ledgers (`clients/*/events/*.jsonl`), coded
   rejection reasons only (culture_breach / off_voice / wrong_goal / too_generic /
   factual_error / unexplained). Threshold: **≥3 occurrences across ≥2 clients** —
   below that it's one client's taste, not a law of the street.
2. **Operational scars** (added June 12) — zoom-out findings triaged REAL (cold eyes
   found it, the pair verified it, the fix shipped at source). Each is already
   evidence-backed, so each drafts directly — no threshold.
3. **The human gate** — every draft lands in `data/crystallize_queue.json` as a
   60-second yes/no card. **Only Mohamed crystallizes.** 3 of his accepts = the rule
   goes permanent (CLAUDE.md / guard / gate). The machine drafts; taste rules.

## Why this shape (rejected alternatives)
- **Auto-applied rules** — rejected: the AI judge scored RANDOM vs Mohamed (+0.08);
  machine-minted law would encode machine taste. DEAD ON ARRIVAL.
- **Per-client learning only** — rejected: 3 pilot ledgers are too thin alone; the
  cross-client axis is where «عادي مرة» becomes a detectable street-wide shape.
- **LLM-summarized lessons** — rejected: lessons must trace to countable events
  (the evidence rule); a summary cannot be grepped.

## Consequences
- Laws are born with provenance: every permanent rule traces to its ledger lines or
  its zoom entry — auditable forever.
- The loop is idle-safe: young ledgers → "the machine waits for real verdicts.
  It runs; it does not invent."
- Cost: zero LLM calls (pure counting). Money law clean.
- Risk accepted: slow law-birth while clients are few — by design; the gate (Mohamed's
  taste) is the moat, and the moat must not be diluted for speed.

## Pointers
`scripts/crystallize_loop.py` · `data/crystallize_queue.json` · scars: `data/make_sure_log.jsonl`
(zoom_out entries) · minted: 3 rules permanent (June 12) · related: ADR-pattern in CONVENTIONS.md
