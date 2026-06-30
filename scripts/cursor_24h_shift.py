#!/usr/bin/env python3
"""24h shift runner — mission bus poll + hourly context refresh + brain heartbeat.

Invoked by com.ogz.cursor-missions LaunchAgent every 5 minutes.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cursor_missions/.24h_state.json"
HEARTBEAT = ROOT / "data/cursor_missions/done/24h-heartbeat.jsonl"
LOG = Path.home() / "logs/cursor_24h_shift.log"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{_now()} {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def _brain_health() -> dict:
    token = ""
    env = Path.home() / ".abraham_env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
                break
    req = urllib.request.Request(
        "http://127.0.0.1:4140/health",
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return {"ok": True, "body": json.loads(r.read().decode())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> int:
    st = _load_state()
    now = time.time()

    # 1) Process one pending mission (Claude Code executor path)
    rc = subprocess.run(
        ["/opt/homebrew/bin/python3", str(ROOT / "scripts/cursor_mission_consumer.py"), "--once"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    consumer_out = (rc.stdout or rc.stderr or "").strip()
    if consumer_out and "No pending" not in consumer_out:
        _log(f"consumer: {consumer_out[:300]}")

    # 2) Hourly context refresh (for Cursor recovery without asking Mohamed)
    last_ctx = float(st.get("last_context_refresh", 0))
    if now - last_ctx >= 3600:
        subprocess.run(
            ["/opt/homebrew/bin/python3", str(ROOT / "scripts/cursor_build_context.py")],
            cwd=str(ROOT),
            check=False,
        )
        subprocess.run(
            ["/opt/homebrew/bin/python3", str(ROOT / "scripts/cursor_mine_history.py")],
            cwd=str(ROOT),
            check=False,
        )
        st["last_context_refresh"] = now
        _log("context refreshed (cursor_build_context + cursor_mine_history)")

    # 3) Brain heartbeat
    health = _brain_health()
    if not health.get("ok"):
        _log(f"brain_api unhealthy: {health.get('error')}")
        subprocess.run(
            ["/opt/homebrew/bin/python3", str(ROOT / "scripts/brain_api_launcher.py")],
            cwd=str(ROOT),
            check=False,
        )
        time.sleep(2)
        health = _brain_health()

    # 4) Nightly readiness (once per 12h if no pending missions)
    last_ready = float(st.get("last_readiness", 0))
    pending = list((ROOT / "data/cursor_missions/pending").glob("*.json"))
    if now - last_ready >= 43200 and not pending:
        mission = {
            "id": "nightly-brain-readiness",
            "from": "24h-shift",
            "created": _now(),
            "type": "brain-readiness",
            "goal": "Scheduled Phase A readiness — 24h daemon",
            "fix_allowed": False,
        }
        path = ROOT / "data/cursor_missions/pending" / f"{_now()[:10]}-nightly-brain-readiness.json"
        path.write_text(json.dumps(mission, indent=2), encoding="utf-8")
        st["last_readiness"] = now
        _log("queued nightly-brain-readiness mission")
        pending = list((ROOT / "data/cursor_missions/pending").glob("*.json"))

    # 4b) Autonomous chain — health cycle every 6h when queue idle
    last_chain = float(st.get("last_health_cycle", 0))
    if now - last_chain >= 21600 and not pending:
        hc = {
            "id": f"wave-health-{_now()[:10]}",
            "from": "24h-shift",
            "type": "commands",
            "goal": "Recurring health + status report",
            "fix_allowed": False,
            "commands": [
                "cd ~/Desktop/ogz-knowledge && python3 scripts/make_sure.py 2>&1 | tail -20",
                "cd ~/Desktop/ogz-knowledge && python3 scripts/cursor_autonomous_report.py",
            ],
        }
        (ROOT / "data/cursor_missions/pending" / f"{_now()[:16].replace(':','')}-health-cycle.json").write_text(
            json.dumps(hc, indent=2), encoding="utf-8"
        )
        st["last_health_cycle"] = now
        _log("queued recurring health-cycle mission")

    st["last_shift"] = now
    st["last_health"] = health
    _save_state(st)

    # 5) Autonomous chain — refresh full status report every shift when idle
    pending_now = list((ROOT / "data/cursor_missions/pending").glob("*.json"))
    if len(pending_now) <= 1:
        subprocess.run(
            ["/opt/homebrew/bin/python3", str(ROOT / "scripts/cursor_autonomous_report.py")],
            cwd=str(ROOT),
            check=False,
        )

    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    with open(HEARTBEAT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), "health": health, "consumer_rc": rc.returncode}, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
