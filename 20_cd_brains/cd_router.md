# CD-Brain Router — How a Brief Picks Its Methodology

**Companion to:** `10_agent_brains/cd_brain_router_rules.yaml` (the machine-readable rules)
**Owner:** CD-Brain Router (deterministic; **not** an LLM)
**Read by:** CEO agent (at routing time) and any humans auditing why a brief was assigned to which CD brain.

---

## Why the router exists

`{PLATFORM_NAME}` has 5 seed CD-brain methodologies:

| Slug | Internal name | One-line shorthand |
|---|---|---|
| `cd_01_firaasa_architect` | The Firaasa Architect | Why-before-What — cultural-contract diagnosis |
| `cd_02_metaphor_architect` | The Metaphor Architect | System-to-Human — full metaphor architecture |
| `cd_03_authenticity_detective` | The Authenticity Detective | Performance/Reality two-scene contrast |
| `cd_04_heritage_decoder` | The Heritage Decoder | Classical-Arabic Inversion via double-meaning word |
| `cd_05_paradox_hunter` | The Paradox Hunter | Counterintuitive flip + product-as-mechanism |

A brief doesn't pick its own brain. The brand's `brand_fingerprint.l1_strategy.cd_routing_weights` does — and the router translates that distribution into a deterministic selection per brief.

The router never invents. It scores, sorts, and (sometimes) returns two brains for the **Two-CD Diagnostic** anti-sameness gate.

---

## The scoring formula

```
score(brain) = brand_weight[brain]
             × brain.sector_affinity[brief.sector_slug]
             × occasion_factor(brain, brief.occasion_slugs)
```

Where:

- **`brand_weight[brain]`** — pulled from `brand_fingerprint.l1_strategy.cd_routing_weights`. The 5 weights sum to 1.0. A brand can lean heavily toward one brain (e.g. `cd_03: 0.50`) or distribute evenly.
- **`brain.sector_affinity[sector]`** — a 0–1 value from the brain's own front-matter. Captures structural fit (e.g. the Paradox Hunter scores `healthcare_wellness: 0.25` because the contrarian register undermines clinical credibility).
- **`occasion_factor`** — `1.0` when no occasion is active; otherwise the max of `brain.occasion_affinity[slug]` across the brief's occasion list (missing entries default to `0.5`).

After the base score is computed, the router applies the **occasion override boosts** declared in `cd_brain_router_rules.yaml`. For example:

| Occasion | Boosted brains | Factor | Why |
|---|---|---|---|
| `ramadan` | `cd_03`, `cd_04` | ×1.20 | Authenticity + heritage register lands hardest in Ramadan content. |
| `eid_al_fitr` | `cd_01`, `cd_03` | ×1.15 | Eid joy is communal and family-rooted. |
| `eid_al_adha` | `cd_03`, `cd_04` | ×1.15 | Reverent, family-hospitality register. |
| `saudi_national_day` | `cd_02`, `cd_04` | ×1.20 | National pride wants both fresh metaphor AND heritage anchoring. |
| `saudi_founding_day` | `cd_04` | ×1.30 | Founding Day is heritage-deep; the Heritage Decoder leads strongly. |

---

## Primary / Secondary selection

1. **Primary** — highest-scoring brain after boosts. Always selected.
2. **Two-CD Diagnostic gate** — if the second-highest score is **within 0.15** of the primary, the router returns BOTH brains. The brief is then routed through both brains in parallel; a brand-side strategist or human reviewer picks the stronger direction. This is the anti-sameness gate — it prevents the formula from collapsing into one default brain that overfits a sector.
3. **Tie-break priority** (in order):
   1. `brand_fingerprint.l1_strategy.primary_cd_brain` wins all ties (a brand lock).
   2. Higher `cd_routing_weights` value wins.
   3. Lower `cd_brain_slug` alphabetical wins (`cd_01 < cd_02 < ...`).
4. **Minimum-score floor** — if no brain scores above `0.10`, the router routes the brief to human review with reason `cd_routing_no_signal`. The brief is likely under-specified; a strategist needs to add context before routing again.

---

## Sector safety locks

A few sector × brain combinations are explicitly disallowed regardless of scoring:

| Sector | Forbidden brain | Reason |
|---|---|---|
| `healthcare_wellness` | `cd_05_paradox_hunter` | Contrarian register undermines clinical credibility. The brain is excluded from healthcare routing even if the brand weight is high. |
| `real_estate` | none forbidden, but `cd_01` and `cd_04` are preferred biases | Aspirational + heritage registers fit real-estate brand narratives best. |

When a forbidden brain wins the raw score, the router demotes it and re-selects from the remaining candidates.

---

## Worked examples

### Example 1 — F&B Ramadan campaign for a heritage-anchored Riyadh brand

**Input**
- sector: `f_and_b`
- occasions: `[ramadan]`
- `cd_routing_weights`: `cd_01: 0.30, cd_02: 0.10, cd_03: 0.30, cd_04: 0.25, cd_05: 0.05`

**Working**
| Brain | weight | sector | occasion | base | × ramadan boost | final |
|---|---|---|---|---|---|---|
| cd_01 | 0.30 | 0.70 | 0.75 | 0.158 | × 1.0 | 0.158 |
| cd_02 | 0.10 | 0.55 | 0.65 | 0.036 | × 1.0 | 0.036 |
| cd_03 | 0.30 | 0.90 | 0.95 | 0.257 | × 1.20 | **0.308** |
| cd_04 | 0.25 | 0.70 | 0.85 | 0.149 | × 1.20 | **0.179** |
| cd_05 | 0.05 | 0.60 | 0.45 | 0.014 | × 1.0 | 0.014 |

**Result**
- Primary: `cd_03_authenticity_detective` (0.308)
- Secondary: `cd_04_heritage_decoder` (0.179) — gap is 0.129, **within 0.15 → Two-CD Diagnostic fires**.
- Trigger reason: "Ramadan boost lifted Authenticity above Heritage by less than a sector-shift's worth; both brains produce a candidate direction."

### Example 2 — Retail launch for a Vision-2030 modern brand

**Input**
- sector: `retail`
- occasions: `[]`
- `cd_routing_weights`: `cd_01: 0.20, cd_02: 0.30, cd_03: 0.15, cd_04: 0.10, cd_05: 0.25`

**Working**
| Brain | weight | sector | occasion | final |
|---|---|---|---|---|
| cd_01 | 0.20 | 0.65 | 1.0 | 0.130 |
| cd_02 | 0.30 | 0.65 | 1.0 | **0.195** |
| cd_03 | 0.15 | 0.75 | 1.0 | 0.113 |
| cd_04 | 0.10 | 0.60 | 1.0 | 0.060 |
| cd_05 | 0.25 | 0.75 | 1.0 | **0.188** |

**Result**
- Primary: `cd_02_metaphor_architect` (0.195)
- Secondary: `cd_05_paradox_hunter` (0.188) — gap 0.007 → **Two-CD Diagnostic fires**.
- Both brains run; the modern-retail tension between systems-metaphor and paradox-mechanism is a productive opposition.

### Example 3 — Healthcare wellness brand brief

If a healthcare brand has `cd_05: 0.40` weight (a high paradox-bias), the router **demotes** `cd_05` per the sector safety lock and selects from the remaining brains. This protects clinical credibility even when the brand-level routing weights would have produced a wrong fit.

---

## Inputs the router needs

To run cleanly, the router requires:

1. **Brief** — `sector_slug`, `occasion_slugs` (0..N), `request_type`.
2. **Brand fingerprint** — `l1_strategy.cd_routing_weights` (5 values summing to 1.0), and optionally `l1_strategy.primary_cd_brain` for a brand lock.
3. **CD-brain files** — the 5 `cd_0X_*.md` files in this folder, each contributing their `sector_affinity` and `occasion_affinity` to the score.

Outputs (logged to `RoutingDecision`):

- `primary`: cd_0X slug
- `secondary`: cd_0Y slug or `null`
- `two_cd_diagnostic`: `true` / `false`
- `scores_by_brain`: full audit map
- `trigger_reason`: explanation string
- `occasion_overrides_applied`: list of occasion slugs that lifted scores
- `sector_safety_lock_applied`: list of brain slugs demoted by sector locks (usually empty)

---

## What the router will NOT do

- It will not pick a brain for a brief without a brand fingerprint. If `brand_fingerprint.l1_strategy.cd_routing_weights` is missing, the router refuses and surfaces a setup error. Brands must complete onboarding before content routing runs.
- It will not call an LLM. The router is deterministic on purpose: the same brief + same brand always routes to the same brain(s). Reproducibility is the asset.
- It will not re-rank based on past campaign outcomes. That is the Learning Agent's job (Sundays, 02:00 Riyadh) and it surfaces as nominated updates to `cd_routing_weights` — not as run-time overrides.

---

## Why the Two-CD Diagnostic matters

The fastest way for a brand to feel formulaic is for every brief in a sector to go to the same brain. The Two-CD Diagnostic was added to fight this: when two brains score within `0.15` of each other, the system FORCES both to produce a direction. The strategist or brand picks the stronger of two genuinely different reads.

The 0.15 threshold was tuned to fire in ~25% of briefs — enough to surface productive opposition, not so often that it slows every routing decision. It's a knob; if the platform sees too much sameness, raise it. If it slows the pipeline, lower it.

---

## Provenance

- **Specification:** `MASTER_PROMPT_FOR_CLAUDE_CODE.md` §3.2
- **Schema:** `12_data_shapes/cd_brain_v1.schema.json`
- **Machine rules:** `10_agent_brains/cd_brain_router_rules.yaml`
- **Confidence:** experimental (seed v1); routing weights and sector safety locks evolve through real-brand operation.
- **Scope:** universal
