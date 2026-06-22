#!/usr/bin/env python3
"""UNIT-ECONOMICS TREND LINES (B097, RABIE's pick — June 22 2026).

THE TOP this serves: the creation system must get BETTER at Mohamed's taste over time —
measurably needing FEWER questions per new client and hardening a HIGHER count of sector
priors. You cannot see a falling curve you never started recording. This plants the
append-only baseline stake and reads the direction once >=2 real points exist.

Two tracked trend lines (Mohamed's law, expressed as required directions):
  - avg_questions_per_client  -> MUST FALL  (the system learns to ask less)
  - net_sector_priors         -> MUST RISE  (more brand patterns harden into priors)

Honesty (no fabricated trend): with <2 recorded points the direction is "baseline" —
neutral, never an alarm. Direction is asserted ONLY across real recorded history.

Rule #6 (consumer same cycle): trend_health() is consumed by unit_economics.py's report
(which week_receipt.py already reads) — the writer is never shipped severed from a reader.

Zero-LLM, pure counting + static history. Usage: python3 scripts/unit_economics_trends.py
"""
from __future__ import annotations
import glob
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TREND_LOG_REL = ("logs", "unit_economics", "trends.jsonl")


def _trend_log(base: Path) -> Path:
    return base.joinpath(*TREND_LOG_REL)


def _load(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _count_questions(path) -> int:
    """Outbound questions asked of a client (the cost we want to fall)."""
    d = _load(path)
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        return sum(len(v) for v in d.values() if isinstance(v, list))
    return 0


def collect_snapshot(base: Path = BASE) -> dict:
    """Current point on each trend line — REAL counts, never guessed."""
    qpc = {}
    pattern = str(base / "clients" / "*" / "presentations" / "outbound_questions.json")
    for f in sorted(glob.glob(pattern)):
        client = Path(f).parent.parent.name
        qpc[client] = _count_questions(f)
    avg_q = round(sum(qpc.values()) / len(qpc), 2) if qpc else None

    drafts = _load(base / "data" / "sector_prior_drafts.json")
    n_drafts = drafts.get("n_drafts", 0) if isinstance(drafts, dict) else 0
    demotions = _load(base / "data" / "prior_demotions.json")
    n_demotions = demotions.get("n_demotions", 0) if isinstance(demotions, dict) else 0

    return {
        "avg_questions_per_client": avg_q,
        "questions_per_client": qpc,
        "n_sector_prior_drafts": n_drafts,
        "n_sector_prior_demotions": n_demotions,
        # net priors hardened = drafts that survived demotion. Degenerate 0 is honest,
        # never inflated (Rule #9). Rises only as real patterns promote (human-gated).
        "net_sector_priors": n_drafts - n_demotions,
    }


def read_series(base: Path = BASE) -> list:
    log = _trend_log(base)
    if not log.exists():
        return []
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def append_snapshot(snapshot: dict, ts: str, base: Path = BASE) -> dict:
    """Append one dated point to the append-only series. ts is INJECTED (deterministic, testable)."""
    log = _trend_log(base)
    log.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": ts, **snapshot}
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def _direction(series: list, key: str, want: str):
    """want in {'fall','rise'}. Returns (verdict, first, last).
    verdict: 'baseline' (<2 numeric points) | 'flat' | 'improving' | 'regressing'."""
    vals = [s[key] for s in series if isinstance(s.get(key), (int, float))]
    if len(vals) < 2:
        last = vals[-1] if vals else None
        return ("baseline", last, last)
    first, last = vals[0], vals[-1]
    if last == first:
        verdict = "flat"
    elif (want == "fall" and last < first) or (want == "rise" and last > first):
        verdict = "improving"
    else:
        verdict = "regressing"
    return (verdict, first, last)


def trend_health(series=None, base: Path = BASE) -> dict:
    """Rule #6 consumer-facing summary. Reads the recorded series, returns per-line direction.
    Never alarms on a single baseline point."""
    if series is None:
        series = read_series(base)
    q_v, q_first, q_last = _direction(series, "avg_questions_per_client", "fall")
    pr_v, pr_first, pr_last = _direction(series, "net_sector_priors", "rise")
    regressing = [name for name, v in
                  (("questions_per_client", q_v), ("sector_prior_hit_rate", pr_v))
                  if v == "regressing"]
    return {
        "n_points": len(series),
        "questions_per_client": {"want": "fall", "verdict": q_v, "first": q_first, "last": q_last},
        "sector_prior_hit_rate": {"want": "rise", "verdict": pr_v, "first": pr_first, "last": pr_last},
        "regressing": regressing,
        "status": "BASELINE" if len(series) < 2 else ("REGRESSING" if regressing else "HEALTHY"),
    }


def record_if_changed(base: Path = BASE, ts: str | None = None) -> dict:
    """Plant a new point ONLY when the snapshot differs from the last recorded one.
    Self-deduping so any consumer can call it every cycle without bloating the series
    with identical points. This is what keeps the series GROWING (RABIE B097 #3) — the
    recorder needs a trigger, and the existing money-report consumer is it.
    Returns {'recorded': bool, 'snapshot': ..., 'reason': ...}."""
    if ts is None:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap = collect_snapshot(base)
    series = read_series(base)
    last = series[-1] if series else None
    same = bool(last) and {k: last.get(k) for k in snap} == snap
    if same:
        return {"recorded": False, "snapshot": snap, "reason": "unchanged"}
    append_snapshot(snap, ts, base)
    return {"recorded": True, "snapshot": snap, "reason": "first point" if last is None else "changed"}


def main():
    res = record_if_changed()
    snap = res["snapshot"]
    series = read_series()
    same = not res["recorded"]
    health = trend_health(series)
    print(f"  avg questions/client: {snap['avg_questions_per_client']}  (want down)")
    print(f"  net sector priors:    {snap['net_sector_priors']}  (want up)")
    print(f"  recorded points: {health['n_points']}  · status: {health['status']}")
    if same:
        print("  (snapshot unchanged — no duplicate point appended)")
    if health["regressing"]:
        print(f"  🔴 REGRESSING: {', '.join(health['regressing'])}")
    return health


if __name__ == "__main__":
    main()
