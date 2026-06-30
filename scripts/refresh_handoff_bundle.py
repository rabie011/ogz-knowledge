#!/usr/bin/env python3
"""Refresh dev handoff bundle — prefill exports + contract fixtures for pilots and sector fakes."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "data/cursor_missions/artifacts/handoff"
FIXTURES = HANDOFF / "contract_fixtures"
DATA_FIXTURES = ROOT / "data/contract_fixtures"

HANDLES = [
    "albaik",
    "eatjurisha",
    "myfitness.sa",
    "fake_fnb",
    "fake_beauty",
    "fake_retail",
    "fake_fashion",
    "fake_realestate",
    "fake_wellness",
]

sys.path.insert(0, str(ROOT / "scripts"))
import export_prefill as ep


def main() -> int:
    HANDOFF.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    DATA_FIXTURES.mkdir(parents=True, exist_ok=True)

    written = []
    for handle in HANDLES:
        if not (ROOT / "clients" / handle).is_dir():
            continue
        payload = ep.export(handle)
        safe = handle.replace(".", "_")
        prefill_path = HANDOFF / f"prefill_{safe}.json"
        extract_path = FIXTURES / f"extract_{safe}.json"
        prefill_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        extract_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        data_copy = DATA_FIXTURES / f"extract_{safe}.json"
        data_copy.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(
            {
                "handle": handle,
                "ready": payload.get("ready"),
                "coverage_pct": (payload.get("_coverage") or {}).get("pct"),
                "prefill": str(prefill_path.relative_to(ROOT)),
            }
        )

    readme = {
        "brain_url": "http://HOST:4140",
        "auth": "Authorization: Bearer BRAIN_API_TOKEN",
        "endpoints": ["/health", "/extract?handle=", "/produce", "/job/{id}", "/performance"],
        "ready_gate": "check ready:true on /extract before /produce",
        "unknown_handle": "200 extraction_pending + background harvest (not 404)",
        "pilots": {
            "albaik": "produce-ready",
            "eatjurisha": "produce-ready",
            "myfitness.sa": "organs filled — render still needed for ready:true",
        },
        "sector_fakes": [h for h in HANDLES if h.startswith("fake_")],
        "files_in_bundle": sorted(p.name for p in HANDOFF.glob("*.json"))
        + ["openapi.yaml", "contract_fixtures/"],
        "exports": written,
        "refreshed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "when_to_wire": "after wire_ready_report.json shows wire_ready:true",
    }
    (HANDOFF / "README.json").write_text(json.dumps(readme, indent=2, ensure_ascii=False), encoding="utf-8")

    if (ROOT / "scripts/openapi.yaml").exists():
        shutil.copy2(ROOT / "scripts/openapi.yaml", HANDOFF / "openapi.yaml")

    report = {
        "id": "handoff-bundle-refresh",
        "generated": readme["refreshed"],
        "written": written,
        "count": len(written),
    }
    out = ROOT / "data/cursor_missions/done/handoff-bundle-refresh.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if len(written) >= 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
