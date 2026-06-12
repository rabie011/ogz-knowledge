#!/usr/bin/env python3
"""SCORECARDS — derived state, FULL RECOMPUTE, never a tap target (June 12).
Rebuilds data/scorecards.json + data/issues_state.json + data/bench.json wholesale
from the ledgers on every run. Idempotent: same inputs → same output. A reversal
anywhere automatically un-streaks, un-benches, un-counts — derived files are folds,
so innocent players are cleared by the same recompute that convicted them.

COUNTS, NOT SCORES (the AI-judge law): a scorecard says «11 موافق / 3 مرفوض», never
«7.2/10». Percentages only at n>=10. Explicit star-ratings → avg with n always shown.
TRUTH FENCING: quarantined rows count nothing; self-reviews excluded + surfaced;
RABIE ratings live ONLY in a provisional column; Mohamed's column is the only ground
truth — streaks, bench, gold, crystallize fire from it alone.
"""
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, is_player, now_iso, read_jsonl
import attribute as attr
from feedback_router import resolve_player

SITTING_MIN = 30          # one bad evening = one data point (rage-tap damping)
STREAK_BENCH = 3          # consecutive rejected|corrected …
BENCH_MIN_LIFETIME = 8    # … but never bench on noise (lifetime n floor)
MIN_N_RATE = 10           # percentages below this are statistics theater


def _dt(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime(1970, 1, 1)


def _blind_ids() -> set:
    """verdict_blind quarantine (June 12): verdicts collected while the card HID the
    occasion/idea never train anything — the judge didn't see what he judged."""
    f = base() / "data/verdict_quarantine.json"
    if not f.exists():
        return set()
    return set(json.loads(f.read_text()).get("quarantined_item_ids", []))


def truth_rows() -> list:
    """The judgment stream that counts: portal answers minus quarantine.
    v1 rows (no auth field) and transition rows (auth:'shared') remain truth;
    auth:'none'/judge:'unverified' never count; verdict_blind items never count."""
    blind = _blind_ids()
    rows = []
    for r in read_jsonl(base() / "data/mohamed_answers.jsonl"):
        if r.get("judge") in ("", None, "unverified") or r.get("auth") == "none":
            continue
        if r.get("item_id") in blind:
            continue
        rows.append(r)
    rows.sort(key=lambda r: r.get("ts", ""))
    return rows


def apply_reversals(rows: list) -> list:
    """Last-verdict-per-chain wins: a REVERSED row negates the most recent prior
    non-reversed verdict on the same item_id. Returns rows with negated ones marked."""
    out = [dict(r) for r in rows]
    for i, r in enumerate(out):
        # repudiation: «مو أنا» negates the referenced row (someone else's tap on this device)
        if r.get("item_id") == "_repudiation" and r.get("in_reply_to"):
            for j in range(i - 1, -1, -1):
                p = out[j]
                if f"{p.get('ts')}+{p.get('item_id')}" == r["in_reply_to"]:
                    p["_negated"] = True
                    p["_repudiated"] = True
                    break
            continue
        if str(r.get("answer")) != "REVERSED":
            continue
        ref = r.get("in_reply_to")
        for j in range(i - 1, -1, -1):
            p = out[j]
            if p.get("_negated") or str(p.get("answer")) == "REVERSED":
                continue
            if ref and f"{p.get('ts')}+{p.get('item_id')}" == ref:
                p["_negated"] = True
                p["_negated_by"] = r.get("judge")
                break
            if not ref and p.get("item_id") == r.get("item_id"):
                p["_negated"] = True
                p["_negated_by"] = r.get("judge")
                break
    return out


def classify(row: dict) -> str:
    a = str(row.get("answer", "")).strip()
    if row.get("item_id") in ("_repudiation", "_general_note"):
        return "note"                 # meta rows judge nobody
    if a == "REVERSED":
        return "reversal"
    if (row.get("fix") or "").strip():
        return "corrected"
    if a in ("rejected", "flagged") or (isinstance(row.get("rating"), int) and row["rating"] <= 2 and a in ("", "comment")):
        return "rejected"
    if a == "approved":
        return "approved"
    if a in ("comment",) and not row.get("rating"):
        return "note"
    return "judged"          # an option pick / number / text answer


def is_stale(row: dict) -> bool:
    """Version mismatch vs the CURRENT artifact — display-stale only; the verdict
    still counts fully against the version it saw (no laundering by regeneration)."""
    aid = row.get("artifact_id")
    seen = row.get("artifact_version")
    if not aid or not isinstance(seen, int):
        return False
    return seen < attr.latest_version(aid)


def author_of(row: dict) -> str:
    return resolve_player(row)


def fold_issues() -> dict:
    """issues.jsonl → per-issue state + alarms."""
    issues = defaultdict(list)
    for e in read_jsonl(base() / "data/issues.jsonl"):
        if e.get("issue_id"):
            issues[e["issue_id"]].append(e)
    state, open_count, oldest_days = {}, 0, 0
    for iid, evs in issues.items():
        evs.sort(key=lambda e: e.get("ts", ""))
        opener = next((e for e in evs if e["event"] == "open"), None)
        if not opener:
            continue
        last = evs[-1]["event"]
        status = {"open": "open", "reopened": "open", "fix_claimed": "fix_claimed",
                  "verified": "verified", "closed": "closed", "voided": "voided"}[last]
        rec = max((e.get("recurrence_count", 0) for e in evs if e["event"] == "reopened"), default=0)
        age = 0
        if status in ("open", "fix_claimed", "verified"):
            open_count += 1
            age = (datetime.now() - _dt(opener["ts"])).days
            oldest_days = max(oldest_days, age)
        state[iid] = {"status": status, "player": opener.get("player"),
                      "reason_code": opener.get("reason_code"), "quote": opener.get("quote"),
                      "severity": opener.get("severity"), "source": opener.get("source"),
                      "opened": opener.get("ts"), "recurrence_count": rec,
                      "open_days": age,
                      "events": [{"event": e["event"], "ts": e["ts"],
                                  **({"commit": e["commit"][:9]} if e.get("commit") else {}),
                                  **({"closed_by": e["closed_by"]} if e.get("closed_by") else {})}
                                 for e in evs]}
    return {"issues": state, "open_count": open_count, "oldest_open_days": oldest_days,
            "generated": now_iso()}


def rabie_provisional() -> dict:
    """RABIE's session ratings — visible, NEVER authoritative, never blended."""
    out = defaultdict(lambda: {"n": 0, "sum": 0})
    sess_dir = Path.home() / "agents/rabie/sessions"
    if not sess_dir.exists():
        return {}
    for f in sorted(sess_dir.glob("*.jsonl"))[-14:]:
        for e in read_jsonl(f):
            r = e.get("rating")
            if isinstance(r, (int, float)) and 0 <= r <= 5:
                t = e.get("target") or "claude"
                out[t]["n"] += 1
                out[t]["sum"] += r
    return {k: {"n": v["n"], "avg": round(v["sum"] / v["n"], 1)} for k, v in out.items() if v["n"]}


def compute() -> dict:
    rows = apply_reversals(truth_rows())
    now = datetime.now()
    players = defaultdict(lambda: {
        "w7": defaultdict(int), "lifetime": defaultdict(int),
        "by_source": {"cards": defaultdict(int), "after_strip": defaultdict(int)},
        "ratings": [], "dots": [], "overridden": 0, "self_review_excluded": 0})

    # ---- judgments fold (Mohamed + team; truth-fenced) ----
    mohamed_seq = defaultdict(list)         # player → [(ts, kind)] mohamed-only, for streaks
    by_item = defaultdict(list)             # conflicts
    for r in rows:
        kind = classify(r)
        if kind in ("reversal", "note"):
            continue
        # TASTE FILTER (June 12 zoom-out): only judgments anchored to an ARTIFACT or an
        # explicit player target count toward player scorecards. Ops option-picks
        # (team_link_share→done etc.) are decisions, not taste — they polluted claude's
        # card with judged:13 before this filter.
        if not (r.get("artifact_id") or r.get("target")):
            continue
        player = author_of(r)
        judge = r.get("judge", "mohamed")
        # self-review: the author judging itself — excluded + surfaced
        if f"judge:{judge}" == player or judge == player:
            players[player]["self_review_excluded"] += 1
            continue
        if r.get("_negated"):
            # negated by reversal: drop from counts; count reversed_against for the player
            players[player]["lifetime"]["reversed_against"] += 1
            if r.get("_negated_by") and r["_negated_by"] != judge:
                players[f"judge:{judge}"]["overridden"] += 1
            continue
        src = "after_strip" if r.get("source") == "after_strip" else "cards"
        stale = is_stale(r)
        buckets = [players[player]["lifetime"]]
        if now - _dt(r.get("ts", "")) <= timedelta(days=7):
            buckets.append(players[player]["w7"])
        for b in buckets:
            b["judged"] += 1
            b[kind if kind in ("approved", "rejected", "corrected") else "other"] += 1
            if stale:
                b["stale"] += 1
        thumb = {"approved": "thumbs_up", "rejected": "thumbs_down"}.get(kind)
        if src == "after_strip" and thumb:
            players[player]["by_source"]["after_strip"][thumb] += 1
        else:
            players[player]["by_source"]["cards"][kind] += 1
        if isinstance(r.get("rating"), int) and 1 <= r["rating"] <= 5:
            players[player]["ratings"].append(r["rating"])
        dot = {"approved": "green", "rejected": "red", "corrected": "yellow"}.get(kind, "grey")
        players[player]["dots"] = (players[player]["dots"] + [("grey" if stale else dot)])[-10:]
        if judge == "mohamed" and src == "cards":
            mohamed_seq[player].append((_dt(r.get("ts", "")), kind))
            by_item[r.get("item_id")].append({"judge": judge, "kind": kind, "ts": r.get("ts")})
        elif src == "cards":
            by_item[r.get("item_id")].append({"judge": judge, "kind": kind, "ts": r.get("ts")})

    # ---- streaks (Mohamed-only, sitting-damped) + bench ----
    bench, streaks = {}, {}
    for player, seq in mohamed_seq.items():
        seq.sort(key=lambda x: x[0])
        streak, last_counted = 0, None
        for ts, kind in seq:
            if kind in ("rejected", "corrected"):
                if last_counted and (ts - last_counted) <= timedelta(minutes=SITTING_MIN):
                    continue                      # same sitting — one data point max
                if last_counted and (ts - last_counted) > timedelta(days=7):
                    streak = 0                    # streaks live in a 7-day window
                streak += 1
                last_counted = ts
            elif kind == "approved":
                streak, last_counted = 0, ts
        streaks[player] = streak
        if streak >= STREAK_BENCH and players[player]["lifetime"]["judged"] >= BENCH_MIN_LIFETIME:
            bench[player] = {"since": now_iso(), "streak": streak,
                             "card_id": f"streak_{player.replace(':','_')}_{now_iso()[:10]}"}

    # ---- conflicts (opposing verdicts, two judges, 7 days) ----
    conflicts = []
    for iid, verdicts in by_item.items():
        kinds = {v["judge"]: v["kind"] for v in verdicts}
        if "mohamed" in kinds and len(kinds) > 1:
            for j, k in kinds.items():
                if j != "mohamed" and {k, kinds["mohamed"]} == {"approved", "rejected"}:
                    conflicts.append({"item_id": iid, "judge": j, "their": k,
                                      "mohamed": kinds["mohamed"]})

    # ---- assemble ----
    inputs_sha = hashlib.sha256()
    for f in ("data/mohamed_answers.jsonl", "data/attribution.jsonl", "data/issues.jsonl"):
        p = base() / f
        if p.exists():
            inputs_sha.update(p.read_bytes())
    issues_state = fold_issues()
    open_by_player = defaultdict(int)
    for iid, st in issues_state["issues"].items():
        if st["status"] in ("open", "fix_claimed", "verified"):
            open_by_player[st["player"]] += 1

    cards = {}
    for player, d in sorted(players.items()):
        if not is_player(player):
            continue
        lt = d["lifetime"]
        n = lt["judged"]
        rates = None
        if n >= MIN_N_RATE:
            rates = {"approved_pct": round(100 * lt["approved"] / n),
                     "rejected_pct": round(100 * lt["rejected"] / n)}
        ratings = d["ratings"]
        cards[player] = {
            "lifetime": dict(lt), "w7": dict(d["w7"]),
            "by_source": {k: dict(v) for k, v in d["by_source"].items()},
            "rates": rates,
            "low_n_note": None if n >= MIN_N_RATE else f"بيانات قليلة (n={n})",
            "rating_avg": (round(sum(ratings) / len(ratings), 1) if ratings else None),
            "rating_n": len(ratings),
            "dots": d["dots"], "streak": streaks.get(player, 0),
            "benched": player in bench,
            "open_issues": open_by_player.get(player, 0),
            "overridden": d["overridden"],
            "self_review_excluded": d["self_review_excluded"],
        }
    return {
        "scorecards": {"generated": now_iso(), "inputs_sha256": inputs_sha.hexdigest(),
                       "players": cards, "conflicts": conflicts,
                       "by_judge": {"rabie_provisional": rabie_provisional()},
                       "unattributed_w7": players.get("system:unattributed", {}).get("w7", {}).get("judged", 0)
                       if "system:unattributed" in players else 0},
        "issues_state": issues_state,
        "bench": bench,
    }


def write_all() -> dict:
    out = compute()
    d = base() / "data"
    d.mkdir(exist_ok=True)
    (d / "scorecards.json").write_text(json.dumps(out["scorecards"], ensure_ascii=False, indent=1))
    (d / "issues_state.json").write_text(json.dumps(out["issues_state"], ensure_ascii=False, indent=1))
    (d / "bench.json").write_text(json.dumps(out["bench"], ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    o = write_all()
    sc = o["scorecards"]["players"]
    print(f"players: {len(sc)} · open issues: {o['issues_state']['open_count']} · benched: {list(o['bench']) or '—'}")
    for p, c in sorted(sc.items()):
        lt = c["lifetime"]
        print(f"  {p:24s} {lt.get('judged',0):3d} حُكم · {lt.get('approved',0)} ✓ · {lt.get('rejected',0)} ✗ · "
              f"{lt.get('corrected',0)} ✏️ · streak {c['streak']}{' 🧊BENCHED' if c['benched'] else ''}")
