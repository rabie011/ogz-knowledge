#!/usr/bin/env python3
"""validate_export.py — prove the weiblocks export is a RELIABLE DEPENDENCY (Rule #8: refuse, don't warn).

DeepSeek/RABIE-designed (W-local Step 1; rebuilt after the July-1 daemon wipe). Exits non-zero if ANY
check fails — a partner loader can gate on this. Checks: schema conformance, controlled-vocab membership
(sector/occasion/dialect/tier/domain/confidence), no raw-slug leakage, provenance completeness, id
uniqueness, cross-entity reference integrity (every sector_key/occasion_key points at a real shipped
node), reference↔observation join, owner-override boundary, native-Arabic-raw. Read-only.
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "exports" / "weiblocks_v1"
SHIPPED_SECTORS = {"F&B", "Beauty_Wellness", "Retail", "Other"}
DIALECTS = {"Najdi", "Hejazi", "Khaleeji", "Fusha (MSA)", None}
TIERS = {"hard_block", "soft_flag", "advisory"}
DOMAINS = {"gesture", "prop", "behavior", "visual", "gender_modesty", "religious"}
CONF = {"verified", "inferred", "experimental"}
# core 8-spec entities; extension files are validated only if present (they may not be rebuilt yet)
FILES = {
    "sectors.json": ("sector", "array", True),
    "occasions.json": ("occasion", "array", True),
    "visual_patterns.json": ("visual_pattern", "array", True),
    "reference_accounts.json": ("reference_account", "array", True),
    "brand_observations.ndjson": ("brand_observation", "ndjson", True),
    "cultural_rules.json": ("cultural_rule", "array", True),
    "caption_patterns.json": ("caption_pattern", "array", False),
    "dialect_variants.json": ("dialect_variant", "array", False),
    "creative_methods.json": ("creative_method", "array", False),
    "routing_rules.json": ("routing_rule", "array", False),
    "scorecard_weights.json": ("scorecard_dimension", "array", False),
}


def load(name):
    raw = (OUT / name).read_text(encoding="utf-8")
    recs = [json.loads(l) for l in raw.split("\n") if l.strip()] if name.endswith(".ndjson") else json.loads(raw)
    return recs, raw


def main():
    fails = []

    def fail(check, detail):
        fails.append((check, detail))

    data = {}
    for name, (_e, _f, required) in FILES.items():
        if not (OUT / name).exists():
            if required:
                fail("load", f"{name}: REQUIRED file missing")
            continue
        try:
            data[name] = load(name)
        except Exception as e:
            fail("load", f"{name}: {type(e).__name__}: {e}")
    occ_keys = ({r.get("occasion_key") for r in data["occasions.json"][0]}
                if "occasions.json" in data else set())

    for name, (entity, fmt, _req) in FILES.items():
        if name not in data:
            continue
        recs, raw = data[name]
        # C10 native Arabic raw
        if raw.count("\\u0"):
            fail("native_arabic", f"{name}: {raw.count(chr(92) + 'u0')} unicode escapes (Arabic not raw)")
        ids = []
        for i, r in enumerate(recs):
            tag = f"{name}[{i}] id={r.get('id')}"
            # C1 schema: id + entity
            if not r.get("id"):
                fail("schema.id", f"{name}[{i}] missing id")
            if r.get("entity") != entity:
                fail("schema.entity", f"{tag} entity={r.get('entity')} expected {entity}")
            ids.append(r.get("id"))
            # C4 provenance completeness
            p = r.get("provenance") or {}
            for pk in ("source", "confidence", "date_added", "scope"):
                if p.get(pk) in (None, ""):
                    fail("provenance", f"{tag} provenance.{pk} missing/empty")
            if p.get("confidence") not in CONF:
                fail("confidence.enum", f"{tag} confidence={p.get('confidence')}")
            # C2 sector_key membership (+ C8 no raw-slug leakage)
            sk = r.get("sector_key", "__absent__")
            if sk not in ("__absent__", None) and sk not in SHIPPED_SECTORS:
                fail("sector_key.member", f"{tag} sector_key={sk!r} not in shipped {sorted(SHIPPED_SECTORS)}")
            # C3 occasion_key validity
            ok_ = r.get("occasion_key", "__absent__")
            if ok_ not in ("__absent__", None) and ok_ not in occ_keys:
                fail("occasion_key.ref", f"{tag} occasion_key={ok_!r} not a shipped occasion")
            # C5 dialect validity
            if "dialect" in r and r.get("dialect") not in DIALECTS:
                fail("dialect.enum", f"{tag} dialect={r.get('dialect')!r}")
            # C6 cultural_rule enums (RULE records only)
            if entity == "cultural_rule" and r.get("rule_key") != "culturalspec_field":
                if r.get("tier") not in TIERS:
                    fail("tier.enum", f"{tag} tier={r.get('tier')}")
                if r.get("domain") not in DOMAINS:
                    fail("domain.enum", f"{tag} domain={r.get('domain')}")
            # C11 owner-override boundary (reader of the owner_overridable wire — Rule #6).
            # Only enforced once the wire exists in the data; hard_block must NEVER be overridable.
            if entity == "cultural_rule" and "owner_overridable" in r:
                if r.get("tier") == "hard_block" and r.get("owner_overridable") is not False:
                    fail("owner_override.hardblock", f"{tag} hard_block must be owner_overridable=false")
        # C7 id uniqueness within file
        seen, dupes = set(), set()
        for x in ids:
            (dupes if x in seen else seen).add(x)
        if dupes:
            fail("id.unique", f"{name}: duplicate ids {list(dupes)[:5]}")

    # C9 reference <-> observation join integrity
    if "reference_accounts.json" in data and "brand_observations.ndjson" in data:
        refs = data["reference_accounts.json"][0]
        obs = data["brand_observations.ndjson"][0]
        obs_ulids = {u for r in obs for u in (r.get("extra", {}).get("observation_ulids") or [])}
        obs_brandcodes = {r.get("brand_code") for r in obs}
        ref_brandcodes = {r.get("brand_code") for r in refs}
        for r in refs:
            for oid in (r.get("observation_ids") or []):
                if oid not in obs_ulids:
                    fail("ref.join", f"reference {r.get('brand_code')} observation_id {oid} not in any brand_observation")
                    break
        for bc in (obs_brandcodes & ref_brandcodes):
            rr = next((x for x in refs if x.get("brand_code") == bc), None)
            if rr is not None and not rr.get("observation_ids"):
                fail("ref.join.empty", f"reference {bc} shares brand with observations but observation_ids is empty")

    print(f"validate_export: {len(data)} files loaded ({sum(1 for n in FILES if FILES[n][2])} required)")
    if not fails:
        print("✅ ALL CHECKS PASS — export is a reliable dependency")
        return 0
    print(f"❌ {len(fails)} FAILURE(S):")
    for check, detail in fails[:40]:
        print(f"   [{check}] {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
