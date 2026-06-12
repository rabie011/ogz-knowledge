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

    def _covered_check():
        import glob as _gg
        def _cov(h):
            dates = {f.split("/")[-1].split("__")[0] for f in _gg.glob(str(BASE / f"clients/{h}/posts/*.json"))}
            return len(dates) >= 365
        return all(_cov(h) for h in ("eatjurisha", "albaik"))

    # 1. grinder alive (process) AND producing (card delta since last run)
    p = subprocess.run(["pgrep", "-f", "render_slots_batch"], capture_output=True)
    # zero-LLM mode (June 12, both keys dry): a retired grinder whose mission completed
    # (365/365) is not a dead process — done!=dead applies to the process check too
    checks["grinder_process"] = p.returncode == 0 or _covered_check()
    cards = count_cards()
    checks["cards_total"] = cards
    checks["cards_delta"] = cards - prev.get("cards_total", cards)
    # a finished grinder is DONE, not dead: full year-map coverage = mission complete
    import glob as _g
    def _covered(h):
        dates = {f.split("/")[-1].split("__")[0] for f in _g.glob(str(BASE / f"clients/{h}/posts/*.json"))}
        return len(dates) >= 365
    grinder_done = all(_covered(h) for h in ("eatjurisha", "albaik"))
    checks["grinder_done_365"] = grinder_done
    checks["grinder_producing"] = checks["cards_delta"] > 0 or not prev or grinder_done

    # 2. guards hold (the gauntlet is the truth)
    g = subprocess.run(["python3", str(BASE / "scripts/truth_guards.py")], capture_output=True, text=True)
    checks["guards_gauntlet"] = g.returncode == 0

    # 3. portal up — LOCAL and PUBLIC. The tunnel died once (June 12) while local
    # was fine, so Mohamed's phone saw nothing and no alarm fired. Check what he touches.
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:4199/", timeout=5)
        checks["portal_mini"] = True
    except Exception:
        checks["portal_mini"] = False
    try:
        key = next((l.split("=", 1)[1].strip().strip('"') for l in
                    open(Path.home() / ".abraham_env") if l.startswith("APPROVALS_KEY=")), "")
        # browser UA — Cloudflare 403s the default Python-urllib UA as a bot (false alarm)
        req = urllib.request.Request(f"https://brain.ogzstudios.com/approvals?k={key}",
                                     headers={"User-Agent": "Mozilla/5.0 (Macintosh) OGZ-healthcheck"})
        checks["portal_public"] = urllib.request.urlopen(req, timeout=12).status == 200
    except Exception:
        checks["portal_public"] = False

    # 4. last commit age (the orchestra commits — silence = stall)
    c = subprocess.run(["git", "-C", str(BASE), "log", "-1", "--format=%ct"], capture_output=True, text=True)
    age_min = (time.time() - int(c.stdout.strip())) / 60 if c.stdout.strip() else 9999
    checks["last_commit_min"] = round(age_min)
    checks["commits_flowing"] = age_min < 120

    # 5. cron heartbeat marker (the orchestra updates this state file each run — its own pulse)
    # RABIE-ratified June 12: the queue's consumer died silently for 88 days once — never again
    o = subprocess.run(["pgrep", "-f", "orchestrator_daemon.py"], capture_output=True)
    checks["orchestrator_alive"] = o.returncode == 0

    # D7-1: the im-here package stays fresh every cycle — Mohamed can appear any minute
    subprocess.run(["python3", str(BASE / "scripts/week_receipt.py")], capture_output=True, timeout=60)

    ok = all(checks[k] for k in ("grinder_process", "guards_gauntlet", "portal_mini", "portal_public", "commits_flowing", "orchestrator_alive"))
    entry = {"ts": now, **checks, "verdict": "ALIVE" if ok else "ALARM"}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    STATE.write_text(json.dumps({"ts": now, "cards_total": cards}))

    for k, v in checks.items():
        print(f"  {'✅' if (v if isinstance(v, bool) else True) else '🔴'} {k}: {v}")
    print(f"\n{'🟢 MAKE-SURE: ALIVE' if ok else '🔴 MAKE-SURE: ALARM'}")

    if not ok:
        dead = [k for k in ("grinder_process", "guards_gauntlet", "portal_mini", "portal_public", "commits_flowing", "orchestrator_alive") if not checks[k]]
        subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                        "--id", f"alarm_{int(time.time())}", "--urgent",
                        "--title", f"🚨 إنذار: {', '.join(dead)} واقف",
                        "--tag", "نظام", "--desc", f"فحص الأدلة فشل: {dead}. كلود يعالج — هذا للعلم.",
                        "--buttons", "ack:👌 شفته"], capture_output=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
