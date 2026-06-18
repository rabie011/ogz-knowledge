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
from pathlib import Path

B = Path(__file__).parent.parent
TASTE = B / "data/taste_elo.json"

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
    """Is the taste signal trustworthy enough to STEER what ships? True only when his live picks
    are testable (graph connected) and the held-out LIVE agreement clears MIN_LIVE_PCT. While the
    bridge taps are still staged this returns False — by design (Rule #9: no unverified number steers
    production)."""
    t = load_taste() if taste is None else taste
    n_testable = t.get("held_out_live_n_testable", 0) or 0
    live_pct = t.get("held_out_live_pct")  # None while degenerate
    if t.get("held_out_agreement_degenerate"):
        return False
    return n_testable >= MIN_TESTABLE and live_pct is not None and live_pct >= MIN_LIVE_PCT


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


def main():
    t = load_taste()
    live = wire_live(t)
    print(f"TASTE→CREATION wire: {'🟢 LIVE — steering selection' if live else '⚪ SHADOW — advisory only'}")
    print(f"  gate: n_testable={t.get('held_out_live_n_testable', 0)} (need >={MIN_TESTABLE}) · "
          f"live_pct={t.get('held_out_live_pct')} (need >={MIN_LIVE_PCT}) · "
          f"degenerate={t.get('held_out_agreement_degenerate')}")
    n = len(t.get("strengths", {}))
    print(f"  reading {n} caption-strengths from taste_elo.json"
          f"{' (write-only no more — Rule #6 reader online)' if n else ' (no picks yet)'}")


if __name__ == "__main__":
    main()
