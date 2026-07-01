#!/usr/bin/env python3
"""build_extensions.py — versioned-knowledge EXTENSIONS beyond the 8-entity spec (panel-ruled;
rebuilt after the July-1 daemon wipe). The spec (§0/§4.7) invites filling gaps; the platform's
Creative-Direction + scorecard logic is KNOWLEDGE that must be versioned, not hardcoded in runtime
code ("you own WHAT, they own HOW" — DeepSeek 38a66141).

  creative_methods.json   — 6 CD brains as versioned method definitions + affinities, HONESTLY mapped
                            to the BrandDNA guide's 6 methods (Vulnerability = OGz gap, never force-fit;
                            feed_cloner = OGz-proprietary, flagged).
  routing_rules.json      — the deterministic CD-brain router (formula + gates + occasion boosts).
                            The WHAT; the dev team keys it to archetype×stage×intent (the HOW).
  scorecard_weights.json  — 5 scorecard dimensions, GUIDE-SOURCED not measured (source=brand_dna_guide,
                            extra.not_measured=true — never presented as empirical).
"""
import glob
import re
from pathlib import Path

import json
import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAINS = ROOT / "20_cd_brains"
ROUTER = ROOT / "10_agent_brains" / "cd_brain_router_rules.yaml"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"

METHOD_MAP = {
    "cd_01_firaasa_architect": ("diagnostic", False),
    "cd_02_metaphor_architect": ("metaphor", False),
    "cd_03_authenticity_detective": ("authenticity", False),
    "cd_04_heritage_decoder": ("heritage", False),
    "cd_05_paradox_hunter": ("paradox", False),
    "cd_06_feed_cloner": ("feed_cloner", True),   # OGz-only; NOT one of the guide's 6
}
GUIDE_METHODS = {"authenticity", "heritage", "vulnerability", "diagnostic", "metaphor", "paradox"}


def _prov(source, scope):
    return {"source": source, "confidence": "experimental", "observed_count": None,
            "date_added": DATE_ADDED, "scope": scope}


def front_matter(fp):
    m = re.search(r"^---\n(.*?)\n---", Path(fp).read_text(encoding="utf-8"), re.DOTALL)
    return (yaml.safe_load(m.group(1)) if m else None) or {}


def build_creative_methods():
    recs = []
    for fp in sorted(glob.glob(str(BRAINS / "cd_0*.md"))):
        fm = front_matter(fp)
        slug = fm.get("cd_brain_slug") or Path(fp).stem
        method_key, is_prop = METHOD_MAP.get(slug, (slug, False))
        recs.append({
            "id": fm.get("cd_brain_ulid") or f"cm_{slug}",
            "entity": "creative_method",
            "method_key": method_key,
            "ogz_brain_slug": slug,
            "name": fm.get("name_external") or fm.get("name_internal"),
            "diagnostic_question": fm.get("diagnostic_question"),
            "voice_register": fm.get("voice_register"),
            "signature_technique": fm.get("signature_technique"),
            "sector_affinity": fm.get("sector_affinity") or {},
            "occasion_affinity": fm.get("occasion_affinity") or {},
            "best_fits": fm.get("best_fits") or [],
            "anti_patterns": fm.get("anti_patterns") or [],
            "provenance": _prov("manual_curation", f"creative_method:{method_key}"),
            "extra": {
                "maps_to_brandDNA_method": method_key if method_key in GUIDE_METHODS else None,
                "is_ogz_proprietary": is_prop,
                "note": ("OGz-proprietary method, not one of the BrandDNA guide's 6" if is_prop else None),
            },
        })
    return recs


def build_routing_rules():
    rr = yaml.safe_load(ROUTER.read_text(encoding="utf-8")) or {}
    sf = rr.get("scoring_formula", {})
    sel = rr.get("selection_rules", {})
    return [{
        "id": "routing_rule_cd_brain_v1",
        "entity": "routing_rule",
        "scoring_formula": sf.get("definition"),
        "occasion_factor_rule": sf.get("occasion_factor_rule"),
        "tie_break_priority": sf.get("tie_break_priority") or [],
        "two_cd_diagnostic_gate": sel.get("two_cd_diagnostic_gate"),
        "minimum_score_floor": sel.get("minimum_score_floor"),
        "occasion_overrides": rr.get("occasion_overrides") or {},
        "provenance": _prov("manual_curation", "universal"),
        "extra": {"keying": "sector×occasion + brand cd_routing_weights (the WHAT); the dev team keys "
                            "to archetype×stage×intent (the HOW)",
                  "owner": "CD-Brain Router (deterministic, not an LLM)"},
    }]


def build_scorecard_weights():
    DIMS = [
        ("cultural_fit", 0.30, "the moat — hardest to fake; our biggest advantage"),
        ("visual_quality", 0.20, "production quality + composition"),
        ("brand_coherence", 0.20, "consistency of identity across content"),
        ("posting_consistency", 0.15, "cadence + rhythm"),
        ("engagement_health", 0.15, "audience response signal"),
    ]
    recs = []
    for dim, w, note in DIMS:
        recs.append({
            "id": f"scorecard_{dim}",
            "entity": "scorecard_dimension",
            "dimension": dim, "weight": w, "note": note,
            "missing_data_rule": "if a dimension has no data it is excluded and its weight shared across the rest",
            "provenance": _prov("brand_dna_guide", "scorecard"),
            "extra": {"guide_sourced": True, "not_measured": True,
                      "warning": "weights come from the BrandDNA guide, NOT from measured outcomes"},
        })
    return recs


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "creative_methods.json": build_creative_methods(),
        "routing_rules.json": build_routing_rules(),
        "scorecard_weights.json": build_scorecard_weights(),
    }
    for name, recs in outputs.items():
        json.dump(recs, open(OUT / name, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"wrote {len(recs):2} -> {name}")
    print("NOTE: BrandDNA method 'vulnerability' has NO OGz brain — flagged as a gap, not force-fit.")
    return outputs


if __name__ == "__main__":
    build()
