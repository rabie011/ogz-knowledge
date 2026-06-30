#!/usr/bin/env python3
"""Flag agent missions that need live Claude Code — shell executor must not run them."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAKE = ROOT / "data/cursor_missions/.wake_claude"
QUEUE = ROOT / "data/cursor_missions/.agent_queue.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def flag(mission_path: Path) -> None:
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    entry = {"ts": _now(), "mission": mission.get("id", mission_path.stem), "path": str(mission_path)}
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    WAKE.write_text(_now(), encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: wake_agent_mission.py <mission.json>")
        return 2
    flag(Path(sys.argv[1]))
    print("flagged for live Claude Code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
