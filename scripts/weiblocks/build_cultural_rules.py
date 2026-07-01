#!/usr/bin/env python3
"""build_cultural_rules.py — Weiblocks §5.4 cultural_rules.json (TWO record types in one file).

DeepSeek-ruled (W3, stamped ab0237a0 / 38a66141):
  RULE records (entity=cultural_rule):
    - 4 universal forbidden lists -> tier=hard_block (source enforcement_level), domain=singular list_kind.
    - gender_rules.patterns -> domain=gender_modesty, tier from `level` (allowed→advisory, else soft_flag/
      hard_block).
    - saudi_visual_rules (color_semantics/motif_rules/photography_conventions) -> domain=visual,
      tier=advisory (guidance, not compliance).
    - arabic_text_rules SKIPPED (no matching domain enum) — logged as unmapped_language_rules.
    - description_ar = null + extra.translation_needed=true (never machine-translate cultural rules).
  FIELD records (entity=cultural_rule, rule_key=culturalspec_field):
    - one per (field_group, field_name) across the 10 cultural-spec files.
    - sector_defaults keyed by SECTOR (primary/base variant per sector); region_variation Najdi/Hejazi
      (F&B only); all style variants preserved in extra.style_variants; held sectors flagged is_held.

Native Arabic raw (ensure_ascii=False).
"""
import glob
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FORBID = ROOT / "15_cultural_specs" / "forbidden_lists"
RULES = ROOT / "04_saudi_rules"
SPECS = ROOT / "15_cultural_specs" / "sector_defaults"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"

LIST_DOMAIN = {"gestures": "gesture", "props": "prop", "behaviors": "behavior", "visuals": "visual"}
# cultural-spec file -> (sector_key, region|None, style|None)
FILEMAP = {
    "f_and_b_najdi": ("F&B", "Najdi", None), "f_and_b_hejazi": ("F&B", "Hejazi", None),
    "beauty_personal_care": ("Beauty_Wellness", None, "personal_care"),
    "beauty_modern": ("Beauty_Wellness", None, "modern"), "beauty_heritage": ("Beauty_Wellness", None, "heritage"),
    "retail_modern": ("Retail", None, "modern"), "retail_heritage": ("Retail", None, "heritage"),
    "retail_lifestyle": ("Retail", None, "lifestyle"),
    "healthcare_modern": ("Healthcare", None, "modern"),
    "real_estate_modern_najdi": ("Real_Estate", "Najdi", "modern"),
}
HELD = {"Healthcare", "Real_Estate"}
PRIMARY = {"F&B": "f_and_b_najdi", "Beauty_Wellness": "beauty_personal_care",
           "Retail": "retail_modern", "Healthcare": "healthcare_modern",
           "Real_Estate": "real_estate_modern_najdi"}
SPEC_GROUPS = ["characters", "wardrobe", "body_language", "gestures", "settings_architecture",
               "props_objects", "behaviors_rituals", "social_dynamics"]


def _id(*parts):
    return "crule_" + hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16].upper()


def _prov(scope, conf="experimental"):
    return {"source": "manual_curation", "confidence": conf, "observed_count": None,
            "date_added": DATE_ADDED, "scope": scope}


def _level_to_tier(level):
    lv = str(level or "").lower()
    if any(k in lv for k in ("forbid", "never", "not_allowed", "prohibited")):
        return "hard_block"
    if "allow" in lv:
        return "advisory"
    return "soft_flag"


def build_rules():
    recs = []
    # 1) forbidden lists
    for fp in sorted(glob.glob(str(FORBID / "universal_*_forbidden.yaml"))):
        d = yaml.safe_load(open(fp, encoding="utf-8")) or {}
        kind = d.get("list_kind")
        domain = LIST_DOMAIN.get(kind, "behavior")
        tier = d.get("enforcement_level", "hard_block")
        for e in (d.get("entries") or []):
            recs.append({
                "id": e.get("id") or _id("forbid", kind, e.get("name")),
                "entity": "cultural_rule", "rule_key": e.get("name"),
                "tier": tier, "domain": domain,
                "description_en": e.get("description"), "description_ar": None,
                "scope": "universal", "action": "block_and_regenerate",
                "rationale": e.get("rationale"), "examples": [],
                "provenance": _prov("universal"),
                "extra": {"severity": e.get("severity"), "detection_hints": e.get("detection_hints") or [],
                          "translation_needed": True, "source_list": kind},
            })
    # 2) gender_rules.patterns -> gender_modesty
    g = yaml.safe_load(open(RULES / "gender_rules.yaml", encoding="utf-8")) or {}
    for name, v in (g.get("patterns") or {}).items():
        rule = v.get("rule") if isinstance(v, dict) else str(v)
        level = v.get("level") if isinstance(v, dict) else None
        recs.append({
            "id": _id("gender", name), "entity": "cultural_rule", "rule_key": name,
            "tier": _level_to_tier(level), "domain": "gender_modesty",
            "description_en": rule, "description_ar": None, "scope": "universal",
            "action": "flag_for_review", "rationale": None, "examples": [],
            "provenance": _prov("universal"),
            "extra": {"level": level, "translation_needed": True, "source": "gender_rules.patterns"},
        })
    # 3) saudi_visual_rules -> visual/advisory (atomize)
    v = yaml.safe_load(open(RULES / "saudi_visual_rules.yaml", encoding="utf-8")) or {}
    for cname, cval in (v.get("color_semantics") or {}).items():
        desc = cval.get("rule") if isinstance(cval, dict) else str(cval)
        recs.append({
            "id": _id("visual", "color", cname), "entity": "cultural_rule", "rule_key": f"color_{cname}",
            "tier": "advisory", "domain": "visual", "description_en": desc, "description_ar": None,
            "scope": "universal", "action": "annotate", "rationale": None, "examples": [],
            "provenance": _prov("universal"),
            "extra": {"hex": (cval.get("hex") if isinstance(cval, dict) else None),
                      "translation_needed": True, "source": "saudi_visual_rules.color_semantics"},
        })
    mr = v.get("motif_rules") or {}
    if mr:
        recs.append({
            "id": _id("visual", "motifs"), "entity": "cultural_rule", "rule_key": "approved_motifs",
            "tier": "advisory", "domain": "visual",
            "description_en": "Culturally authentic Saudi motifs approved when used respectfully.",
            "description_ar": None, "scope": "universal", "action": "annotate", "rationale": None,
            "examples": mr.get("approved_when_authentic") or [], "provenance": _prov("universal"),
            "extra": {"translation_needed": True, "source": "saudi_visual_rules.motif_rules"},
        })
    # 4) arabic_text_rules -> SHIPPED (nothing dropped, §4.7) as advisory records. The spec domain enum
    #    has no 'language/text' value, so domain='visual' (least-wrong: text renders visually) + extra
    #    flags the true domain honestly. NOT 'religious hard_block' (that would mislabel a style rule).
    a = yaml.safe_load(open(RULES / "arabic_text_rules.yaml", encoding="utf-8")) or {}
    mapped_sections = []

    def _txt_rule(rkey, desc, examples=None):
        recs.append({
            "id": _id("arabictext", rkey), "entity": "cultural_rule", "rule_key": f"arabic_text_{rkey}",
            "tier": "advisory", "domain": "visual", "description_en": desc, "description_ar": None,
            "scope": "universal", "action": "annotate", "rationale": None, "examples": examples or [],
            "provenance": _prov("universal"),
            "extra": {"true_domain": "language_text", "enum_mismatch": True, "translation_needed": True,
                      "source": f"arabic_text_rules.{rkey}"},
        })
    for name, val in (a.get("writing_conventions") or {}).items():
        _txt_rule(name, val if isinstance(val, str) else json.dumps(val, ensure_ascii=False))
        mapped_sections.append(f"writing_conventions.{name}")
    ts = a.get("translation_smell") or {}
    if ts:
        _txt_rule("translation_smell", ts.get("description", "Indicators of machine-translated (non-native) Arabic copy."),
                  ts.get("indicators") or [])
        mapped_sections.append("translation_smell")
    for sec in ("rendering", "msa_usage", "codeswitching", "dialect_default"):
        v = a.get(sec)
        if v:
            _txt_rule(sec, v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
            mapped_sections.append(sec)
    return recs, mapped_sections


def build_fields():
    # load all spec files keyed by their stem
    specs = {}
    for fp in glob.glob(str(SPECS / "*.yaml")):
        stem = Path(fp).stem
        if stem in FILEMAP:
            specs[stem] = yaml.safe_load(open(fp, encoding="utf-8")) or {}
    recs = []
    for group in SPEC_GROUPS:
        # collect the field names present in this group across all files
        fields = set()
        for stem, d in specs.items():
            if isinstance(d.get(group), dict):
                fields.update(d[group].keys())
        for field in sorted(fields):
            sector_defaults, style_variants, region_variation, allowed = {}, {}, {}, []
            for stem, (sector, region, style) in FILEMAP.items():
                val = (specs.get(stem, {}).get(group) or {}).get(field)
                if val is None:
                    continue
                allowed.append(val)
                if region:  # F&B najdi/hejazi (and real_estate najdi)
                    region_variation.setdefault(region, val)
                if style:
                    style_variants.setdefault(sector, {})[style] = val
                # sector_defaults = value from the PRIMARY file for the sector
                if stem == PRIMARY.get(sector):
                    sector_defaults[sector] = val
            # dedup allowed_values (only hashable scalars; keep complex as-is once)
            seen, uniq = set(), []
            for a in allowed:
                k = json.dumps(a, ensure_ascii=False, sort_keys=True)
                if k not in seen:
                    seen.add(k)
                    uniq.append(a)
            recs.append({
                "id": _id("cspec", group, field), "entity": "cultural_rule",
                "rule_key": "culturalspec_field", "field_group": group, "field_name": field,
                "tier": "advisory", "allowed_values": uniq,
                "sector_defaults": sector_defaults,
                "region_variation": {"Najdi": region_variation.get("Najdi"),
                                     "Hejazi": region_variation.get("Hejazi")},
                "provenance": _prov(f"culturalspec:{group}.{field}"),
                "extra": {"style_variants": style_variants,
                          "held_sectors": [s for s in sector_defaults if s in HELD],
                          "is_held": any(s in HELD for s in sector_defaults)},
            })
    return recs


def build():
    rules, arabic_sections = build_rules()
    fields = build_fields()
    all_recs = rules + fields
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(all_recs, open(OUT / "cultural_rules.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"wrote {len(all_recs)} cultural_rules -> {len(rules)} RULE + {len(fields)} culturalspec_field")
    print(f"arabic_text_rules shipped (domain=visual, enum_mismatch flagged): {len(arabic_sections)} sections")
    return all_recs


if __name__ == "__main__":
    build()
