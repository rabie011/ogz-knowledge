#!/usr/bin/env python3
"""REAL WINNING FORMULA (June 18) — the honest replacement for build_winning_formula's random enum.
Joins real_engagement_per_obs.json (real likes) to each obs's traits, ranks posts WITHIN each account
(top-quartile-for-that-account = a "winner" — account-size-agnostic, no followers needed, uses all
6,560 obs), then computes per-trait LIFT = P(winner | trait) / P(winner). Output: a trait→lift table
the producer can score generated candidates with. Also reports real-lift vs the old enum (which was
proven ≈ coin-flip). Zero-key, deterministic.
Usage: python3 scripts/build_real_winning_formula.py
"""
import glob, json
from collections import defaultdict
from pathlib import Path

B = Path(__file__).parent.parent
RE = B / "data/real_engagement_per_obs.json"
OUT = B / "data/real_winning_formula.json"
TRAITS = ["occasion", "content_pillar", "emotion_primary", "media_type"]


def main():
    re_ = json.loads(RE.read_text())
    # obs traits keyed by ulid
    traits = {}
    for of in glob.glob(str(B / "11_who_to_learn_from/observations/*/*.json")):
        try:
            o = json.loads(Path(of).read_text())
        except Exception:
            continue
        u = o.get("observation_ulid")
        if u in re_:
            traits[u] = {"occasion": o.get("occasion"), "content_pillar": o.get("content_pillar"),
                         "emotion_primary": o.get("emotion_primary"),
                         "media_type": (o.get("content_ref") or {}).get("content_type")}
    # within-account percentile → winner = top quartile of THAT account's likes
    by_acct = defaultdict(list)
    for u, e in re_.items():
        if isinstance(e.get("likes"), int) and u in traits:
            by_acct[e["handle"]].append((u, e["likes"]))
    winners = set()
    for h, lst in by_acct.items():
        if len(lst) < 4:
            continue
        cut = sorted(l for _, l in lst)[int(len(lst) * 0.75)]
        winners |= {u for u, l in lst if l >= cut}
    scored = [u for h, lst in by_acct.items() if len(lst) >= 4 for u, _ in lst]
    base = len(winners) / len(scored) if scored else 0
    # per-trait-value lift
    lift = {}
    for tr in TRAITS:
        vals = defaultdict(lambda: [0, 0])   # value → [winners, total]
        for u in scored:
            v = traits[u].get(tr)
            if v:
                vals[v][1] += 1
                if u in winners:
                    vals[v][0] += 1
        lift[tr] = {v: {"lift": round((w / t) / base, 2) if t and base else 1.0, "n": t}
                    for v, (w, t) in vals.items() if t >= 8}   # ≥8 for signal
    out = {"method": "within-account top-quartile (account-size-agnostic)", "n_scored": len(scored),
           "n_winners": len(winners), "winner_base_rate": round(base, 3), "trait_lift": lift}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"  scored {len(scored)} obs · {len(winners)} within-account winners (base {round(base*100)}%)")
    for tr in TRAITS:
        top = sorted(lift[tr].items(), key=lambda kv: -kv[1]["lift"])[:3]
        if top:
            print(f"  {tr}: " + " · ".join(f"{v}={d['lift']}× (n={d['n']})" for v, d in top))
    print(f"  ✅ → {OUT.relative_to(B)} (real, vs the enum which was 26%≈25% random)")


if __name__ == "__main__":
    main()
