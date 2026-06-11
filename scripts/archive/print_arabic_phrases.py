#!/usr/bin/env python3
"""
print_arabic_phrases.py
Quick Arabic copywriting lookup for Saudi Instagram content.
Shows top-performing phrases, openers, and cues by occasion or sector.

Usage:
  python3 scripts/print_arabic_phrases.py                      # full corpus top phrases
  python3 scripts/print_arabic_phrases.py --occasion ramadan
  python3 scripts/print_arabic_phrases.py --sector food_and_beverage
  python3 scripts/print_arabic_phrases.py --occasion national_day --sector food_and_beverage
"""
import json, argparse, re
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

SECTOR_KEY = {
    "food_and_beverage":"f_and_b","f&b":"f_and_b","fb":"f_and_b","food":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}

def _is_arabic(text):
    return bool(re.search(r'[؀-ۿ]', str(text)))


def main():
    parser = argparse.ArgumentParser(description="Arabic phrase lookup")
    parser.add_argument("--occasion", type=str, default=None)
    parser.add_argument("--sector",   type=str, default=None)
    parser.add_argument("--min_n",    type=int, default=2)
    args = parser.parse_args()

    sec_key = SECTOR_KEY.get(args.sector.lower(), args.sector) if args.sector else None
    occ_key = args.occasion.lower().replace(" ","_") if args.occasion else None

    # Load analytics
    npi  = _load("notable_phrases_intelligence.json")
    hosp = _load("hospitality_intelligence.json")
    ar   = _load("arabic_copywriting.json")
    pe   = _load("pattern_engagement.json")

    # ── Live corpus scan for matching obs ──
    phrase_eng   = defaultdict(list)
    opener_eng   = defaultdict(list)
    caption_samples = []

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        e  = _eng(d)
        vo = d.get("voice_observations") or {}
        cr = d.get("content_ref") or {}

        # Filters
        if occ_key and d.get("occasion","") != occ_key: continue
        if sec_key and d.get("sector","") != sec_key:   continue
        if e is None: continue

        # Phrases
        for ph in (vo.get("notable_phrases") or []):
            ph = str(ph).strip()
            if ph and len(ph) >= 2:
                phrase_eng[ph].append(e)

        # Opener formula
        op = vo.get("opener_formula","")
        if op: opener_eng[op].append(e)

        # Caption samples (high-eng Arabic captions)
        cap = vo.get("caption_text","") or ""
        if cap and e >= 0.75 and _is_arabic(cap):
            caption_samples.append({
                "caption": cap[:120],
                "eng": e,
                "account": d.get("account_handle_normalized",""),
                "occasion": d.get("occasion",""),
            })

    # Sort phrases by avg engagement
    phrase_stats = []
    for ph, engs in phrase_eng.items():
        if len(engs) >= args.min_n:
            phrase_stats.append({
                "phrase": ph,
                "count": len(engs),
                "avg_eng": _avg(engs),
                "high": sum(1 for e in engs if e >= 0.75),
                "low":  sum(1 for e in engs if e <= 0.50),
                "is_arabic": _is_arabic(ph),
            })
    phrase_stats.sort(key=lambda x: (-(x["avg_eng"] or 0), -x["count"]))

    arabic_phrases  = [p for p in phrase_stats if p["is_arabic"]]
    english_phrases = [p for p in phrase_stats if not p["is_arabic"]]

    opener_stats = [
        {"formula": op, "count": len(engs), "avg_eng": _avg(engs)}
        for op, engs in sorted(opener_eng.items(), key=lambda x: -_avg(x[1]))
        if len(engs) >= 2
    ]

    # Pull pre-computed analytics data
    npi_occ_phrases   = (npi.get("best_by_occasion") or {}).get(occ_key, [])[:8] if occ_key else []
    npi_sec_phrases   = (npi.get("best_by_sector")   or {}).get(sec_key, [])[:8] if sec_key else []
    npi_elite         = (npi.get("elite_phrases")    or [])[:10]
    hosp_cues         = (hosp.get("top_cues_by_engagement") or [])[:6]
    elite_patterns    = (pe.get("elite_patterns") or [])[:5]

    # ── Print ──
    W = 72
    scope = ""
    if occ_key: scope += f" · occasion={occ_key}"
    if sec_key: scope += f" · sector={sec_key}"

    print(f"\n{'═'*W}")
    print(f"  ARABIC COPYWRITING INTEL{scope}")
    print(f"  {len(arabic_phrases)} Arabic phrases  ·  {len(caption_samples)} high-eng caption samples")
    print(f"{'═'*W}\n")

    # ── Top Arabic phrases from live obs ──
    if arabic_phrases:
        print(f"  TOP ARABIC PHRASES (from matching obs, n≥{args.min_n})")
        print(f"  {'─'*66}")
        for p in arabic_phrases[:12]:
            ratio_str = f"{p['high']}↑ {p['low']}↓"
            print(f"  {p['phrase']:<38}  {p['avg_eng']:.0%}  n={p['count']:<3}  {ratio_str}")
        print()

    # ── Pre-computed NPI data ──
    if npi_occ_phrases:
        print(f"  TOP PHRASES BY OCCASION ({occ_key}) — from analytics log")
        print(f"  {'─'*66}")
        for p in npi_occ_phrases:
            n = p.get("count") or p.get("n", 0)
            print(f"  {p.get('phrase',''):<38}  {p.get('avg_engagement',0):.0%}  n={n}")
        print()

    if npi_sec_phrases:
        print(f"  TOP PHRASES BY SECTOR ({sec_key}) — from analytics log")
        print(f"  {'─'*66}")
        for p in npi_sec_phrases:
            n = p.get("count") or p.get("n", 0)
            print(f"  {p.get('phrase',''):<38}  {p.get('avg_engagement',0):.0%}  n={n}")
        print()

    if not npi_occ_phrases and not npi_sec_phrases and npi_elite:
        print(f"  ELITE ARABIC PHRASES — corpus-wide top performers")
        print(f"  {'─'*66}")
        for p in npi_elite:
            ph = p.get("phrase","")
            if _is_arabic(ph):
                cats = " / ".join(p.get("categories",[]))[:25]
                print(f"  {ph:<38}  {p.get('avg_engagement',0):.0%}  n={p.get('n',p.get('count',0))}  [{cats}]")
        print()

    # ── Opener formulas ──
    if opener_stats:
        print(f"  OPENER FORMULAS × ENGAGEMENT")
        print(f"  {'─'*66}")
        for op in opener_stats:
            print(f"  {op['formula']:<30}  {op['avg_eng']:.0%}  n={op['count']}")
        print()

    # ── Hospitality cues ──
    if hosp_cues:
        print(f"  HOSPITALITY CUES (top performing)")
        print(f"  {'─'*66}")
        for c in hosp_cues[:5]:
            cue = c.get("cue","")
            if cue:
                print(f"  {cue:<40}  {c.get('avg_engagement',0):.0%}  n={c.get('count',0)}")
        print()

    # ── Elite patterns ──
    if elite_patterns:
        print(f"  CONTENT PATTERNS (elite — ≥90% engagement)")
        print(f"  {'─'*66}")
        for p in elite_patterns:
            print(f"  {p.get('pattern',''):<45}  {p.get('avg_engagement',0):.0%}  n={p.get('count',0)}")
        print()

    # ── High-eng caption samples ──
    if caption_samples:
        caption_samples.sort(key=lambda x: -x["eng"])
        print(f"  SAMPLE HIGH-ENG CAPTIONS (≥75%) — first 5")
        print(f"  {'─'*66}")
        for s in caption_samples[:5]:
            print(f"  [{s['eng']:.0%}] {s['account']} ({s['occasion']})")
            print(f"  {s['caption']}")
            print()

    print(f"{'═'*W}\n")


if __name__ == "__main__":
    main()
