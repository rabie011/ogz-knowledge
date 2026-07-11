#!/usr/bin/env python3
"""One-time, idempotent classification of the five RFP content fixtures.

FABLE wake63 ruled that these bundles were born synthetic and must never enter
the production-client census. The migration refuses any bundle whose on-disk
birth evidence does not match that ruling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from organ_write import write_organ  # noqa: E402

EXPECTED_HANDLES = {
    "arena-pulse-arabia",
    "mizan-investment",
    "nassaj-arts-lab",
    "nur-litabqa",
    "sahm-founders",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def marker_for(root: Path, handle: str) -> dict:
    cdir = root / "clients" / handle
    state = _read(cdir / "profile" / "state.json")
    source = str((state.get("provenance") or {}).get("source") or "")
    ledger = cdir / "events" / "ledger.jsonl"
    if state.get("fake") is not True or "rfp_synthetic_v1" not in source:
        raise RuntimeError(f"{handle}: missing synthetic birth evidence")
    if ledger.exists() and ledger.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"{handle}: event ledger is non-empty; refuse synthetic reclassification")
    passport = _read(cdir / "profile" / "passport.json")
    sector = passport.get("sector")
    if not isinstance(sector, str) or not sector:
        raise RuntimeError(f"{handle}: passport sector missing")
    return {
        "handle": handle,
        "tier": "ready",
        "sector": sector,
        "purpose": "rfp_synthetic_content_fixture",
        "do_not_aggregate": True,
        "_prov": {
            "source": "rfp_synthetic_v1",
            "date_added": "2026-07-12",
            "confirmer": "FABLE-wake63",
            "confidence": "test_fixture",
            "scope": "fixture",
        },
    }


def migrate(root: Path = ROOT, check: bool = False) -> dict:
    changed = []
    unchanged = []
    for handle in sorted(EXPECTED_HANDLES):
        expected = marker_for(root, handle)
        path = root / "clients" / handle / "profile" / ".synthetic_fixture.json"
        if path.exists():
            if _read(path) != expected:
                raise RuntimeError(f"{handle}: existing synthetic marker differs from wake63 contract")
            unchanged.append(handle)
            continue
        if check:
            raise RuntimeError(f"{handle}: synthetic marker missing")
        write_organ(path, expected)
        changed.append(handle)
    return {"changed": changed, "unchanged": unchanged,
            "total": len(changed) + len(unchanged)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    result = migrate(check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
