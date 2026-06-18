#!/usr/bin/env python3
"""TASTE-SIM — the MEASUREMENT the elo→creation wire was missing (June 18).

The claim "~5 active taps ≈ 15 random taps" lives UNMEASURED inside active_pairs()/bridge_pairs()
docstrings. Rule #9 forbids quoting a number we have not eyeballed. His LIVE held-out is degenerate
(taste_elo.held_out_live_n_testable == 0 while the pilot graph is disconnected — 16 bridge/active
taps still pending on his portal), so we CANNOT measure the active advantage on his live picks yet.

What we CAN measure honestly: his OWN rescued past ratings (pairwise_prefs seed_from_ratings, each
carrying his_rating_winner/loser 0-5) form a real per-caption ORACLE. We replay the loop offline:
start from zero comparisons, repeatedly select a same-brand pair (ACTIVE = the real active_pairs
information-gain rule, run live on the evolving BT estimate; RANDOM = uniform), let the oracle pick
the winner, re-fit Bradley-Terry, and measure how fast the estimate's ranking agrees with the full
oracle ranking. taps-to-threshold for ACTIVE vs RANDOM is the honest number.

HARD HONESTY (Rule #9): this is a SIMULATION on his rescued ratings — NOT his live pilot-pick
convergence. It answers "is the active+bridge selection rule worth his taps on a known-separable
case?" If active does not beat random HERE, it will not on his harder live eye. It is a screen that
runs BEFORE we spend his attention, never a substitute for the live measurement that waits on his
16 pending taps. Quote it ONLY as "simulation on rescued ratings", never as "Mohamed agreement".

Pure numpy, zero-LLM, deterministic (seeded). Usage: python3 scripts/taste_sim.py
"""
import json
from pathlib import Path
import numpy as np

from taste_elo import bradley_terry

B = Path(__file__).parent.parent
PREFS = B / "data/pairwise_prefs.jsonl"
OUT = B / "data/taste_sim.json"


# his rescued ratings are ordinal LABELS, not numbers (excellent/good/weak/fail). Map to a scale.
RATING_SCALE = {"fail": 0.0, "weak": 1.0, "good": 2.0, "excellent": 3.0}


def _to_score(r):
    if r is None:
        return None
    if isinstance(r, (int, float)):
        return float(r)
    return RATING_SCALE.get(str(r).strip().lower())


def oracle_from_seeds():
    """his rescued ratings → {caption: mean his_rating}, grouped by brand. Only captions whose
    oracle strength we actually know (a real rating he gave) enter the universe."""
    if not PREFS.exists():
        return {}, {}
    ratings, brand = {}, {}
    for line in PREFS.read_text().splitlines():
        if not line.strip():
            continue
        p = json.loads(line)
        if p.get("source") != "seed_from_ratings":
            continue
        for side in ("winner", "loser"):
            cap = p.get(f"{side}_caption", "")
            s = _to_score(p.get(f"his_rating_{side}"))
            if cap and s is not None:
                ratings.setdefault(cap, []).append(s)
                brand[cap] = p.get("handle", "?")
    oracle = {c: sum(v) / len(v) for c, v in ratings.items()}
    return oracle, brand


def candidate_pairs(oracle, brand):
    """all same-brand caption pairs the oracle can decide (different ratings)."""
    by_b = {}
    for c, b in brand.items():
        by_b.setdefault(b, []).append(c)
    pairs = []
    for b, caps in by_b.items():
        for i in range(len(caps)):
            for j in range(i + 1, len(caps)):
                a, c = caps[i], caps[j]
                if oracle[a] != oracle[c]:
                    pairs.append((a, c))
    return pairs


def _agreement(strength, eval_pairs, oracle):
    """over ALL the oracle's decidable pairs, how often does the current BT estimate rank the
    oracle-winner above the oracle-loser? Captions not yet compared get NEUTRAL strength (1.0),
    so a pair touching an unseen caption is a coin-flip (0.5 credit) the model only earns by
    actually comparing — this is why the curve must rise from ~50% as coverage grows, instead of
    trivially hitting 100% on the 1 pair seen so far. random baseline == 50%."""
    score = 0.0
    for a, b in eval_pairs:
        hi, lo = (a, b) if oracle[a] > oracle[b] else (b, a)
        shi, slo = strength.get(hi, 1.0), strength.get(lo, 1.0)
        if shi == slo:
            score += 0.5  # indistinguishable (both unseen, or genuinely tied) → coin-flip
        else:
            score += 1.0 if shi > slo else 0.0
    return score / len(eval_pairs) if eval_pairs else 0.0


def _active_score(a, b, strength, degree, w_close=0.5, w_conn=0.5):
    """the SAME information-gain rule as pairwise.active_pairs: close-strength (hard
    discrimination) + low comparison degree (connect the graph)."""
    sa, sb = strength.get(a, 1.0), strength.get(b, 1.0)
    close = 1.0 / (1.0 + abs(sa - sb))
    conn = 1.0 / (1.0 + degree.get(a, 0)) + 1.0 / (1.0 + degree.get(b, 0))
    return w_close * close + w_conn * conn


def _run(strategy, cand, oracle, rng, max_taps):
    """replay the loop under one selection strategy → agreement curve (index k = after k taps)."""
    remaining = list(cand)
    asked, degree = [], {}
    curve = []
    while remaining and len(asked) < max_taps:
        ids, pi = bradley_terry(asked) if asked else ([], np.array([]))
        strength = {ids[m]: pi[m] for m in range(len(ids))}
        if strategy == "active":
            pick = max(remaining, key=lambda p: _active_score(p[0], p[1], strength, degree))
        else:  # random
            pick = remaining[int(rng.integers(len(remaining)))]
        remaining.remove(pick)
        a, b = pick
        winner, loser = (a, b) if oracle[a] > oracle[b] else (b, a)
        asked.append((winner, loser))
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
        ids, pi = bradley_terry(asked)
        strength = {ids[m]: pi[m] for m in range(len(ids))}
        curve.append(_agreement(strength, cand, oracle))
    return curve


def _taps_to(curve, thr):
    for k, v in enumerate(curve, 1):
        if v >= thr:
            return k
    return None


def simulate(threshold=0.9, random_trials=20, max_taps=None, seed=42):
    oracle, brand = oracle_from_seeds()
    cand = candidate_pairs(oracle, brand)
    if not cand:
        return {"ok": False, "reason": "no decidable oracle pairs"}
    if max_taps is None:
        max_taps = len(cand)
    rng = np.random.default_rng(seed)
    active_curve = _run("active", cand, oracle, rng, max_taps)
    # random is stochastic → average taps-to-threshold over several seeded trials
    rnd_taps, rnd_curves = [], []
    for t in range(random_trials):
        rc = _run("random", cand, oracle, np.random.default_rng(seed + 1 + t), max_taps)
        rnd_curves.append(rc)
        k = _taps_to(rc, threshold)
        rnd_taps.append(k if k is not None else max_taps)
    a_taps = _taps_to(active_curve, threshold)
    a_taps = a_taps if a_taps is not None else max_taps
    r_mean = sum(rnd_taps) / len(rnd_taps)
    return {
        "ok": True,
        "oracle_captions": len(oracle),
        "decidable_pairs": len(cand),
        "threshold": threshold,
        "active_taps_to_threshold": a_taps,
        "random_taps_to_threshold_mean": round(r_mean, 2),
        "speedup_x": round(r_mean / a_taps, 2) if a_taps else None,
        "active_curve": [round(v, 3) for v in active_curve],
        "note": "SIMULATION on his rescued ratings (seed_from_ratings) — NOT live pilot-pick "
                "convergence. Honest screen for the selection rule; the live number waits on his "
                "pending portal taps. Quote as 'simulation', never as 'Mohamed agreement' (Rule #9).",
    }


def main():
    res = simulate()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    if not res.get("ok"):
        print("TASTE-SIM: cannot run —", res.get("reason"))
        return
    print("TASTE-SIM (simulation on his rescued ratings — NOT his live eye):")
    print(f"  oracle captions: {res['oracle_captions']} | decidable same-brand pairs: {res['decidable_pairs']}")
    print(f"  target agreement: {int(res['threshold']*100)}%")
    print(f"  ACTIVE taps-to-target: {res['active_taps_to_threshold']}")
    print(f"  RANDOM taps-to-target (mean of trials): {res['random_taps_to_threshold_mean']}")
    sx = res["speedup_x"]
    print(f"  → active speedup: {sx}× fewer taps" if sx else "  → no speedup measurable")
    print(f"  honest: live convergence still 0-testable until his pending bridge taps land.")


if __name__ == "__main__":
    main()
