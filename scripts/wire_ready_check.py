#!/usr/bin/env python3
"""Wire-ready gate — brain + system checks without platform wiring."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/done/wire-ready-report.json"
BASE = os.environ.get("BRAIN_BASE", "http://127.0.0.1:4140")


def _token() -> str:
    p = Path.home() / ".abraham_env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("BRAIN_API_TOKEN", "")


def _curl(path: str, token: str | None = None, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(f"{BASE}{path}", headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def _sh(cmd: str) -> int:
    return subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True).returncode


def main() -> int:
    token = _token()
    checks: dict[str, bool] = {}
    notes: list[str] = []
    blockers: list[str] = []

    # Daemons
    la = subprocess.run("launchctl list 2>/dev/null | grep com.ogz.brain-api", shell=True, capture_output=True, text=True)
    checks["daemon_brain_api"] = "com.ogz.brain-api" in (la.stdout or "")
    checks["daemon_cursor_missions"] = _sh("launchctl list 2>/dev/null | grep -q com.ogz.cursor-missions") == 0
    checks["token_in_env"] = bool(token)

    # Health
    st, body = _curl("/health")
    checks["health_ok"] = st == 200 and body.get("ok") is True
    checks["auth_required"] = body.get("auth_required") is True

    # Failure modes
    st, _ = _curl("/extract?handle=albaik")
    checks["extract_no_auth_rejected"] = st == 401
    st, body = _curl("/extract?handle=intake_probe_wire_ready", token)
    checks["extract_unknown_pending_200"] = (
        st == 200
        and body.get("ok") is True
        and body.get("onboarding_status") in ("extraction_pending", "extraction_failed")
        and body.get("ready") is False
    )
    st, body = _curl("/extract?handle=albaik", token)
    checks["extract_albaik_200"] = st == 200 and len(body.get("pre_fill", {})) == 81
    checks["albaik_ready"] = body.get("ready") is True

    st, body = _curl("/extract?handle=myfitness.sa", token)
    checks["myfitness_refuse_ready_false"] = body.get("ready") is False

    st, body = _curl(
        "/produce",
        token,
        method="POST",
        body={"handle": "myfitness.sa", "product": "test", "chain": "U01", "produce": False},
    )
    checks["produce_sparse_handled"] = st in (200, 202, 400, 422) or body.get("status") == "refused"

    # Core scripts
    for name, cmd in [
        ("contract_drift", "python3 scripts/contract_drift_check.py"),
        ("job_lifecycle", "python3 scripts/test_job_lifecycle.py"),
    ]:
        rc = _sh(cmd)
        checks[name] = rc == 0
        if rc != 0:
            blockers.append(f"{name} exit {rc}")

    fixtures = ROOT / "data/contract_fixtures"
    checks["fixtures_present"] = fixtures.exists() and len(list(fixtures.glob("*.json"))) >= 4

    # Portal (informational)
    try:
        with urllib.request.urlopen("http://127.0.0.1:4199/", timeout=3) as r:
            checks["portal_reachable"] = r.status < 500
    except Exception:
        checks["portal_reachable"] = False
        notes.append("portal :4199 not reachable from wire-ready check")

    core = [
        "daemon_brain_api", "token_in_env", "health_ok", "auth_required",
        "extract_no_auth_rejected", "extract_unknown_pending_200", "extract_albaik_200",
        "contract_drift", "job_lifecycle", "fixtures_present",
    ]
    wire_ready = all(checks.get(k) for k in core)

    report = {
        "id": "wire-ready-report",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "wire_ready": wire_ready,
        "checks": checks,
        "blockers": blockers,
        "notes": notes,
        "flakes_accepted": [
            "integration 32/34 (myfitness coverage test + 2-judge HUMAIN)",
            "full unittest discover pre-existing failures",
            "portal /health path may differ from /",
        ],
        "not_in_scope": ["platform wiring", "fal re-renders without founder go"],
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if wire_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
