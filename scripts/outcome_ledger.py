#!/usr/bin/env python3
"""PUBLISH-LEDGER WRITER (B095w, L4 Bedrock) — the missing PRODUCER of the publish ledger.

THE INVERTED CONSUMER LAW (Rule #6): outcome_receipt.py (B094) and outcome_question.py (B095) are
BOTH read-only consumers of  data/published.jsonl  — two readers, no writer. Until now the file did
not exist, so both outcome halves ran honest-empty: a published piece had no path INTO the ledger,
so its outcome could never flow back (the last hop of the Full Circle, Rule #5.9). This module is
that missing writer. It emits one `published` event {subject_generation_ulid, brand_ulid, timestamp}
when a piece goes live, in the EXACT shape both readers already consume (verified end-to-end in
scripts/tests/test_outcome_ledger_writer.py).

SCOPE BOUNDARY (the open question, root-hunted 2026-06-22): WHERE the real go-live event originates
— our side vs Hesham's platform — is an INTEGRATION hop staged for Mohamed (mohamed_must). This
module is only the organ + its contract: the deterministic, idempotent, guarded writer. WHAT calls
record_published() on a real publish (a portal "published" tap, or a platform webhook/export) is
wired once Mohamed answers that fork. Until then the writer exists, is tested against the real
reader contract, and is callable — the readers are no longer starved of a producer, only of live
events (honest-empty, never severed).

GUARDS (Rule #8 — refuse, don't warn):
  - a malformed event (missing/empty subject_generation_ulid or brand_ulid, or an unparseable
    timestamp) is REFUSED with ValueError — never a half-written row.
  - idempotent: an event whose subject_generation_ulid is already in the ledger is NOT re-appended
    (re-runs are safe; matches outcome_receipt's own dedup contract).

Usage:
  python3 scripts/outcome_ledger.py record --gen <ULID> --brand <ULID> [--ts ISO8601]
  python3 scripts/outcome_ledger.py status        # how many events, per brand, earliest/latest
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
PUBLISHED_LEDGER = BASE / "data/published.jsonl"


def _read_jsonl(path: Path) -> list:
    """Read the append-only ledger into a list of records. Missing/empty file → []."""
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            rows.append(json.loads(ln))
    return rows


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp to an aware UTC datetime (same contract as the readers)."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def record_published(subject_generation_ulid: str, brand_ulid: str, timestamp: str | None = None,
                     path: Path = PUBLISHED_LEDGER) -> dict:
    """Append ONE `published` event to the ledger, in the shape both outcome readers consume.

    Returns the event dict (the existing one, unchanged, if this generation was already recorded —
    idempotent). Raises ValueError on a malformed event (Rule #8: refuse, never half-write)."""
    gen = (subject_generation_ulid or "").strip()
    brand = (brand_ulid or "").strip()
    if not gen:
        raise ValueError("record_published: subject_generation_ulid is required and non-empty")
    if not brand:
        raise ValueError("record_published: brand_ulid is required and non-empty")
    ts = (timestamp or datetime.now(timezone.utc).isoformat()).strip()
    _parse_ts(ts)  # validate — raises ValueError if unparseable, before any write

    path = Path(path)
    existing = _read_jsonl(path)
    for e in existing:
        if e.get("subject_generation_ulid") == gen:
            return e  # idempotent: already published, do not double-append

    event = {"subject_generation_ulid": gen, "brand_ulid": brand, "timestamp": ts}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def status(path: Path = PUBLISHED_LEDGER) -> dict:
    """Honest summary of the ledger: total events, per-brand counts, earliest/latest timestamp."""
    rows = _read_jsonl(path)
    by_brand: dict[str, int] = {}
    stamps = []
    for r in rows:
        b = r.get("brand_ulid")
        if b:
            by_brand[b] = by_brand.get(b, 0) + 1
        if r.get("timestamp"):
            stamps.append(r["timestamp"])
    return {
        "n_published": len(rows),
        "by_brand": by_brand,
        "earliest": min(stamps) if stamps else None,
        "latest": max(stamps) if stamps else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish-ledger writer (B095w)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="record one go-live event")
    rec.add_argument("--gen", required=True, help="subject_generation_ulid of the piece that went live")
    rec.add_argument("--brand", required=True, help="brand_ulid")
    rec.add_argument("--ts", default=None, help="ISO-8601 timestamp (default: now, UTC)")

    sub.add_parser("status", help="summarize the ledger")

    a = ap.parse_args()
    if a.cmd == "record":
        try:
            ev = record_published(a.gen, a.brand, a.ts)
        except ValueError as e:
            print(f"❌ REFUSED: {e}", file=sys.stderr)  # Rule #8 — exit non-zero, never proceed
            return 2
        print(f"✅ published: {ev['subject_generation_ulid']}  brand={ev['brand_ulid']}  @ {ev['timestamp']}")
        return 0
    if a.cmd == "status":
        s = status()
        print(f"📒 publish ledger: {s['n_published']} event(s)"
              f"{' (honest-empty — no live events yet; trigger gated on Mohamed)' if not s['n_published'] else ''}")
        for b, n in sorted(s["by_brand"].items()):
            print(f"   • {b}: {n}")
        if s["earliest"]:
            print(f"   span: {s['earliest']} → {s['latest']}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
