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
import json, sys, hashlib
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


def held_out_live(pairs, prefs):
    """HONEST live-pick generalization (June 17). The public held_out_agreement_pct mixes the 30
    rescued seed pairs (rating-5 vs rating-0 — TRIVIALLY separable) with his real pilot picks; the
    md5 split lets the rescued pairs carry the number to ~100% while every live pick is silently
    DROPPED (each live caption is seen once → no strength when held out → excluded). That 100% is a
    number that lies (Rule #9). This measures ONLY what we care about: hold out ONE of his live
    pairwise picks, does BT trained on everything else rank his chosen caption above the rejected
    one? Leave-one-out (tiny N). Returns (pct, n_testable). n_testable==0 while the pilot pairs are
    DISCONNECTED is the TRUTH — not a 100%. It rises only when the sampler reuses captions so the
    comparison graph connects."""
    live_idx = [i for i, p in enumerate(prefs) if p.get("source") != "seed_from_ratings"]
    agree = total = 0
    for held in live_idx:
        train = [pairs[i] for i in range(len(pairs)) if i != held]
        ids, pi = bradley_terry(train)
        strength = {ids[m]: pi[m] for m in range(len(ids))}
        w, l = pairs[held]
        if w in strength and l in strength and strength[w] != strength[l]:
            total += 1
            agree += strength[w] > strength[l]
    return (round(agree / total * 100) if total else None), total


def _emoji(s):
    return any(ord(ch) > 0x1F000 for ch in s)


def feedback_for(prefs):
    """HONEST instant-tap feedback at low N (June 16). Names a within-pair SURFACE trait the latest
    pick showed + how consistently his picks lean that way — pure counts, no LLM. Deliberately does
    NOT claim 'the model agrees N%' (degenerate at ~6 picks) nor a brain lean (brain='?' on card
    pairs) — those would overclaim (Rule #9). Its only job: make the tap feel like it landed."""
    live = [p for p in prefs if p.get("source") != "seed_from_ratings"]
    if not live:
        return "First pick logged ✓ — the model's starting to learn your eye."
    n = len(live)
    last = live[-1]
    w, l = last.get("winner_caption", ""), last.get("loser_caption", "")
    tail = "logged"
    if len(w) < len(l):
        shorter = sum(1 for p in live if len(p.get("winner_caption", "")) < len(p.get("loser_caption", "")))
        tail = f"you picked the shorter one ({shorter}/{n} of your picks lean short)"
    elif len(w) > len(l):
        longer = sum(1 for p in live if len(p.get("winner_caption", "")) > len(p.get("loser_caption", "")))
        tail = f"you picked the richer one ({longer}/{n} lean longer)"
    elif ("؟" in w or "?" in w) and not ("؟" in l or "?" in l):
        tail = "you went with the one that asks a question"
    elif _emoji(w) != _emoji(l):
        tail = "you picked the one " + ("with" if _emoji(w) else "without") + " an emoji"
    return f"Pick #{n} ✓ — {tail}. The model's learning your eye."


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
    # STABLE shuffle: Python's hash() is per-process randomized (PYTHONHASHSEED), so the old
    # `hash(...)` split was non-reproducible — the held-out number flipped run-to-run (Rule #9: a
    # number that lies). md5 is stable across processes, so the split + the agreement % are now fixed.
    order.sort(key=lambda i: int(hashlib.md5(prefs[i]["winner_caption"].encode()).hexdigest(), 16))
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
    # HONEST live-only number (June 17): the mixed `held` above rides on the rescued seed pairs and
    # drops every live pick — see held_out_live's docstring. This is the only one we may quote as
    # "his agreement", and it is undefined (0 testable) until the pilot comparison graph connects.
    held_live, held_live_n = held_out_live(pairs, prefs)

    # full ranking
    ids, pi = bradley_terry(pairs)
    ranked = sorted(((id2cap[ids[m]], float(pi[m])) for m in range(len(ids))), key=lambda x: -x[1])
    live = [p for p in prefs if p.get("source") != "seed_from_ratings"]
    # active-pick signal (Step 5a, June 16): per-caption strength + comparison DEGREE, keyed by the
    # FULL caption so the selector can look them up. Purely additive — no existing consumer breaks.
    from collections import Counter
    deg = Counter()
    for p in prefs:
        deg[p["winner_caption"]] += 1
        deg[p["loser_caption"]] += 1
    strengths = {id2cap[ids[m]]: round(float(pi[m]), 5) for m in range(len(ids))}
    # HONEST LIVE-vs-SIM SEPARATION (F2, June 21). Three numbers, never conflated:
    #   • held_out_agreement_pct  — the MIXED leave-out-20% number. Rides on the 30 rescued seed
    #     pairs (rating-5 vs rating-0, trivially separable) → it inflates to ~100% while every live
    #     pick is dropped. It is a SIMULATION artifact, NOT his eye — degenerate==True flags exactly
    #     that. NEVER quote it as "his agreement" (Rule #9).
    #   • held_out_live_pct       — the ONLY number that is his LIVE eye: leave-one-out over his real
    #     pilot picks. None / 0-testable until the comparison graph connects (the bridge taps).
    #   • live_n / held_out_live_n_testable — how many of his live picks exist vs how many are
    #     actually held-out-testable. testable==0 with live_n>0 is the SINGLETON truth, said plainly.
    out = {"n_pairs": len(prefs), "n_live_picks": len(live), "n_rescued": len(prefs) - len(live),
           "live_n": len(live),                       # explicit alias the verifier/readers key on
           "held_out_agreement_pct": held,            # MIXED/SIM — never "his agreement" (Rule #9)
           "held_out_agreement_is_simulation": True,  # this number is ALWAYS sim, by construction
           "held_out_agreement_degenerate": held_live_n == 0,
           "held_out_live_pct": held_live,            # his LIVE eye (None until graph connects)
           "held_out_live_n_testable": held_live_n,
           # ONE honest, machine-readable verdict so no reader can mistake sim for live:
           "live_validated": bool(held_live_n) and held_live is not None,
           "honesty": ("LIVE eye UNTESTED — held_out_live_n_testable=0; the mixed "
                       f"{held}% is simulation on rescued seeds, NOT his eye (Rule #9)"
                       if not held_live_n else
                       f"LIVE eye testable on {held_live_n} pick(s): {held_live}% (random=50%)"),
           "last_pick_feedback": feedback_for(prefs),
           "top5_he_likes": [c[:70] for c, _ in ranked[:5]],
           "bottom5_he_rejects": [c[:70] for c, _ in ranked[-5:]],
           "strengths": strengths,
           "n_comparisons": {c: deg[c] for c in strengths}}
    # GUARD (Rule #9): if his live eye is untested, live_validated MUST be False — a degenerate/sim
    # number can never flip the validated flag true. This is the assertion the shadow→live gate trusts.
    assert not (out["live_validated"] and out["held_out_agreement_degenerate"]), \
        "taste_elo: live_validated true while held-out LIVE is degenerate — a sim number leaked as live"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"TASTE-ELO: {len(prefs)} pairs ({len(live)} live picks + {out['n_rescued']} rescued)")
    if held_live_n:
        print(f"  held-out LIVE agreement: {held_live}%  ({held_live_n} of his picks testable · random=50%)")
    else:
        print(f"  held-out LIVE agreement: UNDEFINED — 0 of {len(live)} live picks testable "
              f"(pilot pairs are disconnected; the {held}% mixed number rides on rescued seeds, not his eye)")
    if live:
        print(f"  top he likes: {ranked[0][0][:60]}")
    else:
        print("  (baseline on rescued ratings only — the real number needs his 17 pilot picks)")


if __name__ == "__main__":
    main()
