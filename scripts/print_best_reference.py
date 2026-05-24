#!/usr/bin/env python3
"""
print_best_reference.py
Given a brief (sector + occasion), which benchmark accounts should you study?
Ranks accounts by how well their content DNA matches the brief target.

Usage:
  python3 scripts/print_best_reference.py --sector food_and_beverage --occasion national_day
  python3 scripts/print_best_reference.py --sector beauty --occasion ramadan
  python3 scripts/print_best_reference.py --sector food_and_beverage  # top accounts in sector overall
  python3 scripts/print_best_reference.py --occasion eid_al_fitr       # across all sectors
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

SECTOR_KEY = {
    "food_and_beverage":"f_and_b","f&b":"f_and_b","fb":"f_and_b","food":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}


def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def _build_account_data():
    """Load per-account per-occasion engagement and DNA."""
    accounts = defaultdict(lambda: {
        "sector": "", "all_eng": [],
        "by_occ": defaultdict(list),
        "patterns": Counter(), "content_types": Counter(),
        "tones": Counter(), "compositions": Counter(),
        "complexities": Counter(), "settings": Counter(),
        "heritage": Counter(),
    })

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        acc = d.get("account_handle_normalized","")
        if not acc: continue
        e   = _eng(d)
        cr  = d.get("content_ref") or {}
        vo  = d.get("voice_observations") or {}
        vis = d.get("visual_observations") or {}
        cult= d.get("cultural_notes") or {}
        occ = d.get("occasion","")

        p = accounts[acc]
        p["sector"] = d.get("sector","")
        if e is not None:
            p["all_eng"].append(e)
            if occ: p["by_occ"][occ].append(e)

        ct   = cr.get("content_type","")
        comp = vis.get("composition_style","")
        cpx  = vis.get("visual_complexity","")
        tone = vo.get("tone","")
        sett = vis.get("setting","")
        hvm  = cult.get("heritage_vs_modern","")

        for k, v in [("content_types",ct),("compositions",comp),("complexities",cpx),
                     ("tones",tone),("settings",sett),("heritage",hvm)]:
            if v: p[k][v] += 1

        for pm in d.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: p["patterns"][slug] += 1

    return dict(accounts)


def score_account_for_brief(acc_data, sector_key, occasion, npi):
    """Return a relevance score 0-1 for how well this account fits the brief."""
    score = 0.0
    reasons = []

    # ── 1. Sector match (20 pts) ──
    if sector_key and acc_data["sector"] == sector_key:
        score += 0.20
        reasons.append("sector match")

    # ── 2. Overall performance (30 pts) ──
    all_eng = acc_data["all_eng"]
    if all_eng:
        overall = _avg(all_eng)
        pts = min(0.30, max(0.0, (overall - 0.40) / 0.60 * 0.30))  # 40%→0pts, 100%→30pts
        score += pts
        if overall >= 0.80:
            reasons.append(f"elite overall ({overall:.0%})")
        elif overall >= 0.70:
            reasons.append(f"strong overall ({overall:.0%})")

    # ── 3. Occasion-specific performance (30 pts) ──
    if occasion:
        occ_engs = acc_data["by_occ"].get(occasion, [])
        if len(occ_engs) >= 2:
            occ_avg = _avg(occ_engs)
            pts = min(0.30, max(0.0, (occ_avg - 0.40) / 0.60 * 0.30))
            score += pts
            reasons.append(f"{occasion.replace('_',' ')} avg={occ_avg:.0%} (n={len(occ_engs)})")
        elif len(occ_engs) == 1:
            score += 0.05  # some signal
            reasons.append(f"1 obs on {occasion.replace('_',' ')}")
        # If no occasion obs: 0 pts — account hasn't posted on this occasion

    # ── 4. Content volume / sample reliability (10 pts) ──
    n = len(all_eng)
    if n >= 40:
        score += 0.10
    elif n >= 20:
        score += 0.07
    elif n >= 10:
        score += 0.04

    # ── 5. Pattern breadth (10 pts) ──
    if len(acc_data["patterns"]) >= 5:
        score += 0.10
    elif len(acc_data["patterns"]) >= 3:
        score += 0.05

    return min(1.0, score), reasons


def print_brief_references(sector_key, occasion, accounts):
    """Print ranked account references for the brief."""
    # Load phrase intel
    npi = _load("notable_phrases_intelligence.json")
    opp = _load("occasion_playbook.json")
    osf = _load("occasion_sector_format_matrix.json")

    # Score all accounts
    scored = []
    for acc, data in accounts.items():
        if sector_key and data["sector"] != sector_key: continue
        score, reasons = score_account_for_brief(data, sector_key, occasion, npi)
        if score < 0.10: continue
        scored.append((acc, data, score, reasons))

    # Sort by score
    scored.sort(key=lambda x: -x[2])

    W = 72
    brief_desc = []
    if sector_key: brief_desc.append(f"SECTOR={sector_key.upper()}")
    if occasion:   brief_desc.append(f"OCCASION={occasion.upper()}")
    brief_str = "  ·  ".join(brief_desc) if brief_desc else "ALL"

    print(f"\n{'═'*W}")
    print(f"  BEST REFERENCE ACCOUNTS  —  {brief_str}")
    print(f"  {len(scored)} account(s) ranked · use these as your production benchmarks")
    print(f"{'═'*W}\n")

    # Top 5 accounts
    for rank, (acc, data, score, reasons) in enumerate(scored[:5], 1):
        all_eng   = data["all_eng"]
        overall   = _avg(all_eng) or 0
        n_total   = len(all_eng)
        occ_engs  = data["by_occ"].get(occasion, []) if occasion else []
        occ_avg   = _avg(occ_engs) if occ_engs else None
        grade     = "ELITE" if overall >= 0.80 else "STRONG" if overall >= 0.70 else "AVERAGE" if overall >= 0.55 else "WEAK"
        grade_sym = {"ELITE":"★★","STRONG":"★","AVERAGE":"◆","WEAK":"⚠"}[grade]

        # Top patterns for this account
        top_pats = [k for k,v in data["patterns"].most_common(3)]
        top_ct   = data["content_types"].most_common(1)[0][0] if data["content_types"] else "?"
        top_tone = data["tones"].most_common(1)[0][0] if data["tones"] else "?"
        top_hvm  = data["heritage"].most_common(1)[0][0] if data["heritage"] else "?"

        print(f"  #{rank}  {acc}")
        print(f"      {grade_sym} {grade}  ·  overall {overall:.0%} (n={n_total})", end="")
        if occ_avg is not None:
            print(f"  ·  {occasion.replace('_',' ')} avg {occ_avg:.0%} (n={len(occ_engs)})")
        else:
            print(f"  ·  no {occasion.replace('_',' ')} posts" if occasion else "")
        print(f"      format: {top_ct}  |  tone: {top_tone}  |  heritage: {top_hvm}")
        if top_pats:
            print(f"      top patterns: {', '.join(top_pats)}")
        print(f"      why: {' + '.join(reasons[:3])}")
        print()

    if not scored:
        print(f"  No accounts match this brief.\n")
        return

    # Occasion best practices from playbook
    if occasion:
        pb = next((e for e in (opp.get("playbook") or []) if e.get("occasion","").lower() == occasion.lower()), {})
        recipe = pb.get("overall_recipe") or {}
        best_format_row = None
        for row in (osf.get("full_table") or []):
            if row.get("occasion") == occasion:
                best_format_row = row
                break

        if recipe or best_format_row:
            print(f"  {'─'*W}")
            print(f"  CORPUS RECIPE FOR '{occasion.upper()}'")
            if recipe.get("tone"):     print(f"  Tone:       {recipe['tone']}")
            if recipe.get("setting"):  print(f"  Setting:    {recipe['setting']}")
            if recipe.get("heritage"): print(f"  Heritage:   {recipe['heritage']}")
            if best_format_row:
                print(f"  Best format: {best_format_row.get('content_type','?')} "
                      f"({best_format_row.get('avg_engagement',0):.0%}, n={best_format_row.get('count',0)})")

    # Phrase hints
    if occasion:
        phrases = [(p["phrase"], p.get("avg_engagement",0))
                   for p in ((npi.get("best_by_occasion") or {}).get(occasion) or [])[:4]
                   if p.get("phrase")]
        if phrases:
            print(f"  Top phrases: {' / '.join(ph for ph,_ in phrases[:3])}")

    print(f"\n  ── How to use: run `python3 scripts/print_account_dna.py --account <name>` for each #1-3 ──")
    print(f"{'═'*W}\n")


def main():
    parser = argparse.ArgumentParser(description="Best reference accounts for a brief")
    parser.add_argument("--sector",   type=str, default=None)
    parser.add_argument("--occasion", type=str, default=None)
    args = parser.parse_args()

    sector_key = None
    if args.sector:
        sector_key = SECTOR_KEY.get(args.sector.lower(), args.sector.lower())
    occasion = args.occasion.lower().replace(" ","_") if args.occasion else None

    accounts = _build_account_data()
    print_brief_references(sector_key, occasion, accounts)


if __name__ == "__main__":
    main()
