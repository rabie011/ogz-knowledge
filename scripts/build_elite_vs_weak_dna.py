#!/usr/bin/env python3
"""
build_elite_vs_weak_dna.py
Compare elite accounts (≥85% eng) vs weak accounts (≤50% eng).
67pp gap — what do elite accounts do that weak ones never do?
Output: logs/elite_vs_weak_dna.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _pct(c, total): return round(c/total,3) if total else 0

def main():
    # First pass: compute per-account engagement
    acct_eng = defaultdict(list)
    for f in OBS_ROOT.rglob("*.json"):
        d = json.loads(f.read_text())
        e = _eng(d)
        a = d.get("account_handle_normalized","")
        if a and e is not None: acct_eng[a].append(e)

    elite_accounts = {a for a,v in acct_eng.items() if (_avg(v) or 0) >= 0.85}
    weak_accounts  = {a for a,v in acct_eng.items() if (_avg(v) or 0) <= 0.50}

    # Second pass: collect signal distributions
    dims = [
        "content_type","setting","lighting","composition_style",
        "visual_complexity","heritage_vs_modern","tone","register",
        "production_quality","dialect","aspect_ratio","day_of_week",
        "opener_formula","caption_sentiment","has_emoji",
    ]

    elite_dist = {d: Counter() for d in dims}
    weak_dist  = {d: Counter() for d in dims}
    elite_n = weak_n = 0

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        a   = d.get("account_handle_normalized","")
        if not a: continue
        is_elite = a in elite_accounts
        is_weak  = a in weak_accounts
        if not is_elite and not is_weak: continue

        dist = elite_dist if is_elite else weak_dist
        if is_elite: elite_n += 1
        else:        weak_n  += 1

        cr  = d.get("content_ref",{})
        vis = d.get("visual_observations",{})
        vo  = d.get("voice_observations",{})
        cn  = d.get("cultural_notes",{})
        qa  = d.get("quality_assessment",{})

        def _add(key, val):
            if val and str(val).strip(): dist[key][str(val).strip()] += 1

        _add("content_type",       cr.get("content_type"))
        _add("aspect_ratio",       cr.get("aspect_ratio"))
        _add("day_of_week",        cr.get("day_of_week"))
        _add("setting",            vis.get("setting"))
        _add("lighting",           vis.get("lighting"))
        _add("composition_style",  vis.get("composition_style"))
        _add("visual_complexity",  vis.get("visual_complexity"))
        _add("heritage_vs_modern", cn.get("heritage_vs_modern"))
        _add("tone",               (vo.get("tone","") or "")[:25])
        _add("register",           (vo.get("register","") or "")[:25])
        _add("production_quality", qa.get("production_quality"))
        _add("dialect",            vo.get("dialect_detected"))
        _add("opener_formula",     vo.get("opener_formula"))
        _add("caption_sentiment",  vo.get("caption_sentiment"))
        _add("has_emoji",          vo.get("has_emoji"))

    # Compare: for each dimension, which values elite overindexes vs weak
    diff_table = {}
    for dim in dims:
        e_total = sum(elite_dist[dim].values())
        w_total = sum(weak_dist[dim].values())
        if not e_total or not w_total: continue

        all_vals = set(list(elite_dist[dim].keys()) + list(weak_dist[dim].keys()))
        rows = []
        for val in all_vals:
            e_pct = _pct(elite_dist[dim].get(val,0), e_total)
            w_pct = _pct(weak_dist[dim].get(val,0), w_total)
            diff  = round(e_pct - w_pct, 3)
            if abs(diff) >= 0.05:  # only meaningful differences
                rows.append({
                    "value":       val,
                    "elite_pct":   e_pct,
                    "weak_pct":    w_pct,
                    "elite_advantage": diff,
                })
        rows.sort(key=lambda x: -x["elite_advantage"])
        diff_table[dim] = rows

    # Top elite advantages (elite does more of this than weak)
    all_advantages = []
    for dim, rows in diff_table.items():
        for row in rows:
            all_advantages.append({"dimension":dim, **row})
    all_advantages.sort(key=lambda x: -x["elite_advantage"])

    # Top weak tendencies (weak does more of this than elite)
    weak_tendencies = sorted(all_advantages, key=lambda x: x["elite_advantage"])

    rules = []
    if all_advantages:
        top = all_advantages[:3]
        top_str = " | ".join(r["dimension"] + "=" + r["value"] for r in top)
        rules.append(f"Elite does more: {top_str}")
    if weak_tendencies:
        bot = weak_tendencies[:3]
        bot_str = " | ".join(r["dimension"] + "=" + r["value"] for r in bot)
        rules.append(f"Weak does more: {bot_str}")

    out = {
        "elite_accounts":    sorted(elite_accounts),
        "weak_accounts":     sorted(weak_accounts),
        "elite_obs_count":   elite_n,
        "weak_obs_count":    weak_n,
        "diff_table":        diff_table,
        "top_elite_advantages": all_advantages[:25],
        "top_weak_tendencies":  [r for r in weak_tendencies if r["elite_advantage"]<=0][:25],
        "agency_rules":      rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"elite_vs_weak_dna.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Elite vs Weak DNA — elite: {elite_n} obs ({len(elite_accounts)} accts)  weak: {weak_n} obs ({len(weak_accounts)} accts)\n")
    print(f"{'Dimension':<22}  {'Value':<28}  {'Elite%':>7}  {'Weak%':>6}  {'Diff':>6}")
    print("─"*74)
    for r in all_advantages[:15]:
        diff = f"+{r['elite_advantage']:.0%}"
        print(f"  {r['dimension']:<20}  {r['value']:<28}  {r['elite_pct']:.0%}     {r['weak_pct']:.0%}    {diff}")
    print(f"\n  Weak overindexes:")
    for r in [x for x in weak_tendencies if x["elite_advantage"]<=-0.05][:8]:
        diff = f"{r['elite_advantage']:.0%}"
        print(f"  {r['dimension']:<20}  {r['value']:<28}  {r['elite_pct']:.0%}     {r['weak_pct']:.0%}    {diff}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/elite_vs_weak_dna.json")

if __name__ == "__main__":
    main()
