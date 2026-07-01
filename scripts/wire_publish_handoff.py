#!/usr/bin/env python3
"""After wire-go: merge Tailscale endpoint + wire-ready into handoff bundle."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = ROOT / "data/brain_remote_endpoint.json"
WIRE_READY = ROOT / "data/cursor_missions/done/wire-ready-report.json"
HANDOFF = ROOT / "data/cursor_missions/artifacts/handoff/README.json"
OUT = ROOT / "data/cursor_missions/artifacts/WIRE_STATUS.json"


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status: dict = {
        "id": "wire-status",
        "mohamed_gate": "wire",
        "authorized_at": now,
        "control": "Cursor only — brain via tailnet + GitHub mission bus",
    }

    if ENDPOINT.exists():
        ep = json.loads(ENDPOINT.read_text(encoding="utf-8"))
        status["tailscale"] = ep
        host = ep.get("host")
        port = ep.get("port", 4140)
        if host:
            status["brain_url_tailnet"] = f"http://{host}:{port}"
    else:
        status["tailscale"] = {"ok": False, "error": "brain_remote_endpoint.json missing"}

    if WIRE_READY.exists():
        wr = json.loads(WIRE_READY.read_text(encoding="utf-8"))
        status["wire_ready"] = wr.get("wire_ready")
        status["wire_checks"] = wr.get("checks", {})
        status["wire_blockers"] = wr.get("blockers", [])
    else:
        status["wire_ready"] = None
        status["wire_blockers"] = ["wire-ready-report.json not generated"]

    if HANDOFF.exists():
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        if status.get("brain_url_tailnet"):
            handoff["brain_url"] = status["brain_url_tailnet"]
            handoff["brain_url_local"] = "http://127.0.0.1:4140"
            handoff["wired_at"] = now
            handoff["when_to_wire"] = "Mohamed said wire — tailnet endpoint in WIRE_STATUS.json"
        HANDOFF.write_text(json.dumps(handoff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        status["handoff_updated"] = True
    else:
        status["handoff_updated"] = False

    OUT.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
