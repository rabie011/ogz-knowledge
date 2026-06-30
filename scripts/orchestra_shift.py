#!/usr/bin/env python3
"""Orchestra shift — Cursor's daemon. Plans queue + wakes Claude Code LIVE. NEVER executes missions.

Replaces shell consumer. Claude Code is the only executor (visible session).
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/cursor_missions/.24h_state.json"
HEARTBEAT = ROOT / "data/cursor_missions/done/24h-heartbeat.jsonl"
WAKE_FLAG = ROOT / "data/cursor_missions/.wake_claude"
LOCK = ROOT / "data/cursor_missions/.executor_live.lock"
LIVE = ROOT / "data/cursor_missions/LIVE_STATUS.md"
LOG = Path.home() / "logs/orchestra_shift.log"
PYTHON = "/opt/homebrew/bin/python3"
WAKE_SH = ROOT / "scripts/wake_claude_code_live.sh"  # deprecated — use executor daemon
FEED_PY = ROOT / "scripts/live_feed.py"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{_now()} {msg}\n")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _executor_live() -> bool:
    if not LOCK.exists():
        return False
    try:
        pid = int(json.loads(LOCK.read_text()).get("pid", 0))
        return _pid_alive(pid)
    except Exception:
        return False


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


def _feed(source: str, type_: str, message: str, level: str = "info") -> None:
    try:
        subprocess.run(
            [PYTHON, str(FEED_PY), source, type_, message, level],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
        )
    except Exception:
        pass


def _update_live_board(pending: list, executor_live: bool) -> None:
    LIVE.write_text(
        f"""# LIVE — Orchestra status

Updated: {_now()}

| Role | Who |
|------|-----|
| **Orchestra** | Cursor — plans, drops missions |
| **Executor** | Background daemon — drains `pending/` |
| **You** | Mohamed — **http://localhost:4141** (one tab) |

## Right now

- Pending missions: **{len(pending)}**
- Executor live: **{"yes" if executor_live else "idle — will drain on next tick"}**
- Watch: **http://localhost:4141**

## Pending queue

{chr(10).join(f"- `{p}`" for p in pending) or "_empty_"}
""",
        encoding="utf-8",
    )


def _maybe_wake_claude(pending: list) -> None:
    """No iTerm. Executor daemon (com.ogz.executor) drains pending/."""
    if not pending:
        return
    if _executor_live():
        _log(f"pending={len(pending)} — executor daemon will drain")
        _feed("orchestra", "queue", f"{len(pending)} mission(s) waiting — executor will pick up")
        return
    _feed("orchestra", "queue", f"{len(pending)} mission(s) queued — nudging executor daemon")
    WAKE_FLAG.unlink(missing_ok=True)


def main() -> int:
    st = _load_state()
    now = time.time()
    pending_dir = ROOT / "data/cursor_missions/pending"
    pending = sorted(p.name for p in pending_dir.glob("*.json"))

    # NO cursor_mission_consumer — Claude Code only

    executor_live = _executor_live()
    _update_live_board(pending, executor_live)
    _maybe_wake_claude(pending)

    # Hourly context refresh (for Cursor recovery — read-only scripts OK for orchestra)
    last_ctx = float(st.get("last_context_refresh", 0))
    if now - last_ctx >= 3600:
        subprocess.run([PYTHON, str(ROOT / "scripts/cursor_build_context.py")], cwd=str(ROOT), check=False)
        subprocess.run([PYTHON, str(ROOT / "scripts/cursor_mine_history.py")], cwd=str(ROOT), check=False)
        st["last_context_refresh"] = now
        _log("context refreshed")

    health = _brain_health()
    if health.get("ok"):
        body = health.get("body") or {}
        q = body.get("queue_depth", "?")
        if not st.get("last_brain_ok_feed") or now - float(st.get("last_brain_ok_feed", 0)) >= 3600:
            _feed("brain", "heartbeat", f"Brain API healthy — queue depth {q}")
            st["last_brain_ok_feed"] = now
    else:
        err = health.get("error", "unknown")
        _log(f"brain_api unhealthy: {err}")
        _feed("brain", "error", f"Brain API down — restarting ({err})", level="error")
        subprocess.run([PYTHON, str(ROOT / "scripts/brain_api_launcher.py")], cwd=str(ROOT), check=False)
        time.sleep(2)
        health = _brain_health()

    # Queue health mission for Claude (not shell-run)
    last_chain = float(st.get("last_health_cycle", 0))
    if now - last_chain >= 21600 and not pending:
        hc = {
            "id": f"wave-health-{_now()[:10]}",
            "from": "orchestra",
            "type": "commands",
            "goal": "Recurring health — Claude executes live",
            "fix_allowed": False,
            "commands": [
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/seed_fake_sector_client.py --all",
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/test_sector_coverage.py",
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/fake_platform_client.py",
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/refresh_handoff_bundle.py",
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/wire_ready_check.py",
                f"cd ~/Desktop/ogz-knowledge && {PYTHON} scripts/cursor_autonomous_report.py",
            ],
        }
        path = pending_dir / f"{_now()[:16].replace(':', '')}-health-cycle.json"
        path.write_text(json.dumps(hc, indent=2), encoding="utf-8")
        WAKE_FLAG.write_text(_now(), encoding="utf-8")
        st["last_health_cycle"] = now
        _log("queued health-cycle for Claude")
        pending = sorted(p.name for p in pending_dir.glob("*.json"))
        _maybe_wake_claude(pending)

    st["last_shift"] = now
    st["last_health"] = health
    st["executor_live"] = executor_live
    st["pending_count"] = len(pending)
    _save_state(st)

    subprocess.run([PYTHON, str(ROOT / "scripts/cursor_autonomous_report.py")], cwd=str(ROOT), check=False)

    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    with open(HEARTBEAT, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": _now(),
            "health": health,
            "executor_live": executor_live,
            "pending": len(pending),
            "orchestra": True,
        }, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
