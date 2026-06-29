#!/usr/bin/env python3
"""
orchestra_self_terminate.py — PROACTIVE half of the orchestra leak fix (B286).

ROOT (verified 2026-06-23, re-measured 2026-06-27): each scheduled orchestra fire
makes Claude.app spawn a claude-code session that finishes its turn but NEVER
exits. They accumulate (~2 procs/fire, ~30 min apart) until load > 75 on 10 cores
and the box swaps — hiding every other failure. See memory:
feedback_orchestra_session_leak.

reap_leaked_shifts.py is the REACTIVE half: a Mohamed-tapped reaper that kills
OLD leaked siblings after the fact. This script is the PROACTIVE half. It has TWO
modes, composing into defense in depth:

  --arm  (run at shift START)  the HANG-PROOF layer (B286 root fix, 2026-06-29):
         double-fork+setsid a DETACHED watchdog that sleeps `timeout` then SIGTERMs
         (then SIGKILLs) this fire's OWN claude-code session. Because the watchdog
         is detached it fires EVEN IF the shift hangs, crashes, or the model never
         reaches the end of its turn — the exact failure the synchronous --go path
         below cannot catch. A clean shift exits in well under `timeout`, so the
         watchdog's target is already gone and the kill is a harmless no-op.

  --go   (run at shift END)    the GRACEFUL layer: immediately SIGTERM this fire's
         own session so a well-behaved shift exits the instant its work is done,
         without waiting for the watchdog's wall-clock.

WHY timeout default = 1500s (25 min), NOT 4h: the fire cadence is 30 MINUTES
(rabie-orchestra SKILL: "every 30min"). The watchdog must fire BELOW one cadence so
a leaked fire is gone before the next fire starts on top of it — 1500s leaves a
5-min margin under 1800s. (A panel suggested ~4h, conflating the REACTIVE reaper's
4h leak-AGE floor with the shift duration; the cadence fact settles it — a fire
still alive at 25 min IS the leak.) The reactive reaper's 4h floor remains the
backstop for anything that slips past.

SAFETY (Rule #8 — REFUSE, don't warn; non-zero exit rather than proceed):
  * Target is chosen by select_self_session() — ONLY ever a node in the CALLER'S
    OWN ANCESTRY CHAIN. It is structurally impossible to kill a sibling fire or a
    daemon (locked by test_never_selects_sibling_leak).
  * NEVER targets the Claude.app desktop root or its Helper/disclaimer shims.
  * --arm REFUSES to arm against a session that has a real controlling TTY (a human
    running the shift by hand is never put on a 25-min kill timer).
  * Dry-run by default for both modes; prints the exact PID it would act on.
  * REFUSES (exit non-zero) if it cannot uniquely identify its own session.

The PID-snapshot/ancestry primitives are reused from reap_leaked_shifts (DRY) —
that module is already covered by the leak-reaper test suite, and select_self_session
is covered by test_orchestra_self_terminate.
"""
import argparse
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reap_leaked_shifts import snapshot_procs, ancestry_chain, find_app_pid, _REAL_TTY

DEFAULT_TIMEOUT = 1500   # 25 min — under the 30-min fire cadence (see module docstring)
DEFAULT_GRACE = 20       # seconds between SIGTERM and SIGKILL in the watchdog


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


def _kill_quiet(pid, sig):
    """Signal pid; swallow already-dead / not-permitted. True iff delivered."""
    try:
        os.kill(pid, sig)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def spawn_watchdog(target_pid, timeout, grace):
    """double-fork + setsid a DETACHED watchdog process that:
        sleep(timeout); SIGTERM(target); sleep(grace); SIGKILL(target).
    Survives the parent claude session dying (reparents to init). Returns the
    intermediate child pid in the parent; never returns in the grandchild."""
    child = os.fork()
    if child > 0:
        os.waitpid(child, 0)          # reap the intermediate — no zombie
        return child
    # --- intermediate child ---
    os.setsid()                       # new session/group — outlives the fire
    grandchild = os.fork()
    if grandchild > 0:
        os._exit(0)                   # intermediate exits; grandchild -> init
    # --- grandchild: the actual watchdog ---
    try:
        devnull = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            try:
                os.dup2(devnull, fd)  # detach stdio; a dying parent can't block us
            except OSError:
                pass
        time.sleep(timeout)
        _kill_quiet(target_pid, signal.SIGTERM)
        time.sleep(grace)
        _kill_quiet(target_pid, signal.SIGKILL)
    finally:
        os._exit(0)


def _resolve_self_target(procs=None, my_pid=None):
    """Shared resolution for both modes. Returns (target_pid, app_pid, my_chain, procs).
    target_pid is None when no own claude session is identifiable (caller REFUSEs)."""
    procs = snapshot_procs() if procs is None else procs
    app_pid = find_app_pid(procs)
    if app_pid is None:
        return None, None, set(), procs
    my_pid = os.getpid() if my_pid is None else my_pid
    my_chain = ancestry_chain(my_pid, procs)
    target = select_self_session(procs, my_chain, app_pid)
    return target, app_pid, my_chain, procs


def arm(timeout=DEFAULT_TIMEOUT, grace=DEFAULT_GRACE, dry=False, procs=None, my_pid=None):
    """Arm the hang-proof self-terminate watchdog against this fire's own session.
    Returns a result dict (also used by tests). Does not raise on the no-session case."""
    target, app_pid, my_chain, procs = _resolve_self_target(procs=procs, my_pid=my_pid)
    if app_pid is None:
        return {"armed": False, "reason": "no Claude.app root located", "target": None}
    if target is None:
        return {"armed": False, "reason": "no own claude-code session in my chain", "target": None}
    if target not in my_chain:
        return {"armed": False, "reason": "resolved target not in my chain", "target": target}
    by_pid = {p["pid"]: p for p in procs}
    if _REAL_TTY(by_pid.get(target, {}).get("tty")):
        return {"armed": False, "reason": "session has a real TTY (interactive) — not arming",
                "target": target}
    if dry:
        return {"armed": False, "reason": "dry-run", "target": target, "timeout_s": timeout}
    watchdog_pid = spawn_watchdog(target, timeout, grace)
    return {"armed": True, "target": target, "watchdog_pid": watchdog_pid,
            "timeout_s": timeout, "grace_s": grace}


def _cmd_arm(args):
    res = arm(timeout=args.timeout, grace=args.grace, dry=not args.go)
    print(json.dumps(res))
    if res.get("armed"):
        print(f"ARMED: watchdog PID {res['watchdog_pid']} will SIGTERM my session "
              f"PID {res['target']} in {res['timeout_s']}s if this fire has not exited.")
        return 0
    if res.get("reason") == "dry-run":
        print(f"\nDRY-RUN. Would arm a {res['timeout_s']}s self-terminate watchdog "
              f"against my session PID {res['target']}. Re-run with --go to arm.")
        return 0
    print(f"NOT ARMED: {res.get('reason')}", file=sys.stderr)
    # a missing session at shift start is not a hard failure (e.g. interactive run)
    return 0


def _cmd_go(args):
    """GRACEFUL immediate self-SIGTERM (end-of-shift path)."""
    target, app_pid, my_chain, procs = _resolve_self_target()
    if app_pid is None:
        print("REFUSE: could not locate Claude.app root — aborting.", file=sys.stderr)
        return 2
    if target is None:
        print("REFUSE: could not uniquely identify my own claude session — aborting.",
              file=sys.stderr)
        return 3
    if target not in my_chain or target == app_pid:
        print("REFUSE: target failed an ancestry/app-root invariant — aborting.", file=sys.stderr)
        return 3
    print(f"app_root=PID {app_pid}  my_pid={os.getpid()}  my_chain={sorted(my_chain)}")
    print(f"self claude-code session to terminate: PID {target}")
    if not args.go:
        print("\nDRY-RUN. Re-run with --go to SIGTERM my own session at end of shift. "
              "Nothing killed.")
        return 0
    if _kill_quiet(target, signal.SIGTERM):
        print(f"\nSIGTERM sent to my own session PID {target}. Shift exits cleanly.")
        return 0
    print(f"\nsession PID {target} already gone or not permitted — nothing to do.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Orchestra fire self-terminate (B286)")
    ap.add_argument("--arm", action="store_true",
                    help="arm a hang-proof self-terminate watchdog (run at shift START)")
    ap.add_argument("--go", action="store_true",
                    help="with --arm: actually arm (vs dry-run). alone: graceful self-SIGTERM now (shift END)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"watchdog wall-clock seconds before self-terminate (default {DEFAULT_TIMEOUT})")
    ap.add_argument("--grace", type=int, default=DEFAULT_GRACE,
                    help=f"seconds between SIGTERM and SIGKILL (default {DEFAULT_GRACE})")
    args = ap.parse_args(argv)
    if args.arm:
        return _cmd_arm(args)
    return _cmd_go(args)


if __name__ == "__main__":
    sys.exit(main())
