#!/usr/bin/env python3
"""Bootstrap agent home folders from registry (Mac)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/agent_kit/registry.json"

DIRS = (
    "scripts",
    "lib",
    "prompts",
    "knowledge/clients",
    "knowledge/reference",
    "data/runs",
    "events",
)


def main() -> int:
    agent_id = (sys.argv[1] if len(sys.argv) > 1 else "").upper()
    if not agent_id:
        print("usage: bootstrap_home.py PROPOSALS", file=sys.stderr)
        return 1
    if not REGISTRY.exists():
        print(f"missing {REGISTRY}", file=sys.stderr)
        return 1

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    agent = next((a for a in reg.get("agents", []) if a.get("id") == agent_id), None)
    if not agent:
        print(f"unknown agent: {agent_id}", file=sys.stderr)
        return 1

    home = Path(agent.get("mac_home", ".")).expanduser()
    home.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (home / d).mkdir(parents=True, exist_ok=True)

    learnings = home / "knowledge" / "learnings.jsonl"
    if not learnings.exists():
        learnings.write_text("", encoding="utf-8")

    events = home / "events" / "agent_events.jsonl"
    if not events.exists():
        events.write_text("", encoding="utf-8")

    archive_root = Path(reg.get("mac_archive_root", "~/OGZ-Archive/agents")).expanduser()
    (archive_root / agent_id).mkdir(parents=True, exist_ok=True)

    print(json.dumps({"ok": True, "home": str(home), "archive": str(archive_root / agent_id)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
