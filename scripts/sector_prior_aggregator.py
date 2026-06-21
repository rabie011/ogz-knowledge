#!/usr/bin/env python3
"""SECTOR-PRIOR AGGREGATOR (B096, L4 Bedrock) — turn client-CONFIRMED values into sector priors.

THE TOP it serves: the system that PRODUCES posts. A sector default (05_sector_defaults/*.yaml,
15_cultural_specs/) is a prior every brief in that sector inherits. Today those priors are hand-
seeded. This machine learns them bottom-up the way the Pyramid Law wants: when ENOUGH independent
brands in one sector CONFIRM the same value, that value has earned the right to become a sector
prior — and only then.

THE FLOOR (Rule #9 — never quote a prior you haven't verified across enough brands): a value seen
in ONE brand is that brand's truth, not the sector's. We REFUSE to promote below `min_brands`
DISTINCT confirming brands (default 3). Below threshold → HOLD, no draft. (Rule #8 — the gate
bites, it does not warn.)

NO INFLATION (the fresh-batch scar, Rule #9): the same brand confirming a value twice is still ONE
brand. Distinctness is by brand, never by record count — otherwise one loud client would mint a
sector law alone.

CONFIRMED ONLY: a record with no confirmer is an assumption, not a fact (Rule #9). Unconfirmed
records are dropped before counting.

ANONYMIZED (the how): the draft carries only the COUNT and anonymized brand tokens, never the raw
brand→value attribution — a sector prior is a shared truth, not a leak of who said what.

THE CONSUMER (Rule #6): this writer is NOT write-only. `write_drafts` stages drafts to
data/sector_prior_drafts.json as PROVISIONAL proposals; the specs are never hand-mutated here (the
System Produces — Rule #12 — we stage, a human/PR applies). The draft IS the consumable artifact,
and the synthetic test reads it back end-to-end.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

B = Path(__file__).parent.parent
DRAFTS = B / "data/sector_prior_drafts.json"
CLIENTS = B / "clients"

# A record's confirmer must be in this set to count as a fact (Rule #9). Self-asserted / machine
# guesses never count toward a sector prior.
CONFIRMED_BY = {"mohamed", "client", "owner"}

MIN_BRANDS = 3  # Rule #8 floor: distinct confirming brands required to promote a value.

# Which sector field maps to which spec target (where a promoted prior would land as a PR).
TARGET_FILES = {
    # field -> (sector_defaults yaml key path, cultural_specs subdir)
    "_default": ("05_sector_defaults/{sector}.yaml", "15_cultural_specs/sector_defaults"),
}


def _norm(value):
    """Normalize a value for agreement comparison. Strings: trim + casefold (so 'Halal' and 'halal'
    agree). Other scalars pass through. Lists/dicts → a stable JSON string (order-insensitive for
    dicts) so structured values can agree too."""
    if isinstance(value, str):
        return value.strip().casefold()
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return value


def _anon(brand):
    """Anonymized, stable token for a brand — same brand → same token, never the raw name."""
    return "b_" + hashlib.sha1(str(brand).encode("utf-8")).hexdigest()[:8]


def aggregate(records, min_brands=MIN_BRANDS):
    """Pure core. Group CONFIRMED records by (sector, field, normalized value); count DISTINCT
    confirming brands. Returns a list of bucket dicts (every bucket, promoted or held) sorted for
    determinism — the caller decides what to do with sub-threshold buckets.

    Each record: {"brand", "sector", "field", "value", "confirmer"}. Records missing brand/sector/
    field, or whose confirmer is not in CONFIRMED_BY, are dropped (Rule #9)."""
    buckets = defaultdict(set)          # (sector, field, nvalue) -> {brand, ...}
    raw_value = {}                       # remember one raw value per (sector, field, nvalue)
    for r in records:
        brand = r.get("brand")
        sector = r.get("sector")
        field = r.get("field")
        if not (brand and sector and field):
            continue
        if r.get("confirmer") not in CONFIRMED_BY:
            continue                     # unconfirmed assumption — not a fact
        if "value" not in r:
            continue
        nv = _norm(r["value"])
        key = (sector, field, json.dumps(nv, ensure_ascii=False, sort_keys=True))
        buckets[key].add(brand)
        raw_value.setdefault(key, r["value"])

    out = []
    for (sector, field, nv_key), brands in buckets.items():
        n = len(brands)                  # DISTINCT brands — no inflation by record count
        out.append({
            "sector": sector,
            "field": field,
            "value": raw_value[(sector, field, nv_key)],
            "n_brands": n,
            "brands_anon": sorted(_anon(b) for b in brands),
            "promoted": n >= min_brands,  # Rule #8 gate
        })
    # deterministic order: promoted first, then by strength, then stable by sector/field
    out.sort(key=lambda d: (not d["promoted"], -d["n_brands"], d["sector"], d["field"],
                            json.dumps(d["value"], ensure_ascii=False, sort_keys=True)))
    return out


def draft_prs(records, min_brands=MIN_BRANDS):
    """Only the PROMOTED buckets, shaped as draft-PR records ready to stage. Sub-threshold buckets
    are deliberately excluded (the gate bites — Rule #8)."""
    drafts = []
    for b in aggregate(records, min_brands=min_brands):
        if not b["promoted"]:
            continue
        tgt = TARGET_FILES.get(b["field"], TARGET_FILES["_default"])
        drafts.append({
            "sector": b["sector"],
            "field": b["field"],
            "value": b["value"],
            "n_brands": b["n_brands"],
            "brands_anon": b["brands_anon"],
            "target_sector_default": tgt[0].format(sector=b["sector"]),
            "target_cultural_spec": tgt[1],
            "status": "PROVISIONAL",       # never auto-applied; a PR/human lands it (Rule #12)
        })
    return drafts


def write_drafts(drafts, path=DRAFTS):
    """Stage drafts as the consumable artifact (Rule #6 — the reader is the PR review / the test).
    Provisional staging only; specs are never mutated here."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"n_drafts": len(drafts), "min_brands": MIN_BRANDS, "drafts": drafts}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def scan_clients(root=CLIENTS):
    """Real source: extract STRUCTURED confirmed values from client profiles. A passport answer is
    counted only when it carries a confirmer in CONFIRMED_BY AND a structured (non-prose) value —
    today most pilot answers are free prose, so this honestly yields little/nothing (n<3 on 2-3
    pilots → zero promotions, which is CORRECT, not a bug). The scanner exists so the machine fires
    the instant a 3rd brand in a sector lands a structured confirmation."""
    records = []
    root = Path(root)
    if not root.exists():
        return records
    for cdir in sorted(p for p in root.iterdir() if p.is_dir()):
        state_p = cdir / "profile/state.json"
        pass_p = cdir / "profile/passport.json"
        sector = None
        if state_p.exists():
            try:
                sector = json.loads(state_p.read_text(encoding="utf-8")).get("sector")
            except (json.JSONDecodeError, OSError):
                sector = None
        if not sector or not pass_p.exists():
            continue
        try:
            answers = json.loads(pass_p.read_text(encoding="utf-8")).get("answers", {})
        except (json.JSONDecodeError, OSError):
            continue
        for field, a in answers.items():
            if not isinstance(a, dict):
                continue
            val = a.get("value", a.get("structured"))  # only STRUCTURED, never the prose answer
            if val is None:
                continue
            records.append({
                "brand": cdir.name, "sector": sector, "field": field,
                "value": val, "confirmer": a.get("confirmer"),
            })
    return records


def main():
    records = scan_clients()
    drafts = draft_prs(records)
    write_drafts(drafts)
    promoted = len(drafts)
    held = sum(1 for b in aggregate(records) if not b["promoted"])
    print(f"sector_prior_aggregator: {len(records)} confirmed record(s) scanned · "
          f"{promoted} promoted draft(s) · {held} bucket(s) HELD below n≥{MIN_BRANDS} (Rule #8)")
    if promoted == 0:
        print("  → 0 promotions: no value has ≥3 distinct confirming brands yet (correct on a "
              "2-3 brand pilot; the machine fires when the 3rd lands).")


if __name__ == "__main__":
    main()
