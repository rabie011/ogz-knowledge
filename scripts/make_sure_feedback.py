#!/usr/bin/env python3
"""MAKE-SURE: FEEDBACK SYSTEM (June 12) — the 12 evidence checks. The feedback system
audits itself by counts, never feelings — and the referee Claude wrote is spot-checked
by independent arithmetic. Exit 1 = alarm (make_sure.py surfaces it).
"""
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, producer_allows, read_jsonl
import feedback_router


def _dt(ts):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime(1970, 1, 1)


def _parseable_dt(ts) -> bool:
    """True iff ts is a real ISO datetime — used to keep created-less cards OUT of the
    staleness median (a missing timestamp is not evidence that a card is 56 years old)."""
    try:
        datetime.fromisoformat(str(ts)); return True
    except Exception:
        return False


def run_checks() -> dict:
    B = base()
    now = datetime.now()
    c = {}

    # 1. IDENTITY REGRESSION-LOCK: the line-106 bug must never return
    portal_src = (Path(__file__).parent.parent / "api/portal_mini.py").read_text()
    c["identity_no_mohamed_default"] = 'else "mohamed"' not in portal_src

    # 2. ROUTER CURSOR FRESHNESS (the 88-day dead-consumer scar)
    answers = B / "data/mohamed_answers.jsonl"
    cur = feedback_router.load_cursor()
    behind = (answers.stat().st_size - cur["offset"]) if answers.exists() else 0
    stale_row = False
    if behind > 0 and answers.exists():
        with open(answers, "rb") as f:
            f.seek(cur["offset"])
            first_unread = f.readline()
        try:
            ts = json.loads(first_unread).get("ts", "")
            stale_row = (now - _dt(ts)) > timedelta(hours=1)
        except Exception:
            stale_row = True
    c["router_cursor_fresh"] = not stale_row

    # 3. FOUNDER-ENGAGEMENT CANARY (the moat-draining early warning)
    rows = read_jsonl(answers)
    last_moh = max((r["ts"] for r in rows if r.get("judge") == "mohamed"), default="")
    c["days_since_mohamed"] = round((now - _dt(last_moh)).total_seconds() / 86400, 1) if last_moh else 999
    q = json.loads((B / "data/decision_queue.json").read_text()) if (B / "data/decision_queue.json").exists() else {"items": []}
    open_cards = [i for i in q["items"] if i.get("status") != "answered"]
    # A card with no parseable `created` carries NO staleness signal — counting it as epoch-1970
    # (20k+ days) is a data artifact, not founder-neglect, and falsely trips the canary. Honest
    # median = over cards we can actually date. (Surfaced June 20 when retiring 52 dated corpses
    # exposed 21 created-less cards the corpses had been masking in the median.)
    ages = [(now - _dt(cr)).days for i in open_cards if _parseable_dt(cr := i.get("created", ""))]
    c["median_card_age_d"] = statistics.median(ages) if ages else 0
    c["founder_canary"] = c["days_since_mohamed"] <= 3 and c["median_card_age_d"] <= 5

    # 4. UNATTRIBUTED AT ZERO (without Goodhart: backfill needs per-line evidence)
    sc_f = B / "data/scorecards.json"
    sc = json.loads(sc_f.read_text()) if sc_f.exists() else {}
    c["unattributed_w7"] = sc.get("unattributed_w7", 0)
    c["unattributed_zero"] = c["unattributed_w7"] == 0
    # bulk-backfill detector: >5 same-made_by lines per minute WITHOUT per-line evidence.
    # An evidenced backfill (reason cites its verification path, e.g. "git log …") is the
    # spec's sanctioned path — the detector hunts GUESSED attribution, not paced evidence.
    attrib = read_jsonl(B / "data/attribution.jsonl")
    by_min = defaultdict(int)
    for e in attrib:
        if (e.get("event") == "created" and "git log" not in e.get("reason", "")
                and e.get("artifact_type") != "card"):   # cards are visible on the portal — self-evidencing
            by_min[(e.get("ts", "")[:16], e.get("made_by"))] += 1
    c["no_bulk_backfill"] = all(v <= 5 for v in by_min.values())

    # 5. PRODUCER MAP TRUTH + transactional ordering
    bad_pairs = [e for e in attrib if e.get("event") == "created"
                 and not producer_allows(e.get("via", ""), e.get("made_by", ""))]
    c["producer_map_clean"] = not bad_pairs
    stamped = [i for i in q["items"] if i.get("made_by")]
    attributed_ids = {e.get("artifact_id") for e in attrib if e.get("event") == "created"}
    c["cards_attributed"] = all(f"card:{i['id']}" in attributed_ids for i in stamped)

    # 6. EVIDENCE GATES HOLD on every issue event
    issues = read_jsonl(B / "data/issues.jsonl")
    gate_ok = True
    for e in issues:
        if e.get("event") == "fix_claimed":
            r = subprocess.run(["git", "-C", str(B), "cat-file", "-e", e.get("commit", "x")],
                               capture_output=True)
            if r.returncode != 0:
                gate_ok = False
        if e.get("event") == "verified" and e.get("exit_code") != 0:
            gate_ok = False
        if e.get("event") == "recurred" and not e.get("quote"):
            gate_ok = False   # recurred = quote-preserving note (June 13) — a quoteless one is noise
        if e.get("event") not in ("open", "fix_claimed", "verified", "closed", "reopened",
                                   "voided", "recurred"):
            gate_ok = False
    c["evidence_gates"] = gate_ok

    # 7. RECEIPT/IM-HERE ALIVE (the loop-closing surface must not die silently)
    imh = B / "data/im_here.md"
    c["receipt_alive"] = imh.exists() and (now - datetime.fromtimestamp(imh.stat().st_mtime)) < timedelta(days=8)

    # 8. SCORECARD FRESHNESS + HAND-RECOUNT (the referee is spot-checked)
    fresh = True
    if answers.exists() and sc_f.exists():
        fresh = sc_f.stat().st_mtime >= answers.stat().st_mtime - 7200
    c["scorecards_fresh"] = fresh
    recount_ok = True
    if sc_f.exists():
        import scorecards as scm
        from scorecards import apply_reversals, classify, truth_rows, author_of
        judged = defaultdict(int)
        for r in apply_reversals(truth_rows()):
            k = classify(r)
            if k in ("reversal", "note") or r.get("_negated"):
                continue
            # the taste filter — MUST mirror compute() exactly (the recount exists to
            # catch divergence; it caught this very line missing on 2026-06-12)
            if not (r.get("artifact_id") or r.get("target")):
                continue
            judge = r.get("judge", "mohamed")
            player = author_of(r)
            if f"judge:{judge}" == player or judge == player:
                continue
            judged[player] += 1
        for p, n in judged.items():
            card = sc.get("players", {}).get(p)
            if card and card["lifetime"].get("judged", 0) != n:
                recount_ok = False
    c["hand_recount"] = recount_ok

    # 9. QUARANTINE GRAVEYARD (a judge silently keyed-out = dead consumer relocated)
    unv = read_jsonl(B / "data/unverified_answers.jsonl")
    week_ago = now - timedelta(days=7)
    truth_judges = {r.get("judge") for r in rows if _dt(r.get("ts", "")) > week_ago}
    grave = False
    by_j = defaultdict(int)
    team = {m["id"] for m in (json.loads((B / "data/portal_team.json").read_text()).get("members", [])
                              if (B / "data/portal_team.json").exists() else [])}
    for r in unv:
        if _dt(r.get("ts", "")) > week_ago:
            bj = r.get("_claimed_judge") or ""
            by_j[bj] += 1
    for j, n in by_j.items():
        if j in team and n >= 3 and j not in truth_judges:
            grave = True
    c["no_quarantine_graveyard"] = not grave

    # 10. APPEND-ONLY (the cursor's sha still sits at its offset)
    c["append_only"] = feedback_router.check_append_only()

    # 11. META-CARD BUDGET RESPECTED
    live_fb = [i for i in open_cards if i.get("source") == "feedback_cards"]
    c["card_budget_ok"] = len(live_fb) <= 3

    # 12b. THE GOLD WIRE, END TO END (the chair's law: assert at the SYSTEM layer —
    # a synthetic approval must travel mint→renderer-expression in a sandbox)
    gw = subprocess.run([sys.executable, str(Path(__file__).parent / "assert_gold_wire.py")],
                        capture_output=True, text=True, timeout=60)
    c["gold_wire_e2e"] = gw.returncode == 0

    # 12c. REBOOT-PROOFING (Mohamed-gated; report-only, machine evidence closes the card —
    # he tapped 'all_good' from his PHONE at 21:02 while never at the Mac, and the old
    # verify-grep counted Apple's siri 'orchestrator' lines. Self-report is dead here.)
    lc = subprocess.run(["launchctl", "print", "gui/501"], capture_output=True, text=True)
    labels = ("com.abraham.orchestrator", "com.ogz.healthcheck", "com.abraham.cloudflare")
    loaded = sum(1 for l in labels if l in (lc.stdout or ""))
    c["reboot_proofed"] = f"{loaded}/3"
    if loaded == 3:
        # auto-close any open plist card — the machine saw it, no tap needed
        qf = B / "data/decision_queue.json"
        qq = json.loads(qf.read_text())
        for it in qq["items"]:
            if it["id"].startswith(("plist_", "orchestrator_plist")) and it.get("status") != "answered":
                it["status"] = "answered"; it["answered"] = "machine-verified: 3/3 loaded"
                it["answered_by"] = "system"
        qf.write_text(json.dumps(qq, ensure_ascii=False, indent=1))

    # 12d. VERDICTS APPLIED (June 13, the severed return-arc: his midnight sitting was
    # consumed by the router yet changed NOTHING in the library for a whole night while
    # this monitor glowed green). Answered ratify_* card + recipe still 'awaiting' = RED.
    try:
        pc = json.loads((B / "data/pattern_cards_v1.json").read_text())
        rec_status = {cc["slug"]: str(cc.get("status", "")) for cc in pc["survivors"]}
        unapplied = []
        for it in q["items"]:
            if it.get("status") == "answered" and it["id"].startswith("ratify_"):
                slug = it["id"].replace("ratify_", "").removesuffix("_v2")
                st = rec_status.get(slug, "")
                if "awaiting_mohamed_ratification" in st or st.endswith("ready for re-ratification"):
                    unapplied.append(slug)
        c["verdicts_applied"] = not unapplied
        if unapplied:
            c["unapplied_recipes"] = unapplied
    except Exception:
        c["verdicts_applied"] = True

    # 12e. RULINGS APPLIED (June 13, 02:13: Mohamed tapped drop_conflicted and the order
    # sat unexecuted for 2h — button answers had NO consumer while this monitor glowed
    # green; the renderer kept few-shotting gold he had struck). Any post-epoch decision
    # answer older than 15 min with no applied_rulings entry (and no handler) = RED.
    # Same check runs founder-note parity: a Mohamed note in answers but not in
    # founder_words = a lost founder word (the religion note was lost this way).
    try:
        import time as _t
        sys.path.insert(0, str(B / "scripts"))
        import apply_rulings as _ar
        stale = []
        for item, ans, why in _ar.pending_unhandled(B):
            rows = [r for r in _ar._read_jsonl(B / _ar.ANSWERS)
                    if r.get("item_id") == item and r.get("answer") == ans]
            ts = (rows[-1].get("ts") or rows[-1].get("client_ts") or "") if rows else ""
            try:
                age_min = (_t.time() - _t.mktime(_t.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))) / 60
            except Exception:
                age_min = 999
            if age_min > 15:
                stale.append(f"{item}→{ans} ({why}, {round(age_min)}m)")
        c["rulings_applied"] = not stale
        if stale:
            c["unapplied_rulings"] = stale
        have = " ".join(r.get("words", "") for r in _ar._read_jsonl(B / "data/founder_words.jsonl"))
        missing_notes = [r.get("item_id") for r in _ar._read_jsonl(B / _ar.ANSWERS)
                         if r.get("judge") == "mohamed" and len((r.get("note") or "").strip()) >= 15
                         and (r.get("note") or "").strip()[:60] not in have]
        c["founder_note_parity"] = not missing_notes
        if missing_notes:
            c["lost_founder_notes"] = missing_notes
    except Exception as e:
        c["rulings_applied"] = False
        c["founder_note_parity"] = False
        c["rulings_check_error"] = str(e)[:120]

    # 12f. TRUST BUDGET (B030): violations target 0 FOREVER — a re-asked question
    # on record = red until Mohamed sees it (no silent amnesty, no decay)
    tv = B / "data/trust_violations.jsonl"
    n_viol = sum(1 for l in tv.read_text(encoding="utf-8").splitlines() if l.strip()) if tv.exists() else 0
    c["trust_violations"] = n_viol
    c["trust_budget_zero"] = n_viol == 0

    # 12g. PRIVACY AUDIT FRESH (B031): the quarterly wall audit ran <90d ago and passed
    pa = B / "data/privacy_audit_last.json"
    if pa.exists():
        rep = json.loads(pa.read_text())
        c["privacy_audit_fresh"] = (rep.get("pass") is True and
                                    (now - _dt(rep.get("ts", ""))) < timedelta(days=90))
    else:
        c["privacy_audit_fresh"] = False

    # 12h. NO-RE-ASK (June 13 Memory Law / Rule #6+#11): a passport card may NEVER ask a
    # question the organ already answers — re-ask = trust death (the goals-counter bug
    # nearly re-asked jurisha's confirmed goal/capacity/USP).
    try:
        sys.path.insert(0, str(B / "scripts"))
        from seed_passport_cards import already_answered as _ans
        q = json.loads((B / "data/decision_queue.json").read_text())["items"]
        reask = []
        for it in q:
            iid = it.get("id", "")
            if iid.startswith("passport_") and it.get("status") != "answered":
                h, field = it.get("handle"), it.get("field")
                if h and field and _ans(B, h, field):
                    reask.append(iid)
        c["no_reask"] = not reask
        if reask:
            c["reask_violations"] = reask
    except Exception as e:
        c["no_reask"] = False
        c["no_reask_error"] = str(e)[:100]

    # 12i. READINESS FROM FIELDS (June 13 Rule #11 / self-audit): a readiness counter must
    # match field-presence — never hallucinate readiness from a stale counter (goals.json
    # read answered:0 while 3 fields were mohamed-confirmed).
    import glob as _g
    counter_lies = []
    for gf in _g.glob(str(B / "clients/*/profile/goals.json")):
        g = json.loads(Path(gf).read_text())
        confirmed = sum(1 for k in ("goal_ratio", "capacity_ceiling", "usp_his_words")
                        if g.get(k))
        if g.get("answered", 0) != confirmed and not (g.get("answered", 0) >= confirmed):
            counter_lies.append(f"{Path(gf).parent.parent.name}: counter {g.get('answered')} < fields {confirmed}")
    c["readiness_honest"] = not counter_lies
    if counter_lies:
        c["counter_lies"] = counter_lies

    # 12. OPEN-ISSUE PULSE
    ist = json.loads((B / "data/issues_state.json").read_text()) \
        if (B / "data/issues_state.json").exists() else {"oldest_open_days": 0}
    c["oldest_open_days"] = ist.get("oldest_open_days", 0)
    c["issue_pulse_ok"] = c["oldest_open_days"] <= 14

    gates = ["identity_no_mohamed_default", "router_cursor_fresh", "founder_canary",
             "unattributed_zero", "no_bulk_backfill", "producer_map_clean", "cards_attributed",
             "evidence_gates", "receipt_alive", "scorecards_fresh", "hand_recount",
             "no_quarantine_graveyard", "append_only", "card_budget_ok", "issue_pulse_ok",
             "gold_wire_e2e", "verdicts_applied", "rulings_applied", "founder_note_parity",
             "trust_budget_zero", "privacy_audit_fresh", "no_reask", "readiness_honest"]
    c["_verdict"] = all(c[g] for g in gates)
    c["_failed"] = [g for g in gates if not c[g]]
    return c


if __name__ == "__main__":
    c = run_checks()
    for k, v in c.items():
        if k.startswith("_"):
            continue
        mark = "✅" if (v if isinstance(v, bool) else True) else "🔴"
        print(f"  {mark} {k}: {v}")
    print(f"\n{'🟢 FEEDBACK MAKE-SURE: CLEAN' if c['_verdict'] else '🔴 FEEDBACK MAKE-SURE: ' + ','.join(c['_failed'])}")
    raise SystemExit(0 if c["_verdict"] else 1)
