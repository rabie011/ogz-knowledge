#!/usr/bin/env python3
"""cursor_mission_consumer.py — process pending missions from data/cursor_missions/pending/.

Cursor writes mission JSON; this script (or Claude Code) picks them up, executes, and writes
results to done/ or failed/. Appends a line to data/make_sure_log.jsonl on completion.

Run:  python3 scripts/cursor_mission_consumer.py [--once]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent.parent
MISSIONS = B / "data" / "cursor_missions"
PENDING = MISSIONS / "pending"
RUNNING = MISSIONS / "running"
DONE = MISSIONS / "done"
FAILED = MISSIONS / "failed"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _log_event(mission_id: str, status: str, summary: str) -> None:
    log_p = B / "data" / "make_sure_log.jsonl"
    line = json.dumps({
        "ts": _now(),
        "type": "cursor_mission",
        "mission_id": mission_id,
        "status": status,
        "summary": summary[:500],
    }, ensure_ascii=False)
    with open(log_p, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _run_shell(cmd: str, log_f, env: dict | None = None) -> int:
    log_f.write(f"\n$ {cmd}\n")
    log_f.flush()
    p = subprocess.run(
        cmd,
        shell=True,
        cwd=str(B),
        env=env or os.environ.copy(),
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )
    return p.returncode


def _process_mission(path: Path) -> None:
    mission_id = path.stem
    running_path = RUNNING / path.name
    shutil.move(str(path), str(running_path))
    log_path = DONE / f"{mission_id}.log"

    try:
        mission = json.loads(running_path.read_text(encoding="utf-8"))
    except Exception as e:
        result = {
            "id": mission_id,
            "status": "fail",
            "summary": f"unparseable mission JSON: {e}",
            "blockers": [str(e)],
            "finished": _now(),
        }
        (FAILED / f"{mission_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        running_path.unlink(missing_ok=True)
        _log_event(mission_id, "fail", result["summary"])
        return

    mid = mission.get("id", mission_id)
    mtype = mission.get("type", "commands")
    fix_allowed = bool(mission.get("fix_allowed", False))

    with open(log_path, "w", encoding="utf-8") as log_f:
        log_f.write(f"# cursor mission {mid} · started {_now()}\n")
        exit_codes: dict[str, int] = {}
        blockers: list[str] = []

        if mtype in ("brain-readiness", "orchestra"):
            wf = mission.get("workflow", "brain-readiness-test")
            log_f.write(f"# type={mtype} workflow={wf}\n")
            rc = _run_shell("python3 scripts/run_brain_readiness.py", log_f)
            exit_codes["brain_readiness"] = rc
            if rc != 0:
                blockers.append(f"run_brain_readiness.py exited {rc}")
        else:
            for i, cmd in enumerate(mission.get("commands") or []):
                key = f"cmd_{i}"
                rc = _run_shell(cmd, log_f)
                exit_codes[key] = rc
                if rc != 0:
                    blockers.append(f"command {i} failed (exit {rc}): {cmd[:120]}")

    # Prefer structured result from run_brain_readiness if present
    readiness_result = DONE / f"{mid}.json"
    if mtype in ("brain-readiness", "orchestra") and readiness_result.exists():
        running_path.unlink(missing_ok=True)
        _log_event(mid, json.loads(readiness_result.read_text()).get("status", "unknown"),
                   json.loads(readiness_result.read_text()).get("summary", ""))
        return

    status = "pass" if not blockers else ("partial" if any(v == 0 for v in exit_codes.values()) else "fail")
    result = {
        "id": mid,
        "status": status,
        "exit_codes": exit_codes,
        "summary": "all commands passed" if not blockers else f"{len(blockers)} blocker(s)",
        "log_path": str(log_path.relative_to(B)),
        "blockers": blockers,
        "fix_allowed": fix_allowed,
        "finished": _now(),
    }
    # Mission result JSON — never clobber artifact files missions may write to done/
    (DONE / "missions" / f"{mid}.json").parent.mkdir(parents=True, exist_ok=True)
    (DONE / "missions" / f"{mid}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Legacy path for idempotent lookups
    (DONE / f"{mid}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    running_path.unlink(missing_ok=True)
    _log_event(mid, status, result["summary"])


def main() -> int:
    for d in (PENDING, RUNNING, DONE, FAILED):
        d.mkdir(parents=True, exist_ok=True)

    pending = sorted(PENDING.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not pending:
        print("No pending cursor missions.")
        return 0

    once = "--once" in sys.argv
    for path in pending:
        print(f"Processing mission: {path.name}")
        _process_mission(path)
        if once:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
