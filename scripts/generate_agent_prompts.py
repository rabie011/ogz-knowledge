#!/usr/bin/env python3
"""
Day 3 / Task 3.1 — Generate 3 agent system-prompt files + 1 router-rules YAML.

Source:  ~/Desktop/ogz-knowledge-corpus/OGzStudios_{CEO,COO,CCO}_Prompt_v1.md
Output:  10_agent_brains/{ceo,coo,cco}_system_prompt_v1.md  +  cd_brain_router_rules.yaml

Per CLAUDE.md: prompt bodies are intellectual property — preserved VERBATIM.
We only prepend YAML front-matter for schema/provenance and a small header note.

Platform-name references in the corpus ("OpenClaw", "OGz AI") are kept verbatim
because they are part of the original prompt copy. Mohamed will sed-replace to
{PLATFORM_NAME} or the final chosen name at his discretion.
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent.parent
CORPUS = Path.home() / "Desktop" / "ogz-knowledge-corpus"
OUT_DIR = REPO / "10_agent_brains"
OUT_DIR.mkdir(exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

AGENTS = [
    {
        "role": "CEO",
        "src": "OGzStudios_CEO_Prompt_v1.md",
        "out": "ceo_system_prompt_v1.md",
        "model": "claude-sonnet-4-6",
        "owns": "what should we build for this brief?",
        "synopsis": "Strategic routing. 8-step protocol. 11 human-gate triggers. JSON-only output.",
    },
    {
        "role": "COO",
        "src": "OGzStudios_COO_Prompt_v1.md",
        "out": "coo_system_prompt_v1.md",
        "model": "claude-haiku-4-5",
        "owns": "how do we generate this specific output, safely?",
        "synopsis": "Operations engine. 3 jobs (build_branddna / compile_caption_context / score_confidence). Confidence formula: 0.40 floor × 0.30 arabic_qc × 0.15 occasion × 0.15 policy.",
    },
    {
        "role": "CCO",
        "src": "OGzStudios_CCO_Prompt_v1.md",
        "out": "cco_system_prompt_v1.md",
        "model": "gpt-5",
        "owns": "is this output Saudi-native and culturally correct?",
        "synopsis": "Arabic QC gate. Per-post 0–100 score + dialect/negpat/cultural/brave flags. Calibrated for Saudi Gulf Arabic.",
    },
]


def front_matter(agent: dict) -> str:
    block = {
        "agent_role": agent["role"],
        "schema_version": 1,
        "prompt_version": 1,
        "model_recommended": agent["model"],
        "owns_question": agent["owns"],
        "synopsis": agent["synopsis"],
        "created_at": NOW,
        "provenance": {
            "source": f"internal_research_corpus/{agent['src']}",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal",
        },
    }
    yaml_body = yaml.safe_dump(block, sort_keys=False, allow_unicode=True, width=120)
    return "---\n" + yaml_body + "---\n\n"


def write_agent_prompt(agent: dict) -> None:
    src_path = CORPUS / agent["src"]
    if not src_path.exists():
        raise FileNotFoundError(f"corpus source missing: {src_path}")
    body = src_path.read_text()
    # Preserve the body verbatim. Prepend our YAML front-matter only.
    out_path = OUT_DIR / agent["out"]
    out_path.write_text(front_matter(agent) + body)
    print(f"✓ {out_path.relative_to(REPO)}  ({len(body):,} bytes verbatim · {agent['role']} / {agent['model']})")


# ───────────────────────────────────────────────────────────────────────────
# cd_brain_router_rules.yaml — deterministic routing logic from spec
# ───────────────────────────────────────────────────────────────────────────
def cd_brain_router_rules() -> dict:
    return {
        "schema_version": 1,
        "title": "CD-Brain Router Rules",
        "owner_agent": "CD-Brain Router (deterministic, not LLM)",
        "description": (
            "Selects 1 or 2 CD-brain methodologies per brief. Reads the brand's "
            "cd_routing_weights from brand_fingerprint.l1_strategy plus the brief's "
            "sector and occasion, scores each of the 5 brains, and returns primary "
            "(and optional secondary for the Two-CD Diagnostic anti-sameness gate)."
        ),
        "input_contract": {
            "brief": {
                "brand_id": "ULID — brand whose fingerprint feeds the routing weights",
                "sector_slug": "one of the slugs in 05_sector_defaults/",
                "occasion_slugs": "0..N slugs from 06_saudi_calendar/ (empty list = no occasion)",
                "request_type": "see ceo_system_prompt_v1.md request_type enum",
            },
            "brand_fingerprint": {
                "l1_strategy.cd_routing_weights": "object with cd_01..cd_05 weights summing to 1.0",
                "l1_strategy.primary_cd_brain": "optional brand lock (cd_0X slug) — wins all ties",
            },
        },
        "scoring_formula": {
            "definition": "score(brain) = cd_routing_weights[brain] × brain.sector_affinity[sector_slug] × occasion_factor(brain, occasion_slugs)",
            "occasion_factor_rule": (
                "if occasion_slugs is empty: 1.0. "
                "else: max(brain.occasion_affinity[slug] for slug in occasion_slugs). "
                "missing affinity entries default to 0.5 (neutral)."
            ),
            "tie_break_priority": [
                "1. brand_fingerprint.l1_strategy.primary_cd_brain wins all ties",
                "2. higher cd_routing_weights value wins",
                "3. lower cd_brain_slug alphabetical wins (cd_01 < cd_02 < ...)",
            ],
        },
        "selection_rules": {
            "primary_selection": "highest-scoring brain becomes primary",
            "two_cd_diagnostic_gate": {
                "trigger": "second-highest score is within 0.15 of the primary score",
                "behavior": "include both brains as 'two-cd diagnostic'. The brief generates two parallel direction candidates; brand-side strategist or human reviewer picks the stronger.",
                "rationale": "Anti-sameness — prevents the formula from collapsing into one default brain that overfits a sector.",
            },
            "minimum_score_floor": {
                "threshold": 0.10,
                "behavior": "if no brain scores above 0.10, route to human review with reason 'cd_routing_no_signal'. Brief is likely under-specified.",
            },
        },
        "occasion_overrides": {
            "ramadan": {
                "boost_brains": ["cd_03_authenticity_detective", "cd_04_heritage_decoder"],
                "boost_factor": 1.2,
                "reason": "Authenticity + heritage register lands hardest in Ramadan content.",
            },
            "eid_al_fitr": {
                "boost_brains": ["cd_01_firaasa_architect", "cd_03_authenticity_detective"],
                "boost_factor": 1.15,
                "reason": "Eid joy is communal and family-rooted — Firaasa (cultural insight) + Authenticity fit.",
            },
            "eid_al_adha": {
                "boost_brains": ["cd_04_heritage_decoder", "cd_03_authenticity_detective"],
                "boost_factor": 1.15,
                "reason": "Reverent, family-hospitality register favors heritage + authenticity.",
            },
            "saudi_national_day": {
                "boost_brains": ["cd_04_heritage_decoder", "cd_02_metaphor_architect"],
                "boost_factor": 1.20,
                "reason": "National pride wants heritage anchoring AND fresh metaphor — both, together.",
            },
            "saudi_founding_day": {
                "boost_brains": ["cd_04_heritage_decoder"],
                "boost_factor": 1.30,
                "reason": "Founding Day is heritage-deep; the Heritage Decoder leads strongly.",
            },
        },
        "sector_safety_locks": {
            "healthcare_wellness": {
                "forbidden_brains": ["cd_05_paradox_hunter"],
                "reason": "Paradox + contrarian register is wrong tonal posture for healthcare credibility.",
            },
            "real_estate": {
                "forbidden_brains": [],
                "preferred_brains": ["cd_01_firaasa_architect", "cd_04_heritage_decoder"],
            },
        },
        "output_contract": {
            "primary": "cd_0X slug",
            "secondary": "cd_0Y slug or null",
            "two_cd_diagnostic": "boolean",
            "scores_by_brain": "object cd_0X → numeric score (for audit trail)",
            "trigger_reason": "string explaining why this combination was chosen",
            "occasion_overrides_applied": "array of occasion slugs that boosted the result",
        },
        "examples": [
            {
                "scenario": "F&B Ramadan campaign for a heritage-anchored Riyadh brand",
                "input": {
                    "sector_slug": "f_and_b",
                    "occasion_slugs": ["ramadan"],
                    "cd_routing_weights": {"cd_01": 0.30, "cd_02": 0.10, "cd_03": 0.30, "cd_04": 0.25, "cd_05": 0.05},
                },
                "expected_primary": "cd_03_authenticity_detective",
                "expected_secondary": "cd_04_heritage_decoder (Two-CD Diagnostic likely fires)",
            },
            {
                "scenario": "Retail launch for a Vision-2030 modern brand",
                "input": {
                    "sector_slug": "retail",
                    "occasion_slugs": [],
                    "cd_routing_weights": {"cd_01": 0.20, "cd_02": 0.30, "cd_03": 0.15, "cd_04": 0.10, "cd_05": 0.25},
                },
                "expected_primary": "cd_02_metaphor_architect",
                "expected_secondary": "cd_05_paradox_hunter (within 0.15 — Two-CD Diagnostic fires)",
            },
        ],
        "provenance": {
            "source": "spec:MASTER_PROMPT_FOR_CLAUDE_CODE.md§3.2 + cd_brain_v1.schema.json + occasion files",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal",
        },
    }


def main() -> int:
    print("═══ writing agent prompts (verbatim bodies + front-matter) ═══")
    for agent in AGENTS:
        write_agent_prompt(agent)

    print("\n═══ writing cd_brain_router_rules.yaml ═══")
    data = cd_brain_router_rules()
    out = OUT_DIR / "cd_brain_router_rules.yaml"
    header = (
        "# cd_brain_router_rules.yaml\n"
        "# Deterministic routing rules — read by CD-Brain Router (not an LLM).\n"
        f"# Confidence: {data['provenance']['confidence']}\n"
        f"# Scope: {data['provenance']['scope']}\n\n---\n"
    )
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    out.write_text(header + body)
    print(f"✓ {out.relative_to(REPO)}")

    print(f"\nWrote {len(AGENTS) + 1} files to {OUT_DIR.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
