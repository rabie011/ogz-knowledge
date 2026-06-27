#!/usr/bin/env python3
"""
orchestra_self_terminate.py — PROACTIVE half of the orchestra leak fix (B286).

ROOT (verified 2026-06-23, re-measured 2026-06-27): each scheduled orchestra fire
makes Claude.app spawn a claude-code session that finishes its turn but NEVER
exits. They accumulate (~2 procs/fire, ~30 min apart) until load > 75 on 10 cores
and the box swaps — hiding every other failure. See memory:
feedback_orchestra_session_leak.

reap_leaked_shifts.py is the REACTIVE half: a Mohamed-tapped reaper that kills
OLD leaked siblings after the fact. This script is the PROACTIVE half: at the end
of its own shift a fire calls this to SIGTERM ITS OWN claude-code session, so the
leak never forms. The two compose — proactive self-exit stops accumulation,
reactive reap cleans whatever slips through.

SAFETY (Rule #8 — REFUSE, don't warn; non-zero exit rather than proceed):
  * Only ever targets a node IN THE CALLER'S OWN ANCESTRY CHAIN — it is
    structurally impossible for this tool to kill a sibling fire or a daemon.
  * NEVER targets the Claude.app desktop root or its Helper/disclaimer shims.
  * Dry-run by default; prints the exact PID it would SIGTERM. --go to act.
  * REFUSES (exit non-zero) if it cannot uniquely identify its own session.

The PID-snapshot/ancestry primitives are reused from reap_leaked_shifts (DRY) —
that module is already covered by the leak-reaper test suite.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reap_leaked_shifts import snapshot_procs, ancestry_chain, find_app_pid


def is_claude_session(command: str) -> bool:
    """True for a claude-code SESSION process (the leaking node), False for the
    Claude.app desktop binary and its Helper/disclaimer shims."""
    c = command.lower()
    if "claude" not in c:
        return False
    if "/applications/claude.app/" in c:  # desktop app + Helper/disclaimer shims
        return False
    return True


def select_self_session(procs, my_chain, app_pid):
    """PURE selection: the caller's OWN claude-code session PID to terminate.

    Among the caller's ancestry chain, pick the claude-code session closest to
    the Claude.app root (largest etime = highest ancestor). Returns the PID, or
    None if none qualifies (caller then REFUSES rather than guessing).
    """
    by_pid = {p["pid"]: p for p in procs}
    candidates = [
        by_pid[pid]
        for pid in my_chain
        if pid in by_pid
        and pid != app_pid
        and is_claude_session(by_pid[pid]["command"])
    ]
    if not candidates:
        return None
    # closest to the app root == oldest of my own claude nodes
    candidates.sort(key=lambda p: -p["etime_s"])
    return candidates[0]["pid"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true",
                    help="actually SIGTERM my own session (default: dry-run)")
    args = ap.parse_args()

    procs = snapshot_procs()
    app_pid = find_app_pid(procs)
    if app_pid is None:
        print("REFUSE: could not locate Claude.app root — aborting.", file=sys.stderr)
        sys.exit(2)

    my_chain = ancestry_chain(os.getpid(), procs)
    target = select_self_session(procs, my_chain, app_pid)

    # Rule #8 hard asserts — refuse to proceed if any invariant is violated.
    if target is None:
        print("REFUSE: could not uniquely identify my own claude session — aborting.",
              file=sys.stderr)
        sys.exit(3)
    if target not in my_chain:
        print("REFUSE: target is not in my own ancestry chain — aborting.",
              file=sys.stderr)
        sys.exit(3)
    if target == app_pid:
        print("REFUSE: target is the Claude.app root — aborting.", file=sys.stderr)
        sys.exit(3)

    print(f"app_root=PID {app_pid}  my_pid={os.getpid()}  "
          f"my_chain={sorted(my_chain)}")
    print(f"self claude-code session to terminate: PID {target}")

    if not args.go:
        print("\nDRY-RUN. Re-run with --go to SIGTERM my own session at end of shift. "
              "Nothing killed.")
        return

    try:
        os.kill(target, 15)  # SIGTERM — graceful end-of-shift exit
        print(f"\nSIGTERM sent to my own session PID {target}. Shift exits cleanly.")
    except ProcessLookupError:
        print(f"\nsession PID {target} already gone — nothing to do.")
    except PermissionError:
        print(f"REFUSE: no permission to terminate {target}.", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
