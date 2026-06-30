#!/usr/bin/env python3
"""Validate OGZ 24/7 stack — all agents/daemons respond."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/opt/homebrew/bin/python3"


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def main() -> int:
    results: list[dict] = []

    # Brain API
    try:
        urllib.request.urlopen("http://127.0.0.1:4140/health", timeout=5)
        results.append(check("brain_api", True))
    except Exception as e:
        results.append(check("brain_api", False, str(e)))

    # Live feed
    try:
        urllib.request.urlopen("http://127.0.0.1:4141/", timeout=5)
        results.append(check("live_feed", True))
    except Exception as e:
        results.append(check("live_feed", False, str(e)))

    # Registry
    reg = ROOT / "data/agents/AGENT_REGISTRY.json"
    results.append(check("agent_registry", reg.exists()))

    # Knowledge
    idx = list((ROOT / "data/knowledge/indexed").glob("**/*.json"))
    results.append(check("knowledge_indexed", len(idx) > 0, f"{len(idx)} docs"))

    # LaunchAgents — parked daemons unloaded is OK in Mode A
    parked: set[str] = set()
    reg_path = ROOT / "data/agents/AGENT_REGISTRY.json"
    if reg_path.exists():
        try:
            parked = set(json.loads(reg_path.read_text()).get("parked_daemons", []))
        except Exception:
            pass
    for label in ("com.ogz.executor", "com.ogz.consult-shift", "com.ogz.orchestra", "com.ogz.memory-keeper"):
        rc = subprocess.run(["launchctl", "list", label], capture_output=True, text=True)
        loaded = rc.returncode == 0
        if label in parked and not loaded:
            results.append(check(label, True, "parked (Mode A — expected unloaded)"))
        elif label in parked and loaded:
            results.append(check(label, True, "loaded (unparked)"))
        else:
            results.append(check(label, loaded))

    # Executor lock optional
    lock = ROOT / "data/cursor_missions/.executor_live.lock"
    if lock.exists():
        try:
            pid = int(json.loads(lock.read_text()).get("pid", 0))
            os.kill(pid, 0)
            results.append(check("executor_daemon", True, f"pid {pid}"))
        except Exception:
            results.append(check("executor_daemon", False, "stale lock"))
    else:
        results.append(check("executor_daemon", True, "idle (launchd keepalive)"))

    out = {"ok": all(r["ok"] for r in results), "checks": results}
    path = ROOT / "data/cursor_missions/artifacts/validate_stack.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
