#!/usr/bin/env python3
"""Append-only live feed — plain-English events for the OGZ situation room."""
from __future__ import annotations

import fcntl
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/live_feed/events.jsonl"
LOCK = ROOT / "data/live_feed/.events.lock"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def emit(
    source: str,
    type_: str,
    message: str,
    *,
    level: str = "info",
    **extra: Any,
) -> dict[str, Any]:
    """Append one human-readable event. Thread-safe via flock."""
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    rec: dict[str, Any] = {
        "ts": _now(),
        "source": source,
        "type": type_,
        "level": level,
        "message": message,
    }
    if extra:
        rec.update(extra)
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with open(LOCK, "a", encoding="utf-8") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            with open(EVENTS, "a", encoding="utf-8") as f:
                f.write(line)
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    return rec


def read_recent(limit: int = 100) -> list[dict[str, Any]]:
    if not EVENTS.exists():
        return []
    lines = EVENTS.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: live_feed.py <source> <type> <message> [level]")
        print("Example: live_feed.py cursor mission_queued 'Queued 3 missions' info")
        return 2
    source, type_, message = sys.argv[1], sys.argv[2], sys.argv[3]
    level = sys.argv[4] if len(sys.argv) > 4 else "info"
    rec = emit(source, type_, message, level=level)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
