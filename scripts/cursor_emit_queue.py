#!/usr/bin/env python3
"""Emit live-feed line when Cursor drops missions (orchestra only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "data/cursor_missions/pending"
sys.path.insert(0, str(ROOT / "scripts"))
from live_feed import emit  # noqa: E402


def main() -> int:
    missions = sorted(PENDING.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not missions:
        print("no pending")
        return 0
    names: list[str] = []
    for p in missions[-10:]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            names.append(d.get("id", p.stem))
        except Exception:
            names.append(p.stem)
    msg = f"Cursor queued {len(missions)} mission(s): {', '.join(names)}"
    emit("cursor", "mission_queued", msg)
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
