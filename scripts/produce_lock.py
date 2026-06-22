#!/usr/bin/env python3
"""B285 (June 22, 2026) — the produce-batch in-flight lock.

THE SCAR: the ogz_enricher daemon's commit_and_sync() runs `git add -A`. produce_batch.py
renders candidate posts directly into the tracked clients/<h>/posts/ tree over several minutes.
On 2026-06-22 an enricher cycle fired MID-BATCH and banked 12 partial orch_shadow candidates
into the pilot pool (reverted by hand, commit abafc540). An aborted/in-flight batch must NEVER
enter candidates — Rule #6 (a writer needs a reader, built same cycle), Rule #12 (the SYSTEM
produces clean, never a half batch).

THE GUARD: produce_batch holds this lock for the whole run (try/finally — released even on a
crash path that Python can unwind). The enricher commit READS the lock and REFUSES to commit
while a batch is in flight (Rule #8 — refuse, don't warn), deferring to its next cycle. A STALE
lock — dead PID, or older than the TTL — is swept and ignored, so a SIGKILLed producer can never
wedge the enricher forever.

This is the ONE source both sides share (Rule #6): producer = writer, enricher = consumer.
"""
import json
import os
import time
from pathlib import Path

LOCK = Path(__file__).parent.parent / "data" / ".produce_batch.lock"

# TTL ceiling: a batch is N slots, each bounded by SLOT_TIMEOUT (default 300s). 20 slots ×300s ≈
# 100 min worst case; 2h is a safe outer bound after which a still-present lock is assumed orphaned
# (the producer died without unwinding). Override via PRODUCE_LOCK_TTL for tests.
STALE_TTL_S = int(os.environ.get("PRODUCE_LOCK_TTL", str(2 * 60 * 60)))


def _alive(pid) -> bool:
    """Is this PID a live process? Signal-0 probe. Unknowable → assume alive (conservative:
    keep honoring the lock rather than risk banking a partial batch)."""
    if not isinstance(pid, int):
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but not ours
    except OSError:
        return False


def acquire() -> None:
    """Stamp the lock with our PID + start time. Idempotent (overwrites a prior stamp)."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({"pid": os.getpid(), "started": time.time()}))


def release() -> None:
    """Remove the lock. Safe if already absent."""
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def is_active(now: float | None = None) -> bool:
    """True iff a FRESH produce batch is in flight. A stale lock (unreadable, dead PID, or past
    TTL) is NOT active — and is swept here so it can never wedge the enricher forever."""
    if not LOCK.exists():
        return False
    now = time.time() if now is None else now
    try:
        d = json.loads(LOCK.read_text())
    except Exception:
        release()  # unreadable → orphan, sweep it
        return False
    if (now - d.get("started", 0)) > STALE_TTL_S:
        release()  # past the outer bound → orphan
        return False
    if not _alive(d.get("pid")):
        release()  # producer is gone → orphan
        return False
    return True
