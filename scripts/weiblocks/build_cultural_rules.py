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
    - sector_defaults keyed by SECTOR (primary/base variant per sector) — SHIPPED sectors only
      ({F&B, Retail, Beauty_Wellness, Other}); held-sector (Healthcare/Real_Estate) values live in
      extra.held_sector_defaults with extra.held_sectors + extra.is_held flags (panel ruling:
      include-with-flag; validator C14 enforces the shipped-only join field).
    - region_variation Najdi/Hejazi (F&B primarily); all style variants in extra.style_variants.

ID SCHEME (mixed, intentional — both deterministic):
  - forbidden-list entries carry their source ULIDs verbatim (the YAML entry's own `id`,
    26-char Crockford base32, 21 records) — stable cross-repo references.
  - every derived record (gender/visual/arabic-text rules, culturalspec fields) uses a
    deterministic content hash: crule_<sha256("|".join(parts))[:16] upper>.

PROVENANCE (truth, never fabricated): every output record carries the source YAML's own
provenance verbatim — true `source` string + `confirmer` (+ confidence, + source_date_added).
'manual_curation' is the fallback ONLY when a source file has no provenance block (none today).
FIELD records aggregate the provenance of their CONTRIBUTING spec files (sorted unique sources
joined with ' | '; weakest confidence wins; single unique confirmer or ' | ' join).

OWNER-OVERRIDE WIRE: every record has owner_overridable; tier=hard_block => false (validator C11),
all other tiers => true.

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
SHIPPED = {"F&B", "Retail", "Beauty_Wellness", "Other"}
_CONF_RANK = {"experimental": 0, "inferred": 1, "confirmed": 2}
PRIMARY = {"F&B": "f_and_b_najdi", "Beauty_Wellness": "beauty_personal_care",
           "Retail": "retail_modern", "Healthcare": "healthcare_modern",
           "Real_Estate": "real_estate_modern_najdi"}
SPEC_GROUPS = ["characters", "wardrobe", "body_language", "gestures", "settings_architecture",
               "props_objects", "behaviors_rituals", "social_dynamics"]


def _id(*parts):
    return "crule_" + hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16].upper()


def _prov(scope, src=None):
    """Provenance mixin carrying the source YAML's own provenance block VERBATIM.
    `src` = the source file's provenance dict; its true source/confirmer/confidence are
    never overwritten. Fallback source='manual_curation' ONLY when src has no provenance."""
    src = src or {}
    p = {"source": src.get("source") or "manual_curation",
         "confidence": src.get("confidence") or "experimental",
         "confirmer": src.get("confirmer"),
         "observed_count": src.get("observed_count"),
         "date_added": DATE_ADDED, "scope": scope}
    if src.get("date_added"):
        p["source_date_added"] = str(src["date_added"])
    return p


def _agg_prov(scope, provs):
    """Aggregate provenance for FIELD records across their CONTRIBUTING spec files.
    Sorted unique sources ' | '-joined; WEAKEST confidence wins (never over-claim);
    confirmer = the single unique declared confirmer (or ' | ' join, or None)."""
    provs = [p for p in provs if p]
    sources = sorted({p["source"] for p in provs if p.get("source")})
    confirmers = sorted({p["confirmer"] for p in provs if p.get("confirmer")})
    confs = sorted({p["confidence"] for p in provs if p.get("confidence")},
                   key=lambda c: _CONF_RANK.get(c, 0))
    dates = sorted({str(p["date_added"]) for p in provs if p.get("date_added")})
    out = {"source": " | ".join(sources) if sources else "manual_curation",
           "confidence": confs[0] if confs else "experimental",
           "confirmer": confirmers[0] if len(confirmers) == 1 else (" | ".join(confirmers) or None),
           "observed_count": None, "date_added": DATE_ADDED, "scope": scope}
    if dates:
        out["source_date_added"] = dates[0] if len(dates) == 1 else " | ".join(dates)
    return out


def _flatten(d):
    """Deterministic dict -> readable English summary. NO invented prose — only the dict's
    own text: 'key label: value' parts ' | '-joined; lists '; '-joined; nested 'k — v'."""
    parts = []
    for k, v in d.items():
        label = k.replace("_", " ")
        if isinstance(v, list):
            parts.append(f"{label}: " + "; ".join(str(x) for x in v))
        elif isinstance(v, dict):
            parts.append(f"{label}: " + "; ".join(
                f"{ik.replace('_', ' ')} — {iv}" for ik, iv in v.items()))
        else:
            parts.append(f"{label}: {v}")
    return " | ".join(parts)


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
        fprov = d.get("provenance")
        for e in (d.get("entries") or []):
            recs.append({
                "id": e.get("id") or _id("forbid", kind, e.get("name")),
                "entity": "cultural_rule", "rule_key": e.get("name"),
                "tier": tier, "domain": domain,
                "owner_overridable": tier != "hard_block",
                "description_en": e.get("description"), "description_ar": None,
                "scope": "universal", "action": "block_and_regenerate",
                "rationale": e.get("rationale"), "examples": [],
                "provenance": _prov("universal", fprov),
                "extra": {"severity": e.get("severity"), "detection_hints": e.get("detection_hints") or [],
                          "translation_needed": True, "source_list": kind},
            })
    # 2) gender_rules.patterns -> gender_modesty
    g = yaml.safe_load(open(RULES / "gender_rules.yaml", encoding="utf-8")) or {}
    gprov = g.get("provenance")
    for name, v in (g.get("patterns") or {}).items():
        rule = v.get("rule") if isinstance(v, dict) else str(v)
        level = v.get("level") if isinstance(v, dict) else None
        tier = _level_to_tier(level)
        recs.append({
            "id": _id("gender", name), "entity": "cultural_rule", "rule_key": name,
            "tier": tier, "domain": "gender_modesty",
            "owner_overridable": tier != "hard_block",
            "description_en": rule, "description_ar": None, "scope": "universal",
            "action": "flag_for_review", "rationale": None, "examples": [],
            "provenance": _prov("universal", gprov),
            "extra": {"level": level, "translation_needed": True, "source": "gender_rules.patterns"},
        })
    # 3) saudi_visual_rules -> visual/advisory (atomize)
    v = yaml.safe_load(open(RULES / "saudi_visual_rules.yaml", encoding="utf-8")) or {}
    vprov = v.get("provenance")
    for cname, cval in (v.get("color_semantics") or {}).items():
        desc = cval.get("rule") if isinstance(cval, dict) else str(cval)
        recs.append({
            "id": _id("visual", "color", cname), "entity": "cultural_rule", "rule_key": f"color_{cname}",
            "tier": "advisory", "domain": "visual", "owner_overridable": True,
            "description_en": desc, "description_ar": None,
            "scope": "universal", "action": "annotate", "rationale": None, "examples": [],
            "provenance": _prov("universal", vprov),
            "extra": {"hex": (cval.get("hex") if isinstance(cval, dict) else None),
                      "translation_needed": True, "source": "saudi_visual_rules.color_semantics"},
        })
    mr = v.get("motif_rules") or {}
    if mr:
        recs.append({
            "id": _id("visual", "motifs"), "entity": "cultural_rule", "rule_key": "approved_motifs",
            "tier": "advisory", "domain": "visual", "owner_overridable": True,
            "description_en": "Culturally authentic Saudi motifs approved when used respectfully.",
            "description_ar": None, "scope": "universal", "action": "annotate", "rationale": None,
            "examples": mr.get("approved_when_authentic") or [],
            "provenance": _prov("universal", vprov),
            "extra": {"translation_needed": True, "source": "saudi_visual_rules.motif_rules"},
        })
    # 4) arabic_text_rules -> SHIPPED (nothing dropped, §4.7) as advisory records. The spec domain enum
    #    has no 'language/text' value, so domain='visual' (least-wrong: text renders visually) + extra
    #    flags the true domain honestly. NOT 'religious hard_block' (that would mislabel a style rule).
    a = yaml.safe_load(open(RULES / "arabic_text_rules.yaml", encoding="utf-8")) or {}
    aprov = a.get("provenance")
    mapped_sections = []

    def _txt_rule(rkey, desc, examples=None, structured=None):
        extra = {"true_domain": "language_text", "enum_mismatch": True, "translation_needed": True,
                 "source": f"arabic_text_rules.{rkey}"}
        if structured is not None:
            extra["structured_rule"] = structured  # the raw dict, moved OUT of description_en
        recs.append({
            "id": _id("arabictext", rkey), "entity": "cultural_rule", "rule_key": f"arabic_text_{rkey}",
            "tier": "advisory", "domain": "visual", "owner_overridable": True,
            "description_en": desc, "description_ar": None,
            "scope": "universal", "action": "annotate", "rationale": None, "examples": examples or [],
            "provenance": _prov("universal", aprov),
            "extra": extra,
        })
    for name, val in (a.get("writing_conventions") or {}).items():
        if isinstance(val, str):
            _txt_rule(name, val)
        else:  # readable summary in description_en; raw dict preserved in extra.structured_rule
            _txt_rule(name, _flatten(val), structured=val)
        mapped_sections.append(f"writing_conventions.{name}")
    ts = a.get("translation_smell") or {}
    if ts:
        _txt_rule("translation_smell", ts.get("description", "Indicators of machine-translated (non-native) Arabic copy."),
                  ts.get("indicators") or [], structured=ts)
        mapped_sections.append("translation_smell")
    for sec in ("rendering", "msa_usage", "codeswitching", "dialect_default"):
        v = a.get(sec)
        if v:
            if isinstance(v, str):
                _txt_rule(sec, v)
            else:  # readable summary in description_en; raw dict preserved in extra.structured_rule
                _txt_rule(sec, _flatten(v), structured=v)
            mapped_sections.append(sec)
    return recs, mapped_sections


def build_fields():
    # load all spec files keyed by their stem (sorted glob — deterministic)
    specs = {}
    for fp in sorted(glob.glob(str(SPECS / "*.yaml"))):
        stem = Path(fp).stem
        if stem in FILEMAP:
            specs[stem] = yaml.safe_load(open(fp, encoding="utf-8")) or {}
    spec_prov = {stem: d.get("provenance") for stem, d in specs.items()}
    recs = []
    for group in SPEC_GROUPS:
        # collect the field names present in this group across all files
        fields = set()
        for stem, d in specs.items():
            if isinstance(d.get(group), dict):
                fields.update(d[group].keys())
        for field in sorted(fields):
            sector_defaults, style_variants, region_variation, allowed = {}, {}, {}, []
            contributing = []  # stems whose value feeds this record (provenance truth)
            for stem, (sector, region, style) in FILEMAP.items():
                val = (specs.get(stem, {}).get(group) or {}).get(field)
                if val is None:
                    continue
                allowed.append(val)
                contributing.append(stem)
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
            # held-sector split: the primary join field carries SHIPPED sectors only;
            # Healthcare/Real_Estate values live in extra.held_sector_defaults (include-with-flag)
            shipped_defaults = {s: v for s, v in sector_defaults.items() if s in SHIPPED}
            held_defaults = {s: v for s, v in sector_defaults.items() if s in HELD}
            recs.append({
                "id": _id("cspec", group, field), "entity": "cultural_rule",
                "rule_key": "culturalspec_field", "field_group": group, "field_name": field,
                "tier": "advisory", "owner_overridable": True, "allowed_values": uniq,
                "sector_defaults": shipped_defaults,
                "region_variation": {"Najdi": region_variation.get("Najdi"),
                                     "Hejazi": region_variation.get("Hejazi")},
                "provenance": _agg_prov(f"culturalspec:{group}.{field}",
                                        [spec_prov.get(s) for s in contributing]),
                "extra": {"style_variants": style_variants,
                          "held_sector_defaults": held_defaults,
                          "held_sectors": sorted(held_defaults),
                          "is_held": bool(held_defaults)},
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
