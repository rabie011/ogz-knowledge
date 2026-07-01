#!/usr/bin/env python3
"""build_occasions.py — transform OGZ occasion YAMLs -> Weiblocks §5.3 occasion records.

Reads 06_saudi_calendar/*.yaml (14 real, curated Saudi occasions), maps present fields directly,
and DERIVES the behavior fields the spec wants that our schema lacks (type, priority, lead_weeks,
recommended_mix_shift, tone_shift, sector_applicability, hard_rules). Every derived field is listed
in extra.derived_fields and provenance.confidence carries the source files' self-declared
'experimental' — so nothing is silently presented as observed (honesty rule).

Occasions are RULE-BASED, not date-based: we ship behavior/rules, NOT the resolved date (the engine
resolves Hijri/Gregorian itself). Native Arabic preserved (ensure_ascii=False). Nothing dropped —
source-only fields (recommended_chains, day_specific_variations, etc.) go to extra.
"""
import glob
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from occasion_keys import normalize  # THE one shared slug->occasion_key map (never local)

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "06_saudi_calendar"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"  # stamped (deterministic), not now()

SECTORS = ["F&B", "Retail", "Beauty_Wellness", "Healthcare", "Real_Estate", "Corporate_Services", "Other"]
# Sector baselines NOT shipped in this export (held): consumers get the occasion knowledge
# (it is real) but each held sector object carries held:true so nobody joins to a missing baseline.
HELD_SECTORS = {"Healthcare", "Real_Estate"}
ENTERTAINMENT = {"riyadh_season", "jeddah_season", "esports_world_cup", "leap_conference", "soundstorm"}
COMMERCIAL = {"white_friday", "singles_day"}
# hard_rules = ONLY law/religious/flag/modesty-level. Softer style anti-patterns are NOT hard rules;
# they move to extra.soft_flags. These keywords select the law-tier lines out of donts + anti-patterns.
HARD_KW = ["law", "flag", "fasting", "daylight", "prayer", "haram", "modesty", "alcohol"]


def derive_type(key, cs):
    # PRECEDENCE CONTRACT (do not reorder): religious > entertainment > national > commercial.
    # Entertainment membership beats patriotic_weight — Saudi mega-events (esports_world_cup,
    # leap_conference, riyadh_season) all carry patriotic_weight=high but are entertainment/
    # business occasions, not national holidays. A key in ENTERTAINMENT with religious_weight
    # high would still come out religious — intended: religion always wins.
    if cs.get("religious_weight") in ("highest", "high"):
        return "religious"
    if key in ENTERTAINMENT:
        return "entertainment"
    if cs.get("patriotic_weight") in ("highest", "high"):
        return "national"
    return "commercial"


def derive_priority(cs):
    if "highest" in (cs.get("religious_weight"), cs.get("patriotic_weight")):
        return "critical"
    ca = str(cs.get("commercial_activity", "")).lower()
    return "high" if ("peak" in ca or "high" in ca) else "medium"


def phases_from(dsv):
    out = []
    if isinstance(dsv, dict):
        for k, v in dsv.items():
            g = (v.get("focus") or v.get("content_emphasis") or "") if isinstance(v, dict) else str(v)
            out.append({"phase": k, "guidance": g})
    return out


def tone_shift_from(cs, dsv):
    ems = [v["emotion"] for v in (dsv.values() if isinstance(dsv, dict) else [])
           if isinstance(v, dict) and v.get("emotion")]
    base = "warmer, community-focused" if cs.get("family_centrality") in ("highest", "high") else "elevated, celebratory"
    return base + (" ; phases: " + " → ".join(ems) if ems else "")


def mix_shift_from(cs):
    if cs.get("religious_weight") == "highest":
        return {"emotional": 0.5, "lifestyle": 0.3, "offer": 0.2}
    if cs.get("patriotic_weight") == "highest":
        return {"emotional": 0.45, "lifestyle": 0.35, "offer": 0.2}
    return {"emotional": 0.3, "lifestyle": 0.35, "offer": 0.35}


def sector_applicability(key):
    emap = {
        "ramadan": {"F&B": "iftar/suhoor, family bundles", "Retail": "gifting, eid wardrobe ramp",
                    "Beauty_Wellness": "eid prep, subtle", "Healthcare": "wellness during fasting",
                    "Real_Estate": "family gatherings at home", "Corporate_Services": "greetings, CSR",
                    "Other": "warm seasonal greeting"},
        "national_day": {"F&B": "national menus, green accents", "Retail": "national collections",
                         "Beauty_Wellness": "green-themed looks", "Healthcare": "community pride",
                         "Real_Estate": "Vision 2030 living", "Corporate_Services": "pride, achievement",
                         "Other": "celebratory national greeting"},
        # founding_day is NOT national_day (source YAML content_donts forbid conflating them:
        # Founding = 1727 First Saudi State, Najdi-historical, Dir'iyah palette terracotta/palm
        # green/sand, traditional crafts + dress — NOT green accents, NOT Vision 2030).
        "founding_day": {"F&B": "heritage dishes, Dir'iyah palette (terracotta, palm green, sand)",
                         "Retail": "heritage collections, traditional crafts, terracotta/sand palette",
                         "Beauty_Wellness": "heritage-inspired looks, historic dress accents, subtle",
                         "Healthcare": "community heritage pride, rooted and dignified",
                         "Real_Estate": "Dir'iyah/Najdi heritage architecture (mud-brick, palm groves)",
                         "Corporate_Services": "founding heritage, three centuries narrative (1727)",
                         "Other": "heritage greeting, Dir'iyah palette"},
    }
    emap["eid_fitr"] = emap["eid_adha"] = emap["ramadan"]
    per = emap.get(key)
    out = {}
    for s in SECTORS:
        entry = {"applies": True, "emphasis": (per.get(s, "") if per else "seasonal relevance")}
        if s in HELD_SECTORS:
            entry["held"] = True  # knowledge is real; the sector BASELINE is not shipped in v1
        out[s] = entry
    return out


def _is_hard(s):
    return any(k in s.lower() for k in HARD_KW)


def split_rules(donts, apw):
    """hard_rules = ONLY law/religious/flag/modesty-level lines (keyword-gated) drawn from BOTH
    content_donts and anti_pattern_warnings. Softer STYLE anti-patterns (generic-caption, tonal,
    aesthetic) are NOT hard rules — they go to soft_flags. content_donts stay in full in `donts`
    (the record keeps them there regardless); only the law-tier subset is also lifted into hard_rules.
    Returns (hard_rules, soft_flags)."""
    hard, soft = [], []
    for d in (donts or []):
        s = d if isinstance(d, str) else json.dumps(d, ensure_ascii=False)
        if _is_hard(s):
            hard.append(s)  # law-tier dont is also a hard rule (donts still keeps all of them)
    for a in (apw or []):
        s = a if isinstance(a, str) else json.dumps(a, ensure_ascii=False)
        (hard if _is_hard(s) else soft).append(s)
    return hard, soft


def build():
    records = []
    for fp in sorted(glob.glob(str(SRC / "*.yaml"))):
        d = yaml.safe_load(open(fp, encoding="utf-8"))
        if not d:
            continue
        slug = d.get("occasion_slug") or Path(fp).stem
        key, _ = normalize(slug)  # shared module, never a local map
        if key is None:  # Rule #8: refuse, don't warn — an unmapped occasion must not ship
            raise SystemExit(f"REFUSE: occasion slug {slug!r} ({fp}) not resolvable by "
                             f"occasion_keys.normalize — add it to the shared module first")
        yprov = d.get("provenance", {}) or {}
        cs = d.get("cultural_significance", {}) or {}
        dr = d.get("date_recurrence", {}) or {}
        dsv = d.get("day_specific_variations", {}) or {}
        lead_days = d.get("preparation_lead_days")
        hard_rules, soft_flags = split_rules(d.get("content_donts"), d.get("anti_pattern_warnings"))
        records.append({
            "id": d.get("occasion_ulid"),
            "entity": "occasion",
            "occasion_key": key,
            "name_en": d.get("name_en"),
            "name_ar": d.get("name_ar"),
            "type": derive_type(key, cs),
            "priority": derive_priority(cs),
            "lead_weeks": (round(lead_days / 7) if isinstance(lead_days, (int, float)) else None),
            "calendar_basis": dr.get("type"),  # hijri|gregorian — metadata only, NOT a date
            "phases": phases_from(dsv),
            "recommended_mix_shift": mix_shift_from(cs),
            "themes": d.get("content_focus_themes") or [],
            "tone_shift": tone_shift_from(cs, dsv),
            "sector_applicability": sector_applicability(key),
            "dos": d.get("content_dos") or [],
            "donts": d.get("content_donts") or [],
            "hard_rules": hard_rules,
            # TRUE provenance carried from the YAML's own block (never hardcoded): real source
            # (xlsx corpus / internet_research), Mohamed as confirmer where present, and the
            # YAML's self-declared confidence. Unknown -> null, never invented.
            "provenance": {
                "source": yprov.get("source"), "confidence": yprov.get("confidence") or "experimental",
                "confirmer": yprov.get("confirmer"),
                "observed_count": None, "date_added": DATE_ADDED, "scope": f"occasion:{key}",
            },
            "extra": {
                "source_label": slug,
                "source_date_added": yprov.get("date_added"),  # the YAML's own timestamp
                **({"provenance_missing_source": True} if not yprov.get("source") else {}),
                "derived_fields": ["type", "priority", "lead_weeks", "recommended_mix_shift",
                                   "tone_shift", "sector_applicability", "hard_rules", "soft_flags"],
                "derived_note": "behavior fields inferred from cultural_significance weights + "
                                "day_specific_variations; curated, NOT observed. hard_rules = only "
                                "law/religious/flag/modesty-level lines (keyword-gated: law, flag, "
                                "fasting, daylight, prayer, haram, modesty, alcohol) lifted from "
                                "content_donts + anti_pattern_warnings; softer STYLE anti-patterns "
                                "go to soft_flags",
                "soft_flags": soft_flags,
                "date_recurrence_detail": dr,
                "cultural_significance": cs,
                "recommended_chains": d.get("recommended_chains") or [],
                "reference_campaigns": d.get("reference_campaigns") or [],
                "day_specific_variations": dsv,
            },
        })
    OUT.mkdir(parents=True, exist_ok=True)
    outfp = OUT / "occasions.json"
    json.dump(records, open(outfp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {len(records)} occasion records -> {outfp}")
    print("keys:", ", ".join(r["occasion_key"] for r in records))
    return records


if __name__ == "__main__":
    build()
