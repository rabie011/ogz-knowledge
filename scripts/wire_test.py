#!/usr/bin/env python3
"""End-to-end wire test (Mac). Writes data/cursor_missions/artifacts/wire_test_latest.json."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/cursor_missions/artifacts/wire_test_latest.json"
ENDPOINT = ROOT / "data/brain_remote_endpoint.json"
ENV = Path.home() / ".abraham_env"


def _token() -> str | None:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _curl(url: str, token: str | None = None) -> tuple[bool, int, dict | str]:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read().decode()
            try:
                return True, r.status, json.loads(body)
            except json.JSONDecodeError:
                return True, r.status, body[:500]
    except urllib.error.HTTPError as e:
        try:
            return False, e.code, json.loads(e.read().decode())
        except Exception:
            return False, e.code, str(e)[:200]
    except Exception as e:
        return False, 0, str(e)[:200]


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    token = _token()
    report: dict = {"id": "wire-test", "at": now, "tests": {}, "pass": False}

    # Local brain
    ok, code, body = _curl("http://127.0.0.1:4140/health", token)
    report["tests"]["local_health"] = {"ok": ok and code == 200, "code": code, "body": body}

    # Tailscale endpoint file
    if not ENDPOINT.exists():
        sh = ROOT / "scripts/mac_tailscale_wire.sh"
        if sh.exists():
            subprocess.run(["bash", str(sh)], cwd=ROOT, check=False)
    report["tests"]["endpoint_file"] = ENDPOINT.exists()
    ep = {}
    if ENDPOINT.exists():
        ep = json.loads(ENDPOINT.read_text(encoding="utf-8"))
        report["tailscale_host"] = ep.get("host")

    # Tailnet health
    host = ep.get("host")
    if host:
        ok, code, body = _curl(f"http://{host}:4140/health", token)
        report["tests"]["tailnet_health"] = {"ok": ok and code == 200, "code": code, "url": f"http://{host}:4140/health", "body": body}
    else:
        report["tests"]["tailnet_health"] = {"ok": False, "error": "no tailscale host"}

    # Auth gate
    ok, code, _ = _curl("http://127.0.0.1:4140/extract?handle=albaik")
    report["tests"]["auth_required"] = {"ok": code == 401, "code": code}

    # Albaik extract with auth
    if token:
        ok, code, body = _curl("http://127.0.0.1:4140/extract?handle=albaik", token)
        pre = body.get("pre_fill", {}) if isinstance(body, dict) else {}
        report["tests"]["extract_albaik"] = {
            "ok": ok and code == 200 and len(pre) == 81,
            "code": code,
            "ready": body.get("ready") if isinstance(body, dict) else None,
        }

    # Wire-ready script
    wr = subprocess.run(
        [sys.executable, str(ROOT / "scripts/wire_ready_check.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report["tests"]["wire_ready_script"] = {"ok": wr.returncode == 0, "exit": wr.returncode}
    wr_path = ROOT / "data/cursor_missions/done/wire-ready-report.json"
    if wr_path.exists():
        report["wire_ready"] = json.loads(wr_path.read_text(encoding="utf-8")).get("wire_ready")

    core = [
        report["tests"].get("local_health", {}).get("ok"),
        report["tests"].get("tailnet_health", {}).get("ok"),
        report["tests"].get("auth_required", {}).get("ok"),
    ]
    report["pass"] = all(core)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
