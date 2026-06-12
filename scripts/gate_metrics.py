#!/usr/bin/env python3
"""GATE METRICS (B026, June 12 — RABIE's pick).
Mohamed's attention is the scarcest resource; the 60-second law was a promise,
never a measurement. This reads his real portal answers, groups them into
sessions (30min gap = new session), and reports seconds-per-verdict and
session shapes. Numbers never feelings — the ADHD contract, instrumented.

Usage: python3 scripts/gate_metrics.py
"""
import datetime, json, statistics
from pathlib import Path

BASE = Path(__file__).parent.parent
SESSION_GAP_MIN = 30


def sessions():
    f = BASE / "data/mohamed_answers.jsonl"
    if not f.exists():
        return []
    answers = []
    for l in f.read_text().strip().split("\n"):
        try:
            e = json.loads(l)
            e["_t"] = datetime.datetime.fromisoformat(e["ts"])
            answers.append(e)
        except Exception:
            continue
    answers.sort(key=lambda e: e["_t"])
    out, cur = [], []
    for e in answers:
        if cur and (e["_t"] - cur[-1]["_t"]).total_seconds() > SESSION_GAP_MIN * 60:
            out.append(cur)
            cur = []
        cur.append(e)
    if cur:
        out.append(cur)
    return out


def main():
    ss = sessions()
    if not ss:
        print("no answers yet — metrics wait for real taps (honest zero)")
        return
    report = []
    for s in ss:
        gaps = [(b["_t"] - a["_t"]).total_seconds() for a, b in zip(s, s[1:])]
        report.append({
            "start": s[0]["ts"], "verdicts": len(s),
            "duration_min": round((s[-1]["_t"] - s[0]["_t"]).total_seconds() / 60, 1),
            "median_sec_per_verdict": round(statistics.median(gaps), 1) if gaps else None,
            "max_gap_sec": round(max(gaps), 1) if gaps else None,
        })
        r = report[-1]
        law = ("✅ inside the 60-sec law" if r["median_sec_per_verdict"] and r["median_sec_per_verdict"] <= 60
               else "🔴 over 60 sec/verdict" if r["median_sec_per_verdict"] else "single tap")
        print(f"  session {r['start'][:16]}: {r['verdicts']} verdicts · {r['duration_min']} min "
              f"· median {r['median_sec_per_verdict']}s/verdict · {law}")
    out = BASE / "data/gate_metrics.json"
    out.write_text(json.dumps({"computed": datetime.datetime.now().isoformat(timespec="seconds"),
                                 "sessions": report}, ensure_ascii=False, indent=1))
    q = json.loads((BASE / "data/decision_queue.json").read_text())
    open_n = len([i for i in q.get("items", []) if i.get("status") == "open"])
    print(f"\n  open cards now: {open_n} · total sessions measured: {len(report)} → data/gate_metrics.json")


if __name__ == "__main__":
    main()
