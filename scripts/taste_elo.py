#!/usr/bin/env python3
"""TASTE-ELO — the model-free consumer the pairwise loop was missing (Step 1 of the 2026-06-15
architecture strategy; replaces the broken 47% averaged absolute scorer with Mohamed's OWN signal).
Bradley-Terry (minorization-maximization, pure numpy — no choix/GPU/LLM/key) over his A-vs-B picks
in pairwise_prefs.jsonl → a per-caption "Mohamed-Elo" (his taste, ranked) + a held-out agreement
number (does the Elo rank his held-out winner above the loser? random=50%).

Runs on the heartbeat after each tap (wired into apply_rulings) so the taste signal is always
current. Uses BOTH his rescued past ratings (30 seed pairs) and his fresh pilot picks.
Usage: python3 scripts/taste_elo.py
"""
import json, sys
from pathlib import Path
import numpy as np

B = Path(__file__).parent.parent
PREFS = B / "data/pairwise_prefs.jsonl"
OUT = B / "data/taste_elo.json"


def _prefs():
    if not PREFS.exists():
        return []
    return [json.loads(l) for l in PREFS.read_text().splitlines() if l.strip()]


def bradley_terry(pairs, iters=200, tol=1e-9):
    """pairs: list of (winner_id, loser_id) over integer item ids. Returns strength array (sum=n)."""
    ids = sorted({i for w, l in pairs for i in (w, l)})
    idx = {i: k for k, i in enumerate(ids)}
    n = len(ids)
    if n == 0:
        return ids, np.array([])
    wins = np.zeros(n)
    comp = np.zeros((n, n))   # comp[i,j] = # comparisons between i and j
    for w, l in pairs:
        a, b = idx[w], idx[l]
        wins[a] += 1
        comp[a, b] += 1
        comp[b, a] += 1
    pi = np.ones(n)
    for _ in range(iters):
        prev = pi.copy()
        denom = np.zeros(n)
        for i in range(n):
            for j in range(n):
                if comp[i, j]:
                    denom[i] += comp[i, j] / (pi[i] + pi[j])
        new = np.where(denom > 0, wins / denom, pi)
        new = np.where(new <= 0, 1e-9, new)
        new *= n / new.sum()
        pi = new
        if np.abs(pi - prev).max() < tol:
            break
    return ids, pi


def main():
    prefs = _prefs()
    if not prefs:
        print("no picks yet — nothing to rank"); return
    # map captions → ids
    caps = {}
    def cid(c):
        return caps.setdefault(c, len(caps))
    pairs = [(cid(p["winner_caption"]), cid(p["loser_caption"])) for p in prefs]
    id2cap = {v: k for k, v in caps.items()}

    # held-out agreement (leave-out 20%): does BT trained on the rest rank the held-out winner higher?
    import random as _r
    order = list(range(len(pairs)))
    # deterministic shuffle (no Math.random ban concern — this is python, but keep it stable)
    order.sort(key=lambda i: hash(prefs[i]["winner_caption"]) & 0xffff)
    k = max(1, len(pairs) // 5)
    test, train = order[:k], order[k:]
    agree = total = 0
    if train:
        ids, pi = bradley_terry([pairs[i] for i in train])
        strength = {ids[m]: pi[m] for m in range(len(ids))}
        for i in test:
            w, l = pairs[i]
            if w in strength and l in strength and strength[w] != strength[l]:
                total += 1
                agree += strength[w] > strength[l]
    held = round(agree / total * 100) if total else None

    # full ranking
    ids, pi = bradley_terry(pairs)
    ranked = sorted(((id2cap[ids[m]], float(pi[m])) for m in range(len(ids))), key=lambda x: -x[1])
    live = [p for p in prefs if p.get("source") != "seed_from_ratings"]
    out = {"n_pairs": len(prefs), "n_live_picks": len(live), "n_rescued": len(prefs) - len(live),
           "held_out_agreement_pct": held,
           "top5_he_likes": [c[:70] for c, _ in ranked[:5]],
           "bottom5_he_rejects": [c[:70] for c, _ in ranked[-5:]]}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"TASTE-ELO: {len(prefs)} pairs ({len(live)} live picks + {out['n_rescued']} rescued)")
    print(f"  held-out agreement: {held}%  [random=50% · the broken absolute judge was 47%]")
    if live:
        print(f"  top he likes: {ranked[0][0][:60]}")
    else:
        print("  (baseline on rescued ratings only — the real number needs his 17 pilot picks)")


if __name__ == "__main__":
    main()
