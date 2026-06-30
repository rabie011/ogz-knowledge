#!/usr/bin/env python3
"""Append failures to mistake_registry.jsonl — never repeat scars at machine speed."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/mistake_registry.jsonl"

KNOWN_SCARS = {
    "severed_wire": "Built but not consumed (Rule #6)",
    "dead_handler": "UI card with no handler (Rule #7)",
    "gate_whisper": "Gate warned instead of refused (Rule #8)",
    "hand_curated": "Human did creative work system should do (Rule #12)",
    "false_approved": "Marked done without passing gate (Rule #13)",
    "judge_no_memory": "Verdict not persisted (Rule #14)",
    "consult_after_build": "DeepSeek consulted too late (Rule #19)",
    "session_leak": "Headless processes leaked",
    "readiness_lie": "False PREPARED / ready state",
    "home_glob": "Scanned home directory — hung",
    "shell_fix_lie": "fix_allowed on shell executor",
    "mission_fail": "Generic mission failure",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append(
    scar_class: str,
    mission_id: str,
    detail: str,
    *,
    source: str = "executor",
    blockers: list | None = None,
) -> dict:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": _now(),
        "scar_class": scar_class,
        "known": KNOWN_SCARS.get(scar_class, scar_class),
        "mission_id": mission_id,
        "source": source,
        "detail": detail[:500],
        "blockers": blockers or [],
    }
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def classify_failure(mission: dict, blockers: list[str]) -> str:
    text = " ".join(blockers).lower()
    if "wire" in text or "not connected" in text:
        return "severed_wire"
    if "ready" in text and "false" in text:
        return "readiness_lie"
    if mission.get("fix_allowed"):
        return "shell_fix_lie"
    if "~/" in text and "ogz-knowledge" not in text:
        return "home_glob"
    return "mission_fail"


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: mistake_registry.py <scar_class> <mission_id> <detail>")
        return 2
    entry = append(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
