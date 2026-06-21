#!/usr/bin/env python3
"""OUTCOME RECEIPT COLLECTOR (B094, L4 Bedrock) — the missing CONSUMER of published outcomes.

THE FULL CIRCLE (Rule #5.9): the system PRODUCES → Mohamed JUDGES → the post goes live →
its REAL outcome must flow back so the next batch is better. Until now nothing read that last
hop: a published piece had no path back into the ledger. That is a severed wire (Rule #6).
This collector closes it.

WHAT IT DOES (read-only over its inputs; append-only over its output):
  1. Reads the publish ledger  data/published.jsonl  — `published` outcome events, each naming a
     subject_generation_ulid + brand_ulid + timestamp. (Writer is a separate concern / may be empty.)
  2. For each piece that has reached T+7d AND has countables in  data/post_metrics.jsonl , emits a
     `metric_recorded` outcome event into  data/receipts.jsonl  (validates against outcome_event_v1).
  3. Compares each receipt to the BRAND'S OWN baseline ONLY — the median of that same brand's prior
     receipts. Never cross-piece / cross-brand vanity. Fewer than MIN_BASELINE_N priors → baseline
     INSUFFICIENT, NO number quoted (Rule #9).
  4. Flags pieces published > 30d ago that still have NO receipt — no-outcome-30d (a silent post).

DELIBERATE DESIGN NOTES:
  - outcome_event_v1 is additionalProperties:false, so the receipt EVENT stays schema-pure; the
    vs-own-baseline delta + flags live in the RUN REPORT and data/receipts_summary.json, never
    smuggled into the event.
  - event_ulid is DETERMINISTIC from (subject_generation_ulid, window) → re-runs are idempotent;
    a receipt already in the ledger is never re-emitted.
  - Empty/absent inputs → honest "0 published, nothing to collect" (Pre-Build Q2), never a crash.

Usage:
  python3 scripts/outcome_receipt.py            # collect; append new receipts; print report
  python3 scripts/outcome_receipt.py --dry-run  # report only, write nothing
"""
import argparse
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
PUBLISHED_LEDGER = BASE / "data/published.jsonl"
METRICS_FEED = BASE / "data/post_metrics.jsonl"
RECEIPTS_LEDGER = BASE / "data/receipts.jsonl"
RECEIPTS_SUMMARY = BASE / "data/receipts_summary.json"

WINDOW_DAYS = 7          # T+7d countables window
NO_OUTCOME_DAYS = 30     # published & silent this long with no receipt → flagged
MIN_BASELINE_N = 3       # fewer prior same-brand receipts than this → baseline INSUFFICIENT
ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# the countable a brand is benchmarked against itself on (kept single + explicit; not vanity reach)
BASELINE_METRIC = "engagement_rate"


def deterministic_ulid(seed: str) -> str:
    """Deterministic 26-char Crockford-base32 ULID from a seed (mirrors generate_chains.py)."""
    import hashlib
    val = int(hashlib.sha256(seed.encode()).hexdigest()[:32], 16)
    out = []
    for _ in range(26):
        out.append(ULID_ALPHABET[val % 32])
        val //= 32
    return "".join(reversed(out))


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            rows.append(json.loads(ln))
    return rows


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp to an aware UTC datetime."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def collect(now: datetime | None = None, dry_run: bool = False) -> dict:
    """Collect receipts for matured published pieces. Returns a report dict; appends new receipts
    to the ledger unless dry_run. `now` is injectable so tests are deterministic (no Date.now in src)."""
    now = now or datetime.now(timezone.utc)

    published = _read_jsonl(PUBLISHED_LEDGER)
    metrics = {m["subject_generation_ulid"]: m for m in _read_jsonl(METRICS_FEED)
               if m.get("subject_generation_ulid")}
    existing = _read_jsonl(RECEIPTS_LEDGER)
    already = {e["subject_generation_ulid"] for e in existing if e.get("subject_generation_ulid")}

    # per-brand baseline = median of that brand's PRIOR receipts only (own-baseline law)
    prior_by_brand: dict[str, list] = {}
    for e in existing:
        v = (e.get("performance_metrics") or {}).get(BASELINE_METRIC)
        if v is not None:
            prior_by_brand.setdefault(e.get("brand_ulid"), []).append(v)

    new_receipts, comparisons, no_outcome = [], [], []

    for pub in published:
        gen = pub.get("subject_generation_ulid")
        brand = pub.get("brand_ulid")
        ts = pub.get("timestamp")
        if not (gen and brand and ts):
            continue  # malformed publish row — skip, never guess
        age_days = (now - _parse_ts(ts)).total_seconds() / 86400.0

        if gen in already:
            continue  # idempotent: this piece already has a receipt

        m = metrics.get(gen)
        if not m or age_days < WINDOW_DAYS:
            # no countables yet, or not matured to T+7d
            if age_days >= NO_OUTCOME_DAYS and not m:
                no_outcome.append({"subject_generation_ulid": gen, "brand_ulid": brand,
                                   "age_days": round(age_days, 1)})
            continue

        perf = {k: m[k] for k in ("engagement_rate", "save_rate", "share_rate",
                                  "comment_quality_score", "reach", "impressions", "platform")
                if k in m}
        receipt = {
            "event_ulid": deterministic_ulid(f"receipt:{gen}:T{WINDOW_DAYS}"),
            "event_type": "metric_recorded",
            "timestamp": now.isoformat(),
            "brand_ulid": brand,
            "subject_generation_ulid": gen,
            "schema_version": 1,
            "performance_metrics": perf,
            "actor": "system",
            "provenance": {
                "source": "outcome_receipt.py (B094)",
                "date_added": now.date().isoformat(),
                "confirmer": "system",
                "confidence": "experimental",
                # provenance_mixin scope pattern: brand:<lowercase slug> (never the bare word)
                "scope": "brand:" + re.sub(r"[^a-z0-9_]", "_", str(brand).lower()),
                "metrics_source": m.get("metrics_source", "post_metrics_feed"),
            },
        }
        new_receipts.append(receipt)

        # vs OWN baseline — same brand's priors only; insufficient → no number (Rule #9)
        priors = prior_by_brand.get(brand, [])
        val = perf.get(BASELINE_METRIC)
        if len(priors) >= MIN_BASELINE_N and val is not None:
            base = statistics.median(priors)
            comparisons.append({"subject_generation_ulid": gen, "brand_ulid": brand,
                                "metric": BASELINE_METRIC, "value": val,
                                "own_baseline": round(base, 4),
                                "delta_pct": round((val - base) / base * 100, 1) if base else None,
                                "baseline_n": len(priors)})
        else:
            comparisons.append({"subject_generation_ulid": gen, "brand_ulid": brand,
                                "metric": BASELINE_METRIC, "value": val,
                                "own_baseline": None, "delta_pct": None,
                                "baseline_n": len(priors), "status": "INSUFFICIENT_BASELINE"})
        # this receipt becomes a prior for later pieces of the same brand in this very run
        if val is not None:
            prior_by_brand.setdefault(brand, []).append(val)

    report = {
        "published_seen": len(published),
        "already_receipted": len(already),
        "new_receipts": len(new_receipts),
        "comparisons": comparisons,
        "no_outcome_30d": no_outcome,
        "dry_run": dry_run,
    }

    if new_receipts and not dry_run:
        with RECEIPTS_LEDGER.open("a", encoding="utf-8") as fh:
            for r in new_receipts:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        RECEIPTS_SUMMARY.write_text(
            json.dumps({"generated_at": now.isoformat(), **report}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    return report


def _print(report: dict) -> None:
    print("── OUTCOME RECEIPT COLLECTOR (B094)")
    print(f"  published seen      : {report['published_seen']}")
    print(f"  already receipted   : {report['already_receipted']}")
    print(f"  new receipts        : {report['new_receipts']}"
          + ("  (dry-run, not written)" if report["dry_run"] else ""))
    for c in report["comparisons"]:
        if c.get("status") == "INSUFFICIENT_BASELINE":
            print(f"  • {c['subject_generation_ulid'][:8]} {c['metric']}={c['value']} "
                  f"— baseline INSUFFICIENT (n={c['baseline_n']}<{MIN_BASELINE_N}), no number (Rule #9)")
        else:
            d = c["delta_pct"]
            arrow = "↑" if (d or 0) > 0 else "↓" if (d or 0) < 0 else "→"
            print(f"  • {c['subject_generation_ulid'][:8]} {c['metric']}={c['value']} "
                  f"vs own {c['own_baseline']} {arrow} {d}% (n={c['baseline_n']})")
    if report["no_outcome_30d"]:
        print(f"  ⚠️  {len(report['no_outcome_30d'])} published >30d with NO outcome (silent posts):")
        for n in report["no_outcome_30d"]:
            print(f"      - {n['subject_generation_ulid'][:8]} ({n['brand_ulid']}) {n['age_days']}d")
    if not report["published_seen"]:
        print("  (no published pieces yet — nothing to collect; the reader is live, awaiting the writer)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()
    _print(collect(dry_run=args.dry_run))
