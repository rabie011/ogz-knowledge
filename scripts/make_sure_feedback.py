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
    ages = [(now - _dt(i.get("created", ""))).days for i in open_cards]
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
        if e.get("event") == "created" and "git log" not in e.get("reason", ""):
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
        if e.get("event") not in ("open", "fix_claimed", "verified", "closed", "reopened", "voided"):
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

    # 12. OPEN-ISSUE PULSE
    ist = json.loads((B / "data/issues_state.json").read_text()) \
        if (B / "data/issues_state.json").exists() else {"oldest_open_days": 0}
    c["oldest_open_days"] = ist.get("oldest_open_days", 0)
    c["issue_pulse_ok"] = c["oldest_open_days"] <= 14

    gates = ["identity_no_mohamed_default", "router_cursor_fresh", "founder_canary",
             "unattributed_zero", "no_bulk_backfill", "producer_map_clean", "cards_attributed",
             "evidence_gates", "receipt_alive", "scorecards_fresh", "hand_recount",
             "no_quarantine_graveyard", "append_only", "card_budget_ok", "issue_pulse_ok"]
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
