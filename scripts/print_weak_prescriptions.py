#!/usr/bin/env python3
"""
print_weak_prescriptions.py
For every AVERAGE/WEAK account, show the highest-ROI changes.
Sorted by biggest potential lift — use this to prioritise which accounts to fix first.

Usage:
  python3 scripts/print_weak_prescriptions.py
  python3 scripts/print_weak_prescriptions.py --sector food_and_beverage
  python3 scripts/print_weak_prescriptions.py --all   # include STRONG/ELITE too
"""
import json, argparse
from pathlib import Path
from collections import Counter, defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

SECTOR_KEY = {
    "food_and_beverage":"f_and_b","f&b":"f_and_b","fb":"f_and_b","food":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}

DIMS = [
    ("Format",       "content_type",        "content_types",  "eng_by_ct"),
    ("Aspect ratio", "aspect_ratio",        "aspect_ratios",  "eng_by_ar"),
    ("Setting",      "setting",             "settings",       "eng_by_set"),
    ("Lighting",     "lighting",            "lightings",      "eng_by_lit"),
    ("Composition",  "composition_style",   "compositions",   "eng_by_comp"),
    ("Complexity",   "visual_complexity",   "complexities",   "eng_by_cpx"),
    ("Tone",         "tone",                "tones",          "eng_by_tone"),
    ("Register",     "register",            "registers",      "eng_by_reg"),
    ("Heritage",     "heritage_vs_modern",  "heritage",       None),
    ("Best day",     "day_of_week",         "days",           "eng_by_day"),
]


def _build_profiles():
    profiles = defaultdict(lambda: {
        "obs": [], "sector": "",
        "content_types": Counter(), "aspect_ratios": Counter(),
        "settings": Counter(), "lightings": Counter(),
        "compositions": Counter(), "complexities": Counter(),
        "tones": Counter(), "registers": Counter(),
        "heritage": Counter(), "days": Counter(),
        "eng_by_ct": defaultdict(list), "eng_by_ar": defaultdict(list),
        "eng_by_set": defaultdict(list), "eng_by_lit": defaultdict(list),
        "eng_by_comp": defaultdict(list), "eng_by_cpx": defaultdict(list),
        "eng_by_tone": defaultdict(list), "eng_by_reg": defaultdict(list),
        "eng_by_day": defaultdict(list),
    })
    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        acc = d.get("account_handle_normalized","")
        if not acc: continue
        e   = _eng(d)
        cr  = d.get("content_ref")  or {}
        vo  = d.get("voice_observations") or {}
        vis = d.get("visual_observations") or {}
        cult= d.get("cultural_notes") or {}
        p   = profiles[acc]
        p["sector"] = d.get("sector","")
        if e is not None: p["obs"].append(e)
        ct   = cr.get("content_type","")
        ar   = cr.get("aspect_ratio","")
        day  = cr.get("day_of_week","")
        sett = vis.get("setting","")
        lit  = vis.get("lighting","")
        comp = vis.get("composition_style","")
        cpx  = vis.get("visual_complexity","")
        tone = vo.get("tone","")
        reg  = vo.get("register","")
        hvm  = cult.get("heritage_vs_modern","")
        for key, val in [("content_types",ct),("aspect_ratios",ar),("days",day),
                         ("settings",sett),("lightings",lit),("compositions",comp),
                         ("complexities",cpx),("tones",tone),("registers",reg),("heritage",hvm)]:
            if val: p[key][val] += 1
        if e is not None:
            for eng_key, val in [("eng_by_ct",ct),("eng_by_ar",ar),("eng_by_day",day),
                                  ("eng_by_set",sett),("eng_by_lit",lit),
                                  ("eng_by_comp",comp),("eng_by_cpx",cpx),
                                  ("eng_by_tone",tone),("eng_by_reg",reg)]:
                if val: p[eng_key][val].append(e)
    return dict(profiles)


def _corpus_best(dim_key, all_obs, min_n=5):
    eng_by_val = defaultdict(list)
    dim_map = {
        "content_type":  lambda d: (d.get("content_ref") or {}).get("content_type",""),
        "aspect_ratio":  lambda d: (d.get("content_ref") or {}).get("aspect_ratio",""),
        "day_of_week":   lambda d: (d.get("content_ref") or {}).get("day_of_week",""),
        "setting":       lambda d: (d.get("visual_observations") or {}).get("setting",""),
        "lighting":      lambda d: (d.get("visual_observations") or {}).get("lighting",""),
        "composition_style": lambda d: (d.get("visual_observations") or {}).get("composition_style",""),
        "visual_complexity": lambda d: (d.get("visual_observations") or {}).get("visual_complexity",""),
        "tone":          lambda d: (d.get("voice_observations") or {}).get("tone",""),
        "register":      lambda d: (d.get("voice_observations") or {}).get("register",""),
        "heritage_vs_modern": lambda d: (d.get("cultural_notes") or {}).get("heritage_vs_modern",""),
    }
    getter = dim_map.get(dim_key, lambda d: "")
    for d in all_obs:
        e = _eng(d)
        val = getter(d)
        if val and e is not None:
            eng_by_val[val].append(e)
    for threshold in (min_n, 3, 1):
        candidates = [(v, _avg(engs), len(engs)) for v, engs in eng_by_val.items()
                      if len(engs) >= threshold]
        if candidates: break
    if not candidates: return None, None, 0
    # Skip un-normalized values (raw descriptions > 30 chars)
    candidates = [(v, a, n) for v, a, n in candidates if len(str(v)) <= 30]
    if not candidates: return None, None, 0
    best = max(candidates, key=lambda x: x[1])
    return best[0], best[1], best[2]


def compute_gaps(profile, all_obs, corpus_avg):
    if len(profile["obs"]) < 5: return []
    acc_avg = _avg(profile["obs"])
    gaps = []
    for label, dim_key, profile_key, eng_key in DIMS:
        counter = profile[profile_key]
        if not counter: continue
        current_val = counter.most_common(1)[0][0]
        if not current_val: continue
        if eng_key and profile[eng_key].get(current_val):
            current_eng = _avg(profile[eng_key][current_val])
        else:
            current_eng = acc_avg
        best_val, best_eng, best_n = _corpus_best(dim_key, all_obs)
        if not best_val or best_val == current_val: continue
        if best_eng is None or current_eng is None: continue
        if best_n < 3: continue
        lift = best_eng - current_eng
        if lift < 0.05: continue
        gaps.append({"label": label, "current": current_val, "current_eng": current_eng,
                     "best": best_val, "best_eng": best_eng, "best_n": best_n, "lift": lift})
    gaps.sort(key=lambda x: -x["lift"])
    return gaps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", type=str, default=None)
    parser.add_argument("--all",    action="store_true", help="Include STRONG/ELITE accounts too")
    args = parser.parse_args()

    sec_filter = SECTOR_KEY.get(args.sector.lower(), args.sector) if args.sector else None

    profiles  = _build_profiles()
    all_obs   = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]
    all_engs  = [e for p in profiles.values() for e in p["obs"]]
    corpus_avg = _avg(all_engs) or 0.65

    # Filter accounts
    results = []
    for acc, p in profiles.items():
        if sec_filter and p["sector"] != sec_filter: continue
        if len(p["obs"]) < 5: continue
        avg = _avg(p["obs"]) or 0
        grade = "ELITE" if avg >= 0.80 else "STRONG" if avg >= 0.70 else "AVERAGE" if avg >= 0.55 else "WEAK"
        if not args.all and grade in ("ELITE", "STRONG"): continue
        gaps = compute_gaps(p, all_obs, corpus_avg)
        results.append((acc, p, avg, grade, gaps))

    # Sort by biggest top-gap (most fixable first)
    results.sort(key=lambda x: -(x[4][0]["lift"] if x[4] else 0))

    W = 72
    scope = f" — {sec_filter.upper()}" if sec_filter else ""
    grade_label = "ALL" if args.all else "AVERAGE/WEAK"
    print(f"\n{'═'*W}")
    print(f"  WEAK ACCOUNT PRESCRIPTIONS{scope}")
    print(f"  {len(results)} {grade_label} accounts  ·  corpus avg {corpus_avg:.0%}")
    print(f"{'═'*W}")

    for acc, p, avg, grade, gaps in results:
        grade_sym = {"ELITE":"★★","STRONG":"★","AVERAGE":"◆","WEAK":"⚠"}[grade]
        n = len(p["obs"])
        top_lift = gaps[0]["lift"] if gaps else 0

        print(f"\n  {acc}")
        print(f"  {grade_sym} {grade} ({avg:.0%})  ·  {n} obs  ·  sector: {p['sector']}")

        if not gaps:
            print(f"  ✓ No clear dimension gaps found (data may be sparse)")
            continue

        print(f"  Biggest opportunity: +{top_lift:.0%} if you change {gaps[0]['label'].lower()}")
        print(f"  {'─'*60}")
        for g in gaps[:3]:
            priority = "🔴" if g["lift"] >= 0.20 else "🟡" if g["lift"] >= 0.10 else "🟢"
            cur = g["current"][:22] + "…" if len(g["current"]) > 25 else g["current"]
            print(f"  {priority} Change {g['label']:<14} '{cur}' → '{g['best']}'  +{g['lift']:.0%}")

    if not results:
        print(f"\n  No {grade_label} accounts found.\n")
        return

    # Summary table
    print(f"\n{'─'*W}")
    print(f"  PRIORITY RANKING — fix these first")
    print(f"  {'─'*60}")
    print(f"  {'ACCOUNT':<44}  {'AVG':>5}  {'TOP CHANGE':<30}  LIFT")
    for acc, p, avg, grade, gaps in results:
        if not gaps: continue
        g = gaps[0]
        best_display = g["best"][:18] + "…" if len(g["best"]) > 20 else g["best"]
        change = f"{g['label']}: →{best_display}"
        print(f"  {acc:<44}  {avg:.0%}  {change:<30}  +{g['lift']:.0%}")

    print(f"\n{'═'*W}\n")


if __name__ == "__main__":
    main()
