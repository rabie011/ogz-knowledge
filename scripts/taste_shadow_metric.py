#!/usr/bin/env python3
"""TASTE→CREATION wire — the METRIC READER over the shadow divergence log (B268, Rule #6/#9).

B267 made produce_batch APPEND one divergence record per run to data/taste_shadow_log.jsonl (what
taste WOULD prefer vs the control baseline order). That log was a write-only organ until this
reader — a value written with no consumer is a lie that looks like progress (Rule #6). This module
is the consumer: it reads the log and computes the active-pick-vs-random divergence at the REAL
seam, instead of riding the rescued-seed sim.

THE FLOOR (Rule #9 — verify the number before you say it): a mean over 1-2 runs is noise. This
reader REFUSES to quote any aggregate below FLOOR runs — it returns status INSUFFICIENT and the
caller (make_sure, a report) must NOT print a number. No unverified number reaches Mohamed.

THE CONTROL (B268 — why baseline matters): while the gate is CLOSED, ship order == baseline, so
order_diff = taste-vs-system displacement (a real shadow signal: how much his learned taste
disagrees with the system's content-rule selection). When the gate OPENS, ship BECOMES the taste
order; if we measured advisory-vs-ship it would collapse to 0. shadow_entry now records the
pre-taste baseline as a separate control, so order_diff stays the advisory-vs-baseline displacement
both before and after the flip — the active-vs-random comparison keeps its control.

WHAT THIS DOES *NOT* CLAIM: this is the SHADOW seam. It measures taste-vs-baseline divergence, not
his live held-out agreement. The "~N taps to 90%" claim still awaits his bridge taps landing and the
gate opening (held_out_live_pct in taste_elo.json). This reader builds the measurement now; the live
agreement number is claimed later, from his real eye."""
import json
from pathlib import Path

B = Path(__file__).parent.parent
SHADOW_LOG = B / "data/taste_shadow_log.jsonl"

# Minimum runs before any aggregate may be quoted (Rule #9). Below this the answer is "not enough
# data", never a number.
FLOOR = 5

# A batch needs >= this many items to have any orderable divergence. A 1-item batch CANNOT be
# reordered, so its order_diff is trivially 0 — it carries no measurement. Such rows must not count
# toward FLOOR (they would inflate the gate with noise) nor enter the aggregate (a spurious 0 biases
# active_vs_random_gap toward "taste diverges less than random"). Dropped before counting/averaging
# (Rule #9 — only meaningful measurements reach Mohamed). Found June 22: the live log held an n=1
# row counted as 1 of 2 "distinct runs" toward FLOOR.
MIN_ORDERABLE_N = 2


def load_log(path=SHADOW_LOG):
    """Read the append-only shadow log into a list of records. Missing/empty file → []."""
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            continue  # tolerate a torn last line; never crash the reader on one bad row
    return rows


def _random_expected_diff(n):
    """Expected displaced positions under a uniform-random permutation of n items. The expected
    number of FIXED points of a random permutation is exactly 1 (any n>=1), so expected displaced =
    n - 1. This is the RANDOM control the active signal is compared against."""
    return max(0, n - 1)


def _run_fingerprint(r):
    """The identity of a divergence MEASUREMENT — what makes two runs the SAME observation (Rule #9).

    While the gate is closed and no new taps land, the elo state is frozen, so produce_batch keeps
    selecting the same captions in the same order: every run emits a byte-identical divergence record.
    The persistent orchestra is DESIGNED to accumulate runs, so on its own it would drive the log to
    FLOOR copies of one measurement and trip a false 'measured' number to Mohamed — the exact lie the
    fresh-batch scar warns about. The fingerprint is the content that determines the outcome: the
    permutation indices + n + gate state + order_diff. Deliberately EXCLUDES `built` (the timestamp) —
    folding time in would let the same measurement at two clock ticks count as two runs, reopening the
    hole. Same observation ⇒ same fingerprint ⇒ counts ONCE toward FLOOR."""
    return json.dumps([
        int(r.get("n", 0)),
        bool(r.get("wire_live")),
        r.get("advisory_order_idx"),
        r.get("ship_order_idx"),
        r.get("baseline_order_idx"),
        int(r.get("order_diff", 0)),
    ], sort_keys=True, ensure_ascii=False)


def _distinct_runs(rows):
    """Collapse byte-identical measurements to one. Order-preserving (keeps the first of each)."""
    seen, out = set(), []
    for r in rows:
        fp = _run_fingerprint(r)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(r)
    return out


def compute(rows):
    """Compute the divergence metric from shadow-log rows.

    Returns a dict that ALWAYS carries `status`:
      • INSUFFICIENT — n_runs < FLOOR; no aggregate is quoted (Rule #9). The caller must not print a
        mean. Carries n_runs/floor only.
      • OK           — n_runs >= FLOOR; carries the aggregates below.

    Aggregates (OK only):
      mean_order_diff        — mean positions taste would move vs the control baseline
      mean_random_diff       — mean expected displacement of a random permutation (the control)
      displacement_ratio     — mean(order_diff / random_expected); ~1.0 ⇒ taste scatters like random
                               vs baseline, ~0.0 ⇒ taste tracks the baseline. Lower = taste carries
                               structure the random control does not.
      active_vs_random_gap   — mean_random_diff - mean_order_diff; positive ⇒ taste diverges LESS than
                               random (it is doing something non-trivial relative to the control).
      gate_open_runs         — runs recorded after the gate flipped (independent control present).
                               While 0, the baseline == ship for every run and the number is a
                               PRELIMINARY shadow read, flagged so it is never quoted as the live one.

    FLOOR counts DISTINCT measurements, never raw rows (Rule #9). Byte-identical records — what a
    frozen elo state emits run after run — collapse to one before the FLOOR check, so an inflated log
    (5 copies of one observation) reads INSUFFICIENT, not OK. `n_rows`/`n_duplicates` are surfaced so
    a thin-but-padded log can't hide as a rich one.
    """
    n_rows = len(rows)
    # Drop non-orderable batches (n < 2) BEFORE counting/averaging — they carry no divergence signal
    # and would inflate FLOOR + bias the aggregate (Rule #9; see MIN_ORDERABLE_N).
    orderable = [r for r in rows if int(r.get("n", 0)) >= MIN_ORDERABLE_N]
    n_degenerate = n_rows - len(orderable)
    rows = _distinct_runs(orderable)          # collapse repeated identical measurements (Rule #9)
    n_runs = len(rows)
    out = {"n_runs": n_runs, "n_rows": n_rows, "n_degenerate": n_degenerate,
           "n_duplicates": len(orderable) - n_runs, "floor": FLOOR, "log": str(SHADOW_LOG)}
    if n_runs < FLOOR:
        out["status"] = "INSUFFICIENT"
        parts = []
        if out["n_duplicates"]:
            parts.append(f"{out['n_duplicates']} duplicate")
        if n_degenerate:
            parts.append(f"{n_degenerate} degenerate n<{MIN_ORDERABLE_N}")
        extra = f" ({n_rows} rows: {', '.join(parts)})" if parts else ""
        out["reason"] = (f"n_runs={n_runs} < FLOOR={FLOOR}{extra} — refusing to quote an aggregate "
                         f"(Rule #9; FLOOR counts DISTINCT ORDERABLE measurements, not raw rows)")
        return out

    diffs = [int(r.get("order_diff", 0)) for r in rows]
    ns = [int(r.get("n", 0)) for r in rows]
    rand = [_random_expected_diff(n) for n in ns]
    # per-run normalized displacement (guard the n==1 / random==0 degenerate run)
    ratios = [d / rnd for d, rnd in zip(diffs, rand) if rnd > 0]
    gate_open = sum(1 for r in rows if r.get("wire_live"))

    out["status"] = "OK"
    out["mean_order_diff"] = round(sum(diffs) / n_runs, 3)
    out["mean_random_diff"] = round(sum(rand) / n_runs, 3)
    out["displacement_ratio"] = round(sum(ratios) / len(ratios), 3) if ratios else None
    out["active_vs_random_gap"] = round((sum(rand) - sum(diffs)) / n_runs, 3)
    out["gate_open_runs"] = gate_open
    out["control_independent"] = gate_open > 0  # baseline != ship only after the gate flips
    out["note"] = ("SHADOW divergence vs the system baseline — NOT his live held-out agreement; the "
                   "'~N taps to 90%' claim awaits his bridge taps + gate-open (Rule #9).")
    if gate_open == 0:
        out["preliminary"] = ("all runs gate-closed → baseline==ship; divergence reads how much his "
                              "learned taste disagrees with the system's selection, not an "
                              "independent active-vs-random control yet")
    return out


def metric(path=SHADOW_LOG):
    """Top-level: read the log and compute. The single entry point for callers (make_sure, reports)."""
    return compute(load_log(path))


def main():
    m = metric()
    print(f"TASTE SHADOW METRIC — {m['log']}")
    if m["status"] == "INSUFFICIENT":
        print(f"  ⚪ INSUFFICIENT: {m['reason']}")
        print(f"  (need >= {m['floor']} DISTINCT produce-batch runs logged before any number is quoted)")
        return
    dup = f", {m['n_duplicates']} duplicate collapsed" if m.get("n_duplicates") else ""
    print(f"  runs={m['n_runs']} distinct of {m['n_rows']} rows{dup} "
          f"(gate-open={m['gate_open_runs']}, control_independent={m['control_independent']})")
    print(f"  mean_order_diff={m['mean_order_diff']}  vs  mean_random_diff={m['mean_random_diff']}")
    print(f"  displacement_ratio={m['displacement_ratio']}  active_vs_random_gap={m['active_vs_random_gap']}")
    if m.get("preliminary"):
        print(f"  ⚠ PRELIMINARY — {m['preliminary']}")
    print(f"  note: {m['note']}")


if __name__ == "__main__":
    main()
