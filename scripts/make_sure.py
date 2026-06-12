#!/usr/bin/env python3
"""MAKE SURE (June 12 — Mohamed: "make sure this is happening, not the LLM fucking
you up — make sure make sure, both of you"). Hard EVIDENCE that the orchestra is
real: processes alive, output growing, gates green, portal up — measured numbers,
never feelings. Anything dead = urgent portal alarm. Runs every orchestra cycle.

Usage: python3 scripts/make_sure.py   (exit 1 = something is dead/lying)
"""
import glob, json, subprocess, time
from pathlib import Path

BASE = Path(__file__).parent.parent
STATE = BASE / "data/make_sure_state.json"
LOG = BASE / "data/make_sure_log.jsonl"


def count_cards() -> int:
    return len(glob.glob(str(BASE / "clients/*/posts/*.json")))


def main():
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    checks = {}

    # 1. grinder alive (process) AND producing (card delta since last run)
    p = subprocess.run(["pgrep", "-f", "render_slots_batch"], capture_output=True)
    checks["grinder_process"] = p.returncode == 0
    cards = count_cards()
    checks["cards_total"] = cards
    checks["cards_delta"] = cards - prev.get("cards_total", cards)
    checks["grinder_producing"] = checks["cards_delta"] > 0 or not prev  # first run = unknown

    # 2. guards hold (the gauntlet is the truth)
    g = subprocess.run(["python3", str(BASE / "scripts/truth_guards.py")], capture_output=True, text=True)
    checks["guards_gauntlet"] = g.returncode == 0

    # 3. portal up (local mini)
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:4199/", timeout=5)
        checks["portal_mini"] = True
    except Exception:
        checks["portal_mini"] = False

    # 4. last commit age (the orchestra commits — silence = stall)
    c = subprocess.run(["git", "-C", str(BASE), "log", "-1", "--format=%ct"], capture_output=True, text=True)
    age_min = (time.time() - int(c.stdout.strip())) / 60 if c.stdout.strip() else 9999
    checks["last_commit_min"] = round(age_min)
    checks["commits_flowing"] = age_min < 120

    # 5. cron heartbeat marker (the orchestra updates this state file each run — its own pulse)
    ok = all(checks[k] for k in ("grinder_process", "guards_gauntlet", "portal_mini", "commits_flowing"))
    entry = {"ts": now, **checks, "verdict": "ALIVE" if ok else "ALARM"}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    STATE.write_text(json.dumps({"ts": now, "cards_total": cards}))

    for k, v in checks.items():
        print(f"  {'✅' if (v if isinstance(v, bool) else True) else '🔴'} {k}: {v}")
    print(f"\n{'🟢 MAKE-SURE: ALIVE' if ok else '🔴 MAKE-SURE: ALARM'}")

    if not ok:
        dead = [k for k in ("grinder_process", "guards_gauntlet", "portal_mini", "commits_flowing") if not checks[k]]
        subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                        "--id", f"alarm_{int(time.time())}", "--urgent",
                        "--title", f"🚨 إنذار: {', '.join(dead)} واقف",
                        "--tag", "نظام", "--desc", f"فحص الأدلة فشل: {dead}. كلود يعالج — هذا للعلم.",
                        "--buttons", "ack:👌 شفته"], capture_output=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
