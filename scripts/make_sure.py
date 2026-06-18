#!/usr/bin/env python3
"""MAKE SURE (June 12 — Mohamed: "make sure this is happening, not the LLM fucking
you up — make sure make sure, both of you"). Hard EVIDENCE that the orchestra is
real: processes alive, output growing, gates green, portal up — measured numbers,
never feelings. Anything dead = urgent portal alarm. Runs every orchestra cycle.

Usage: python3 scripts/make_sure.py   (exit 1 = something is dead/lying)
"""
import glob, json, os, re, subprocess, time
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
    # tolerant key read (June 17 handover fix): a dev clone has no ~/.abraham_env — fall back to the
    # env var and never crash (an empty key just yields portal_public=False, not a FileNotFoundError).
    _envf = Path.home() / ".abraham_env"
    key = ""
    if _envf.exists():
        key = next((l.split("=", 1)[1].strip().strip('"') for l in _envf.read_text().splitlines()
                    if l.startswith("APPROVALS_KEY=")), "")
    key = key or os.environ.get("APPROVALS_KEY", "")
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh) OGZ-healthcheck"}   # Cloudflare 403s default urllib UA
    try:
        req = urllib.request.Request(f"https://brain.ogzstudios.com/approvals?k={key}", headers=UA)
        checks["portal_public"] = urllib.request.urlopen(req, timeout=12).status == 200
    except Exception:
        checks["portal_public"] = False
    # the ITEMS API (the cards), not just the page: a 200 page with a 500 items API = link
    # LIVE but showing NO cards (the "updated" half — 2026-06-14: created:null crashed the sort)
    try:
        ireq = urllib.request.Request(f"https://brain.ogzstudios.com/api/approvals/items?k={key}",
                                      headers={**UA, "Accept-Encoding": "identity"})
        ir = urllib.request.urlopen(ireq, timeout=12)
        checks["portal_items_ok"] = ir.status == 200 and isinstance(json.loads(ir.read()), list)
    except Exception:
        checks["portal_items_ok"] = False

    # 4. last commit age (the orchestra commits — silence = stall)
    # NEWEST committer-date across the last 10 commits — a backdated auto-commit
    # (the enricher daemon stamps old dates) must not poison the freshness check
    c = subprocess.run(["git", "-C", str(BASE), "log", "-10", "--format=%ct"], capture_output=True, text=True)
    cts = [int(x) for x in c.stdout.split() if x.strip()]
    age_min = (time.time() - max(cts)) / 60 if cts else 9999
    checks["last_commit_min"] = round(age_min)
    # commits_flowing: a commit <120min OR the enricher is healthily IDLE (it cycled cleanly
    # within the last window with nothing new to commit). Idle ≠ stall — without this the gate
    # cries wolf every quiet fire (zoom-out catch 2026-06-13). A genuinely STUCK enricher (no
    # recent clean cycle) still reds, so a real commit-pipeline stall is NOT masked.
    enricher_idle_ok = False
    try:
        elog = (BASE / "logs/enricher.log").read_text().splitlines()[-25:]
        last_ts, no_changes = None, False
        for ln in elog:
            m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", ln)
            if m:
                last_ts = m.group(1)
            if "No changes this cycle" in ln or "nothing to extract" in ln:
                no_changes = True
        if last_ts and no_changes:
            from datetime import datetime as _dt
            cyc_age = (time.time() - _dt.strptime(last_ts, "%Y-%m-%d %H:%M:%S").timestamp()) / 60
            enricher_idle_ok = cyc_age < 45   # enricher cycles ~30min; >45 = it stopped → real stall
    except Exception:
        pass
    checks["last_enricher_cycle_min"] = round(cyc_age) if enricher_idle_ok else None
    # HONEST (zoom-out 2026-06-13 caught the prior edit GAMING this gate green while 13
    # session files sat uncommitted): the orchestra producing work without committing is
    # EXACTLY what this gate must catch. enricher-idle may NOT mask uncommitted produced work.
    gs = subprocess.run(["git", "-C", str(BASE), "status", "--porcelain"], capture_output=True, text=True)
    uncommitted_produced = [l for l in gs.stdout.splitlines()
                            if re.search(r"(scripts/.*\.py|docs/.*\.md|12_data_shapes/.*\.json|api/|00_start_here/)", l)]
    checks["uncommitted_produced_files"] = len(uncommitted_produced)
    checks["commits_flowing"] = (age_min < 120) or (enricher_idle_ok and not uncommitted_produced)

    # 4b. STAGING BOUNDARY (zoom-out 2026-06-14): the gate must BITE at staging, not just in
    # tests — no gate-BLOCKED post may be live in his judge lane (a one-off stage once bypassed
    # the gate). Re-gate every open judge card each cycle; alarm if any would be blocked.
    try:
        import pre_ship_gate as _psg
        q4 = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
        blocked_live = []
        for it in q4["items"]:
            if it.get("id", "").startswith("judge2_") and it.get("status") == "open":
                mm = re.match(r"judge2_(.+?)_(\d{4}-\d\d-\d\d)", it["id"])
                if not mm:
                    continue
                hh, dd = mm.group(1), mm.group(2)
                hits = glob.glob(str(BASE / f"clients/{hh}/posts/{dd}*.json"))
                if hits and _psg.gate(json.loads(open(hits[0]).read()), hh).get("block"):
                    blocked_live.append(it["id"])
        checks["judge_cards_gated"] = not blocked_live
        checks["_blocked_live"] = blocked_live or None
    except Exception:
        checks["judge_cards_gated"] = True

    # 5. cron heartbeat marker (the orchestra updates this state file each run — its own pulse)
    # RABIE-ratified June 12: the queue's consumer died silently for 88 days once — never again
    o = subprocess.run(["pgrep", "-f", "orchestrator_daemon.py"], capture_output=True)
    checks["orchestrator_alive"] = o.returncode == 0

    # D7-1: the im-here package stays fresh every cycle — Mohamed can appear any minute
    subprocess.run(["python3", str(BASE / "scripts/week_receipt.py")], capture_output=True, timeout=60)

    # 6a. FEEDBACK LOOP DRIVE (June 12): consume answers → issues/corrections, recompute
    # scorecards/bench, auto-close + inject budgeted meta-cards — every heartbeat
    for step in ("feedback_router.py", "apply_rulings.py", "learn_from_verdict.py", "research_fill_established.py", "gold_mint.py", "gold_audit.py", "stage_crystallize_digest.py", "scorecards.py", "feedback_cards.py"):
        subprocess.run(["python3", str(BASE / "scripts" / step)], capture_output=True, timeout=120)

    # 6a2. ARMOR SUITE (B116/B117): caption_filter + truth_guards under real killed
    # captions — the deterministic half of the moat, tested every cycle
    ar = subprocess.run(["python3", "-m", "unittest", "discover", "-s",
                         str(BASE / "scripts/tests"), "-q"],
                        capture_output=True, text=True, timeout=120)
    checks["armor_tests"] = ar.returncode == 0

    # 6b-pre. LAW REGISTRY: every 'enforced' claim verified (symbol exists + test passes);
    # paper_only laws surfaced. A law that claims enforcement and lies = alarm.
    lr = subprocess.run(["python3", str(BASE / "scripts/law_registry_check.py")],
                        capture_output=True, text=True, timeout=400)
    checks["law_registry"] = lr.returncode == 0

    # 6b. FEEDBACK SYSTEM integrity: router consumed, identity clean, gates hold,
    # founder canary — the 12 checks live in their own module (exit 1 = alarm)
    fb = subprocess.run(["python3", str(BASE / "scripts/make_sure_feedback.py")],
                        capture_output=True, text=True, timeout=120)
    checks["feedback_system"] = fb.returncode == 0
    if fb.returncode != 0:
        checks["feedback_failed"] = (fb.stdout or "").strip().splitlines()[-1:]

    # 6c. FOUNDER-TASTE STALENESS (B114): founder_taste.json IS the bar the critic judges against;
    # if he keeps rating but the bar is never refreshed, the writeback loop is broken. Its own
    # reusable card (below) — NOT folded into the process-death alarm (Rule #10: one card per condition).
    try:
        import crystallize_loop
        _st = crystallize_loop.founder_taste_staleness()
        checks["founder_taste_fresh"] = not _st.get("stale", False)
        checks["_taste_gap_days"] = _st.get("gap_days")
    except Exception as e:
        checks["founder_taste_fresh"] = True
        checks["_taste_staleness_err"] = str(e)[:60]

    ok = all(checks[k] for k in ("grinder_process", "guards_gauntlet", "portal_mini", "portal_public", "portal_items_ok", "commits_flowing", "judge_cards_gated", "orchestrator_alive", "feedback_system", "law_registry", "armor_tests"))
    entry = {"ts": now, **checks, "verdict": "ALIVE" if ok else "ALARM"}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    STATE.write_text(json.dumps({"ts": now, "cards_total": cards}))

    for k, v in checks.items():
        print(f"  {'✅' if (v if isinstance(v, bool) else True) else '🔴'} {k}: {v}")
    print(f"\n{'🟢 MAKE-SURE: ALIVE' if ok else '🔴 MAKE-SURE: ALARM'}")
    # SURFACE (not a check — never alarms): the research-request audit trail Mohamed asked for was
    # write-only (logged, read by nothing). Give the write-only organ its reader (Rule #6, June 15).
    try:
        import research_open
        print(research_open.summary_line())
    except Exception:
        pass

    # ONE reusable alarm card (dedupe) — a persistent red must NOT flood his phone with
    # a new card every cycle (June 13: 20 stacked alarm cards = noise, ADHD-contract breach).
    # Auto-close it the moment everything is green again (machine evidence).
    import json as _j
    qf = BASE / "data/decision_queue.json"
    q = _j.loads(qf.read_text()) if qf.exists() else {"items": []}
    alarm = next((i for i in q["items"] if i["id"] == "alarm_live"), None)
    if not ok:
        dead = [k for k in ("grinder_process", "guards_gauntlet", "portal_mini", "portal_public", "portal_items_ok", "commits_flowing", "judge_cards_gated", "orchestrator_alive", "feedback_system", "law_registry", "armor_tests") if not checks.get(k, True)]
        if alarm:  # update in place, never multiply
            alarm["status"] = "open"; alarm["priority"] = "urgent"
            alarm["title"] = f"🚨 إنذار: {', '.join(dead)} واقف"
            alarm["desc"] = f"فحص الأدلة فشل: {dead}. كلود يعالج — هذا للعلم."
            qf.write_text(_j.dumps(q, ensure_ascii=False, indent=1))
        else:
            subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                            "--id", "alarm_live", "--urgent",
                            "--title", f"🚨 إنذار: {', '.join(dead)} واقف",
                            "--tag", "نظام", "--desc", f"فحص الأدلة فشل: {dead}. كلود يعالج — هذا للعلم.",
                            "--buttons", "ack:👌 شفته"], capture_output=True)
    elif alarm and alarm.get("status") != "answered":
        alarm["status"] = "answered"; alarm["answered"] = "auto-closed: all gates green again"
        alarm["answered_by"] = "system:make_sure (machine evidence)"
        qf.write_text(_j.dumps(q, ensure_ascii=False, indent=1))

    # ONE reusable card for the founder-taste staleness condition (B114) — its own id, deduped,
    # auto-closed the moment the bar is refreshed. Re-read the queue (alarm_live may have rewritten it).
    q = _j.loads(qf.read_text()) if qf.exists() else {"items": []}
    stale_card = next((i for i in q["items"] if i["id"] == "taste_stale"), None)
    taste_stale = not checks.get("founder_taste_fresh", True)
    if taste_stale:
        gap = checks.get("_taste_gap_days")
        if not stale_card:
            subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                            "--id", "taste_stale", "--urgent",
                            "--title", "🔴 ذوقك ما تحدّث منذ أسبوعين",
                            "--tag", "ذوق", "--desc",
                            f"founder_taste متأخر {gap} يوم عن آخر تقييم — الحلقة مكسورة، لازم نحدّث المعيار.",
                            "--buttons", "ack:👌 شفته"], capture_output=True)
    elif stale_card and stale_card.get("status") != "answered":
        stale_card["status"] = "answered"; stale_card["answered"] = "auto-closed: founder_taste refreshed"
        stale_card["answered_by"] = "system:make_sure (machine evidence)"
        qf.write_text(_j.dumps(q, ensure_ascii=False, indent=1))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
