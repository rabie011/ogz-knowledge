#!/usr/bin/env python3
"""THE ONE ATTRIBUTION LEDGER — sole writer (June 12).
Every artifact the system ships carries WHO made it: no attribution line = the artifact
does not exist for feedback purposes. Append-only events: created | retired.

Defenses built in:
- grammar check (feedback_lib.validate_target on made_by)
- TRUTH check (producer_map: this `via` script may claim this made_by — kills
  self-misattribution, the named worst failure)
- version auto-increment; duplicate (artifact_id, version) refused
- tombstones: --retire archives a target cleanly (judgments keep lifetime history,
  open issues auto-close at the next router pass, no drift crash)

Usage:
  from attribute import attribute, retire, latest_version, made_by_of
  attribute("card:my_id", "card", "claude", via="scripts/queue_decision.py", reason="...")
  python3 scripts/attribute.py --retire card:old_thing --reason "DELETE APPROVED ..."
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import (append_jsonl, base, is_player, now_iso,
                          producer_allows, read_jsonl)

ARTIFACT_TYPES = {"card", "caption", "post", "batch", "summary", "receipt",
                  "report", "session", "portal", "portal_change"}


def ledger() -> Path:
    return base() / "data/attribution.jsonl"


def _git_short() -> str:
    try:
        r = subprocess.run(["git", "-C", str(base()), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or ""
    except Exception:
        return ""


def latest_version(artifact_id: str) -> int:
    """Highest created-version for this artifact (0 = never attributed)."""
    return max((e.get("artifact_version", 0) for e in read_jsonl(ledger())
                if e.get("artifact_id") == artifact_id and e.get("event") == "created"), default=0)


def is_retired(artifact_id: str) -> bool:
    return any(e.get("artifact_id") == artifact_id and e.get("event") == "retired"
               for e in read_jsonl(ledger()))


def made_by_of(artifact_id: str):
    """(made_by, version, members) of the LATEST created event, or (None, 0, None)."""
    best = None
    for e in read_jsonl(ledger()):
        if e.get("artifact_id") == artifact_id and e.get("event") == "created":
            if best is None or e.get("artifact_version", 0) > best.get("artifact_version", 0):
                best = e
    if not best:
        return None, 0, None
    return best.get("made_by"), best.get("artifact_version", 0), best.get("members")


def attribute(artifact_id: str, artifact_type: str, made_by: str, via: str,
              reason: str, inputs: list = None, members: list = None) -> dict:
    """Append a created-event. Raises (writes NOTHING) on any validation failure."""
    if artifact_type not in ARTIFACT_TYPES:
        raise ValueError(f"unknown artifact_type {artifact_type!r}")
    if not is_player(made_by):
        raise ValueError(f"made_by {made_by!r} is not a valid PLAYER")
    if not producer_allows(via, made_by):
        raise ValueError(f"producer_map: {via!r} may not claim made_by {made_by!r}")
    entry = {"schema_v": 1, "ts": now_iso(), "event": "created",
             "artifact_id": artifact_id, "artifact_type": artifact_type,
             "made_by": made_by, "via": via, "inputs": inputs or [],
             "reason": (reason or "")[:200],
             "artifact_version": latest_version(artifact_id) + 1,
             "members": members, "commit": _git_short()}
    append_jsonl(ledger(), entry)
    return entry


def retire(artifact_id: str, reason: str, by: str = "claude") -> dict:
    """Tombstone: the target archives cleanly everywhere downstream."""
    entry = {"schema_v": 1, "ts": now_iso(), "event": "retired",
             "artifact_id": artifact_id, "reason": (reason or "")[:200], "by": by}
    append_jsonl(ledger(), entry)
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retire", metavar="ARTIFACT_ID")
    ap.add_argument("--reason", default="")
    a = ap.parse_args()
    if a.retire:
        if not a.reason.strip():
            raise SystemExit("retire needs --reason")
        e = retire(a.retire, a.reason)
        print(f"🪦 retired {a.retire}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
