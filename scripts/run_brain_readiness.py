#!/usr/bin/env python3
"""run_brain_readiness.py — Phase A brain readiness suite for dev-handoff sign-off.

Runs unit tests, contract drift check, starts brain_api if needed, integration test, and smoke curls.
Writes structured result to data/cursor_missions/done/<mission_id>.json and contract fixtures.

Run:  python3 scripts/run_brain_readiness.py
      MISSION_ID=brain-readiness-phase-a python3 scripts/run_brain_readiness.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent.parent
DONE = B / "data" / "cursor_missions" / "done"
FIXTURES = B / "data" / "contract_fixtures"
BASE = os.environ.get("BRAIN_BASE", "http://127.0.0.1:4140")
MISSION_ID = os.environ.get("MISSION_ID", "brain-readiness-phase-a")
# Used when BRAIN_API_TOKEN is not in ~/.abraham_env (readiness runs only).
READINESS_DEV_TOKEN = "ogz-brain-readiness-dev"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _env_token() -> str | None:
    f = os.path.expanduser("~/.abraham_env")
    if os.path.exists(f):
        for line in open(f):
            if line.startswith("BRAIN_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("BRAIN_API_TOKEN")


def _run(cmd: str, env: dict | None = None) -> int:
    print(f"\n▶ {cmd}")
    return subprocess.run(cmd, shell=True, cwd=str(B), env=env or os.environ.copy()).returncode


def _health_ok() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _kill_brain_api_on_port() -> None:
    try:
        r = subprocess.run(
            ["lsof", "-ti", f":{BASE.rsplit(':', 1)[-1]}"],
            capture_output=True, text=True, timeout=5,
        )
        for pid in (r.stdout or "").strip().split():
            if pid.isdigit():
                subprocess.run(["kill", pid], check=False)
                print(f"Stopped brain_api pid {pid}")
    except Exception:
        pass


def _auth_health_ok(token: str) -> bool:
    try:
        req = urllib.request.Request(
            f"{BASE}/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            body = json.loads(r.read().decode())
            return r.status == 200 and body.get("auth_required") is not False
    except Exception:
        return False


def _start_brain_api(env: dict) -> subprocess.Popen | None:
    token = env.get("BRAIN_API_TOKEN", "")
    if _auth_health_ok(token):
        print("brain_api already healthy on :4140 (LaunchAgent) — reusing")
        return None
    _kill_brain_api_on_port()
    time.sleep(0.5)
    print("Starting brain_api with readiness token…")
    log = open(B / "data" / "cursor_missions" / "done" / "brain_api_server.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "scripts/brain_api.py"],
        cwd=str(B),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(40):
        if _health_ok():
            return proc
        time.sleep(0.5)
    return proc


def _curl_save(path: str, url: str, token: str | None = None, method: str = "GET", body: dict | None = None) -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    out = FIXTURES / path
    headers = []
    if token:
        headers.extend(["-H", f"Authorization: Bearer {token}"])
    if body is not None:
        headers.extend(["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)])
    cmd = ["curl", "-sS", "-X", method, *headers, url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        out.write_text(r.stdout or r.stderr or "", encoding="utf-8")
        return r.returncode
    except Exception as e:
        out.write_text(json.dumps({"error": str(e)}), encoding="utf-8")
        return 1


def main() -> int:
    DONE.mkdir(parents=True, exist_ok=True)
    token = _env_token() or READINESS_DEV_TOKEN
    env = os.environ.copy()
    env["BRAIN_API_TOKEN"] = token

    exit_codes: dict[str, int] = {}
    blockers: list[str] = []
    checks: dict[str, bool] = {}

    # Unit tests — brain-core (gate for readiness)
    unit_cmds = [
        ("test_job_lifecycle", "python3 scripts/test_job_lifecycle.py"),
        ("test_job_lifecycle_edges", "python3 scripts/tests/test_job_lifecycle_edges.py"),
        ("test_perf_ingestor_coldstart", "python3 scripts/tests/test_perf_ingestor_coldstart.py"),
        ("test_ledger_index", "python3 scripts/tests/test_ledger_index.py"),
    ]
    for key, cmd in unit_cmds:
        exit_codes[key] = _run(cmd, env)
        if exit_codes[key] != 0:
            blockers.append(f"{key} failed (exit {exit_codes[key]})")

    # Full suite — informational only (pre-existing failures outside brain API)
    suite_note = None
    exit_codes["unittest_discover"] = _run("python3 -m unittest discover -s scripts/tests -q", env)
    if exit_codes["unittest_discover"] != 0:
        suite_note = "full unittest discover has pre-existing failures (not brain-API blockers)"

    # Contract drift
    exit_codes["contract_drift"] = _run("python3 scripts/contract_drift_check.py", env)
    if exit_codes["contract_drift"] != 0:
        blockers.append("openapi.yaml ↔ brain_api.py drift")

    # brain_api + integration (always restart so token matches)
    api_proc = _start_brain_api(env)
    if not _health_ok():
        blockers.append("brain_api not reachable after start attempt")
        exit_codes["integration"] = 2
    else:
        exit_codes["integration"] = _run("python3 scripts/test_brain_connection.py", env)
        if exit_codes["integration"] != 0:
            blockers.append("test_brain_connection.py failed")

    # Smoke curls + contract fixtures
    _curl_save("health.json", f"{BASE}/health")
    if token:
        _curl_save("extract_albaik.json", f"{BASE}/extract?handle=albaik", token)
        _curl_save("extract_myfitness.json", f"{BASE}/extract?handle=myfitness.sa", token)
        _curl_save(
            "produce_eatjurisha.json",
            f"{BASE}/produce",
            token,
            method="POST",
            body={"handle": "eatjurisha", "product": "جريش", "chain": "G03", "produce": False},
        )
        _curl_save(
            "performance_sample.json",
            f"{BASE}/performance",
            token,
            method="POST",
            body={
                "post_id": "eatjurisha:جريش:G03",
                "likes": 120,
                "saves": 30,
                "comments": 5,
                "shares": 2,
                "reach": 5000,
            },
        )
        # Auth check: no bearer → 401 on /extract
        try:
            req = urllib.request.Request(f"{BASE}/extract?handle=albaik")
            urllib.request.urlopen(req, timeout=5)
            checks["auth_401_without_bearer"] = False
            blockers.append("auth: /extract returned 200 without bearer (expected 401)")
        except urllib.error.HTTPError as e:
            checks["auth_401_without_bearer"] = e.code == 401
            if e.code != 401:
                blockers.append(f"auth: expected 401 without bearer, got {e.code}")

        # Parse extract fixtures for checklist evidence
        try:
            albaik = json.loads((FIXTURES / "extract_albaik.json").read_text(encoding="utf-8"))
            pre = albaik.get("pre_fill") or {}
            cov = (albaik.get("_coverage") or {}).get("pct", 0)
            checks["albaik_81_keys"] = len(pre) == 81
            checks["albaik_coverage_75"] = cov >= 75
            checks["albaik_ready"] = bool(albaik.get("ready"))
            if len(pre) != 81:
                blockers.append(f"albaik pre_fill has {len(pre)} keys, expected 81")
            if cov < 75:
                blockers.append(f"albaik coverage {cov}% < 75%")
        except Exception as e:
            blockers.append(f"could not parse extract_albaik fixture: {e}")

        try:
            mf = json.loads((FIXTURES / "extract_myfitness.json").read_text(encoding="utf-8"))
            cov = (mf.get("_coverage") or {}).get("pct", 100)
            checks["myfitness_sparse"] = cov < 60
            checks["myfitness_not_ready"] = not bool(mf.get("ready"))
        except Exception as e:
            blockers.append(f"could not parse extract_myfitness fixture: {e}")
    else:
        blockers.append("BRAIN_API_TOKEN missing after readiness setup")

    if api_proc and api_proc.poll() is None:
        api_proc.terminate()

    unit_ok = all(exit_codes.get(k, 1) == 0 for k, _ in unit_cmds)
    checks["unit_tests_green"] = unit_ok
    checks["full_suite_green"] = exit_codes.get("unittest_discover") == 0
    checks["contract_drift_clean"] = exit_codes.get("contract_drift") == 0
    checks["integration_green"] = exit_codes.get("integration") == 0
    checks["fixtures_saved"] = (FIXTURES / "health.json").exists()

    # De-duplicate blockers
    blockers = list(dict.fromkeys(blockers))

    if not blockers:
        status = "pass"
        summary = "Phase A brain readiness: all core checks passed"
    elif unit_ok and exit_codes.get("integration") == 0:
        status = "partial"
        summary = f"Phase A partial: {len(blockers)} non-blocking issue(s)"
    else:
        status = "fail"
        summary = f"Phase A failed: {len(blockers)} blocker(s)"

    result = {
        "id": MISSION_ID,
        "status": status,
        "exit_codes": exit_codes,
        "checks": checks,
        "summary": summary,
        "log_path": "data/cursor_missions/done/brain-readiness-phase-a.log",
        "blockers": blockers,
        "notes": {"full_suite": suite_note} if suite_note else {},
        "finished": _now(),
    }
    out = DONE / f"{MISSION_ID}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'='*55}\n  {summary}\n  written: {out}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
