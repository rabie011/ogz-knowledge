# 10_agent_brains/

System prompts for the production agents + the deterministic CD-brain router rules.

## Files

| File | What it is |
|---|---|
| `ceo_system_prompt_v1.md` | CEO Agent — strategic routing. Claude Sonnet 4.6. 8-step routing protocol, 11 human-gate triggers, JSON-only output. |
| `coo_system_prompt_v1.md` | COO Agent — operations engine. Claude Haiku 4.5. Three jobs: `build_branddna`, `compile_caption_context`, `score_confidence`. |
| `cco_system_prompt_v1.md` | CCO Agent — Arabic QC gate. GPT-5. Per-post 0–100 score + dialect/negpat/cultural/brave flags. Calibrated for Saudi Gulf Arabic. |
| `cd_brain_router_rules.yaml` | CD-Brain Router — deterministic rules selecting 1 or 2 brains per brief (Two-CD Diagnostic gate). |

## Rules

- **Prompt bodies are intellectual property.** They are preserved verbatim from the research corpus. Only the YAML front-matter on each MD is `{PLATFORM_NAME}` overhead (schema_version, provenance, model_recommended).
- **Storage:** in production, these prompts are n8n credential objects — never in source code or workflow node text. This repo stores the canonical version for review and audit.
- **Updates:** any change to a prompt body goes through PR review + Cultural Advisor sign-off on the CCO prompt. Versioned via filename (`v1` → `v2`).
- The CD-Brain Router is **deterministic** — NOT an LLM. Reproducibility is the asset. See companion narrative at `20_cd_brains/cd_router.md`.

## Cross-references

- Routing logic narrative: `20_cd_brains/cd_router.md`
- CD-brain methodology profiles: `20_cd_brains/cd_0{1..5}_*.md`
- Confidence formula weights (in COO prompt): 0.40 floor × 0.30 arabic_qc × 0.15 occasion × 0.15 policy
- CEO routing protocol references: occasion calendar (`06_saudi_calendar/`), sector baselines (`05_sector_defaults/`), forbidden lists (`15_cultural_specs/forbidden_lists/`)
