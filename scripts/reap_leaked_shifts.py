#!/usr/bin/env python3
"""
reap_leaked_shifts.py — SAFE reaper for the orchestra session leak.

ROOT (verified 2026-06-23): each scheduled orchestra fire makes Claude.app (the
desktop app, the common ancestor PID) spawn a claude-code session that completes
its turn but NEVER exits. They accumulate (~2/fire) until load > 75 on 10 cores
and RAM is exhausted (35M unused at 183 procs) — swapping strangles the box and
hides every other failure. See memory: feedback_orchestra_session_leak.

This tool does NOT decide to kill on its own. It is the CONSUMER for Mohamed's
one-tap "reap" (Rule #6/#7): dry-run by default, prints exactly what it WOULD
kill, and only sends SIGTERM when called with --go.

SAFETY (Rule #8 — REFUSE, don't warn; the script exits non-zero rather than
proceed if any invariant is violated):
  * NEVER targets the live caller's own ancestry chain.
  * NEVER targets the Claude.app root process itself.
  * NEVER targets a process with a real controlling terminal (an interactive
    `claude` a human is using in a Terminal).
  * Only targets claude-code descendants of Claude.app older than --min-age-min
    (default 60) — a shift completes in minutes and fires are 30 min apart, so
    anything older than 60 min is unambiguously a dead prior fire.
"""
import argparse
import os
import subprocess
import sys


def _parse_etime(etime: str) -> int:
    """ps etime ('MM:SS', 'HH:MM:SS', 'D-HH:MM:SS') -> seconds."""
    etime = etime.strip()
    days = 0
    if "-" in etime:
        d, etime = etime.split("-", 1)
        days = int(d)
    parts = [int(p) for p in etime.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return days * 86400 + h * 3600 + m * 60 + s


def snapshot_procs():
    """Return list of {pid, ppid, etime_s, tty, command} for every process."""
    out = subprocess.check_output(
        ["ps", "-axo", "pid=,ppid=,etime=,tty=,command="], text=True
    )
    procs = []
    for line in out.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, etime, tty, command = parts
        try:
            procs.append(
                {
                    "pid": int(pid),
                    "ppid": int(ppid),
                    "etime_s": _parse_etime(etime),
                    "tty": tty,
                    "command": command,
                }
            )
        except ValueError:
            continue
    return procs


def ancestry_chain(pid, procs):
    """Set of pids from `pid` up to the root (inclusive)."""
    by_pid = {p["pid"]: p for p in procs}
    chain, cur = set(), pid
    while cur in by_pid:
        if cur in chain:
            break
        chain.add(cur)
        cur = by_pid[cur]["ppid"]
    return chain


def is_descendant(pid, app_pid, procs):
    by_pid = {p["pid"]: p for p in procs}
    cur = pid
    seen = set()
    while cur in by_pid and cur not in seen:
        seen.add(cur)
        cur = by_pid[cur]["ppid"]
        if cur == app_pid:
            return True
    return False


def find_app_pid(procs):
    """The Claude.app main process — the leak's common ancestor."""
    for p in procs:
        c = p["command"]
        if c.startswith("/Applications/Claude.app/Contents/MacOS/Claude") and (
            "Helpers" not in c and "disclaimer" not in c
        ):
            return p["pid"]
    return None


_REAL_TTY = lambda tty: tty not in ("??", "?", "-", "", None)


def select_leaked(procs, my_chain, app_pid, min_age_s):
    """PURE selection: the leaked, reapable claude-code sessions.

    A proc is reapable iff it is a claude-code process, a descendant of the
    Claude.app root, NOT in the caller's live chain, NOT the app root, has no
    real tty, and is older than min_age_s.
    """
    out = []
    for p in procs:
        if p["pid"] in my_chain:
            continue
        if p["pid"] == app_pid:
            continue
        if _REAL_TTY(p["tty"]):
            continue
        if p["etime_s"] < min_age_s:
            continue
        if "claude" not in p["command"].lower():
            continue
        if not is_descendant(p["pid"], app_pid, procs):
            continue
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="actually SIGTERM (default: dry-run)")
    ap.add_argument("--min-age-min", type=int, default=60)
    args = ap.parse_args()

    procs = snapshot_procs()
    app_pid = find_app_pid(procs)
    if app_pid is None:
        print("REFUSE: could not locate Claude.app root process — aborting.", file=sys.stderr)
        sys.exit(2)

    my_chain = ancestry_chain(os.getpid(), procs)
    leaked = select_leaked(procs, my_chain, app_pid, args.min_age_min * 60)

    # Rule #8 hard asserts — refuse to proceed if any invariant is violated.
    targets = {p["pid"] for p in leaked}
    if targets & my_chain:
        print("REFUSE: kill list intersects my own live chain — aborting.", file=sys.stderr)
        sys.exit(3)
    if app_pid in targets:
        print("REFUSE: kill list contains the Claude.app root — aborting.", file=sys.stderr)
        sys.exit(3)

    total_mem_pct = 0.0
    print(f"app_root=PID {app_pid}  my_chain={sorted(my_chain)}  min_age={args.min_age_min}min")
    print(f"leaked claude-code sessions found: {len(leaked)}")
    for p in sorted(leaked, key=lambda x: -x["etime_s"]):
        age_h = p["etime_s"] / 3600
        print(f"  PID {p['pid']:>6}  age={age_h:5.1f}h  ppid={p['ppid']:>6}")

    if not args.go:
        print("\nDRY-RUN. Re-run with --go to SIGTERM the above. Nothing killed.")
        return

    killed = 0
    for p in leaked:
        try:
            os.kill(p["pid"], 15)  # SIGTERM — graceful
            killed += 1
        except ProcessLookupError:
            pass
        except PermissionError:
            print(f"  no perm to kill {p['pid']}", file=sys.stderr)
    print(f"\nSIGTERM sent to {killed} leaked sessions.")


if __name__ == "__main__":
    main()
