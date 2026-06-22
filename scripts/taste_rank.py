#!/usr/bin/env python3
"""TASTE → CREATION wire, the READER for taste_elo's write-only organ (Rule #6, June 18).

taste_elo.py writes per-caption `strengths` (Bradley-Terry, learned from Mohamed's live pairwise
picks) but NOTHING read them — every producer (produce_batch, build_judging_batch, batch20,
render_client_slot, judge_batch) had 0 references. A value written with no reader is a lie that
looks like progress. This module is that missing reader: it ranks a producer's candidate captions
by his learned taste-strength.

THE GATE (honest staged maturity + Rule #8 refuse-don't-warn + Rule #9 verify-the-number):
the strengths from his 12 live picks are NOT YET TRUSTWORTHY — the held-out LIVE test is UNDEFINED
(held_out_live_n_testable == 0; the pilot comparison graph is disconnected, the bridge taps that
connect it are still staged on his portal). Wiring an unvalidated signal into what ships would
amplify noise into Mohamed's eye and break Rule #12/#13 (the system produces proven work).

So the wire is built but GATED. `wire_live()` opens ONLY when his picks are testable AND the elo
beats random by a real margin. Below the gate, `select()` returns candidates UNCHANGED and attaches
the ranking as ADVISORY metadata only — it does not influence order. It does not silently pass
noise (Rule #8): the influence path is closed, not whispering. When his bridge taps land and the
held-out number proves out, the gate flips and the same code path goes live — no rewrite."""
import json
import time
from pathlib import Path

B = Path(__file__).parent.parent
TASTE = B / "data/taste_elo.json"
SHADOW_LOG = B / "data/taste_shadow_log.jsonl"

# Gate thresholds: his live picks must be measurable (graph connected) AND the elo must rank his
# held-out chosen caption above the rejected one meaningfully better than a coin (random = 50%).
MIN_TESTABLE = 5      # at least 5 of his live picks held-out-testable (graph connected enough)
MIN_LIVE_PCT = 60     # held-out LIVE agreement >= 60% (a real margin over the 50% coin)


def load_taste(path=TASTE):
    """Read taste_elo's output. Returns {} if it hasn't been computed yet (no picks)."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def wire_live(taste=None):
    """Is the taste signal trustworthy enough to STEER what ships? THE ONE computed gate (F3): it
    fires shadow→live ONLY when his live picks are held-out-testable (graph connected) AND the
    held-out LIVE agreement clears MIN_LIVE_PCT (a real margin over the 50% coin). While the bridge
    taps are still staged this returns False — by design (Rule #9: no unverified number steers
    production). The moment held_out_live proves out, this same predicate flips true and the producer
    reorders with no code change.

    It also honors taste_elo's single honest verdict (F2): if `live_validated` is present it must be
    True — a degenerate/simulation number can never open the gate even if the raw fields look close.
    Refuses any non-numeric live_pct rather than truthy-coercing it (Rule #8/#9)."""
    t = load_taste() if taste is None else taste
    if t.get("held_out_agreement_degenerate"):
        return False                                       # sim-only number — never steers (Rule #9)
    if "live_validated" in t and not t.get("live_validated"):
        return False                                       # taste_elo itself says: not his eye yet
    n_testable = t.get("held_out_live_n_testable", 0) or 0
    live_pct = t.get("held_out_live_pct")                  # None while degenerate
    if not isinstance(live_pct, (int, float)):
        return False
    return n_testable >= MIN_TESTABLE and live_pct >= MIN_LIVE_PCT


def gate_status(taste=None):
    """HONEST one-call report of the shadow→live gate (F3) — the ONE place the promotion condition is
    named, so the verifier and make_sure read the same truth. Returns a typed dict: whether the wire
    is live now, the exact thresholds, the current measured values, and the human-readable reason it
    is (or is not) firing. Never fabricates a number — live_pct stays None until his eye is testable."""
    t = load_taste() if taste is None else taste
    live = wire_live(t)
    n_testable = t.get("held_out_live_n_testable", 0) or 0
    live_pct = t.get("held_out_live_pct")
    if live:
        reason = f"LIVE — n_testable={n_testable}>={MIN_TESTABLE} and live_pct={live_pct}>={MIN_LIVE_PCT}"
    elif t.get("held_out_agreement_degenerate") or ("live_validated" in t and not t.get("live_validated")):
        reason = ("SHADOW — his live eye is UNTESTED (held_out_live_n_testable=0; the model is not "
                  "validated). The bridge taps that connect his graph are still pending (Rule #9).")
    elif n_testable < MIN_TESTABLE:
        reason = f"SHADOW — only {n_testable}/{MIN_TESTABLE} live picks held-out-testable"
    else:
        reason = f"SHADOW — live_pct={live_pct} below the {MIN_LIVE_PCT}% margin over the coin"
    return {"wire_live": live, "min_testable": MIN_TESTABLE, "min_live_pct": MIN_LIVE_PCT,
            "n_testable": n_testable, "live_pct": live_pct,
            "degenerate": bool(t.get("held_out_agreement_degenerate")),
            "live_validated": t.get("live_validated"), "reason": reason}


def rank_candidates(captions, taste=None):
    """Rank candidate captions by his learned taste-strength. ADVISORY — pure ranking, no gating
    decision here. A caption the elo has never seen gets strength=None (unknown, not zero) and sorts
    after all known captions, stably. Returns a list of dicts in ranked order."""
    t = load_taste() if taste is None else taste
    strengths = t.get("strengths", {})
    ncmp = t.get("n_comparisons", {})
    rows = []
    for i, c in enumerate(captions):
        s = strengths.get(c)            # exact full-caption match (the key taste_elo writes)
        rows.append({"caption": c, "strength": s,
                     "n_comparisons": ncmp.get(c, 0), "orig_index": i})
    # known strengths first (desc); unknown (None) last, preserving original order (stable)
    rows.sort(key=lambda r: (r["strength"] is None, -(r["strength"] or 0.0), r["orig_index"]))
    for rank, r in enumerate(rows):
        r["rank"] = rank
    return rows


def select(captions, taste=None):
    """The producer-facing entry point. Returns (ordered_captions, meta).

    GATE OPEN  → captions reordered by his taste-strength (a COMPUTED selection rule — Rule #12: the
                 system selects by rule, never a hand-pick).
    GATE CLOSED→ captions returned in their ORIGINAL order, untouched; the taste ranking rides along
                 in meta['advisory_rank'] for visibility but steers nothing (Rule #8)."""
    t = load_taste() if taste is None else taste
    live = wire_live(t)
    ranked = rank_candidates(captions, t)
    meta = {"wire_live": live,
            "n_testable": t.get("held_out_live_n_testable", 0) or 0,
            "live_pct": t.get("held_out_live_pct"),
            "advisory_rank": [r["caption"] for r in ranked]}
    if live:
        return [r["caption"] for r in ranked], meta
    return list(captions), meta


def _positions_in(ref_caps):
    """Map each caption to its positions in ref_caps (duplicates queued left-to-right)."""
    pos = {}
    for i, c in enumerate(ref_caps):
        pos.setdefault(c, []).append(i)
    return pos


def _index_against(caps, ref_pos):
    """Resolve each caption in `caps` to a position in the reference frame, consuming duplicates
    left-to-right. Missing captions resolve to None."""
    ref_pos = {k: list(v) for k, v in ref_pos.items()}  # don't mutate caller's map
    out = []
    for c in caps:
        slots = ref_pos.get(c)
        out.append(slots.pop(0) if slots else None)
    return out


def shadow_entry(ship_caps, meta, baseline_caps=None, ts=None):
    """Build ONE append-only divergence record for the taste->creation wire (B267/B268, Rule #6/#9).

    The seam writes what taste WOULD prefer (meta['advisory_rank']) next to the CONTROL — the
    system's pre-taste selection order (`baseline_caps`). Everything is measured in the baseline's
    reference frame so the divergence stat keeps a stable control:

      • GATE CLOSED — taste steers nothing, so ship order IS the baseline. baseline_caps defaults to
        ship_caps and `order_diff` = how many positions taste WOULD move from what the system ships.
      • GATE OPEN  — ship order BECOMES the taste order, so ship == advisory and ship-vs-advisory
        would be a degenerate 0. The active-vs-random comparison would lose its control. To prevent
        that (B268), the caller MUST pass the pre-taste selection as `baseline_caps`; `order_diff`
        then stays meaningful = advisory-vs-baseline displacement, the real signal.

    order_diff == 0 means taste agrees with the system's own (pre-taste) pick this run."""
    baseline = list(baseline_caps) if baseline_caps is not None else list(ship_caps)
    advisory = meta.get("advisory_rank") or list(ship_caps)
    base_pos = _positions_in(baseline)
    adv_idx = _index_against(advisory, base_pos)         # advisory in the baseline frame
    ship_idx = _index_against(ship_caps, base_pos)       # what shipped, in the baseline frame
    n = len(baseline)
    order_diff = sum(1 for k, idx in enumerate(adv_idx) if idx != k)
    return {
        "built": ts or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n": n,
        "wire_live": bool(meta.get("wire_live")),
        "n_testable": meta.get("n_testable", 0),
        "live_pct": meta.get("live_pct"),
        "baseline_order_idx": list(range(n)),  # the control: system's pre-taste order, the reference
        "ship_order_idx": ship_idx,            # what actually shipped (== baseline while gate closed)
        "advisory_order_idx": adv_idx,         # what taste would prefer, in the baseline frame
        "order_diff": order_diff,
    }


def append_shadow_log(entry, path=SHADOW_LOG):
    """Append one shadow_entry as a JSONL line (append-only history — Rule #6 consumer).

    REFUSES (Rule #8) to persist an UNORDERABLE measurement (n < MIN_ORDERABLE_N): a batch too
    small to be reordered carries no divergence signal (order_diff is trivially 0) and would inflate
    the wire's distinct-run count with noise — exactly the n=1 row found polluting the live log
    (June 22). The reader (taste_shadow_metric) already drops these defensively; this closes the
    WRITER half so the organ never accumulates meaningless rows in the first place (writer/consumer
    symmetry). MIN_ORDERABLE_N is imported from the reader — ONE source of truth, no duplicate floor.
    The entry is still RETURNED (flagged `logged`) so callers can inspect/print order_diff and n."""
    try:
        from taste_shadow_metric import MIN_ORDERABLE_N
    except ImportError:                                   # ensure scripts/ is importable, then retry
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from taste_shadow_metric import MIN_ORDERABLE_N
    if int(entry.get("n", 0)) < MIN_ORDERABLE_N:          # refuse at the source, not just at read
        return {**entry, "logged": False}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {**entry, "logged": True}


def main():
    t = load_taste()
    g = gate_status(t)
    print(f"TASTE→CREATION wire: {'🟢 LIVE — steering selection' if g['wire_live'] else '⚪ SHADOW — advisory only'}")
    print(f"  gate: n_testable={g['n_testable']} (need >={MIN_TESTABLE}) · "
          f"live_pct={g['live_pct']} (need >={MIN_LIVE_PCT}) · "
          f"degenerate={g['degenerate']} · live_validated={g['live_validated']}")
    print(f"  reason: {g['reason']}")
    n = len(t.get("strengths", {}))
    print(f"  reading {n} caption-strengths from taste_elo.json"
          f"{' (write-only no more — Rule #6 reader online)' if n else ' (no picks yet)'}")


if __name__ == "__main__":
    main()
