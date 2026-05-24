#!/usr/bin/env python3
"""
build_account_coach_reports.py
For every account in the corpus, generate a specific coaching report:
  - Current engagement vs corpus baseline
  - Where they underperform vs elite benchmark
  - Exact 3 things to change (data-backed)
  - What they're already doing right
Output: logs/account_coach_reports.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP  = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
ELITE_THRESHOLD = 0.85
CORPUS_AVG = 0.65

def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _pct(c,t): return round(c/t,3) if t else 0


def main():
    # Load elite vs weak DNA for comparison
    evw = {}
    evw_path = LOGS / "elite_vs_weak_dna.json"
    if evw_path.exists():
        evw = json.loads(evw_path.read_text())

    elite_advantages = {r["dimension"]+"___"+r["value"]: r["elite_advantage"]
                        for r in (evw.get("top_elite_advantages") or [])}
    weak_tendencies  = {r["dimension"]+"___"+r["value"]: abs(r["elite_advantage"])
                        for r in (evw.get("top_weak_tendencies") or []) if r.get("elite_advantage",0) < 0}

    # Dimension extractors
    def _extract(d):
        cr  = d.get("content_ref",{}) or {}
        vis = d.get("visual_observations",{}) or {}
        vo  = d.get("voice_observations",{}) or {}
        cn  = d.get("cultural_notes",{}) or {}
        qa  = d.get("quality_assessment",{}) or {}
        return {
            "content_type":       cr.get("content_type",""),
            "aspect_ratio":       cr.get("aspect_ratio","") or "",
            "day_of_week":        cr.get("day_of_week","") or "",
            "setting":            vis.get("setting","") or "",
            "lighting":           vis.get("lighting","") or "",
            "composition_style":  vis.get("composition_style","") or "",
            "visual_complexity":  vis.get("visual_complexity","") or "",
            "heritage_vs_modern": cn.get("heritage_vs_modern","") or "",
            "tone":               (vo.get("tone","") or "")[:25],
            "register":           (vo.get("register","") or "")[:25],
            "production_quality": qa.get("production_quality","") or "",
            "dialect":            vo.get("dialect_detected","") or "",
            "opener_formula":     vo.get("opener_formula","") or "",
        }

    # Per-account data
    acct_eng     = defaultdict(list)
    acct_dims    = defaultdict(lambda: defaultdict(Counter))  # acct → dim → val → count
    acct_sector  = defaultdict(Counter)
    acct_obs_n   = Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        a   = d.get("account_handle_normalized","")
        if not a: continue
        acct_obs_n[a] += 1
        if e is not None: acct_eng[a].append(e)
        for dim, val in _extract(d).items():
            if val and str(val).strip():
                acct_dims[a][dim][str(val).strip()] += 1
        sec = d.get("sector","")
        if sec: acct_sector[a][sec] += 1

    # Build per-account profiles
    reports = {}
    for acct in sorted(acct_dims.keys()):
        avg   = _avg(acct_eng[acct]) or 0
        n     = acct_obs_n[acct]
        tier  = "elite" if avg >= ELITE_THRESHOLD else "strong" if avg >= 0.75 else "average" if avg >= 0.60 else "weak"
        lift  = round(avg - CORPUS_AVG, 3)
        sector= acct_sector[acct].most_common(1)[0][0] if acct_sector[acct] else "unknown"

        # What are they already doing right (matches elite advantages)
        strengths = []
        for dim, vals in acct_dims[acct].items():
            total = sum(vals.values())
            if not total: continue
            top_val = vals.most_common(1)[0][0]
            pct     = _pct(vals.most_common(1)[0][1], total)
            key     = dim + "___" + top_val
            if key in elite_advantages and pct >= 0.3:
                strengths.append({
                    "dimension": dim,
                    "value": top_val,
                    "pct": round(pct, 3),
                    "elite_advantage": elite_advantages[key],
                })
        strengths.sort(key=lambda x: -x["elite_advantage"])

        # What should they change (matches weak tendencies with high usage)
        gaps = []
        for dim, vals in acct_dims[acct].items():
            total = sum(vals.values())
            if not total: continue
            for val, count in vals.items():
                pct = _pct(count, total)
                key = dim + "___" + val
                if key in weak_tendencies and pct >= 0.25:
                    gaps.append({
                        "dimension": dim,
                        "current_value": val,
                        "current_pct": round(pct, 3),
                        "penalty": weak_tendencies[key],
                    })
        gaps.sort(key=lambda x: -(x["penalty"] * x["current_pct"]))

        # Profile of their dominant approach
        profile = {}
        for dim, vals in acct_dims[acct].items():
            total = sum(vals.values())
            if not total: continue
            top   = vals.most_common(1)[0]
            profile[dim] = {"dominant": top[0], "pct": round(_pct(top[1], total), 3)}

        reports[acct] = {
            "account":            acct,
            "sector":             sector,
            "obs_count":          n,
            "avg_engagement":     avg,
            "tier":               tier,
            "lift_vs_corpus":     lift,
            "strengths":          strengths[:4],
            "priority_changes":   gaps[:3],
            "current_profile":    profile,
        }

    # Sort by engagement
    sorted_reports = sorted(reports.values(), key=lambda x: -x["avg_engagement"])

    # Summary stats
    tiers = Counter(r["tier"] for r in sorted_reports)

    out = {
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_avg": CORPUS_AVG,
        "elite_threshold": ELITE_THRESHOLD,
        "tier_distribution": dict(tiers),
        "account_reports": sorted_reports,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"account_coach_reports.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Account coaching reports — {len(sorted_reports)} accounts\n")
    print(f"  Tier distribution: {dict(tiers)}\n")
    print(f"  {'Account':<40}  {'Avg':>5}  {'Tier':<9}  {'Lift':>6}  Gaps")
    print(f"  {'─'*90}")
    for r in sorted_reports:
        lift = f"+{r['lift_vs_corpus']:.2f}" if r['lift_vs_corpus'] >= 0 else f"{r['lift_vs_corpus']:.2f}"
        n_gaps = len(r["priority_changes"])
        print(f"  {r['account']:<40}  {r['avg_engagement']:.0%}  {r['tier']:<9}  {lift}  {n_gaps} changes needed")

    print(f"\n  Sample — top improvement targets:")
    for r in sorted_reports:
        if r["priority_changes"]:
            print(f"\n  @{r['account']} ({r['tier']}, {r['avg_engagement']:.0%}):")
            for g in r["priority_changes"][:2]:
                print(f"    ✗ STOP {g['dimension']}={g['current_value']} ({int(g['current_pct']*100)}% of posts)")
            for s in r["strengths"][:1]:
                print(f"    ✓ KEEP {s['dimension']}={s['value']} (+{int(s['elite_advantage']*100)}pp elite signal)")

    print(f"\n  Output → logs/account_coach_reports.json")

if __name__ == "__main__":
    main()
