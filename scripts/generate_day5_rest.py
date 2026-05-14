#!/usr/bin/env python3
"""
Day 5 / Tasks 5.2 + 5.4 + 5.5 — generate:
  - 5 org-context YAMLs in 22_org_context/
  - 6 operations runbook MDs in 09_how_to_run/
  - character library stub (README + 6 subfolders × MANIFEST/.gitkeep)
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def prov(source: str, scope: str = "universal") -> dict:
    return {"source": source, "date_added": NOW, "confirmer": "Mohamed",
            "confidence": "experimental", "scope": scope}


def write_yaml(path: Path, data: dict, note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"# {path.name}\n# {note}\n# Confidence: {data['provenance']['confidence']}\n"
              f"# Scope: {data['provenance']['scope']}\n\n---\n")
    path.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
    print(f"✓ {path.relative_to(REPO)}")


def write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"✓ {path.relative_to(REPO)}")


# ────────────────────────────────────────────────────────────────────────────
# 22_org_context/ (5 files)
# ────────────────────────────────────────────────────────────────────────────

ORG = REPO / "22_org_context"

def org_structure():
    return {
        "schema_version": 1,
        "title": "Organizational structure (anonymized, role-titled)",
        "description": "4-cluster CD organization. Role titles only — personnel names redacted per CONVENTIONS.",
        "leadership": {
            "ceo": {"role": "Creative CEO", "owns": "macro brand architecture, pitch strategy, awards strategy"},
            "cco": {"role": "Chief Creative Officer", "owns": "CD-cluster oversight, creative-quality QC"},
            "cgo_coo": {"role": "Chief Growth Officer + Chief Operating Officer (dual-title)", "owns": "BD, operations, client services, brand marketing"},
        },
        "creative_clusters": [
            {"cluster_id": "C1", "lead_methodology": "cd_02_metaphor_architect", "client_specialty": ["telecom", "cybersecurity_authority", "vision_2030"]},
            {"cluster_id": "C2", "lead_methodology": "cd_03_authenticity_detective", "client_specialty": ["luxury_gifting", "beverage_major", "tax_authority", "foundation"]},
            {"cluster_id": "C3", "lead_methodology": "cd_04_heritage_decoder", "client_specialty": ["banking_major", "heritage_fashion", "human_rights_commission", "literary_commission"]},
            {"cluster_id": "C4", "lead_methodology": "cd_05_paradox_hunter", "client_specialty": ["fintech_wallet", "ministry_of_commerce", "energy_major_green", "heritage_sports"]},
        ],
        "operational_departments": {
            "strategy": {"members_count_target": 2, "owns": "brief diagnosis, positioning"},
            "operations": {"members_count_target": 4, "owns": "production pipeline"},
            "finance": {"members_count_target": 4, "owns": "AR / cost control / cashback policy"},
            "hr": {"members_count_target": 2, "owns": "talent + culture"},
            "client_services": {"members_count_target": 19, "owns": "account management across all clusters"},
            "business_development": {"members_count_target": 4, "owns": "RFP responses + new-client acquisition"},
            "brand_marketing": {"members_count_target": 4, "owns": "agency's own brand"},
        },
        "board": {
            "size": 7,
            "roles": ["Chairman", "Vice Chairman", "Member", "Member", "Member/CEO", "Member/CGO-COO", "Member/CCO"],
            "secretary": True,
        },
        "provenance": prov(
            source="research_corpus/ogz_org_and_kpis.md + ogz_bd_pipeline.md (anonymized)",
        ),
    }


def kpi_definitions():
    return {
        "schema_version": 1,
        "title": "Internally tracked KPIs",
        "categories": {
            "financial": [
                {"name": "annual_revenue_target_sar", "owner": "CGO+COO", "cadence": "yearly", "target_2026": "150M+ SAR equivalent (post-platform-scale baseline)"},
                {"name": "net_profit_margin_pct", "owner": "CGO+COO + Finance", "cadence": "yearly", "target": "11% + 10% cashback = 21% combined"},
                {"name": "cogs_pct_of_revenue", "owner": "CGO+COO", "cadence": "quarterly", "target": "below 80%; production cap at 70% of project budget, plan to reduce to 65%"},
                {"name": "ar_outstanding_days", "owner": "Finance", "cadence": "monthly", "target": "median 45 days"},
            ],
            "client": [
                {"name": "client_renewal_rate_annual", "owner": "CGO+COO + Client Services", "cadence": "yearly", "target": "≥80% on retainers"},
                {"name": "new_client_pipeline_value_sar", "owner": "BD", "cadence": "monthly"},
                {"name": "rfp_win_rate", "owner": "BD", "cadence": "quarterly"},
                {"name": "client_satisfaction_score", "owner": "Client Services", "cadence": "quarterly"},
            ],
            "creative": [
                {"name": "festival_award_count_annual", "owner": "CCO + Pitch Team", "cadence": "yearly", "notes": "Athar + Effie + Cannes"},
                {"name": "two_cd_diagnostic_fire_rate", "owner": "CCO", "cadence": "monthly", "target": "20-30% of briefs (anti-sameness signal)"},
                {"name": "brand_fingerprint_distinctiveness_score_avg", "owner": "CCO", "cadence": "monthly", "target": "≥0.50 across active brands"},
            ],
            "platform_operational": [
                {"name": "ccoo_arabic_qc_avg_score", "owner": "CCO Agent operator", "cadence": "monthly", "target": "80% of posts scoring ≥50"},
                {"name": "first_post_to_value_time_min", "owner": "Product", "cadence": "weekly", "target": "<10 min from onboarding-complete"},
                {"name": "human_gate_trigger_rate", "owner": "CEO Agent operator", "cadence": "monthly", "target": "10-15% (too low = under-vigilant; too high = under-trained)"},
            ],
        },
        "provenance": prov(source="research_corpus/ogz_org_and_kpis.md (anonymized)"),
    }


def bd_pipeline_status():
    return {
        "schema_version": 1,
        "title": "BD pipeline — stages + qualification criteria",
        "stages": [
            {"id": 1, "name": "Lead", "criteria": "Inbound inquiry or outbound contact made. No qualification yet."},
            {"id": 2, "name": "Qualified", "criteria": "Budget bracket confirmed (≥X SAR), decision-maker identified, timeline known."},
            {"id": 3, "name": "Discovery Complete", "criteria": "Discovery call done. Brief understood. Sector fit confirmed."},
            {"id": 4, "name": "Proposal Sent", "criteria": "Financial + technical proposal delivered."},
            {"id": 5, "name": "Negotiation", "criteria": "Client counter-position received. Terms in active discussion."},
            {"id": 6, "name": "Won", "criteria": "Contract signed; payment terms agreed."},
            {"id": 7, "name": "Lost", "criteria": "Client chose competitor, deferred indefinitely, or budget pulled."},
        ],
        "qualification_questions": [
            "Is the contract value above Starter-tier minimum?",
            "Is the brand sector in our covered list (F&B / Retail / Beauty / Real Estate / Healthcare / Government)?",
            "Does the brand have Saudi-domestic primary audience?",
            "Is the decision-maker engaged or are we talking to a gatekeeper?",
            "Is the timeline realistic (>3 weeks for Growth, >6 weeks for Enterprise)?",
        ],
        "win_rate_thresholds": {
            "qualified_to_proposal": "≥60%",
            "proposal_to_won": "≥30%",
        },
        "provenance": prov(source="research_corpus/ogz_bd_pipeline.md + ogz_org_and_kpis.md (anonymized)"),
    }


def communication_rules():
    return {
        "schema_version": 1,
        "title": "Internal communication rules",
        "channels": {
            "decisions": "Mohamed (architect) chat + checkpoint events in audit log",
            "operations": "n8n workflow logs + Memory Controller events",
            "ad_hoc_questions": "Telegram via Mira bot (notification layer)",
            "deep_async_thinking": "Markdown PR comments on this repo",
        },
        "rituals": {
            "sunday_learning_cycle": {"when": "Sundays 02:00 Riyadh", "owner": "Learning Agent", "deliverable": "proposed pattern-library + cd_routing_weight updates"},
            "monthly_kpi_review": {"when": "first of month", "owner": "CGO+COO", "attendees": "leadership"},
            "weekly_account_status": {"when": "Tuesdays", "owner": "Client Services Director per cluster"},
            "morning_briefing": {"when": "daily 08:15 Riyadh", "owner": "Abraham operator script"},
        },
        "first_message_rule": "Every new session opens with status one-liner: date, last session summary, still-open items. Then stop and wait.",
        "send_rule": "No external email / proposal / communication sent without explicit Mohamed approval in chat first.",
        "provenance": prov(source="research_corpus/ogz_ingestion_log.md + Abraham operator rules"),
    }


def operational_rituals():
    return {
        "schema_version": 1,
        "title": "Operational rituals",
        "rituals": [
            {
                "name": "Sunday Learning Cycle",
                "when": "Sundays 02:00 Riyadh",
                "owner": "Learning Agent (Claude Sonnet 4.6)",
                "inputs": ["past-week outcome events", "past-week generation events", "current patterns library"],
                "outputs": "nominated pattern updates + cd_routing_weight nudges (PR proposals, human-approved before merge)",
            },
            {
                "name": "Weekly account review",
                "when": "Tuesdays 11:00 Riyadh per cluster",
                "owner": "Client Services Director",
                "purpose": "Surface accounts at risk, celebrate wins, escalate to CGO+COO if needed",
            },
            {
                "name": "Monthly KPI review",
                "when": "First Tuesday of each month",
                "owner": "CGO+COO",
                "purpose": "Review revenue / margin / distinctiveness-score / award-pipeline KPIs",
            },
            {
                "name": "Quarterly board review",
                "when": "First month of each quarter",
                "owner": "Chairman + Vice Chairman",
                "purpose": "Strategic priorities, succession planning, governance",
            },
            {
                "name": "Annual Athar/Cannes submission cycle",
                "when": "April-September",
                "owner": "CCO + Awards Strategist",
                "purpose": "Identify campaigns with festival potential; craft submission narratives",
            },
        ],
        "provenance": prov(source="research_corpus/ogz_org_and_kpis.md + ogz_ingestion_log.md"),
    }


# ────────────────────────────────────────────────────────────────────────────
# 09_how_to_run/ (6 files)
# ────────────────────────────────────────────────────────────────────────────

RUN = REPO / "09_how_to_run"

OPS_PIPELINE_A = """# Pipeline A — Operational Flow

**Tier:** Starter
**Audience:** Saudi SMEs, self-service
**Monthly content:** 8 posts
**Price point:** SAR 2,500/month
**Onboarding time:** under 4 minutes

## End-to-end flow

1. **Signup + payment** — Stripe customer + initial subscription
2. **15-question intake** (`14_brand_fingerprint/enhanced_onboarding/15_question_critical_starter.md`)
3. **Auto-extraction** — Apify (Instagram) + website + Google Business scrapers
4. **COO `build_branddna`** — maps form + extractions to 10 critical BrandDNA fields with confidence states
5. **Brand snapshot card** — client confirms or corrects fields (triggers revision flow)
6. **First calendar generation** — CEO routes → COO compiles CaptionContext → DeepSeek generates 8 captions → CCO Arabic QC → COO confidence score
7. **Gate routing** — clean (score ≥75) / watermarked (50-74) / hold (<50)
8. **Delivery** — Resend email + calendar dashboard

## Gates and auto-triggers

- **Confidence floor**: 0.6. Below this: paused, prompted to complete missing fields.
- **Auto-route to human gate**: first-ever output, healthcare sector, government sector, dialect_unconfirmed_hero content.
- **Watermark required**: confidence_mode `Cautious` or `Minimal`.

## What happens when something fails

| Failure | Auto-response |
|---|---|
| Apify scrape times out | Mark Instagram fields `inferred_low`; continue with form data only |
| BrandDNA `dialect_confirmed: false` | Surface dialect-confirm prompt; hold hero content |
| CCO returns `HARD_BLOCK` on any post | Auto-regenerate; if 2nd attempt also fails, route to human review |
| Cost ceiling breached for the month | Pause generation; surface upgrade prompt |
"""

OPS_PIPELINE_B = """# Pipeline B — Operational Flow

**Tier:** Growth + Enterprise
**Audience:** Saudi growing brands + larger / government / enterprise
**Monthly content:** 20-40+ posts
**Onboarding time:** 25-40 minutes across 2-3 sessions
**Strategist + Cultural Advisor involved**

## End-to-end flow

1. **Sales qualification** — BD discovery call
2. **Strategist assigned** — primary contact for onboarding
3. **60-question intake** (`14_brand_fingerprint/enhanced_onboarding/60_question_full_intake.md`) — across 7 sections, 3 strategist checkpoints
4. **Cultural Advisor review** — full cultural-spec sign-off before activation
5. **COO build-branddna (extended)** — all fields `explicitly_confirmed`
6. **Strategist final review** — 60-min call walking through complete fingerprint + first-month content plan
7. **Monthly calendar generation** — Growth: 20 posts; Enterprise: 40+
8. **Hero content human-reviewed** — CD lead level (Enterprise) or strategist (Growth)

## Confidence floors

- Growth: 0.65
- Enterprise: 0.7

## What happens when something fails

Same auto-responses as Pipeline A, plus:

- **Strategist call missed**: reschedule within 5 business days; pause onboarding past 14 days
- **Cultural Advisor flags review**: hero content paused; strategist + Mohamed + brand jointly review
"""

OPS_DECISION_AUTH = """# Decision Authority

**Who decides what.** Per Pipeline A vs Pipeline B.

## Pipeline A (Starter) — distribution

- **System decides:** ~15 routine decisions per brief (chain selection, occasion check, confidence scoring, gate routing).
- **Client decides:** ~5 decisions (brand DNA confirmation, post approval, schedule preferences, brand corrections, upgrade choice).

## Pipeline B (Growth + Enterprise) — distribution

- **System decides:** ~15 routine decisions (same as Starter).
- **Client decides:** ~25 decisions (all hero content, cd_routing_weights, Cultural Advisor sign-off acceptance, monthly content plan approval).
- **Strategist decides:** ~20 decisions (creative direction, occasion plays, brave-route approvals, monthly retros).

## Override authority

In all cases:
1. Universal forbidden lists (hard-blocks) — non-negotiable. No override.
2. Saudi compliance rules — Cultural Advisor + Mohamed jointly required for override.
3. Brand explicit rejection — respected absolutely.
4. Cultural Advisor verdict — beats CCO score.
5. Brand fingerprint — beats sector default.
6. Occasion overrides — beat standard sector defaults during active windows.
"""

OPS_DATA_CONSENT = """# Data Consent Policy (PDPL-aligned)

## Scope

All client data processed by `{PLATFORM_NAME}`. Includes onboarding form answers, scraped Instagram / website / Google Business public data, generated content, outcome events.

## PDPL principles applied

- **Lawfulness, fairness, transparency**: clients informed at signup of all data we collect.
- **Purpose limitation**: data used only for the platform's content-generation purposes. No cross-brand data mixing.
- **Data minimization**: collect only the 10 critical BrandDNA Lite fields + opt-in extras.
- **Accuracy**: clients can correct any field via revision flow at any time.
- **Storage limitation**: 90-day soft-quarantine on deletion; hard delete on documented process.
- **Integrity and confidentiality**: RLS-isolated per-brand storage; encrypted-at-rest.
- **Accountability**: every data event logged in audit trail.

## Client rights under PDPL

- Right to access (export all data)
- Right to rectification (correct any field)
- Right to erasure (delete brand data; 30-day SLA)
- Right to object to processing (pause generation)
- Right to data portability (export to standard format)

## What the platform does NOT do

- Does not sell or share brand data with third parties
- Does not cross-brand-mix data
- Does not use brand-specific data to train shared LoRAs without explicit consent
- Does not retain scraped data beyond what's needed for content generation
"""

OPS_DATA_RESIDENCY = """# Data Residency Policy

## Stance

`{PLATFORM_NAME}` is a Saudi-native platform. Data residency posture reflects that.

## Primary region

- **Supabase Postgres**: `me-central-1` (Bahrain) — closest to Saudi with full Supabase regional support.
- **Object storage (R2/S3)**: KSA region where available; Bahrain fallback.
- **fal.ai**: regional endpoint where available; global with KSA data residency clauses negotiated.

## Backup

- Daily encrypted backup to KSA-based backup region.
- 90-day backup retention; quarterly snapshots for 1 year.

## What stays in KSA (mandatory)

- Customer identifying information
- Brand fingerprint and brand-specific generated content
- Outcome events with engagement data
- OAuth tokens (encrypted at rest)

## What can be processed regionally

- Generic chain definitions (universal, no brand-specific data)
- Universal forbidden lists
- Public benchmark account references

## Compliance posture

- PDPL aligned (Personal Data Protection Law of KSA)
- ISO 27001 target for 2026 Q4
- SOC 2 Type II target for 2027

## Breach response

See `breach_response.md`.
"""

OPS_BREACH = """# Breach Response Runbook

## PDPL 72-hour notification requirement

Under Saudi PDPL, data subjects must be notified of a breach affecting their personal data within **72 hours** of the breach being identified.

## Detection

Breach indicators:
- Unauthorized access logged in audit trail
- Data exfiltration detected by infrastructure monitoring
- Customer reports unusual activity
- Cross-brand data exposure detected (RLS failure)

## Immediate response (within 1 hour of detection)

1. **Contain** — revoke any compromised credentials, freeze affected services
2. **Notify CGO+COO and CEO** — internal escalation
3. **Activate Incident Response Team** — Mohamed + Cultural Advisor + Infrastructure lead
4. **Preserve evidence** — snapshot logs, no destructive actions yet

## Investigation (within 24 hours)

1. Scope assessment — which brands' data was affected?
2. Root cause identification
3. Containment effectiveness verification
4. Customer impact estimate

## Notification (within 72 hours)

1. Affected customers — email + platform inbox notification
2. PDPL regulator notification (if required by scope)
3. Public statement (only if scope warrants and after legal review)

## Remediation

1. Patch / fix the underlying issue
2. Audit log review for similar patterns
3. Process update — what would prevent this next time?
4. Post-mortem document (internal)

## Post-incident

- Update threat model
- Retrain incident response team
- Adjust monitoring rules
"""


# ────────────────────────────────────────────────────────────────────────────
# 16_character_library/ stub
# ────────────────────────────────────────────────────────────────────────────

CHAR_README = """# 16_character_library/

Visual content reference library for character / wardrobe / architecture / props / gestures / rituals.

**Status:** Stub structure for v1.0.0. Actual reference content lives in object storage with LFS pointers; this folder holds the organizational manifest.

## Subfolders

| Folder | Contents |
|---|---|
| `faces/` | Reference face crops by region (Najdi / Hejazi / Eastern / Southern) and age bracket |
| `wardrobe/` | Reference thobe / abaya / accessory / fabric crops by sector × region |
| `architecture/` | Reference architectural elements (Najdi mud-brick arches, Hejazi rawasheen, modern Riyadh) |
| `props/` | Reference props (dallah, fenjan, mabkhara, sadu, modern tech) |
| `gestures/` | Reference gesture stills (right-hand-only serving, hand-on-heart, etc.) |
| `rituals/` | Reference ritual scene stills (iftar moment, Eid greeting, prayer-on-camera-pause) |

## Each subfolder contains

- `MANIFEST.md` — what goes in this folder
- `.gitkeep` — preserves folder in git when empty

## What goes in vs object storage

- **In git** (this repo): manifest + .gitkeep + small reference thumbnails (<100KB each)
- **In object storage**: full-resolution reference images; URIs tracked in `frame_v1.schema.json` records
"""


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────

def main() -> int:
    print("═══ 22_org_context/ (5 yamls) ═══")
    write_yaml(ORG / "org_structure.yaml",      org_structure(),       "Anonymized 4-cluster organization.")
    write_yaml(ORG / "kpi_definitions.yaml",    kpi_definitions(),     "KPIs tracked internally.")
    write_yaml(ORG / "bd_pipeline_status.yaml", bd_pipeline_status(),  "BD pipeline stages + qualification criteria.")
    write_yaml(ORG / "communication_rules.yaml", communication_rules(), "Internal communication rules + first-message + send rules.")
    write_yaml(ORG / "operational_rituals.yaml", operational_rituals(), "Sunday Learning Cycle + weekly + monthly + quarterly + annual rituals.")

    print("\n═══ 09_how_to_run/ (6 docs) ═══")
    write_md(RUN / "pipeline_a_flow.md", OPS_PIPELINE_A)
    write_md(RUN / "pipeline_b_flow.md", OPS_PIPELINE_B)
    write_md(RUN / "decision_authority.yaml", OPS_DECISION_AUTH)  # actually .yaml-style? keep .md
    write_md(RUN / "data_consent_policy.md", OPS_DATA_CONSENT)
    write_md(RUN / "data_residency_policy.md", OPS_DATA_RESIDENCY)
    write_md(RUN / "breach_response.md", OPS_BREACH)

    print("\n═══ 16_character_library/ stub ═══")
    write_md(REPO / "16_character_library" / "README.md", CHAR_README)
    for subfolder in ["faces", "wardrobe", "architecture", "props", "gestures", "rituals"]:
        p = REPO / "16_character_library" / subfolder
        p.mkdir(parents=True, exist_ok=True)
        (p / ".gitkeep").write_text("")
        (p / "MANIFEST.md").write_text(f"# {subfolder.capitalize()} manifest\n\nFull-resolution reference content lives in object storage. Manifests + references tracked via `frame_v1.schema.json` records.\n")
        print(f"✓ 16_character_library/{subfolder}/ ({{MANIFEST.md, .gitkeep}})")

    print(f"\nDay 5 generators (org + ops + character) complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
