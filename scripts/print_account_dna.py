#!/usr/bin/env python3
"""
print_account_dna.py
Deep-dive on any account in the corpus: what makes them tick,
what's working, what's not, vs sector and corpus benchmarks.

Usage:
  python3 scripts/print_account_dna.py                     # list all accounts
  python3 scripts/print_account_dna.py --account barnscoffee
  python3 scripts/print_account_dna.py --account albaik
  python3 scripts/print_account_dna.py --sector food_and_beverage  # all F&B accounts
"""
import json, argparse, re
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
    """Parse all obs into per-account profiles."""
    accounts = defaultdict(lambda: {
        "obs": [], "sector": "", "handle_normalized": "",
        "occasions": Counter(), "content_types": Counter(),
        "aspect_ratios": Counter(), "settings": Counter(),
        "lightings": Counter(), "compositions": Counter(),
        "complexities": Counter(), "tones": Counter(),
        "registers": Counter(), "heritage": Counter(),
        "patterns": Counter(), "phrases": Counter(),
        "has_captions": 0, "has_emoji": 0,
    })

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        acc = d.get("account_handle_normalized","")
        if not acc: continue
        e   = _eng(d)
        cr  = d.get("content_ref")     or {}
        vo  = d.get("voice_observations") or {}
        vis = d.get("visual_observations") or {}
        cult= d.get("cultural_notes")  or {}

        p = accounts[acc]
        p["sector"]             = d.get("sector","")
        p["handle_normalized"]  = acc
        if e is not None: p["obs"].append(e)
        p["occasions"][d.get("occasion","")]  += 1
        p["content_types"][cr.get("content_type","")]   += 1
        p["aspect_ratios"][cr.get("aspect_ratio","")]   += 1
        p["settings"][vis.get("setting","")]            += 1
        p["lightings"][vis.get("lighting","")]          += 1
        p["compositions"][vis.get("composition_style","")]   += 1
        p["complexities"][vis.get("visual_complexity","")]   += 1
        p["tones"][vo.get("tone","")]                   += 1
        p["registers"][vo.get("register","")]           += 1
        p["heritage"][cult.get("heritage_vs_modern","")]     += 1
        for pm in d.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: p["patterns"][slug] += 1
        for ph in (vo.get("notable_phrases") or []):
            ph = str(ph).strip()
            if ph: p["phrases"][ph] += 1
        if vo.get("caption_text") is not None:
            p["has_captions"] += 1
        if vo.get("has_emoji"):
            p["has_emoji"] += 1

    return dict(accounts)


def print_account(acc_key, profile, corpus_avg, sector_avg, sector_key):
    obs   = profile["obs"]
    n     = len(obs)
    if not n: return
    avg   = _avg(obs)
    high  = sum(1 for e in obs if e >= 0.75)
    low   = sum(1 for e in obs if e <= 0.50)

    W = 70
    grade = "ELITE" if avg >= 0.80 else "STRONG" if avg >= 0.70 else "AVERAGE" if avg >= 0.55 else "WEAK"
    grade_sym = {"ELITE":"★★","STRONG":"★","AVERAGE":"◆","WEAK":"⚠"}[grade]

    print(f"\n{'═'*W}")
    print(f"  {acc_key:<40}  {grade_sym} {grade}")
    print(f"  Sector: {profile['sector']:<20}  Obs: {n}  Avg: {avg:.0%}  "
          f"(corpus {corpus_avg:.0%} / sector {sector_avg:.0%})")
    print(f"  High-eng: {high}/{n} ({_pct(high,n)})  "
          f"Low-eng: {low}/{n} ({_pct(low,n)})  "
          f"Lift vs corpus: {avg-corpus_avg:+.0%}")
    print(f"{'─'*W}")

    def _top(counter, n=3, skip=("",)):
        return [(k,v) for k,v in counter.most_common(n+2) if k not in skip][:n]

    # Format DNA
    ct   = _top(profile["content_types"])
    ar   = _top(profile["aspect_ratios"])
    set_ = _top(profile["settings"])
    lit  = _top(profile["lightings"])
    comp = _top(profile["compositions"])
    cpx  = _top(profile["complexities"])
    tone = _top(profile["tones"])
    reg  = _top(profile["registers"])
    hvm  = _top(profile["heritage"])
    occ  = _top(profile["occasions"])

    print(f"\n  CONTENT DNA")
    row1 = f"  Format:     {', '.join(f'{k}({v})' for k,v in ct)}"
    row2 = f"  Aspect:     {', '.join(f'{k}({v})' for k,v in ar)}"
    print(f"{row1:<55}{row2}")
    row3 = f"  Setting:    {', '.join(f'{k[:18]}({v})' for k,v in set_)}"
    row4 = f"  Lighting:   {', '.join(f'{k[:14]}({v})' for k,v in lit)}"
    print(f"{row3:<55}{row4}")
    row5 = f"  Complexity: {', '.join(f'{k}({v})' for k,v in cpx)}"
    row6 = f"  Tone:       {', '.join(f'{k[:14]}({v})' for k,v in tone)}"
    print(f"{row5:<55}{row6}")
    row7 = f"  Register:   {', '.join(f'{k[:14]}({v})' for k,v in reg)}"
    row8 = f"  Framing:    {', '.join(f'{k}({v})' for k,v in hvm)}"
    print(f"{row7:<55}{row8}")

    top_occ = ', '.join(f"{k}({v})" for k,v in occ if k)
    print(f"  Occasions:  {top_occ}")
    print(f"  Captions:   {profile['has_captions']}/{n} ({_pct(profile['has_captions'],n)}) filled  "
          f"·  Emoji: {profile['has_emoji']}/{n} ({_pct(profile['has_emoji'],n)})")

    # Top patterns
    top_pats = _top(profile["patterns"], n=4)
    if top_pats:
        print(f"\n  TOP PATTERNS")
        for pat, cnt in top_pats:
            print(f"    {pat:<45}  ×{cnt}")

    # Top phrases
    top_phrases = [(ph, cnt) for ph, cnt in profile["phrases"].most_common(6) if len(ph) >= 3]
    if top_phrases:
        print(f"\n  TOP PHRASES")
        for ph, cnt in top_phrases[:5]:
            print(f"    {ph[:50]:<52}  ×{cnt}")

    # Coaching notes
    print(f"\n  COACHING")
    if avg < corpus_avg:
        gap = corpus_avg - avg
        print(f"  ⚠ {gap:.0%} below corpus avg — needs strategic shift")
        # Identify top weakness
        dominant_ct  = ct[0][0] if ct else ""
        dominant_cpx = cpx[0][0] if cpx else ""
        if dominant_ct == "video":
            print(f"  ↳ Heavy video usage — shift to carousel/image to gain +{0.08:.0%}")
        if dominant_cpx == "moderate":
            print(f"  ↳ Moderate visual complexity — push to complex for +28pp")
        if dominant_ct == "reel" and n < 20:
            print(f"  ↳ Limited reel data — increase reel cadence to test 81% potential")
    else:
        print(f"  ✓ Above corpus avg — key advantage: {tone[0][0] if tone else '?'} tone + {ct[0][0] if ct else '?'} format")
        if avg >= 0.85:
            print(f"  ✓ Elite performer — use as benchmark for other accounts")

    print(f"{'═'*W}")


def main():
    parser = argparse.ArgumentParser(description="Account DNA deep-dive")
    parser.add_argument("--account", type=str, default=None,
                        help="Account handle (partial match OK, e.g. 'albaik')")
    parser.add_argument("--sector",  type=str, default=None)
    args = parser.parse_args()

    profiles   = _build_account_profiles()
    all_engs   = [e for p in profiles.values() for e in p["obs"]]
    corpus_avg = _avg(all_engs) or 0.65

    # Sector averages
    sector_avgs = {}
    for sec in ["f_and_b","beauty","retail"]:
        engs = [e for p in profiles.values() if p["sector"]==sec for e in p["obs"]]
        sector_avgs[sec] = _avg(engs) or 0.65

    # List mode
    if not args.account and not args.sector:
        print(f"\n  OGZ CORPUS — {len(profiles)} accounts  ·  corpus avg {corpus_avg:.0%}\n")
        print(f"  {'ACCOUNT':<45}  {'SECTOR':<8}  {'AVG':>5}  {'N':>4}  GRADE")
        print(f"  {'─'*72}")
        for acc, p in sorted(profiles.items(), key=lambda x: -_avg(x[1]["obs"] or [0])):
            avg = _avg(p["obs"])
            if avg is None: continue
            n   = len(p["obs"])
            sec = p["sector"]
            grade = "ELITE" if avg >= 0.80 else "STRONG" if avg >= 0.70 else "AVG" if avg >= 0.55 else "WEAK"
            print(f"  {acc:<45}  {sec:<8}  {avg:.0%}  {n:>4}  {grade}")
        return

    # Filter accounts
    if args.account:
        query = args.account.lower().replace("@","").replace("_","-")
        matched = {acc: p for acc, p in profiles.items()
                   if query in acc.lower().replace("@","").replace("_","-")}
    elif args.sector:
        sk = SECTOR_KEY.get(args.sector.lower(), args.sector)
        matched = {acc: p for acc, p in profiles.items() if p["sector"] == sk}
    else:
        matched = profiles

    if not matched:
        print(f"\n  No accounts found matching '{args.account or args.sector}'\n")
        print(f"  Available: {', '.join(sorted(profiles.keys()))}\n")
        return

    for acc, p in sorted(matched.items(), key=lambda x: -_avg(x[1]["obs"] or [0])):
        sec_avg = sector_avgs.get(p["sector"], corpus_avg)
        print_account(acc, p, corpus_avg, sec_avg, p["sector"])


if __name__ == "__main__":
    main()
