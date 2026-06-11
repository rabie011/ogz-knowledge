#!/usr/bin/env python3
"""
print_content_gap.py
For a given account, map every dimension gap vs corpus and sector benchmarks.
Shows what to CHANGE and estimated engagement lift.

Usage:
  python3 scripts/print_content_gap.py --account Reference-006
  python3 scripts/print_content_gap.py --account albaik
  python3 scripts/print_content_gap.py --sector beauty     # all accounts in sector
  python3 scripts/print_content_gap.py                     # all accounts, sorted by gap size
"""
import json, argparse
from pathlib import Path
from collections import Counter, defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _pct(n,t): return f"{n/t:.0%}" if t else "—"

SECTOR_KEY = {
    "food_and_beverage":"f_and_b","f&b":"f_and_b","fb":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def _build_account_profiles():
    """Per-account profiles: raw obs + key dimension counters + eng lists."""
    profiles = defaultdict(lambda: {
        "obs": [], "sector": "", "occasions": Counter(),
        "content_types": Counter(), "aspect_ratios": Counter(),
        "settings": Counter(), "lightings": Counter(),
        "compositions": Counter(), "complexities": Counter(),
        "tones": Counter(), "registers": Counter(),
        "heritage": Counter(), "days": Counter(),
        # eng per dimension value
        "eng_by_ct": defaultdict(list), "eng_by_ar": defaultdict(list),
        "eng_by_set": defaultdict(list), "eng_by_lit": defaultdict(list),
        "eng_by_comp": defaultdict(list), "eng_by_cpx": defaultdict(list),
        "eng_by_tone": defaultdict(list), "eng_by_reg": defaultdict(list),
        "eng_by_occ": defaultdict(list), "eng_by_day": defaultdict(list),
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

        p = profiles[acc]
        p["sector"] = d.get("sector","")
        if e is not None: p["obs"].append(e)

        ct   = cr.get("content_type","")
        ar   = cr.get("aspect_ratio","")
        day  = cr.get("day_of_week","")
        occ  = d.get("occasion","")
        sett = vis.get("setting","")
        lit  = vis.get("lighting","")
        comp = vis.get("composition_style","")
        cpx  = vis.get("visual_complexity","")
        tone = vo.get("tone","")
        reg  = vo.get("register","")
        hvm  = cult.get("heritage_vs_modern","")

        for key, val in [("content_types",ct),("aspect_ratios",ar),("days",day),
                          ("occasions",occ),("settings",sett),("lightings",lit),
                          ("compositions",comp),("complexities",cpx),("tones",tone),
                          ("registers",reg),("heritage",hvm)]:
            if val: p[key][val] += 1

        if e is not None:
            for eng_key, val in [("eng_by_ct",ct),("eng_by_ar",ar),("eng_by_day",day),
                                   ("eng_by_set",sett),("eng_by_lit",lit),
                                   ("eng_by_comp",comp),("eng_by_cpx",cpx),
                                   ("eng_by_tone",tone),("eng_by_reg",reg),
                                   ("eng_by_occ",occ)]:
                if val: p[eng_key][val].append(e)

    return dict(profiles)


def _corpus_best(dimension_key, obs_list, min_n=5):
    """Find the best-performing value for a dimension across obs_list, n>=min_n."""
    eng_by_val = defaultdict(list)
    for d in obs_list:
        e   = _eng(d)
        cr  = d.get("content_ref") or {}
        vo  = d.get("voice_observations") or {}
        vis = d.get("visual_observations") or {}
        cult= d.get("cultural_notes") or {}

        val = {
            "content_type":   cr.get("content_type",""),
            "aspect_ratio":   cr.get("aspect_ratio",""),
            "setting":        vis.get("setting",""),
            "lighting":       vis.get("lighting",""),
            "composition":    vis.get("composition_style",""),
            "complexity":     vis.get("visual_complexity",""),
            "tone":           vo.get("tone",""),
            "register":       vo.get("register",""),
            "heritage":       (cult.get("heritage_vs_modern","") if cult else ""),
            "day_of_week":    cr.get("day_of_week",""),
        }.get(dimension_key,"")

        if val and e is not None:
            eng_by_val[val].append(e)

    # Require min_n observations; relax to 3 then 1 if sparse
    for threshold in (min_n, 3, 1):
        candidates = [(v, _avg(engs), len(engs)) for v, engs in eng_by_val.items()
                      if len(engs) >= threshold and _avg(engs) is not None]
        if candidates: break
    if not candidates: return None, None, 0
    best = max(candidates, key=lambda x: x[1])
    return best[0], best[1], best[2]


def compute_gaps(acc_key, profile, corpus_avg, sector_avg, all_obs, sector_obs):
    """Return list of gap dicts: {dimension, current, current_eng, best, best_eng, lift, priority}."""
    gaps = []
    n = len(profile["obs"])
    if n < 5: return gaps  # too little data

    acc_avg = _avg(profile["obs"])

    DIMS = [
        ("Format",      "content_type",  "content_types",  "eng_by_ct"),
        ("Aspect ratio","aspect_ratio",   "aspect_ratios",  "eng_by_ar"),
        ("Setting",     "setting",        "settings",       "eng_by_set"),
        ("Lighting",    "lighting",       "lightings",      "eng_by_lit"),
        ("Composition", "composition",    "compositions",   "eng_by_comp"),
        ("Complexity",  "complexity",     "complexities",   "eng_by_cpx"),
        ("Tone",        "tone",           "tones",          "eng_by_tone"),
        ("Register",    "register",       "registers",      "eng_by_reg"),
        ("Heritage",    "heritage",       "heritage",       None),
        ("Best day",    "day_of_week",    "days",           "eng_by_day"),
    ]

    for label, dim_key, profile_key, eng_key in DIMS:
        # Account's dominant value for this dimension
        counter = profile[profile_key]
        if not counter: continue
        current_val = counter.most_common(1)[0][0]
        if not current_val: continue

        # Account's avg eng when using current_val
        if eng_key and profile[eng_key].get(current_val):
            current_eng = _avg(profile[eng_key][current_val])
        else:
            current_eng = acc_avg

        # Corpus best for this dimension (sector-preferred, then corpus)
        best_val_sec, best_eng_sec, best_n_sec   = _corpus_best(dim_key, sector_obs)
        best_val_corp, best_eng_corp, best_n_corp = _corpus_best(dim_key, all_obs)
        # Prefer sector best if it has enough observations
        if best_val_sec and best_n_sec >= 5:
            best_val, best_eng, best_n = best_val_sec, best_eng_sec, best_n_sec
        else:
            best_val, best_eng, best_n = best_val_corp, best_eng_corp, best_n_corp

        if not best_val or best_val == current_val: continue
        if best_eng is None or current_eng is None: continue
        if best_n < 3: continue  # skip noise — fewer than 3 obs

        lift = best_eng - current_eng
        if lift < 0.05: continue  # less than 5pp — not worth flagging

        gaps.append({
            "label":        label,
            "current":      current_val,
            "current_eng":  current_eng,
            "best":         best_val,
            "best_eng":     best_eng,
            "best_n":       best_n,
            "lift":         lift,
        })

    # Sort by lift descending
    gaps.sort(key=lambda x: -x["lift"])
    return gaps


def print_account_gaps(acc_key, profile, corpus_avg, sector_avg, all_obs, sector_obs):
    obs   = profile["obs"]
    n     = len(obs)
    if n < 5: return

    avg   = _avg(obs)
    grade = "ELITE" if avg >= 0.80 else "STRONG" if avg >= 0.70 else "AVERAGE" if avg >= 0.55 else "WEAK"
    grade_sym = {"ELITE":"★★","STRONG":"★","AVERAGE":"◆","WEAK":"⚠"}[grade]

    W = 72
    print(f"\n{'═'*W}")
    print(f"  {acc_key:<42}  {grade_sym} {grade}")
    print(f"  Sector: {profile['sector']:<14}  Avg: {avg:.0%}  "
          f"(corpus {corpus_avg:.0%}  /  sector {sector_avg:.0%}  /  lift {avg-corpus_avg:+.0%})")
    print(f"{'─'*W}")

    gaps = compute_gaps(acc_key, profile, corpus_avg, sector_avg, all_obs, sector_obs)

    if not gaps:
        print(f"  ✓ No significant dimension gaps found — DNA is well-aligned with corpus.")
        print(f"{'═'*W}")
        return

    biggest = gaps[0]["lift"] if gaps else 0
    print(f"  {len(gaps)} gap(s) found — biggest single gain: +{biggest:.0%} (change {gaps[0]['label'].lower() if gaps else '?'})\n")

    print(f"  {'DIMENSION':<14}  {'CURRENT':>18}  {'BEST (n)':>20}  {'LIFT':>6}  PRIORITY")
    print(f"  {'─'*66}")

    for i, g in enumerate(gaps[:8]):
        priority = "🔴 HIGH" if g["lift"] >= 0.20 else "🟡 MED" if g["lift"] >= 0.10 else "🟢 LOW"
        curr_str = f"{g['current'][:14]}({g['current_eng']:.0%})"
        best_str = f"{g['best'][:14]}({g['best_eng']:.0%},n={g['best_n']})"
        print(f"  {g['label']:<14}  {curr_str:>18}  {best_str:>20}  {g['lift']:>+.0%}  {priority}")

    # Summary prescription
    print(f"\n  TOP PRESCRIPTION")
    print(f"  {'─'*64}")
    top = gaps[:3]
    for g in top:
        lift_pp = int(g["lift"] * 100)
        print(f"  ► Change {g['label']} from '{g['current']}' → '{g['best']}' (+{lift_pp}pp)")

    # Occasion analysis — are they missing high-engagement occasions?
    occ_data = profile["eng_by_occ"]
    best_occ_in_corpus = {}
    from collections import defaultdict
    corpus_occ_eng = defaultdict(list)
    for d in all_obs:
        occ = d.get("occasion","")
        e   = _eng(d)
        if occ and e is not None:
            corpus_occ_eng[occ].append(e)

    missing_opps = []
    for occ, corp_engs in corpus_occ_eng.items():
        if not occ or len(corp_engs) < 3: continue
        corp_occ_avg = _avg(corp_engs)
        acc_uses     = profile["occasions"].get(occ, 0)
        acc_occ_avg  = _avg(occ_data.get(occ, [])) if occ_data.get(occ) else None
        if acc_uses == 0 and corp_occ_avg and corp_occ_avg > corpus_avg + 0.10:
            missing_opps.append((occ, corp_occ_avg))
        elif acc_uses > 0 and acc_occ_avg and corp_occ_avg and corp_occ_avg - acc_occ_avg > 0.15:
            missing_opps.append((occ, corp_occ_avg, acc_occ_avg, acc_uses))

    if missing_opps:
        print(f"\n  OCCASION GAPS")
        print(f"  {'─'*64}")
        missing_opps.sort(key=lambda x: -x[1])
        for item in missing_opps[:4]:
            if len(item) == 2:
                occ, corp_avg = item
                print(f"  ◆ '{occ}': corpus avg {corp_avg:.0%} — NOT IN THIS ACCOUNT's calendar")
            else:
                occ, corp_avg, acc_avg_occ, n_used = item
                print(f"  ◆ '{occ}': corpus {corp_avg:.0%} vs this account {acc_avg_occ:.0%} (n={n_used}) — underperforming by {corp_avg-acc_avg_occ:.0%}")

    print(f"\n{'═'*W}")


def main():
    parser = argparse.ArgumentParser(description="Account content gap analysis")
    parser.add_argument("--account", type=str, default=None)
    parser.add_argument("--sector",  type=str, default=None)
    args = parser.parse_args()

    profiles   = _build_account_profiles()
    all_obs    = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]
    all_engs   = [e for p in profiles.values() for e in p["obs"]]
    corpus_avg = _avg(all_engs) or 0.65

    sector_avgs = {}
    for sec in ["f_and_b","beauty","retail"]:
        engs = [e for p in profiles.values() if p["sector"] == sec for e in p["obs"]]
        sector_avgs[sec] = _avg(engs) or 0.65

    # Filter accounts
    if args.account:
        query   = args.account.lower().replace("@","").replace("_","-")
        matched = {acc: p for acc, p in profiles.items()
                   if query in acc.lower().replace("@","").replace("_","-")}
    elif args.sector:
        sk      = SECTOR_KEY.get(args.sector.lower(), args.sector)
        matched = {acc: p for acc, p in profiles.items() if p["sector"] == sk}
    else:
        matched = profiles

    if not matched:
        print(f"\n  No accounts found matching '{args.account or args.sector}'\n")
        return

    W = 72
    print(f"\n{'═'*W}")
    print(f"  OGZ CONTENT GAP ANALYSIS  —  corpus avg {corpus_avg:.0%}  |  {len(matched)} account(s)")
    print(f"{'═'*W}")

    for acc, p in sorted(matched.items(), key=lambda x: _avg(x[1]["obs"] or [0]) or 0):
        sec_key  = p["sector"]
        sec_avg  = sector_avgs.get(sec_key, corpus_avg)
        sec_obs  = [d for d in all_obs if d.get("sector","") == sec_key]
        print_account_gaps(acc, p, corpus_avg, sec_avg, all_obs, sec_obs)


if __name__ == "__main__":
    main()
