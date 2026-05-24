#!/usr/bin/env python3
"""
build_account_performance_analysis.py
Per-account engagement fingerprints — what makes top accounts different?
56pp gap between best (96%) and worst (35%) account in corpus.
Output: logs/account_performance_analysis.json
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
def _mode(counter): return counter.most_common(1)[0][0] if counter else None

def main():
    acct_data = defaultdict(lambda: {
        "eng":[], "sector":"", "content_types":Counter(), "settings":Counter(),
        "compositions":Counter(), "lighting":Counter(), "tones":Counter(),
        "heritage":Counter(), "occasions":Counter(), "complexity":Counter(),
        "patterns":Counter(), "production_quality":Counter(),
    })

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        a   = d.get("account_handle_normalized","")
        if not a: continue
        ad  = acct_data[a]
        vis = d.get("visual_observations",{})
        vo  = d.get("voice_observations",{})
        cn  = d.get("cultural_notes",{})
        cr  = d.get("content_ref",{})
        qa  = d.get("quality_assessment",{})

        ad["eng"].append(e)
        ad["sector"]                         = d.get("sector","")
        ad["content_types"][cr.get("content_type","?")] += 1
        ad["settings"][vis.get("setting","?")] += 1
        ad["compositions"][vis.get("composition_style","?")] += 1
        ad["lighting"][vis.get("lighting","?")] += 1
        if vo.get("tone"): ad["tones"][vo["tone"][:25]] += 1
        if cn.get("heritage_vs_modern"): ad["heritage"][cn["heritage_vs_modern"]] += 1
        occ = d.get("occasion","") or "evergreen"
        ad["occasions"][occ] += 1
        if vis.get("visual_complexity"): ad["complexity"][vis["visual_complexity"]] += 1
        for pm in d.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","")
            if slug: ad["patterns"][slug] += 1
        if qa.get("production_quality"): ad["production_quality"][qa["production_quality"]] += 1

    global_avg = _avg([v for ad in acct_data.values() for v in ad["eng"]]) or 0

    accounts = []
    for acct, ad in sorted(acct_data.items(), key=lambda x: -(_avg(x[1]["eng"]) or 0)):
        v   = ad["eng"]
        avg = _avg(v) or 0
        accounts.append({
            "account":            acct,
            "sector":             ad["sector"],
            "obs_count":          len(v),
            "avg_engagement":     avg,
            "lift_vs_corpus":     round(avg - global_avg, 3),
            "high_rate":          round(sum(1 for x in v if x>=0.75)/len(v), 3),
            "performance_tier":   "elite" if avg>=0.85 else "strong" if avg>=0.70 else "average" if avg>=0.55 else "weak",
            "signature": {
                "top_content_type":  _mode(ad["content_types"]),
                "top_setting":       _mode(ad["settings"]),
                "top_composition":   _mode(ad["compositions"]),
                "top_lighting":      _mode(ad["lighting"]),
                "top_tone":          _mode(ad["tones"]),
                "heritage_framing":  _mode(ad["heritage"]),
                "top_occasion":      _mode(ad["occasions"]),
                "visual_complexity": _mode(ad["complexity"]),
                "top_production":    _mode(ad["production_quality"]),
                "top_patterns":      [k for k,_ in ad["patterns"].most_common(3)],
            },
        })

    # Elite vs weak account signal differences
    elite = [a for a in accounts if a["performance_tier"] == "elite"]
    weak  = [a for a in accounts if a["performance_tier"] == "weak"]

    def _sig_compare(accts, key):
        c = Counter()
        for a in accts:
            v = a["signature"].get(key)
            if v: c[v] += 1
        return c.most_common(3)

    elite_signals = {
        "content_type":  _sig_compare(elite, "top_content_type"),
        "setting":       _sig_compare(elite, "top_setting"),
        "composition":   _sig_compare(elite, "top_composition"),
        "lighting":      _sig_compare(elite, "top_lighting"),
        "heritage":      _sig_compare(elite, "heritage_framing"),
        "complexity":    _sig_compare(elite, "visual_complexity"),
    }
    weak_signals = {
        "content_type":  _sig_compare(weak, "top_content_type"),
        "setting":       _sig_compare(weak, "top_setting"),
        "composition":   _sig_compare(weak, "top_composition"),
    }

    # Tier distribution
    tier_dist = Counter(a["performance_tier"] for a in accounts)

    rules = []
    if elite:
        e_comp = elite_signals["composition"][0][0] if elite_signals["composition"] else "—"
        e_set  = elite_signals["setting"][0][0]     if elite_signals["setting"]      else "—"
        rules.append(f"Elite accounts ({len(elite)}) use: {e_comp} + {e_set}")
    gap = round(accounts[0]["avg_engagement"] - accounts[-1]["avg_engagement"], 3) if accounts else 0
    rules.append(f"Performance gap: {gap:.0%} between best and worst account")

    out = {
        "total_accounts":   len(accounts),
        "global_avg":       round(global_avg,3),
        "tier_distribution":dict(tier_dist),
        "accounts_ranked":  accounts,
        "elite_signals":    {k:[{"val":v,"n":n} for v,n in vs] for k,vs in elite_signals.items()},
        "weak_signals":     {k:[{"val":v,"n":n} for v,n in vs] for k,vs in weak_signals.items()},
        "agency_rules":     rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"account_performance_analysis.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Account performance — {len(accounts)} accounts  (global {global_avg:.0%})\n")
    print(f"{'Account':<32}  {'Eng':>4}  {'Lift':>6}  {'Tier':<8}  n")
    print("─"*65)
    for a in accounts:
        lift = f"+{a['lift_vs_corpus']:.2f}" if a['lift_vs_corpus']>=0 else f"{a['lift_vs_corpus']:.2f}"
        print(f"  {a['account']:<30}  {a['avg_engagement']:.0%}  {lift:>6}  {a['performance_tier']:<8}  {a['obs_count']}")
    print(f"\nTiers: {dict(tier_dist)}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/account_performance_analysis.json")

if __name__ == "__main__":
    main()
