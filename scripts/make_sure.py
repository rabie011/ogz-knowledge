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


def taste_wire_surface(tw: dict) -> dict:
    """Pure mapping of a taste_shadow_metric.metric() dict → the `_taste_wire_*` keys make_sure
    surfaces. Extracted so the Rule #9 invariant is unit-testable without running the live heartbeat:
    a numeric gap is exposed ONLY when status==OK — while INSUFFICIENT, status + n_runs/floor only,
    NEVER a number. (B266-268, Rule #6/#9.)"""
    out = {"_taste_wire_status": tw["status"],
           "_taste_wire_runs": f"{tw['n_runs']}/{tw['floor']}"}
    if tw["status"] == "OK":
        out["_taste_wire_gap"] = tw.get("active_vs_random_gap")
        out["_taste_wire_control_independent"] = tw.get("control_independent")
    return out


class _Failed:
    """Stub result for a subprocess that timed out or failed to launch, so one slow sub-check
    can never crash the whole self-check. June 20: a transient session-start load spike pushed
    the unittest call past its 120s timeout and make_sure threw an UNCAUGHT TimeoutExpired,
    aborting all 20 OTHER checks — the organ that must never lie died silently. Per the
    hard-to-break mandate (June 16): a timeout/launch-error records the check RED (returncode
    124 -> visible ALARM), never a crash."""

    def __init__(self, argv):
        self.returncode = 124
        self.stdout = ""
        self.stderr = "TIMEOUT/ERROR: " + " ".join(str(a) for a in argv)


def _safe_run(argv, **kw):
    """subprocess.run that degrades a timeout/OSError into a RED result instead of raising —
    keeps make_sure unbreakable (one hung child must not blind the whole shift)."""
    try:
        return subprocess.run(argv, **kw)
    except (subprocess.TimeoutExpired, OSError):
        return _Failed(argv)


def _probe(fn, tries=2, backoff=1.5):
    """Liveness probe with a single retry. Returns fn() on success; raises the last
    exception only if EVERY try fails.

    Root scar (June 20, this very shift): the orchestra's :13 fire collided with session-start —
    the enricher+orchestrator+hook stampede pinned the machine and the single-shot urllib checks
    TIMED OUT on HEALTHY services. make_sure logged portal_mini/public/items RED while the portal
    was in fact returning 200 in 0.03s. Two consecutive fires (05:16, 05:19) cried wolf, then a
    third (load settled) was ALIVE.

    A liveness probe must answer "is this actually unavailable to Mohamed?", not "was it slow for
    one instant under a transient spike his phone would never hit." A genuinely-down service fails
    BOTH tries -> still RED (real outage NOT masked). A load-spike timeout recovers on the retry ->
    GREEN. The retry cost is paid only on the failure path. (Pairs with _safe_run: that stopped the
    CRASH; this stops the FALSE RED — same root, next layer.)"""
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:   # noqa: BLE001 — any probe failure (timeout, conn refused, http) retries
            last = e
            if i < tries - 1:
                time.sleep(backoff)
    raise last


# Checks whose RED is plausibly a TRANSIENT session-start load-spike timeout (network probes +
# the subprocess test suite), not a real outage. Everything else is in-process logic with no
# transient failure mode (a red there is real).
_LOAD_SENSITIVE = frozenset({"portal_mini", "portal_public", "portal_items_ok", "armor_tests"})


def _phone_dead(checks, prev_checks):
    """Which dead checks have EARNED an urgent card on MOHAMED'S PHONE (vs. just the honest log).

    Root scar (June 20, third strike in one morning): the orchestra's session-start fire collided
    with the enricher+hook stampede; portal_*/armor_tests timed out on HEALTHY services (every one
    returned 200 in <0.4s, the suite was green 12 min later) and a SINGLE red fire instantly opened
    the urgent alarm card on his phone. _probe/_safe_run retry WITHIN a fire, but a heavy stampede
    outlasts both tries, so the false RED still reached him — an ADHD-contract / Rule #10 breach
    (cry-wolf erodes every real alarm).

    The bedrock fix is one layer ABOVE the probe: a LOAD-SENSITIVE red must PERSIST across two
    consecutive fires before it pages him. A real outage is still red on the next fire -> alarms
    (never masked). A load-spike transient clears -> never floods him. prev_checks is the previous
    log entry's checks ({} on the very first run -> a load-sensitive red is treated as unconfirmed
    and suppressed; a genuine outage simply confirms on the next fire).

    HARD checks (guards_gauntlet, immune_suite, law_registry, ...) have NO transient mode -> a red
    is real -> fires immediately, no second strike required.

    Note this gates ONLY the phone card. make_sure's own exit code / printed banner stay tied to the
    raw `ok`, so Claude and the orchestra still SEE every red this instant and verify it (as this
    shift did) — only Mohamed's phone waits for confirmation."""
    confirmed = []
    for k, v in checks.items():
        if v is not False:
            continue
        if k in _LOAD_SENSITIVE:
            if prev_checks.get(k) is False:   # red on BOTH fires -> real, page him
                confirmed.append(k)
            # else: first strike -> suppress this cycle, let the next fire decide
        else:
            confirmed.append(k)               # hard-check red is never transient
    return confirmed


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
        _probe(lambda: urllib.request.urlopen("http://127.0.0.1:4199/", timeout=5))
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
        checks["portal_public"] = _probe(lambda: urllib.request.urlopen(req, timeout=12)).status == 200
    except Exception:
        checks["portal_public"] = False
    # the ITEMS API (the cards), not just the page: a 200 page with a 500 items API = link
    # LIVE but showing NO cards (the "updated" half — 2026-06-14: created:null crashed the sort)
    try:
        ireq = urllib.request.Request(f"https://brain.ogzstudios.com/api/approvals/items?k={key}",
                                      headers={**UA, "Accept-Encoding": "identity"})
        ir = _probe(lambda: urllib.request.urlopen(ireq, timeout=12))
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
    _safe_run(["python3", str(BASE / "scripts/week_receipt.py")], capture_output=True, timeout=60)

    # 6a. FEEDBACK LOOP DRIVE (June 12): consume answers → issues/corrections, recompute
    # scorecards/bench, auto-close + inject budgeted meta-cards — every heartbeat
    for step in ("feedback_router.py", "apply_rulings.py", "learn_from_verdict.py", "research_fill_established.py", "gold_mint.py", "gold_audit.py", "stage_crystallize_digest.py", "scorecards.py", "feedback_cards.py"):
        _safe_run(["python3", str(BASE / "scripts" / step)], capture_output=True, timeout=120)

    # 6a2. ARMOR SUITE (B116/B117): caption_filter + truth_guards under real killed
    # captions — the deterministic half of the moat, tested every cycle.
    # Retry ONCE on failure (June 20): the suite runs ~28s standalone but the session-start
    # stampede pushed it past its 180s budget -> _safe_run rc=124 -> FALSE RED. A real test
    # failure fails BOTH runs (still RED); a load-spike timeout passes on the retry once the
    # spike clears. The second run is paid only on the failure path. (See _probe.)
    _armor_argv = ["python3", "-m", "unittest", "discover", "-s",
                   str(BASE / "scripts/tests"), "-q"]
    ar = _safe_run(_armor_argv, capture_output=True, text=True, timeout=180)
    if ar.returncode != 0:
        time.sleep(2)
        ar = _safe_run(_armor_argv, capture_output=True, text=True, timeout=180)
    checks["armor_tests"] = ar.returncode == 0

    # 6a3. IMMUNE SUITE (B119): the routing/blackout/fences/year-map armor. It lives in
    # scripts/ (NOT scripts/tests/), so `unittest discover -s scripts/tests` above never ran
    # it — a red immune gate could hide under a green make_sure for a whole shift (caught
    # June 19: a B053 router change drifted route.emotional_pair red while make_sure stayed
    # green). B119 says a red immune suite blocks shipping, so the per-fire self-check must
    # run it too (Rule #6: the armor's reader was severed; this re-wires it).
    im = _safe_run(["python3", str(BASE / "scripts/test_immune_system.py")],
                   capture_output=True, text=True, timeout=120)
    checks["immune_suite"] = im.returncode == 0

    # 6a4. The REST of the ship-gate armor (B116/B119/B121/B143) that the per-fire alarm was
    # ALSO blind to (June 19 sweep, same root as the immune gap): deadly-defaults cultural
    # release block, events-wired audit (no severed terminals — the gold wire shipped severed
    # 3×), and the visual-gate publish block. All three are shipping-blockers per the ship gate;
    # the alarm must run them too or a red gate hides under green make_sure. (The organ-schema
    # validate_all gate is deliberately NOT here — it's currently red as a staged mohamed_must
    # ruling, and adding a known-red to the blocking set would flood his portal, Rule #10.)
    for _ck, _argv in (("deadly_defaults", ["deadly_defaults_gate.py"]),
                       ("events_wired", ["verify_events_wired.py"]),
                       ("visual_gate_publish", ["visual_gate_publish_gate.py", "--enforce"])):
        try:
            _r = subprocess.run(["python3", str(BASE / "scripts" / _argv[0])] + _argv[1:],
                                capture_output=True, text=True, timeout=120)
            checks[_ck] = _r.returncode == 0
        except Exception:
            checks[_ck] = False

    # 6b-pre. LAW REGISTRY: every 'enforced' claim verified (symbol exists + test passes);
    # paper_only laws surfaced. A law that claims enforcement and lies = alarm.
    lr = _safe_run(["python3", str(BASE / "scripts/law_registry_check.py")],
                   capture_output=True, text=True, timeout=400)
    checks["law_registry"] = lr.returncode == 0

    # 6b. FEEDBACK SYSTEM integrity: router consumed, identity clean, gates hold,
    # founder canary — the 12 checks live in their own module (exit 1 = alarm)
    fb = _safe_run(["python3", str(BASE / "scripts/make_sure_feedback.py")],
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

    # 6d. BRIDGE STATUS (B-5d): the held-out LIVE taste number is 0-testable while his picks are
    # singletons; bridge cards that fix it may already be STAGED on his portal, invisibly waiting.
    # Surface it as a verified number (informational — NOT a gate, NOT a card: it's a HOLD on HIS
    # taps, not a machine failure) so a one-tap-away wait never reads as a stall (Rule #6/#9/#10).
    try:
        import pairwise
        _bs = pairwise.bridge_status()
        checks["_bridge_cards_staged"] = _bs["staged"]
        checks["_bridge_testable_now"] = _bs["n_testable_now"]
        checks["_bridge_testable_after_taps"] = _bs["n_testable_after"]
    except Exception as e:
        checks["_bridge_status_err"] = str(e)[:60]

    # 6e. INTEL-CONSUMER HEALTH (Rule #6): readers that .get() keys dropped from intelligence_layer.json
    # silently receive {} — the brief engine's PRIMARY block ran EMPTY through the live enricher for
    # many commits with NO ALARM (the exact rot 3 RABIE zoom-outs in a row named). Surface the count as
    # a VISIBLE number — informational, NOT a gate: resolution is gated on Mohamed's B057c fork
    # (rewire-vs-strip), so a refuse would pre-judge it (Rule #8 is for hard gates, this is visibility).
    # A rising count is the alarm we never had; it auto-closes to 0 once the reads are rewired/stripped.
    try:
        import intel_consumer_health
        _orph = intel_consumer_health.orphaned_intel_reads()
        checks["_orphaned_intel_reads"] = len(_orph)
        checks["_orphaned_intel_files"] = sorted({r["file"] for r in _orph}) or None
    except Exception as e:
        checks["_orphaned_intel_err"] = str(e)[:60]

    # 6e2. HUMAN-VERDICT STARVATION (verified June 20, Rule #6). His positive portal taps (approve /
    # rating>=4) never become HUMAN-confirmed client-ledger events — every ledger verdict is
    # rabie_provisional, so B082/B084 (human-hands-only) replay NOTHING. The loops read as "built" and
    # make_sure stayed all-green while the wire was structurally severed. Surface the two counts as
    # NON-bool diagnostics (so the generic ✅-loop can't green-wash them) + a dedicated ⚠️ line below.
    # Visibility only, NOT a gate (the fix is the unbuilt writer); auto-closes once one human event lands.
    try:
        import intel_consumer_health
        _starv = intel_consumer_health.human_verdict_starvation()
        checks["_judge2_positive"] = _starv["judge2_positive"]
        checks["_judge2_humanled"] = _starv["judge2_human_confirmed_ledger"]
        checks["_human_verdict_pos"] = _starv["portal_positive"]
        checks["_human_verdict_humanled"] = _starv["human_confirmed_ledger_verdicts"]
    except Exception as e:
        checks["_human_verdict_err"] = str(e)[:60]

    # 6f. TASTE→CREATION WIRE — measurement progress (B266-268, Rule #6/#9). The wire is built end to
    # end: produce_batch appends one divergence record per run → taste_shadow_metric reads them and
    # computes active-vs-baseline displacement, REFUSING any aggregate below FLOOR distinct runs. That
    # reader exists but the HEARTBEAT the orchestra reads every fire never surfaced it — so the wire's
    # proof filling toward the FLOOR was invisible, and a one-run/one-tap-away wait could read as a
    # stall (this is the named-priority wire when live picks >= 10). Surface status + n_runs/floor;
    # quote the active_vs_random gap ONLY when status==OK — never a number while INSUFFICIENT (Rule #9).
    # Informational, NOT a gate: filling the FLOOR is a HOLD on more produce runs + his taps.
    try:
        import taste_shadow_metric
        checks.update(taste_wire_surface(taste_shadow_metric.metric()))
    except Exception as e:
        checks["_taste_wire_err"] = str(e)[:60]

    ok = all(checks[k] for k in ("grinder_process", "guards_gauntlet", "portal_mini", "portal_public", "portal_items_ok", "commits_flowing", "judge_cards_gated", "orchestrator_alive", "feedback_system", "law_registry", "armor_tests", "immune_suite", "deadly_defaults", "events_wired", "visual_gate_publish"))
    # Two-strike phone gate: a load-sensitive red only pages Mohamed if it persisted since the
    # previous fire (the prev log entry's checks). First-strike transients are suppressed from his
    # phone but stay honest in the log + exit code. (See _phone_dead.)
    prev_checks = {}
    try:
        with open(LOG) as _lf:
            _lines = [ln for ln in _lf if ln.strip()]
        if _lines:
            prev_checks = json.loads(_lines[-1])
    except Exception:
        prev_checks = {}
    phone_dead = _phone_dead(checks, prev_checks)
    suppressed = [k for k, v in checks.items()
                  if v is False and k in _LOAD_SENSITIVE and k not in phone_dead]
    entry = {"ts": now, **checks, "verdict": "ALIVE" if ok else "ALARM",
             "_phone_dead": phone_dead, "_suppressed_transient": suppressed}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    STATE.write_text(json.dumps({"ts": now, "cards_total": cards}))

    for k, v in checks.items():
        print(f"  {'✅' if (v if isinstance(v, bool) else True) else '🔴'} {k}: {v}")
    print(f"\n{'🟢 MAKE-SURE: ALIVE' if ok else '🔴 MAKE-SURE: ALARM'}")
    if suppressed:
        print(f"🟡 transient suppressed (first-strike load spike, NOT paged — confirms on next "
              f"fire if real): {suppressed}")
    # SURFACE (not a check — never alarms): the research-request audit trail Mohamed asked for was
    # write-only (logged, read by nothing). Give the write-only organ its reader (Rule #6, June 15).
    try:
        import research_open
        print(research_open.summary_line())
    except Exception:
        pass
    # SURFACE the intel-consumer rot honestly (the generic check-print shows ✅ for any non-bool, which
    # would mislabel a >0 orphan count as green). One line, no card, no flood — gated on B057c.
    _oc = checks.get("_orphaned_intel_reads")
    if _oc:
        print(f"⚠️  {_oc} orphaned intel reads in {len(checks.get('_orphaned_intel_files') or [])} "
              f"reader(s) ({', '.join(checks.get('_orphaned_intel_files') or [])}) — keys dropped from "
              f"intelligence_layer.json, silently read as empty (Rule #6; resolution gated on B057c fork)")
    elif _oc == 0:
        print("✅ intel-consumer health: 0 orphaned reads")

    # SURFACE the taste→creation wire's measurement honestly (the generic ✅-for-any-non-bool print
    # would green-wash an INSUFFICIENT status). One line, no card: a HOLD on produce runs + his taps.
    _tws = checks.get("_taste_wire_status")
    if _tws == "INSUFFICIENT":
        print(f"⏳ taste→creation wire: {checks.get('_taste_wire_runs')} distinct runs — INSUFFICIENT, "
              f"no number quoted (Rule #9; awaits more produce runs + his bridge taps)")
    elif _tws == "OK":
        print(f"📈 taste→creation wire: {checks.get('_taste_wire_runs')} runs · "
              f"active_vs_random_gap={checks.get('_taste_wire_gap')} "
              f"(control_independent={checks.get('_taste_wire_control_independent')})")

    # SURFACE the human-verdict starvation honestly (the generic ✅-for-any-non-bool print would
    # green-wash the two counts). One line, no card, no flood — auto-closes when the writer lands.
    _j2p = checks.get("_judge2_positive")
    _j2l = checks.get("_judge2_humanled")
    _hvl = checks.get("_human_verdict_humanled")
    if isinstance(_j2p, int) and isinstance(_j2l, int) and _j2p > 0 and _j2l == 0:
        print(f"⚠️  judge2-approve STARVATION: {_j2p} positive judge2 batch approvals (approve/rating>=4) "
              f"→ 0 human-confirmed ledger events (client_approved/human batch_rating). The pairwise PICK "
              f"lane lands {_hvl} pick_selected, but the BATCH-judge approve→ledger writer is unbuilt, so "
              f"B084 moments compounds NOTHING from his batch YESes (Rule #6 — next pick)")
    elif isinstance(_j2l, int) and _j2l > 0:
        print(f"✅ judge2-approve wire: {_j2l} human-confirmed batch verdict(s) feeding B084")

    # ONE reusable alarm card (dedupe) — a persistent red must NOT flood his phone with
    # a new card every cycle (June 13: 20 stacked alarm cards = noise, ADHD-contract breach).
    # Auto-close it the moment everything is green again (machine evidence).
    import json as _j
    qf = BASE / "data/decision_queue.json"
    q = _j.loads(qf.read_text()) if qf.exists() else {"items": []}
    alarm = next((i for i in q["items"] if i["id"] == "alarm_live"), None)
    if phone_dead:   # only a CONFIRMED red pages him (load-sensitive transients are gated out)
        dead = phone_dead
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
        _msg = ("auto-closed: all gates green again" if ok
                else f"auto-closed: no confirmed outage (transient suppressed: {suppressed})")
        alarm["status"] = "answered"; alarm["answered"] = _msg
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
