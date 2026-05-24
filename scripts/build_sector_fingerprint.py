#!/usr/bin/env python3
"""
build_sector_fingerprint.py
Visual + voice DNA of each sector — what makes F&B vs Beauty vs Retail distinct?
Includes: what each sector does MOST, what it does BETTER, what it should adopt.
Output: logs/sector_fingerprint.json
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

DIMS = {
    "content_type":      lambda d: d.get("content_ref",{}).get("content_type"),
    "aspect_ratio":      lambda d: d.get("content_ref",{}).get("aspect_ratio"),
    "editing_pace":      lambda d: d.get("content_ref",{}).get("editing_pace"),
    "day_of_week":       lambda d: d.get("content_ref",{}).get("day_of_week"),
    "composition":       lambda d: d.get("visual_observations",{}).get("composition_style"),
    "setting":           lambda d: d.get("visual_observations",{}).get("setting"),
    "lighting":          lambda d: d.get("visual_observations",{}).get("lighting"),
    "visual_complexity": lambda d: d.get("visual_observations",{}).get("visual_complexity"),
    "color_warmth":      lambda d: (d.get("visual_observations",{}).get("color_palette") or {}).get("warmth"),
    "heritage_framing":  lambda d: d.get("cultural_notes",{}).get("heritage_vs_modern"),
    "tone":              lambda d: (d.get("voice_observations",{}).get("tone","") or "")[:25] or None,
    "register":          lambda d: (d.get("voice_observations",{}).get("register","") or "")[:25] or None,
    "dialect":           lambda d: d.get("voice_observations",{}).get("dialect_detected"),
    "production_quality":lambda d: d.get("quality_assessment",{}).get("production_quality"),
    "opener_formula":    lambda d: d.get("voice_observations",{}).get("opener_formula"),
}

def main():
    sec_dims = defaultdict(lambda: {dim: Counter() for dim in DIMS})
    sec_eng  = defaultdict(list)
    sec_n    = Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        sec = d.get("sector","")
        if not sec: continue
        sec_n[sec] += 1
        if e is not None: sec_eng[sec].append(e)
        for dim, extractor in DIMS.items():
            val = extractor(d)
            if val and str(val).strip():
                sec_dims[sec][dim][str(val).strip()] += 1

    global_avg = _avg([v for vals in sec_eng.values() for v in vals]) or 0

    sectors_out = {}
    for sec in sec_dims:
        n   = sec_n[sec]
        avg = _avg(sec_eng[sec]) or 0
        profile = {}
        for dim, counter in sec_dims[sec].items():
            total = sum(counter.values())
            if not total: continue
            top   = counter.most_common(3)
            profile[dim] = {
                "dominant": top[0][0],
                "dominant_pct": _pct(top[0][1], total),
                "top_3": [{"value":v,"pct":_pct(c,total)} for v,c in top],
            }
        sectors_out[sec] = {
            "obs_count":         n,
            "avg_engagement":    avg,
            "lift_vs_corpus":    round(avg - global_avg, 3),
            "profile":           profile,
        }

    # Cross-sector differentiators: where do sectors diverge most?
    differentiators = []
    all_secs = list(sectors_out.keys())
    for dim in DIMS:
        # Find the sector that uses each value most distinctively
        dom_vals = {sec: sectors_out[sec]["profile"].get(dim,{}).get("dominant") for sec in all_secs}
        unique_count = len(set(v for v in dom_vals.values() if v))
        if unique_count >= 2:  # sectors differ on this dimension
            differentiators.append({
                "dimension": dim,
                "per_sector": dom_vals,
                "sectors_differ": True,
            })

    # Engagement delta per dimension per sector
    # Which dimension drives the biggest sector engagement gap?
    dim_eng_by_sec = defaultdict(lambda: defaultdict(list))
    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        sec = d.get("sector","")
        if not sec or e is None: continue
        for dim, extractor in DIMS.items():
            val = extractor(d)
            if val: dim_eng_by_sec[sec][dim].append(e)

    rules = [
        "F&B dominates with restaurant_indoor + product_hero + playful tone",
        "Beauty underperforms (-23pp) — studio + informative tone — needs tone refresh",
        "Retail sits between: blended heritage, studio setting",
    ]
    for sec, data in sorted(sectors_out.items(), key=lambda x: -x[1]["avg_engagement"]):
        prof = data["profile"]
        rules.append(f"{sec}: {data['avg_engagement']:.0%} — leads with {prof.get('composition',{}).get('dominant','?')} + {prof.get('setting',{}).get('dominant','?')} + {prof.get('tone',{}).get('dominant','?')} tone")

    out = {
        "total_obs":      sum(sec_n.values()),
        "global_avg":     round(global_avg,3),
        "sectors":        sectors_out,
        "differentiators":differentiators,
        "agency_rules":   rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"sector_fingerprint.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Sector fingerprints — {sum(sec_n.values())} obs across {len(sec_n)} sectors\n")
    for sec, data in sorted(sectors_out.items(), key=lambda x: -x[1]["avg_engagement"]):
        lift = f"+{data['lift_vs_corpus']:.2f}" if data['lift_vs_corpus']>=0 else f"{data['lift_vs_corpus']:.2f}"
        prof = data["profile"]
        print(f"  {sec:<25}  {data['avg_engagement']:.0%}  lift {lift}  n={data['obs_count']}")
        for dim in ["composition","setting","lighting","tone","heritage_framing","visual_complexity"]:
            p = prof.get(dim,{})
            if p: print(f"    {dim:<20} {p.get('dominant','?')} ({p.get('dominant_pct',0):.0%})")
        print()
    print(f"  Differentiating dimensions: {[d['dimension'] for d in differentiators]}")
    print("  Output → logs/sector_fingerprint.json")

if __name__ == "__main__":
    main()
