#!/usr/bin/env python3
"""Shell mission executor (file name is historical — NOT Claude Code LLM).

Runs commands[] from pending/*.json via executor_daemon. For code fixes use
type:agent missions → wake_agent_mission.py → live Claude Code session.

  python3 scripts/claude_code_claim_executor.py drain   # claim → run-all → release
  python3 scripts/claude_code_claim_executor.py claim
  python3 scripts/claude_code_claim_executor.py run-next
  python3 scripts/claude_code_claim_executor.py release
  python3 scripts/claude_code_claim_executor.py status
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "data/cursor_missions"
PENDING = MISSIONS / "pending"
RUNNING = MISSIONS / "running"
DONE = MISSIONS / "done"
FAILED = MISSIONS / "failed"
LOCK = MISSIONS / ".executor_live.lock"
LIVE = MISSIONS / "LIVE_STATUS.md"
PYTHON = "/opt/homebrew/bin/python3"
FEED_URL = "http://localhost:4141"


def _feed(source: str, type_: str, message: str, level: str = "info", **extra) -> None:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from live_feed import emit

        emit(source, type_, message, level=level, **extra)
    except Exception:
        pass


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_lock() -> dict | None:
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _update_live(msg: str) -> None:
    body = f"""# LIVE — Claude Code executor

Updated: {_now()}

{msg}

## Queue

| Pending | Running |
|---------|---------|
| {len(list(PENDING.glob('*.json')))} | {len(list(RUNNING.glob('*.json')))} |

## Watch live (one tab)

**{FEED_URL}** — plain-English feed. Pin in browser. No iTerm required.

Cursor drops missions to `pending/`; executor daemon drains them.
"""
    LIVE.write_text(body, encoding="utf-8")


def cmd_status() -> int:
    lock = _read_lock()
    alive = lock and _pid_alive(int(lock.get("pid", 0)))
    print(json.dumps({
        "lock": lock,
        "lock_alive": bool(alive),
        "pending": [p.name for p in sorted(PENDING.glob("*.json"))],
        "running": [p.name for p in sorted(RUNNING.glob("*.json"))],
    }, indent=2))
    return 0


def cmd_claim() -> int:
    lock = _read_lock()
    if lock and _pid_alive(int(lock.get("pid", 0))):
        print(f"Executor already claimed by pid {lock['pid']}")
        return 1
    if lock:
        LOCK.unlink(missing_ok=True)
    payload = {"pid": os.getpid(), "claimed_at": _now(), "session": "executor_daemon"}
    LOCK.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _update_live(f"**Claimed** by executor pid {os.getpid()} at {_now()}")
    _feed("executor", "startup", f"Executor claimed queue at {_now()[:16]}")
    print("claimed")
    return 0


def cmd_release() -> int:
    LOCK.unlink(missing_ok=True)
    _update_live(f"**Released** at {_now()} — queue idle or blocked.")
    _feed("executor", "idle", "Executor released — queue idle")
    print("released")
    return 0


def _fix_cmd(cmd: str) -> str:
    """Prefix bare python3 only — do not double /opt/homebrew/bin/python3 in path."""
    if PYTHON in cmd:
        return cmd
    return cmd.replace("python3 ", f"{PYTHON} ")


def _run_shell(cmd: str, log_f) -> int:
    log_f.write(f"\n$ {cmd}\n")
    log_f.flush()
    env = os.environ.copy()
    env["PATH"] = f"/Users/abarihm/.local/bin:/opt/homebrew/bin:{env.get('PATH', '')}"
    return subprocess.run(_fix_cmd(cmd), shell=True, cwd=str(ROOT), env=env, stdout=log_f, stderr=subprocess.STDOUT).returncode


def cmd_run_next() -> int:
    for d in (PENDING, RUNNING, DONE, FAILED):
        d.mkdir(parents=True, exist_ok=True)

    pending = sorted(PENDING.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not pending:
        print("no pending")
        return 0

    path = pending[0]
    mission_id = path.stem
    mission_peek = json.loads(path.read_text(encoding="utf-8"))
    mtype_peek = mission_peek.get("type", "commands")
    if mtype_peek == "agent" or (
        mission_peek.get("fix_allowed") and not mission_peek.get("commands")
    ):
        subprocess.run(
            [PYTHON, str(ROOT / "scripts/wake_agent_mission.py"), str(path)],
            cwd=str(ROOT),
            check=False,
        )
        _feed(
            "executor",
            "blocked",
            f"Mission {mission_peek.get('id', mission_id)} needs live Claude Code — flagged, not shell-run",
            level="warn",
        )
        print(f"agent mission flagged: {mission_id}")
        return 0

    running_path = RUNNING / path.name
    shutil.move(str(path), str(running_path))
    mission = mission_peek
    mid = mission.get("id", mission_id)
    log_path = DONE / f"{mission_id}.log"

    goal = mission.get("goal", mid)
    _update_live(f"**Running** mission `{mid}` — started {_now()}")
    _feed("executor", "mission_start", f"Started: {mid} — {goal[:120]}")

    with open(log_path, "w", encoding="utf-8") as log_f:
        log_f.write(f"# Claude Code mission {mid} · {_now()}\n")
        exit_codes: dict[str, int] = {}
        blockers: list[str] = []
        mtype = mission.get("type", "commands")

        if mtype in ("brain-readiness", "orchestra"):
            rc = _run_shell(f"{PYTHON} scripts/run_brain_readiness.py", log_f)
            exit_codes["brain_readiness"] = rc
            if rc != 0:
                blockers.append(f"run_brain_readiness.py exited {rc}")
        else:
            for i, cmd in enumerate(mission.get("commands") or []):
                # Only replace bare 'python3' not already prefixed with a full path
                fixed = re.sub(r'(?<![/\w])python3\b', PYTHON, cmd)
                rc = _run_shell(fixed, log_f)
                exit_codes[f"cmd_{i}"] = rc
                if rc != 0:
                    blockers.append(f"command {i} failed (exit {rc}): {cmd[:100]}")

    readiness = DONE / f"{mid}.json"
    if mtype in ("brain-readiness", "orchestra") and readiness.exists():
        running_path.unlink(missing_ok=True)
        _update_live(f"**Done** `{mid}` (brain-readiness) at {_now()}")
        print(f"done: {mid}")
        return 0

    status = "pass" if not blockers else ("partial" if any(v == 0 for v in exit_codes.values()) else "fail")
    result = {
        "id": mid,
        "executor": "shell",
        "status": status,
        "exit_codes": exit_codes,
        "summary": "all commands passed" if not blockers else f"{len(blockers)} blocker(s)",
        "log_path": str(log_path.relative_to(ROOT)),
        "blockers": blockers,
        "fix_allowed": bool(mission.get("fix_allowed", False)),
        "finished": _now(),
    }
    (DONE / "missions").mkdir(parents=True, exist_ok=True)
    (DONE / "missions" / f"{mid}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (DONE / f"{mid}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    running_path.unlink(missing_ok=True)

    summary = result.get("summary", status)
    level = "error" if status == "fail" else ("warn" if status == "partial" else "info")
    if status in ("fail", "partial"):
        try:
            from mistake_registry import append, classify_failure

            scar = classify_failure(mission, blockers)
            append(scar, mid, summary, blockers=blockers)
        except Exception:
            pass
    _feed(
        "executor",
        "mission_done",
        f"Finished {mid}: {status} — {summary}",
        level=level,
        status=status,
        mission_id=mid,
    )
    _update_live(f"**Finished** `{mid}` → {status} at {_now()}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status == "pass" else 1


def cmd_drain() -> int:
    """Claim, run all pending missions, release — single process (lock stays valid)."""
    if cmd_claim() != 0:
        return 1
    rc = 0
    try:
        while list(PENDING.glob("*.json")):
            step = cmd_run_next()
            if step != 0:
                rc = step
                break
    finally:
        cmd_release()
    return rc


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "claim":
        return cmd_claim()
    if cmd == "release":
        return cmd_release()
    if cmd == "run-next":
        return cmd_run_next()
    if cmd == "drain":
        return cmd_drain()
    if cmd == "status":
        return cmd_status()
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
