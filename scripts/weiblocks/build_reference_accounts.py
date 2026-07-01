#!/usr/bin/env python3
"""build_reference_accounts.py — 110 benchmark accounts -> Weiblocks §5.8 reference_account records.

DeepSeek-ruled (W2 Step 1):
  - INCLUDE all 110; trust = verified(63) | unverified(46 dead + any unmatched). Engine self-filters
    to trust:verified for fallback; we do not delete dead nodes (keeps provenance traceable).
  - PRIVACY: the real IG handle (account_handle_internal, e.g. "jine.sa") is NEVER emitted. Trust is
    matched via the already-anonymous account_handle_normalized == handle_verification 'normalized'.
  - observation_ids=[] now; back-populated in Step 2 when brand_observations builds (no dangling ref).
  - trust ⟂ provenance.confidence (handle-exists vs data-quality are orthogonal).

Native Arabic preserved (ensure_ascii=False).
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACC = ROOT / "11_who_to_learn_from" / "accounts"
VERIF = ROOT / "11_who_to_learn_from" / "handle_verification.json"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"
SECTOR_MAP = {"f_and_b": "F&B", "beauty": "Beauty_Wellness", "retail": "Retail"}


def load_trust():
    """map anon normalized code -> verdict (verified|dead|restricted). Keyed by the ANON code, so the
    real handle never enters the build path."""
    d = json.load(open(VERIF, encoding="utf-8"))
    m = {}
    for v in (d.get("handles") or {}).values():
        norm = v.get("normalized")
        if norm:
            m[norm] = v.get("verdict")
    return m


def build():
    trust_map = load_trust()
    records = []
    for fp in sorted(glob.glob(str(ACC / "*" / "account_*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        brand_code = d.get("account_handle_normalized")
        sector = d.get("sector")
        verdict = trust_map.get(brand_code)  # None => unmatched => unverified
        trust = "verified" if verdict == "verified" else "unverified"
        records.append({
            "id": d.get("account_ulid"),
            "entity": "reference_account",
            "brand_code": brand_code,
            "sector_key": SECTOR_MAP.get(sector, sector),
            "observation_ids": [],  # back-populated in Step 2 (brand_observations)
            "summary": {
                "voice": d.get("distinctive_voice_traits") or [],
                "visual": d.get("distinctive_visual_traits") or [],
            },
            "trust": trust,
            "provenance": {
                "source": "manual_curation",  # xlsx benchmark corpus (confirmer: Mohamed)
                "confidence": (d.get("provenance") or {}).get("confidence", "experimental"),
                "observed_count": None,
                "date_added": DATE_ADDED,
                "scope": f"sector:{SECTOR_MAP.get(sector, sector)}+brand:{brand_code}",
            },
            "extra": {
                "source_label": sector,
                "verification_verdict": verdict or "not_verified",
                "content_patterns_observed": d.get("content_patterns_observed") or [],
                "high_engagement_themes": d.get("high_engagement_themes") or [],
                "low_engagement_themes": d.get("low_engagement_themes") or [],
                "anti_patterns_observed": d.get("anti_patterns_observed") or [],
                "follower_tier": d.get("follower_tier"),
                # PRIVACY: account_handle_internal (real IG handle) is DELIBERATELY EXCLUDED.
            },
        })
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(records, open(OUT / "reference_accounts.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    v = sum(1 for r in records if r["trust"] == "verified")
    print(f"wrote {len(records)} reference_accounts -> trust verified={v} unverified={len(records) - v}")
    return records


if __name__ == "__main__":
    build()
