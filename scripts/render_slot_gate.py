#!/usr/bin/env python3
"""B254 (June 22) — the blackout-aware render_slot decision, PURE so the
orchestrator→render seam is testable without a live daemon or a real render.

A `render_slot` queue task asks ONE question before it renders a client slot:
is a hard blackout in force? blackout_gate.check() owns that truth (the switch is
human-only — B140/B136). This function consumes it and returns an action:

  • {"action": "requeue", reason, blackout: True, warnings}
        a hard blackout (national mourning, etc.) is active → the slot must NOT
        render and must NOT flip the switch. The orchestrator requeues it with the
        reason; it retries once the human lifts the switch.
  • {"action": "render", reason: None, blackout: False, warnings}
        no hard block → render. `warnings` (quiet hours / maghrib / jumuah / low-
        activity weekday) are ADVISORY only — they never block a render, they ride
        along for the report (the negative-space law blocks on the SWITCH alone).

Rule #6: the orchestrator's render_slot handler is the consumer, wired + tested the
same step. Rule #8: a hard blackout REQUEUES (refuses to render), it does not warn-
and-proceed.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from blackout_gate import check as blackout_check

# B254b (June 22) — requeue backoff. A hard blackout can last days (national mourning).
# Without backoff the orchestrator re-picks the requeued slot every ~10s, writing a new
# file + a new Mira line each cycle (load + Rule #10 flood). The cure: each requeue stamps
# a not_before that grows exponentially and the consumer skips slots not yet due.
_BACKOFF_BASE_SEC = 60          # first requeue waits 1 min
_BACKOFF_CAP_SEC = 1800         # never wait more than ~30 min between retries


def backoff_seconds(requeue_count: int) -> int:
    """Exponential backoff, capped. count=1→60s, 2→120, 3→240 … cap 1800s (~30min).

    A count <= 0 is treated as the first retry (60s) — a requeue always waits.
    """
    n = max(1, int(requeue_count))
    # 60 * 2**(n-1), but cap the exponent so 2**big never overflows before min().
    if n - 1 >= 16:  # 60 * 2**15 already far past the cap
        return _BACKOFF_CAP_SEC
    return min(_BACKOFF_BASE_SEC * (2 ** (n - 1)), _BACKOFF_CAP_SEC)


def plan_requeue(task: dict, decision: dict, now=None) -> dict:
    """Pure: given the current task + a requeue decision, return the NEW task dict to
    persist — requeue_count incremented, reason recorded, and a not_before stamped
    backoff_seconds() into the future. The orchestrator writes this to a STABLE filename
    (one reusable file per handle) so a long blackout overwrites in place, never piles up.
    """
    now = now or datetime.now()
    count = int(task.get("requeue_count", 0)) + 1
    rq = dict(task)
    rq["requeue_count"] = count
    rq["requeue_reason"] = decision.get("reason") or "blackout active"
    rq["not_before"] = (now + timedelta(seconds=backoff_seconds(count))).isoformat(timespec="seconds")
    return rq


def is_ready(task: dict, now=None) -> bool:
    """Consumer predicate (Rule #6): is this task due to run? True unless it carries a
    not_before in the future. A missing/malformed not_before is treated as ready — the
    gate fails OPEN here because the blackout gate itself is the real refuse-don't-warn
    guard; not_before is only a spin damper, never the safety boundary.
    """
    nb = task.get("not_before")
    if not nb:
        return True
    now = now or datetime.now()
    try:
        return datetime.fromisoformat(nb) <= now
    except (ValueError, TypeError):
        return True


def decide(now=None) -> dict:
    """Should this render_slot run now? Pure read of the blackout gate."""
    g = blackout_check(now)
    warnings = g.get("warnings") or []
    if not g.get("publish_allowed", True):
        hb = g.get("hard_block") or {}
        return {
            "action": "requeue",
            "reason": hb.get("reason") or "blackout active",
            "blackout": True,
            "warnings": warnings,
        }
    return {"action": "render", "reason": None, "blackout": False, "warnings": warnings}


if __name__ == "__main__":
    import json
    print(json.dumps(decide(), ensure_ascii=False, indent=2))
