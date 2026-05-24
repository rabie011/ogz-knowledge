#!/usr/bin/env python3
"""
build_occasion_readiness_report.py
Pre-production intelligence pack for any occasion × sector.
What worked, what failed, what to do differently — for any upcoming occasion.

Usage:
  python3 scripts/build_occasion_readiness_report.py \
    --occasion national_day --sector food_and_beverage
  python3 scripts/build_occasion_readiness_report.py --interactive

Output: logs/occasion_readiness/{occasion}_{sector}.json + stdout
"""
import json, argparse
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP  = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

SECTOR_ALIASES = {
    "fb":"food_and_beverage","f&b":"food_and_beverage","food":"food_and_beverage",
    "food_and_beverage":"food_and_beverage","beauty":"beauty_personal_care",
    "personal_care":"beauty_personal_care","retail":"retail_lifestyle","retail":"retail_lifestyle",
}
SECTOR_KEY_MAP = {
    "food_and_beverage":"f_and_b","beauty_personal_care":"beauty","retail_lifestyle":"retail",
}

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def generate_report(occasion, sector):
    sk = SECTOR_KEY_MAP.get(sector, sector)

    # Load analytics
    osf   = _load("occasion_sector_format_matrix.json")
    opp   = _load("occasion_playbook.json")
    pat   = _load("pattern_engagement.json")
    npi   = _load("notable_phrases_intelligence.json")
    hosp  = _load("hospitality_intelligence.json")
    dow   = _load("day_of_week_analysis.json")
    tone_r= _load("tone_register_analysis.json")
    cult  = _load("cultural_signal_analysis.json")
    sfp   = _load("sector_fingerprint.json")
    cap_lh= _load("caption_length_hashtag_analysis.json")

    # ── Pull corpus obs for this occasion × sector ──────────────────────
    occ_obs = []
    for f in OBS_ROOT.rglob("*.json"):
        d = json.loads(f.read_text())
        obs_occ = d.get("occasion","") or d.get("cultural_notes",{}).get("occasion_relevance","")
        obs_sec = d.get("sector","")
        if obs_occ == occasion and obs_sec == sk:
            e = _eng(d)
            if e is not None:
                occ_obs.append({
                    "eng": e,
                    "content_type": d.get("content_ref",{}).get("content_type",""),
                    "aspect_ratio":  d.get("content_ref",{}).get("aspect_ratio","") or "",
                    "setting":       d.get("visual_observations",{}).get("setting","") or "",
                    "lighting":      d.get("visual_observations",{}).get("lighting","") or "",
                    "composition":   d.get("visual_observations",{}).get("composition_style","") or "",
                    "visual_complexity": d.get("visual_observations",{}).get("visual_complexity","") or "",
                    "tone":          (d.get("voice_observations",{}).get("tone","") or "")[:25],
                    "register":      (d.get("voice_observations",{}).get("register","") or "")[:25],
                    "hvm":           d.get("cultural_notes",{}).get("heritage_vs_modern","") or "",
                    "patterns":      [pm.get("pattern_slug","") if isinstance(pm,dict) else pm
                                      for pm in d.get("pattern_matches",[])],
                    "phrases":       d.get("voice_observations",{}).get("notable_phrases",[]),
                    "account":       d.get("account_handle_normalized",""),
                })

    n_occ  = len(occ_obs)
    avg_occ= _avg([o["eng"] for o in occ_obs])

    # ── What worked (high eng obs) ──
    high_obs = [o for o in occ_obs if o["eng"] >= 0.75]
    low_obs  = [o for o in occ_obs if o["eng"] <= 0.50]

    def _dominant(lst, key, min_n=1):
        if not lst: return None
        c = Counter(o[key] for o in lst if o.get(key))
        if not c: return None
        top = c.most_common(1)[0]
        return {"value": top[0], "count": top[1], "pct": round(top[1]/len(lst),3)}

    def _top_signals(lst, keys, min_n=2):
        """Find which signals appear most in high-eng obs."""
        result = []
        for key in keys:
            c = Counter(o[key] for o in lst if o.get(key))
            for val, count in c.most_common(3):
                if count >= min_n:
                    result.append({"dimension": key, "value": val, "count": count,
                                   "pct": round(count/len(lst),3)})
        return sorted(result, key=lambda x: -x["pct"])[:8]

    SIGNAL_KEYS = ["content_type","aspect_ratio","setting","lighting","composition","visual_complexity","tone","register","hvm"]
    winning_signals = _top_signals(high_obs, SIGNAL_KEYS)
    losing_signals  = _top_signals(low_obs,  SIGNAL_KEYS)

    # Patterns in high-eng obs
    high_patterns = Counter()
    for o in high_obs:
        for p in o.get("patterns",[]):
            if p: high_patterns[p] += 1
    top_patterns = [{"pattern": p, "count": c, "pct": round(c/max(len(high_obs),1),3)}
                    for p,c in high_patterns.most_common(5)]

    # Phrases in high-eng obs
    high_phrases = Counter()
    for o in high_obs:
        for ph in o.get("phrases",[]):
            if ph: high_phrases[str(ph).strip()] += 1
    top_phrases = [p for p,c in high_phrases.most_common(5) if c >= 1]

    # ── Lookup analytics logs ──
    # Best format from 3-way matrix
    osf_lookup = {}
    for e in (osf.get("best_format_table") or []):
        key = e["occasion"] + "__" + e["sector"]
        osf_lookup[key] = e
    osf_entry = osf_lookup.get(f"{occasion}__{sk}") or {}

    # Playbook entry
    pb = next((e for e in (opp.get("playbook") or []) if e.get("occasion") == occasion), None)

    # Best patterns for this occasion
    occ_patterns = [(p["pattern"], p.get("avg_engagement",0))
                    for p in ((pat.get("best_by_occasion") or {}).get(occasion) or [])[:5]]

    # Notable phrases for this occasion
    occ_phrases = [p["phrase"] for p in ((npi.get("best_by_occasion") or {}).get(occasion) or [])[:4]]
    if not occ_phrases:
        # Fall back to sector phrases
        occ_phrases = [p["phrase"] for p in ((npi.get("best_by_sector") or {}).get(sk) or [])[:4]]

    # Hospitality cues for this occasion
    hosp_occ = [(c["cue"], c.get("avg_engagement",0))
                for c in ((hosp.get("best_by_occasion") or {}).get(occasion) or [])[:4] if c.get("cue")]

    # Best posting day
    best_day_occ = ((dow.get("best_by_occasion") or {}).get(occasion) or {}).get("best_day")
    best_day_sec = ((dow.get("best_by_sector") or {}).get(sector) or {}).get("best_day")

    # Tone recommendations
    best_tone_occ = ((tone_r.get("best_tone_by_occasion") or {}).get(occasion) or [{}])[0].get("tone")
    best_reg_sec  = ((tone_r.get("best_reg_by_sector") or {}).get(sector) or [{}])[0].get("register")

    # Heritage framing for this occasion
    best_hvm_occ = ((cult.get("hvm_by_occasion") or {}).get(occasion) or [{}])[0].get("hvm")

    # Sector DNA
    sfp_sec = (sfp.get("sectors") or {}).get(sk) or {}

    # ── Red flags (what NOT to do) ──
    red_flags = []
    if osf_entry.get("worst_format"):
        red_flags.append(f"AVOID format: {osf_entry['worst_format']} ({osf_entry.get('worst_eng',0):.0%} eng for this occasion)")
    if losing_signals:
        for s in losing_signals[:2]:
            red_flags.append(f"AVOID: {s['dimension']}={s['value']} (found in {int(s['pct']*100)}% of low-eng posts)")

    # Add corpus-wide known red flags
    red_flags.append("AVOID: vertical_9x16 — weakest aspect ratio for most occasions (-55pp vs elite)")
    red_flags.append("AVOID: video format if images/carousels are viable — video underperforms")

    # ── Recommended formula ──
    formula = {
        "format":            osf_entry.get("best_format") or (pb or {}).get("overall_recipe",{}).get("media_type"),
        "predicted_eng":     osf_entry.get("best_eng"),
        "aspect_ratio":      "square_1x1",  # corpus best
        "tone":              best_tone_occ or (pb or {}).get("overall_recipe",{}).get("tone"),
        "register":          best_reg_sec,
        "heritage_framing":  best_hvm_occ or (pb or {}).get("overall_recipe",{}).get("heritage_vs_modern"),
        "visual_complexity": "complex",  # consistently best
        "posting_day":       best_day_occ or best_day_sec or "sunday",
        "caption_length":    "10-30 words",
        "hashtag_count":     "1-5",
        "patterns":          [p[0] for p in occ_patterns[:3]],
        "phrases_to_use":    occ_phrases[:3],
        "hospitality_cues":  [c[0] for c in hosp_occ[:3]],
    }

    # ── Posting schedule for the occasion ──
    # Suggest 3 posts: teaser → peak → closing
    posting_schedule = [
        {"timing": "3-4 days before", "post_type": "teaser",  "format": formula.get("format") or "image",    "tone": "anticipatory"},
        {"timing": "peak day",         "post_type": "hero",    "format": formula.get("format") or "carousel_slide", "tone": best_tone_occ or "celebratory"},
        {"timing": "2 days after",     "post_type": "follow_up","format": "image", "tone": "gratitude"},
    ]

    out = {
        "occasion":     occasion,
        "sector":       sector,
        "sector_key":   sk,
        "corpus_data": {
            "obs_in_corpus":  n_occ,
            "avg_engagement": avg_occ,
            "high_eng_count": len(high_obs),
            "low_eng_count":  len(low_obs),
        },
        "winning_signals":  winning_signals,
        "losing_signals":   losing_signals[:4],
        "top_patterns":     top_patterns,
        "top_phrases_in_winners": top_phrases,
        "recommended_formula": formula,
        "red_flags": red_flags,
        "posting_schedule": posting_schedule,
        "analytics_support": {
            "format_matrix_best":  osf_entry.get("best_format"),
            "occasion_patterns":   [p[0] for p in occ_patterns],
            "occasion_phrases":    occ_phrases,
            "hospitality_cues":    [c[0] for c in hosp_occ],
            "playbook_obs_count":  (pb or {}).get("obs_count", 0),
        },
    }
    return out


def print_report(rep):
    W = 70
    occ = rep["occasion"].replace("_"," ").upper()
    sec = rep["sector"].replace("_"," ").upper()
    cd  = rep["corpus_data"]
    print(f"\n{'═'*W}")
    print(f"  OGZ OCCASION READINESS REPORT")
    print(f"  {occ} × {sec}")
    print(f"{'═'*W}")
    if cd["obs_in_corpus"]:
        print(f"\n  Corpus: {cd['obs_in_corpus']} obs — avg {(cd['avg_engagement'] or 0):.0%} "
              f"({cd['high_eng_count']} high, {cd['low_eng_count']} low)\n")
    else:
        print(f"\n  ⚠ No direct obs for this occasion × sector. Using corpus-wide data.\n")

    f = rep["recommended_formula"]
    print(f"  ── RECOMMENDED FORMULA ────────────────────────────────────────")
    fmt_eng = f" → {f['predicted_eng']:.0%}" if f.get("predicted_eng") else ""
    print(f"  Format:       {f.get('format') or '—'} {fmt_eng}")
    print(f"  Aspect:       {f.get('aspect_ratio') or '—'}")
    print(f"  Tone:         {f.get('tone') or '—'}  ·  {f.get('register') or '—'}")
    print(f"  Framing:      {f.get('heritage_framing') or '—'}")
    print(f"  Complexity:   {f.get('visual_complexity') or '—'}")
    print(f"  Post day:     {(f.get('posting_day') or '—').title()}")
    print(f"  Caption:      {f.get('caption_length') or '—'}  ·  {f.get('hashtag_count') or '—'} hashtags")
    if f.get("patterns"):
        print(f"  Patterns:     {' | '.join(f['patterns'])}")
    if f.get("phrases_to_use"):
        print(f"  Arabic cues:  {' / '.join(f['phrases_to_use'])}")
    if f.get("hospitality_cues"):
        print(f"  Hosp. cues:   {' / '.join(f['hospitality_cues'])}")

    if rep.get("winning_signals"):
        print(f"\n  ── WHAT WINS IN CORPUS ────────────────────────────────────────")
        for s in rep["winning_signals"][:5]:
            print(f"    ✓ {s['dimension']}={s['value']}  ({int(s['pct']*100)}% of high-eng posts)")
    if rep.get("top_phrases_in_winners"):
        print(f"  Top phrases:  {' / '.join(rep['top_phrases_in_winners'][:4])}")

    if rep.get("red_flags"):
        print(f"\n  ── RED FLAGS ──────────────────────────────────────────────────")
        for r in rep["red_flags"][:4]:
            print(f"    ✗ {r}")

    print(f"\n  ── POSTING SCHEDULE ───────────────────────────────────────────")
    for p in rep["posting_schedule"]:
        print(f"    {p['timing']:<20} {p['post_type']:<12} {p['format']:<18} {p['tone']}")

    print(f"\n{'═'*W}\n")


def main():
    parser = argparse.ArgumentParser(description="OGZ Occasion Readiness Report")
    parser.add_argument("--occasion", type=str)
    parser.add_argument("--sector",   type=str)
    parser.add_argument("--save",     action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or not args.occasion:
        print("\nOGZ Occasion Readiness Report")
        print("─"*35)
        print("Occasions: national_day | ramadan | eid_al_fitr | founding_day | eid_al_adha | evergreen")
        occasion = input("Occasion: ").strip().lower().replace(" ","_")
        print("Sectors: food_and_beverage | beauty_personal_care | retail_lifestyle")
        sector = SECTOR_ALIASES.get(input("Sector: ").strip().lower(), "food_and_beverage")
    else:
        occasion = args.occasion.lower().replace(" ","_")
        sector   = SECTOR_ALIASES.get(args.sector.lower(), args.sector.lower())

    rep = generate_report(occasion, sector)
    print_report(rep)

    save = args.save or (args.interactive and input("Save? [y/N]: ").lower() == "y")
    if save:
        d = LOGS / "occasion_readiness"
        d.mkdir(exist_ok=True)
        fn = f"{occasion}_{sector}.json"
        (d / fn).write_text(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"  Saved: logs/occasion_readiness/{fn}")

if __name__ == "__main__":
    main()
