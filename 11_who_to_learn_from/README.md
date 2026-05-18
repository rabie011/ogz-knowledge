# 11_who_to_learn_from/

Curated Saudi Instagram benchmark accounts + extracted cross-account patterns. The library the platform learns from — never copies.

## Layout

```
11_who_to_learn_from/
├── INDEX.json                          — full lookup (accounts + patterns)
├── accounts/
│   ├── f_and_b/account_001..NN.json    — 37 F&B benchmark accounts
│   ├── retail/account_001..NN.json     — 40 retail accounts
│   └── beauty/account_001..NN.json     — 31 beauty / wellness accounts
└── patterns/
    ├── visual_compositions/            — 10 visual composition patterns
    ├── voice_techniques/               — 10 voice techniques
    ├── content_types/                  — 10 content-type patterns
    └── occasion_plays/                 — 10 occasion plays
```

**Account total:** ~108 (target was ~100).
**Pattern total:** 40 substantive cross-account patterns (honest delivery vs. the speculative 300 target — quality over count).

## Account anonymization

- `account_handle_normalized`: external-facing label, format `OGZ-<SECTOR>-Reference-NNN`. Used in client-facing dashboards.
- `account_handle_internal`: the raw Instagram handle. Never surfaced to clients. Used by COO for similarity computation.

This is system-design discipline (consistency), not a legal requirement. Per Mohamed: "no IP / consent / legal concerns" on benchmark sample.

## Schema validation

- Accounts validate against `12_data_shapes/benchmark_account_v1.schema.json`.
- Patterns validate against `12_data_shapes/account_pattern_v1.schema.json`.

## How patterns work

A pattern is a cross-account abstraction. It carries:
- `structural_recipe` — what the pattern is, in terms not tied to a specific brand
- `why_it_works` — the underlying mechanism
- `transplantation_caveats` — where it fails
- `applicable_chains` — which TF chains can execute this pattern
- `observed_in_account_count` — how many of our accounts use it

The CEO agent uses patterns as **inspiration material**, not templates to copy. Generated content draws on the pattern's recipe but uses the specific brand's fingerprint.

## Extraction infrastructure (v1.2.0)

```
11_who_to_learn_from/
├── source_library/
│   └── my_picks/                       — Mohamed's account picks per sector
│       └── MY_PICKS_TEMPLATE.yaml      — copy + rename to start a sector
├── _calibration_set/
│   ├── content/                        — calibration images (gitignored)
│   ├── claude_extractions/             — Claude Code's calibration output
│   ├── GROUND_TRUTH.yaml              — Mohamed's answers (do not show to Claude Code)
│   └── CALIBRATION_SETUP_GUIDE.md     — how to build the calibration set
├── _inbox/                             — per-account content (gitignored)
│   └── @handle/                        — download content here
└── observations/
    ├── f_and_b/                        — extraction records for F&B
    ├── retail/                         — extraction records for Retail
    └── beauty/                         — extraction records for Beauty
```

- Observations validate against `12_data_shapes/observation_v1.schema.json`.
- See `START_HERE_EXTRACTION.md` for the full workflow.
- See `EXTRACTION_PROMPT_FOR_CLAUDE_CODE.md` for Claude Code's extraction instructions.

## Updates

- New accounts: added monthly during brand-onboarding sweep.
- Pattern refinements: Learning Agent (Sundays 02:00 Riyadh) proposes updates based on outcome events.
- Mohamed approves changes via PR.
