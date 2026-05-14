# AGENT_MANIFEST.md

**Who reads what, who writes what.** This manifest is the contract between the agents and the knowledge base.

The runtime layer (separate repo) implements these agents. This repo provides the knowledge they consume.

---

## The Agents

The `{PLATFORM_NAME}` production system has 6 agents organized in a C-Suite pattern plus a CD-Brain router layer.

### CEO Agent — Strategic Routing
- **Model recommended:** Claude Sonnet 4.6 (or Opus for high-stakes briefs)
- **Reads:** `10_agent_brains/ceo_system_prompt_v1.md`, `01_how_to_decide/*.yaml`, `02_what_to_build/INDEX.json`, the brand's `brand_fingerprint` from runtime DB, `20_cd_brains/cd_router.md`
- **Writes:** routing decisions as events (in runtime DB, not this repo)
- **Owns:** the question "what should we build for this brief?"

### COO Agent — Operational Execution
- **Model recommended:** Claude Haiku 4.5 (speed-optimized)
- **Reads:** `10_agent_brains/coo_system_prompt_v1.md`, `02_what_to_build/{family}/{chain}.json`, the brand's `brand_fingerprint`, `15_cultural_specs/sector_defaults/`, `15_cultural_specs/forbidden_lists/`
- **Writes:** composed prompts, fal.ai requests, generation events
- **Owns:** the question "how do we generate this specific output, safely?"

### CCO Agent — Cultural & Creative Compliance
- **Model recommended:** GPT-5 (or Claude Sonnet 4.6) — Arabic quality critical
- **Reads:** `10_agent_brains/cco_system_prompt_v1.md`, `15_cultural_specs/`, `04_saudi_rules/`, `06_saudi_calendar/`, generated outputs
- **Writes:** compliance gate results, Arabic quality scores, escalation flags
- **Owns:** the question "is this output Saudi-native and culturally correct?"

### CD-Brain Router — Creative Methodology Selection
- **Logic:** deterministic (not an LLM by default)
- **Reads:** `20_cd_brains/cd_router.md`, `20_cd_brains/cd_0[1-5]_*.md`, the brief intent, the brand's `brand_fingerprint.l1_strategy`
- **Writes:** which CD brain(s) get applied to this brief
- **Owns:** the question "which creative-thinking methodology fits this brief?"

### Memory Controller — The Only Write Path
- **Logic:** deterministic, never an LLM
- **Reads:** propose-review-merge PRs against this repo; outcome events from runtime
- **Writes:** every record in this repo (via PR); the runtime DB (via sync_to_supabase.py)
- **Owns:** "did this write follow all the rules?"
- **Critical:** no agent writes directly to the DB or this repo. All writes go through the Memory Controller. No exceptions.

### Learning Agent — Weekly Pattern Synthesis
- **Model recommended:** Claude Sonnet 4.6
- **Reads:** outcome events from past week, generation events, current patterns, current heuristics
- **Writes:** proposed updates to `11_who_to_learn_from/patterns/`, proposed CD-brain routing weight updates, proposed new heuristics
- **Schedule:** Sundays 02:00 Riyadh time
- **Owns:** "what did we learn this week?"
- **Important:** outputs are PROPOSALS; a human reviewer approves before they merge.

---

## Read Map by Folder

| Folder | Read by | Frequency |
|---|---|---|
| `00_start_here/` | All agents on cold start | Once per session |
| `01_how_to_decide/` | CEO Agent | Every brief |
| `02_what_to_build/` | CEO Agent, COO Agent | Every brief / every generation |
| `04_saudi_rules/` | CCO Agent, COO Agent | Every generation |
| `05_sector_defaults/` | All agents | Every brief |
| `06_saudi_calendar/` | CCO Agent, CEO Agent (occasion triggers) | Continuous |
| `09_how_to_run/` | Human operators | As needed |
| `10_agent_brains/` | CEO/COO/CCO (their own prompts) | Every session |
| `11_who_to_learn_from/` | CEO Agent, Learning Agent | Every brief / weekly |
| `12_data_shapes/` | Memory Controller, validate scripts | Every write |
| `13_database/` | sync_to_supabase.py, runtime infra | Migrations |
| `14_brand_fingerprint/` | Memory Controller (at brand onboarding) | Per brand |
| `15_cultural_specs/` | CCO Agent, COO Agent | Every generation |
| `16_character_library/` | COO Agent (visual references) | Selective |
| `20_cd_brains/` | CD-Brain Router, CEO Agent | Every brief |
| `21_campaign_archive/` | CEO Agent (RAG retrieval) | Every brief (top-k) |
| `22_org_context/` | Human operators, dashboard | Reference |

---

## Write Map (Who Modifies What)

| Folder | Who can modify | How |
|---|---|---|
| `12_data_shapes/` | Mohamed only | PR with approval; schema changes are major versions |
| `02_what_to_build/` | Mohamed via PR | Generator script preferred |
| `05_sector_defaults/`, `06_saudi_calendar/` | Mohamed + Cultural Advisor | PR |
| `15_cultural_specs/` | Cultural Advisor (lead), Mohamed | PR |
| `20_cd_brains/` | Mohamed (initially); CD leads (when assigned) | PR |
| `21_campaign_archive/` | Memory Controller (auto-add after client approval) + Mohamed (curation) | PR |
| `11_who_to_learn_from/` | Learning Agent (proposes) + Mohamed (approves) | PR |
| All other folders | Mohamed | PR |

**Direct pushes to main are blocked by branch protection.**

---

## The Spine / Joints / Tools Distinction

(From the deep research spec.)

**Spine — always deterministic, never LLM:**
- Memory Controller
- Routing rules in `01_how_to_decide/`
- Compliance gate evaluation in `04_saudi_rules/`
- sync_to_supabase.py
- All schema validation

**Joints — agents that selectively engage LLMs:**
- CEO Agent
- COO Agent
- CCO Agent
- Learning Agent

**Tools — stateless LLM calls or models:**
- fal.ai chains
- The actual Claude/GPT-5 calls made by the Joints

A failure in a Tool is recoverable. A failure in a Joint is operational. A failure in the Spine is critical. This is why the Spine never depends on LLMs.

---

## When This Manifest Changes

This manifest is the contract. It changes only when:
1. A new agent is added
2. Read/write patterns change
3. The agent roles are restructured

Any such change requires:
- PR to update this file
- Corresponding ADR in `00_start_here/decisions/`
- Mohamed's approval

---

## See Also

- `10_agent_brains/ceo_system_prompt_v1.md` — the CEO Agent's actual prompt
- `10_agent_brains/coo_system_prompt_v1.md` — the COO Agent's actual prompt
- `10_agent_brains/cco_system_prompt_v1.md` — the CCO Agent's actual prompt
- `20_cd_brains/cd_router.md` — CD-Brain Router rules
- `00_start_here/decisions/ADR-0001-files-first.md` — why this manifest exists at all
