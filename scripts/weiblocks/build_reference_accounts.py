#!/usr/bin/env python3
"""build_reference_accounts.py — 110 benchmark accounts -> Weiblocks §5.8 reference_account records.

DeepSeek-ruled (W2 Step 1):
  - INCLUDE all 110; trust = verified(63) | unverified(46 dead + any unmatched). Engine self-filters
    to trust:verified for fallback; we do not delete dead nodes (keeps provenance traceable).
  - PRIVACY: the real IG handle (account_handle_internal, e.g. "jine.sa") is NEVER emitted. Trust is
    matched via the already-anonymous account_handle_normalized == handle_verification 'normalized'.
  - observation_ids: granular source ULIDs, back-populated by build_brand_observations.py (Step 2)
    into the SHIPPED json. We carry them forward on re-run (never wipe another builder's write).
  - trust ⟂ provenance.confidence (handle-exists vs data-quality are orthogonal).

Join contract (W2 Step 3, DeepSeek-consulted):
  - brand_observation_id = 'bobs_<brand_code>' — the TOP-LEVEL node join, emitted ONLY on records
    whose brand_code has a shipped brand_observation node. Cross-checked against the actual id in
    the shipped ndjson; drift -> refuse (Rule #8). The 95 without observations OMIT the field.
  - observation_ids stay (granular drill-down); extra.join_note documents both ends of the contract.
  - extra.follower_tier now maps source profile.follower_count_bucket verbatim (was reading a
    nonexistent top-level key -> null on all 110).

Native Arabic preserved (ensure_ascii=False).
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACC = ROOT / "11_who_to_learn_from" / "accounts"
VERIF = ROOT / "11_who_to_learn_from" / "handle_verification.json"
OUT = ROOT / "exports" / "weiblocks_v1"
OBS_NDJSON = OUT / "brand_observations.ndjson"
REF_OUT = OUT / "reference_accounts.json"
DATE_ADDED = "2026-07-01"
SECTOR_MAP = {"f_and_b": "F&B", "beauty": "Beauty_Wellness", "retail": "Retail"}
JOIN_NOTE = ("observation_ids are granular source ULIDs (drill-down via "
             "brand_observation.extra.observation_ulids); brand_observation_id "
             "is the top-level node join")


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


def load_obs_join():
    """brand_code -> top-level id, read from the SHIPPED brand_observations.ndjson (READ-ONLY —
    build_brand_observations.py is owned by Step 2; we never edit or run it). A missing/empty
    ndjson means the join contract cannot be built: REFUSE (Rule #8), never ship join-less
    records silently."""
    if not OBS_NDJSON.exists():
        raise SystemExit(f"REFUSE: {OBS_NDJSON} missing — cannot build the brand_observation join")
    m = {}
    with open(OBS_NDJSON, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                o = json.loads(line)
                m[o["brand_code"]] = o["id"]
    if not m:
        raise SystemExit(f"REFUSE: {OBS_NDJSON} is empty — cannot build the brand_observation join")
    return m


def load_shipped_observation_ids():
    """id -> observation_ids carried forward from the CURRENT shipped reference_accounts.json.
    Step 2 back-populates these AFTER this transformer runs; a re-run of THIS script must not
    wipe another builder's write (Rule #6 — the consumer stays wired). Missing shipped file
    (fresh build) -> empty map (Step 2 populates later). Corrupt file -> crash loud."""
    if not REF_OUT.exists():
        return {}
    shipped = json.load(open(REF_OUT, encoding="utf-8"))
    return {r["id"]: r["observation_ids"] for r in shipped if r.get("observation_ids")}


def _norm_conf(c):
    """map source confidence vocab (BrandDNA ladder: confirmed/high/medium/low) -> spec enum
    {verified, inferred, experimental}. validate_export caught 2 accounts carrying 'confirmed'."""
    c = (c or "").strip().lower()
    if c in ("confirmed", "verified", "high"):
        return "verified"
    if c in ("inferred", "medium"):
        return "inferred"
    return "experimental"


def build():
    trust_map = load_trust()
    obs_join = load_obs_join()                    # brand_code -> shipped bobs_ id
    shipped_obs = load_shipped_observation_ids()  # id -> back-populated ULIDs (Step 2's write)
    records = []
    for fp in sorted(glob.glob(str(ACC / "*" / "account_*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        ulid = d.get("account_ulid")
        brand_code = d.get("account_handle_normalized")
        sector = d.get("sector")
        verdict = trust_map.get(brand_code)  # None => unmatched => unverified
        trust = "verified" if verdict == "verified" else "unverified"
        has_join = brand_code in obs_join
        if has_join and f"bobs_{brand_code}" != obs_join[brand_code]:
            raise SystemExit(f"REFUSE: id scheme drifted — expected bobs_{brand_code}, "
                             f"shipped ndjson carries {obs_join[brand_code]}")
        observation_ids = shipped_obs.get(ulid, [])
        if observation_ids and not has_join:
            raise SystemExit(f"REFUSE: {brand_code} has back-populated observation_ids but no "
                             f"brand_observation node in {OBS_NDJSON} — severed join contract")
        records.append({
            "id": ulid,
            "entity": "reference_account",
            "brand_code": brand_code,
            "sector_key": SECTOR_MAP.get(sector, sector),
            # top-level node join, ONLY where a brand_observation node ships (omitted otherwise)
            **({"brand_observation_id": f"bobs_{brand_code}"} if has_join else {}),
            "observation_ids": observation_ids,  # granular ULIDs, back-populated by Step 2
            "summary": {
                "voice": d.get("distinctive_voice_traits") or [],
                "visual": d.get("distinctive_visual_traits") or [],
            },
            "trust": trust,
            "provenance": {
                "source": "manual_curation",  # xlsx benchmark corpus (confirmer: Mohamed)
                "confidence": _norm_conf((d.get("provenance") or {}).get("confidence")),
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
                # source bucket verbatim (profile.follower_count_bucket); null only if absent
                "follower_tier": (d.get("profile") or {}).get("follower_count_bucket"),
                **({"join_note": JOIN_NOTE} if has_join else {}),
                # PRIVACY: account_handle_internal (real IG handle) is DELIBERATELY EXCLUDED.
            },
        })
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(records, open(REF_OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    v = sum(1 for r in records if r["trust"] == "verified")
    j = sum(1 for r in records if "brand_observation_id" in r)
    t = sum(1 for r in records if r["extra"]["follower_tier"] is not None)
    print(f"wrote {len(records)} reference_accounts -> trust verified={v} unverified={len(records) - v} "
          f"| joined={j} | follower_tier={t}")
    return records


if __name__ == "__main__":
    build()
