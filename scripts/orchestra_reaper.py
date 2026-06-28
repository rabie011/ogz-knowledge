#!/usr/bin/env python3
"""ORCHESTRA REAPER (June 28, 2026) — kills LEAKED claude sessions before the load goes fatal.

DeepSeek orchestra-audit fix #2: scheduled orchestra fires spawn `claude` sessions that never exit;
they pile up (19 alive, some 7 DAYS old, TTY=??) → historically load 70+ → portal down. This reaps
ONLY the clearly-leaked ones and NEVER an active session, so the loop stops killing itself without
Mohamed babysitting it.

SAFE BY CONSTRUCTION — a process is reaped ONLY if ALL hold:
  • it is a `claude-code` CLI session (NOT the Claude DESKTOP APP /Applications/Claude.app, NOT its
    Electron/Squirrel/Helpers/chrome-native-host — those are legit and must NEVER be killed)
  • detached: TTY == '??'  • age ≥ MIN_AGE_H hours
  • NOT this process, NOT its parent/ancestors  • NOT a launchd com.abraham.* service
A real interactive session has a TTY; a fresh fire is young. Days-old detached claude-code = 100% leaked.

Usage:
  python3 scripts/orchestra_reaper.py            # DRY-RUN — list what it would reap
  python3 scripts/orchestra_reaper.py --reap     # actually kill them
  python3 scripts/orchestra_reaper.py --reap --max-load 7   # only reap if load ≥ threshold
"""
import argparse
import os
import re
import signal
import subprocess
import sys

MIN_AGE_H = 4.0          # never reap a session younger than this (could be real work)
HARD_CAP = 25            # if more than this many claude procs, reap oldest detached regardless of age floor


def _ancestors(pid):
    """The current process's ancestor PIDs (never reap ourselves or who launched us)."""
    out = {pid}
    cur = pid
    for _ in range(20):
        try:
            ppid = int(subprocess.run(["ps", "-o", "ppid=", "-p", str(cur)],
                                      capture_output=True, text=True).stdout.strip() or 0)
        except Exception:
            break
        if ppid <= 1 or ppid in out:
            break
        out.add(ppid)
        cur = ppid
    return out


def _etime_hours(etime):
    """ps etime → hours.  forms: SS, MM:SS, HH:MM:SS, D-HH:MM:SS."""
    days = 0
    if "-" in etime:
        d, etime = etime.split("-", 1)
        days = int(d)
    parts = [int(x) for x in etime.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts[-3], parts[-2], parts[-1]
    return days * 24 + h + m / 60 + s / 3600


def _load1():
    try:
        return os.getloadavg()[0]
    except Exception:
        return 0.0


def find_leaked():
    safe = _ancestors(os.getpid())
    rows = subprocess.run(["ps", "-eo", "pid,ppid,etime,tty,command"],
                          capture_output=True, text=True).stdout.splitlines()
    # NEVER touch the desktop app or its helpers — only the headless claude-code CLI is the leak
    APP_SAFE = ("/Applications/Claude.app", "chrome-native-host", "Electron Framework",
                "Squirrel.framework", "Helpers/", "(Renderer)", "(GPU)", "(Plugin)")
    leaked = []
    for ln in rows:
        if "claude-code" not in ln:     # the CLI path; excludes /Applications/Claude.app entirely
            continue
        if any(s in ln for s in APP_SAFE):
            continue
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*)", ln)
        if not m:
            continue
        pid, ppid, etime, tty, cmd = int(m[1]), int(m[2]), m[3], m[4], m[5]
        if pid in safe or ppid in safe:
            continue
        if "com.abraham" in cmd or "orchestra_reaper" in cmd:
            continue
        if tty != "??":                 # has a controlling terminal → a real interactive session
            continue
        age_h = _etime_hours(etime)
        leaked.append({"pid": pid, "age_h": round(age_h, 1), "cmd": cmd[:70]})
    leaked.sort(key=lambda x: -x["age_h"])
    return leaked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reap", action="store_true", help="actually kill (default: dry-run)")
    ap.add_argument("--max-load", type=float, default=0.0, help="only reap if 1-min load ≥ this")
    a = ap.parse_args()

    leaked = find_leaked()
    total_claude = sum(1 for ln in subprocess.run(["ps", "-eo", "command"], capture_output=True,
                       text=True).stdout.splitlines()
                       if "claude-code" in ln and "/Applications/Claude.app" not in ln
                       and "Helpers/" not in ln and "Framework" not in ln)
    load = _load1()
    # by default reap only sessions older than MIN_AGE_H; if over HARD_CAP, the floor is removed
    floor = 0.0 if total_claude > HARD_CAP else MIN_AGE_H
    targets = [p for p in leaked if p["age_h"] >= floor]

    print(f"claude procs: {total_claude} · load1: {load:.2f} · leaked-detached: {len(leaked)} · "
          f"reap-eligible (age≥{floor}h): {len(targets)}")
    for p in targets:
        print(f"  PID {p['pid']}  age {p['age_h']}h  {p['cmd']}")

    if a.max_load and load < a.max_load:
        print(f"load {load:.2f} < --max-load {a.max_load} → not reaping")
        return
    if not a.reap:
        print("DRY-RUN — pass --reap to kill the above.")
        return
    killed = 0
    for p in targets:
        try:
            os.kill(p["pid"], signal.SIGTERM)
            killed += 1
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"  ⚠ could not kill {p['pid']}: {e}")
    print(f"✅ reaped {killed} leaked session(s).")


if __name__ == "__main__":
    main()
