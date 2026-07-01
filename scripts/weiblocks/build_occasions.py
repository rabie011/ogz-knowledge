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
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "06_saudi_calendar"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"  # stamped (deterministic), not now()

# REAL occasion_slug (read from inside each YAML, NOT the filename) -> spec occasion_key
# (controlled vocab §3; stable snake_case invented for the new ones). The two that used to
# fall through to raw slugs — 'mdl_beast' and '11_11_shopping' — are now mapped explicitly.
# Original slug is preserved verbatim in extra.source_label.
KEY_MAP = {
    "ramadan": "ramadan", "eid_al_fitr": "eid_fitr", "eid_al_adha": "eid_adha",
    "hajj_season": "hajj_season", "saudi_national_day": "national_day",
    "saudi_founding_day": "founding_day", "riyadh_season": "riyadh_season",
    "jeddah_season": "jeddah_season", "white_friday": "white_friday",
    "11_11_shopping": "singles_day", "arab_mothers_day": "mothers_day",
    "esports_world_cup": "esports_world_cup", "leap_conference": "leap_conference",
    "mdl_beast": "soundstorm",
}
SECTORS = ["F&B", "Retail", "Beauty_Wellness", "Healthcare", "Real_Estate", "Corporate_Services", "Other"]
ENTERTAINMENT = {"riyadh_season", "jeddah_season", "esports_world_cup", "leap_conference", "soundstorm"}
COMMERCIAL = {"white_friday", "singles_day"}
# hard_rules = ONLY law/religious/flag/modesty-level. Softer style anti-patterns are NOT hard rules;
# they move to extra.soft_flags. These keywords select the law-tier lines out of donts + anti-patterns.
HARD_KW = ["law", "flag", "fasting", "daylight", "prayer", "haram", "modesty", "alcohol"]


def derive_type(key, cs):
    if cs.get("religious_weight") in ("highest", "high"):
        return "religious"
    if cs.get("patriotic_weight") in ("highest", "high"):
        return "national"
    if key in ENTERTAINMENT:
        return "entertainment"
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
    }
    emap["eid_fitr"] = emap["eid_adha"] = emap["ramadan"]
    emap["founding_day"] = emap["national_day"]
    per = emap.get(key)
    out = {}
    for s in SECTORS:
        out[s] = {"applies": True, "emphasis": (per.get(s, "") if per else "seasonal relevance")}
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
        key = KEY_MAP.get(slug, slug)
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
            "provenance": {
                "source": "manual_curation", "confidence": "experimental",
                "observed_count": None, "date_added": DATE_ADDED, "scope": f"occasion:{key}",
            },
            "extra": {
                "source_label": slug,
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
