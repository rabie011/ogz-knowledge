#!/usr/bin/env python3
"""Append an agent event to jsonl (append-only memory)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/agent_kit/registry.json"


def _ulid_placeholder() -> str:
    try:
        from ulid import ULID  # type: ignore

        return str(ULID())
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:26].ljust(26, "0")


def _resolve_events_path(agent_id: str, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_absolute() else ROOT / p
    if not REGISTRY.exists():
        raise SystemExit(f"registry missing: {REGISTRY}")
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for agent in reg.get("agents", []):
        if agent.get("id") == agent_id:
            home = Path(agent.get("mac_home", ".")).expanduser()
            rel = agent.get("events", "events/agent_events.jsonl")
            if rel.endswith("/") or "creative_outputs" in rel:
                return home / "data" / "agent_events.jsonl"
            return home / rel
    raise SystemExit(f"agent not in registry: {agent_id}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Log agent kit event (append-only)")
    ap.add_argument("--agent", required=True, help="Agent ID e.g. PROPOSALS")
    ap.add_argument("--type", required=True, dest="event_type")
    ap.add_argument("--client", default="", dest="client_slug")
    ap.add_argument("--run-ulid", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--artifacts", default="{}", help="JSON object")
    ap.add_argument("--events-path", default="", help="Override events file path")
    args = ap.parse_args()

    try:
        artifacts = json.loads(args.artifacts)
    except json.JSONDecodeError as e:
        print(f"invalid --artifacts JSON: {e}", file=sys.stderr)
        return 1

    path = _resolve_events_path(args.agent.upper(), args.events_path or None)
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "event_ulid": _ulid_placeholder(),
        "agent_id": args.agent.upper(),
        "event_type": args.event_type,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "client_slug": args.client_slug or None,
        "run_ulid": args.run_ulid or _ulid_placeholder(),
        "artifacts": artifacts,
        "summary": args.summary,
        "provenance": {
            "source": "scripts/agent_kit/log_event.py",
            "date_added": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "confirmer": "system",
            "confidence": "experimental",
            "scope": f"agent:{args.agent.lower()}",
        },
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "path": str(path), "event_ulid": event["event_ulid"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
