# 20_cd_brains/

The 5 seed CD-brain methodologies + the router narrative.

## Files

| File | Methodology | Diagnostic question |
|---|---|---|
| `cd_01_firaasa_architect.md` | The Firaasa Architect | What is the Saudi cultural contract this brand needs to honor — and is currently breaking or ignoring? |
| `cd_02_metaphor_architect.md` | The Metaphor Architect | What is the invisible system this brand is trying to protect, connect, or enable — and what is the most Saudi daily-life thing that works exactly the same way? |
| `cd_03_authenticity_detective.md` | The Authenticity Detective | Where is the GAP between what people PERFORM for others and what they actually FEEL when no one is watching? |
| `cd_04_heritage_decoder.md` | The Heritage Decoder | What Arabic word or phrase operates on two levels — one the client sees, one the audience feels before they can name it? |
| `cd_05_paradox_hunter.md` | The Paradox Hunter | What is the PARADOX? What's the counterintuitive truth that makes the obvious answer wrong? |
| `cd_router.md` | Router narrative | Companion to the machine-readable `10_agent_brains/cd_brain_router_rules.yaml`. |

## How a brain gets used

1. Brand has `brand_fingerprint.l1_strategy.cd_routing_weights` (5 values summing to 1.0).
2. For each brief, the deterministic CD-Brain Router scores each of the 5 brains using:
   `score = brand_weight × brain.sector_affinity[sector] × occasion_factor(brain, occasions)`
3. The top-scoring brain becomes primary.
4. If the second-highest score is within 0.15 of the primary → **Two-CD Diagnostic** fires; both brains produce a candidate direction.
5. Sector safety locks override raw scores (e.g., Paradox Hunter is excluded for healthcare).

Full logic: `cd_router.md` (narrative) + `10_agent_brains/cd_brain_router_rules.yaml` (machine).

## How a brain RUNS (June 23 — "all agents and minds")

Routing picks WHICH brain(s); two runners EXECUTE the chosen methodology against an LLM:

- **Single pen** — `scripts/render_client_slot.py::make_angle` applies ONE routed brain's full
  methodology body (`brain_router.brain_method`) on GPT-4o (Sonnet fallback). The default path.
- **The PANEL** — `scripts/cd_panel.py::run_panel` (run with `--panel` on `render_client_slot.py`
  or `produce_batch.py`, or `PRODUCE_PANEL=1`) runs the slot's CD-brain spread as a panel of
  distinct minds, **each brain on a DIFFERENT model** (GPT / Gemini / Groq via `scripts/consult.py`).
  It returns the lead brain's angle with the rival brains' angles attached as `panel_alts` so the
  caption is *born from the minds*, not invented mechanically. A dead model falls back to a live one;
  all-dead falls back to the single pen — the pipeline never stalls on the minds.

## Rules

- **Each brain's front-matter** validates against `12_data_shapes/cd_brain_v1.schema.json`.
- **The methodology body** is restructured from the research corpus with placeholder names removed and client references anonymized to category labels.
- **`status: seed_v1`, `confidence: experimental`** — these are starting points. They evolve through real client work, not through speculative re-authoring.
- **The Inversion Test** (in each brain's front-matter) is the anti-formula gate — the question the brain asks of its own output to verify the work isn't formula in costume.

## Voice anchors per brain (one-line)

- **Firaasa** — MSA-leaning, philosophical, certainty without hype; opens with the cultural problem, closes with inevitability
- **Metaphor** — MSA structure + Saudi rhythm; "تخيل معي..." opener; "But wait!" pivot; full metaphor architecture
- **Authenticity** — Saudi colloquial + parallel-original bilingual; "لمّا..." emotional hinge; two-scene performance/reality contrast
- **Heritage** — Classical Arabic + Saudi warmth; double-meaning words as structural keys; unhurried internal rhythm
- **Paradox** — Saudi colloquial sharp; "غلطان" pivots; long poetic build → short punch landing; product-as-mechanism

## Updates

CD brains are evolved through:
- Real client outcomes (Learning Agent proposes pattern updates Sundays 02:00 Riyadh)
- Cultural Advisor review of brand-specific overrides
- Mohamed approval on any front-matter change

Direct edits without PR are blocked by branch protection.
