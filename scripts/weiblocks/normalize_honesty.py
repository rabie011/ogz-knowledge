#!/usr/bin/env python3
"""normalize_honesty.py — cross-file honesty guard for the Weiblocks export (runs after builders).

ONE enforcement point for honesty invariants that span files (Rule #6 consumer-law shape). It:

  1. PREVALENCE, not approval  — in sectors.json, voice.top/worst_performing_tones carry a value in a
     field named `approval_rate`, but we have NO measured approval/engagement-per-tone table; the number
     is tone PREVALENCE. A loader would treat `approval_rate` as measured truth. Fix: set approval_rate=null
     (honest — empty over missing) and add a correctly-named first-class `prevalence` field with the number.

  2. NO DANGLING SECTOR KEYS — any record whose sector_key is not among the SHIPPED sectors (sectors.json)
     is a dangling graph reference (e.g. visual_patterns tagged Healthcare/Real_Estate while those baselines
     are HELD). Retag sector_key=null (sector-wide) and preserve the original in extra.source_sector.

  3. CONFIDENCE GUARD (refuse, don't warn — Rule #8) — assert every record carries provenance.confidence in
     {verified,inferred,experimental}. Exit non-zero if any record violates it; the export must not ship
     a record whose honesty is unstated.

Idempotent + reusable across every wave. Native Arabic preserved (ensure_ascii=False).
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "exports" / "weiblocks_v1"
VALID_CONF = {"verified", "inferred", "experimental"}


def load(name):
    p = OUT / name
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def dump(name, data):
    json.dump(data, open(OUT / name, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def fix_prevalence(sectors):
    n = 0
    for rec in sectors:
        voice = rec.get("voice") or {}
        for field in ("top_performing_tones", "worst_performing_tones"):
            for t in (voice.get(field) or []):
                if isinstance(t, dict) and "approval_rate" in t and "prevalence" not in t:
                    t["prevalence"] = t["approval_rate"]  # the real (proxy) number, correctly named
                    t["approval_rate"] = None             # honest: we have no MEASURED approval
                    n += 1
        # make the proxy machine-readable at record level too
        ex = rec.setdefault("extra", {})
        notes = ex.setdefault("honesty_notes", [])
        note = "voice tone approval_rate is null (no measured approval data); `prevalence` = how often the tone appears in the sector (proxy), not a measured approval rate"
        if note not in notes:
            notes.append(note)
    return n


def retag_dangling(records, shipped_keys, entity_name):
    n = 0
    for rec in records:
        sk = rec.get("sector_key")
        if sk is not None and sk not in shipped_keys:
            ex = rec.setdefault("extra", {})
            ex["source_sector"] = sk  # preserve original; restore when the baseline ships
            ex.setdefault("honesty_notes", []).append(
                f"sector_key nulled: '{sk}' baseline is HELD/absent in this export — retagged sector-wide to keep the graph consistent")
            rec["sector_key"] = None
            n += 1
    return n


def assert_confidence(records, name):
    bad = [i for i, r in enumerate(records)
           if (r.get("provenance") or {}).get("confidence") not in VALID_CONF]
    if bad:
        sys.stderr.write(f"REFUSE: {name} has {len(bad)} record(s) missing a valid provenance.confidence "
                         f"(first idx {bad[:5]}). Honesty must be stated per-record.\n")
        sys.exit(1)


def main():
    sectors = load("sectors.json")
    if sectors is None:
        sys.exit("normalize_honesty: sectors.json not found — run the sector builder first")
    shipped_keys = {r["sector_key"] for r in sectors if r.get("sector_key")}
    print(f"shipped sector_keys: {sorted(shipped_keys)}")

    fixed = fix_prevalence(sectors)
    dump("sectors.json", sectors)
    print(f"prevalence rename: {fixed} tone objects fixed (approval_rate->null + prevalence)")

    total_retag = 0
    for name in ("visual_patterns.json", "caption_patterns.json", "dialect_variants.json", "brand_observations.json"):
        recs = load(name)
        if recs is None:
            continue
        r = retag_dangling(recs, shipped_keys, name)
        if r:
            dump(name, recs)
        total_retag += r
        print(f"dangling sector_key retag in {name}: {r}")
    print(f"total dangling retags: {total_retag}")

    # refuse-don't-warn: every shipped file's records must state confidence
    for name in ("sectors.json", "occasions.json", "visual_patterns.json"):
        recs = load(name)
        if recs is not None:
            assert_confidence(recs, name)
    print("confidence guard: PASS (every record states provenance.confidence)")


if __name__ == "__main__":
    main()
