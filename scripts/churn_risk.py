#!/usr/bin/env python3
"""CHURN-RISK DASHBOARD + RUBBER-STAMP DETECTOR (B092, L4 Bedrock — RABIE's pick 2026-06-22).

Mohamed's judgment IS the calibration signal — the whole creation system learns his eye from
his taps. So the scarcest, most fragile input is HIS ENGAGEMENT. Two ways it fails:
  1. CHURN — he goes quiet, latency rises, completion falls, outcomes stop moving. The signal
     starves and the system silently drifts on stale taste.
  2. RUBBER-STAMP — he taps through without thinking (same answer, near-zero gap). Worse than
     silence: it LOOKS like fresh signal but is noise that POISONS the calibration (Rule #13 —
     a deterministic all-green is a false green; this is its human analogue).

This is the missing CONSUMER (Rule #6) of the engagement organs: it READS data/mohamed_answers.jsonl
(his verdict stream, also B026's source), data/receipts_summary.json (real-world outcome movement,
B094), and a thresholds config (data/state.json if present, else documented defaults) and computes a
GREEN/YELLOW/RED risk read. PURE NUMBERS — no AI sentiment, no LLM (Rule #12: cheap/zero-key).

SCOPE NOTE (autonomous-shift choice, flagged for Mohamed): the only engagement stream we have is
HIS judging cadence (the pilot has no separate per-client client-side stream yet). So this measures
JUDGE-ENGAGEMENT churn — the integrity of the taste signal. The per-CLIENT red-client layer (B093,
account-owner human-touch task) builds ON this once a client-side cadence stream exists.

HONESTY (Rule #9): every signal that lacks enough data says so and quotes NO number — absent
receipts → flat_receipts=INSUFFICIENT, a single session → no latency trend. Honest zero, never a
crash (Pre-Build Q2). Risk never escalates on a signal that is INSUFFICIENT.

Usage:
  python3 scripts/churn_risk.py            # compute + print dashboard → data/churn_risk.json
  python3 scripts/churn_risk.py --quiet    # write only
"""
import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

import gate_metrics  # single-source the 30-min session law (B026); never re-define it here

BASE = Path(__file__).parent.parent
ANSWERS = BASE / "data/mohamed_answers.jsonl"
RECEIPTS = BASE / "data/receipts_summary.json"
STATE = BASE / "data/state.json"
OUT = BASE / "data/churn_risk.json"

# Documented default thresholds (used when data/state.json carries no `churn_thresholds` block).
# Numbers, not feelings — tune via state.json, never by editing taste-of-the-day.
DEFAULTS = {
    "days_silent_yellow": 3,        # >3d no tap → drifting
    "days_silent_red": 7,           # >7d no tap → starved
    "latency_rise_factor": 1.5,     # last session median >1.5x the prior baseline → rising
    "completion_drop_factor": 0.6,  # last session verdict-count <0.6x baseline → falling
    "rubber_stamp_gap_sec": 5,      # median gap <5s ...
    "rubber_stamp_distinct_ratio": 0.34,  # ...AND <34% distinct answers in a session = rubber-stamp
    "rubber_stamp_min_taps": 4,     # need >=4 taps in a session before the pattern means anything
    "trend_min_session_taps": 3,    # a session smaller than this is NOT a comparable unit for trends
    "trend_recent_sessions": 3,     # the "recent" window = the last N comparable sessions (pooled)
    "latency_min_gaps": 5,          # refuse a latency trend until the recent window pools >=5 gaps
}


def load_answers(path=ANSWERS):
    """Parse the verdict stream → time-sorted list of {ts, _t, item_id, answer}. Honest [] if absent."""
    if not Path(path).exists():
        return []
    out = []
    for ln in Path(path).read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            e = json.loads(ln)
            e["_t"] = datetime.fromisoformat(e["ts"])
            out.append(e)
        except Exception:
            continue
    out.sort(key=lambda e: e["_t"])
    return out


def group_sessions(answers):
    """30-min-gap sessions (B026's law, single-sourced via gate_metrics.SESSION_GAP_MIN)."""
    gap = gate_metrics.SESSION_GAP_MIN * 60
    out, cur = [], []
    for e in answers:
        if cur and (e["_t"] - cur[-1]["_t"]).total_seconds() > gap:
            out.append(cur)
            cur = []
        cur.append(e)
    if cur:
        out.append(cur)
    return out


def _median_gap(session):
    gaps = [(b["_t"] - a["_t"]).total_seconds() for a, b in zip(session, session[1:])]
    return statistics.median(gaps) if gaps else None


def rubber_stamp(session, th):
    """A session is rubber-stamped when he taps fast AND samey: median gap < gap_sec AND the
    distinct-answer ratio < distinct_ratio, over at least min_taps taps. Returns a verdict dict;
    `flag` is None (INSUFFICIENT) below min_taps — never a false alarm on a 1-2 tap session."""
    n = len(session)
    if n < th["rubber_stamp_min_taps"]:
        return {"flag": None, "reason": f"INSUFFICIENT ({n} taps < {th['rubber_stamp_min_taps']})"}
    mg = _median_gap(session)
    answers = [str(e.get("answer", "")) for e in session]
    distinct_ratio = len(set(answers)) / n
    fast = mg is not None and mg < th["rubber_stamp_gap_sec"]
    samey = distinct_ratio < th["rubber_stamp_distinct_ratio"]
    return {"flag": bool(fast and samey), "median_gap_sec": round(mg, 1) if mg is not None else None,
            "distinct_ratio": round(distinct_ratio, 2), "taps": n}


def _comparable(sessions, th):
    """Sessions big enough to be a measurable unit. A 1-2 tap trailing session is NOT 'completion
    fell off a cliff' nor a latency spike — it is noise, and trending on it quotes a lie (Rule #9,
    the degenerate-tiny-session scar, 2026-06-22). Both trends compare only these."""
    return [s for s in sessions if len(s) >= th["trend_min_session_taps"]]


def _within_gaps(sessions):
    """All within-session gaps (seconds) pooled across the given sessions."""
    out = []
    for s in sessions:
        out += [(b["_t"] - a["_t"]).total_seconds() for a, b in zip(s, s[1:])]
    return out


def latency_trend(sessions, th):
    """RECENT-WINDOW median sec/verdict vs the PRIOR window — gaps POOLED across the last N
    comparable sessions, NOT one fragile session. A single session's 2-gap median swings wildly
    on one step-away (the x30.69 scar, 2026-06-22); pooling smooths it. INSUFFICIENT (None) until
    the recent window holds >= latency_min_gaps gaps and a prior window exists (Rule #9)."""
    comp = _comparable(sessions, th)
    r = th["trend_recent_sessions"]
    if len(comp) < r + 1:
        return {"trend": None, "reason": f"INSUFFICIENT (<{r + 1} comparable sessions)"}
    recent = _within_gaps(comp[-r:])
    prior = _within_gaps(comp[:-r])
    if len(recent) < th["latency_min_gaps"] or not prior:
        return {"trend": None, "reason": f"INSUFFICIENT (recent gaps {len(recent)} < {th['latency_min_gaps']})"}
    rm, pm = statistics.median(recent), statistics.median(prior)
    return {"trend": round(rm / pm, 2) if pm else None, "recent_median_sec": round(rm, 1),
            "prior_median_sec": round(pm, 1), "recent_gaps": len(recent)}


def completion_trend(sessions, th):
    """RECENT-window mean verdicts/session vs the PRIOR window (falling = disengaging). Averaged
    over the last N comparable sessions so one short session can't read as collapse. INSUFFICIENT
    with too few comparable sessions either side (Rule #9)."""
    comp = _comparable(sessions, th)
    r = th["trend_recent_sessions"]
    if len(comp) < r + 1:
        return {"ratio": None, "reason": f"INSUFFICIENT (<{r + 1} comparable sessions)"}
    recent = statistics.mean(len(s) for s in comp[-r:])
    prior = statistics.mean(len(s) for s in comp[:-r])
    return {"ratio": round(recent / prior, 2) if prior else None, "recent_mean_verdicts": round(recent, 1),
            "prior_mean_verdicts": round(prior, 1)}


def flat_receipts(receipts_summary):
    """Real-world outcome movement (B094). Absent / empty → INSUFFICIENT, NO number (Rule #9)."""
    if not receipts_summary:
        return {"flag": None, "reason": "INSUFFICIENT (no receipts yet — B094 collector idle)"}
    n = receipts_summary.get("n_receipts", receipts_summary.get("count", 0))
    if n == 0:
        return {"flag": None, "reason": "INSUFFICIENT (0 receipts)"}
    moved = receipts_summary.get("n_with_baseline_delta", receipts_summary.get("moved", None))
    if moved is None:
        return {"flag": None, "reason": "INSUFFICIENT (receipts present, no baseline movement field)"}
    return {"flag": moved == 0, "n_receipts": n, "moved": moved}


def compute(answers, receipts_summary, now, thresholds=None):
    """PURE risk read — all inputs injected so it is fully testable. Returns the dashboard dict."""
    th = {**DEFAULTS, **(thresholds or {})}
    if not answers:
        return {"risk": "INSUFFICIENT", "reason": "no taps yet (honest zero)", "signals": {}}
    sessions = group_sessions(answers)
    days_silent = round((now - answers[-1]["_t"]).total_seconds() / 86400, 1)
    lat = latency_trend(sessions, th)
    comp = completion_trend(sessions, th)
    rs = rubber_stamp(sessions[-1], th)
    fr = flat_receipts(receipts_summary)

    # Escalation — a signal only votes when it is NOT insufficient (Rule #9: insufficient never escalates).
    red, yellow = [], []
    if days_silent > th["days_silent_red"]:
        red.append(f"silent {days_silent}d (>{th['days_silent_red']})")
    elif days_silent > th["days_silent_yellow"]:
        yellow.append(f"silent {days_silent}d (>{th['days_silent_yellow']})")
    if rs["flag"] is True:
        red.append(f"rubber-stamp: gap {rs['median_gap_sec']}s, distinct {rs['distinct_ratio']}")
    if lat["trend"] is not None and lat["trend"] >= th["latency_rise_factor"]:
        yellow.append(f"latency rising x{lat['trend']}")
    if comp["ratio"] is not None and comp["ratio"] <= th["completion_drop_factor"]:
        yellow.append(f"completion falling x{comp['ratio']}")
    if fr["flag"] is True:
        yellow.append("receipts flat (0 moved)")

    risk = "RED" if red else "YELLOW" if yellow else "GREEN"
    return {
        "risk": risk, "reasons": red + yellow,
        "days_silent": days_silent, "n_taps": len(answers), "n_sessions": len(sessions),
        "signals": {"latency": lat, "completion": comp, "rubber_stamp": rs, "flat_receipts": fr},
    }


def _load_thresholds():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text()).get("churn_thresholds")
        except Exception:
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    answers = load_answers()
    receipts = json.loads(RECEIPTS.read_text()) if RECEIPTS.exists() else None
    now = datetime.now()
    dash = compute(answers, receipts, now, _load_thresholds())
    dash["computed"] = now.isoformat(timespec="seconds")
    OUT.write_text(json.dumps(dash, ensure_ascii=False, indent=1))
    if not a.quiet:
        icon = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢", "INSUFFICIENT": "⚪"}.get(dash["risk"], "•")
        print(f"{icon} CHURN-RISK: {dash['risk']}")
        if dash.get("reasons"):
            for r in dash["reasons"]:
                print(f"   • {r}")
        if dash["risk"] != "INSUFFICIENT":
            s = dash["signals"]
            print(f"   taps={dash['n_taps']} sessions={dash['n_sessions']} silent={dash['days_silent']}d")
            print(f"   latency={s['latency'].get('trend')} completion={s['completion'].get('ratio')} "
                  f"rubber_stamp={s['rubber_stamp'].get('flag')} flat_receipts={s['flat_receipts'].get('flag')}")
        print(f"   → {OUT}")


if __name__ == "__main__":
    main()
