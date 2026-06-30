#!/usr/bin/env python3
"""Assert every canonical sector has ready + sparse synthetic fixtures."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/fake_clients/manifest.yaml"
OUT = ROOT / "data/cursor_missions/done/sector-coverage-test.json"
CANONICAL = [
    "f_and_b",
    "beauty_personal_care",
    "retail_lifestyle",
    "fashion",
    "real_estate",
    "healthcare_wellness",
]


def _load_manifest() -> dict:
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML required")
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data.get("clients") or {}


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    import export_prefill as ep

    manifest = _load_manifest()
    by_sector: dict[str, dict] = {s: {"ready": [], "sparse": []} for s in CANONICAL}
    details = []

    for handle, spec in manifest.items():
        sector = spec.get("sector")
        tier = spec.get("tier", "ready")
        if sector not in by_sector:
            continue
        root = ROOT / "clients" / handle
        marker = root / "profile" / ".synthetic_fixture.json"
        exists = root.is_dir() and marker.exists()
        exported = ep.export(handle) if exists else {}
        row = {
            "handle": handle,
            "sector": sector,
            "tier": tier,
            "exists": exists,
            "ready": exported.get("ready") if exists else False,
            "coverage_pct": (exported.get("_coverage") or {}).get("pct"),
        }
        details.append(row)
        if exists:
            by_sector[sector][tier if tier in ("ready", "sparse") else "ready"].append(handle)

    missing = []
    for sector in CANONICAL:
        if not by_sector[sector]["ready"]:
            missing.append(f"{sector}: no ready fake")
        if not by_sector[sector]["sparse"]:
            missing.append(f"{sector}: no sparse fake")

    bad_ready = [d for d in details if d["tier"] == "ready" and d["exists"] and not d["ready"]]
    bad_sparse = [d for d in details if d["tier"] == "sparse" and d["exists"] and d["ready"]]

    ok = not missing and not bad_ready and not bad_sparse
    report = {
        "id": "sector-coverage-test",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "canonical_sectors": CANONICAL,
        "by_sector": by_sector,
        "details": details,
        "missing": missing,
        "bad_ready": bad_ready,
        "bad_sparse": bad_sparse,
        "pass": ok,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
