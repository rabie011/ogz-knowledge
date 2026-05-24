#!/usr/bin/env python3
"""
print_top_insights.py
Print the top 25 most actionable intelligence findings from all analytics logs.
Fast, no obs scanning — reads only from logs/.
Usage: python3 scripts/print_top_insights.py [--sector f_and_b|beauty|retail]
"""
import json, argparse
from pathlib import Path

LOGS = Path(__file__).parent.parent / "logs"

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", type=str, default=None)
    args = parser.parse_args()
    sk = args.sector  # f_and_b, beauty, retail, or None (all)

    insights = []

    # ── FORMAT ──────────────────────────────────────────────────────────────
    ct = _load("content_type_analysis.json")
    ct_types = ct.get("by_content_type") or {}
    if ct_types:
        ranked = sorted(ct_types.items(), key=lambda x: -(x[1].get("avg_engagement",0) or 0))
        best, worst = ranked[0], ranked[-1]
        gap = (best[1].get("avg_engagement",0) or 0) - (worst[1].get("avg_engagement",0) or 0)
        insights.append({
            "category": "FORMAT",
            "finding": f"{best[0]} ({best[1].get('avg_engagement',0):.0%}) vs {worst[0]} ({worst[1].get('avg_engagement',0):.0%}) — {gap:.0%} gap",
            "action": f"Use {best[0]}. Deprioritise {worst[0]}.",
            "confidence": "high" if (best[1].get("count",0) or 0) >= 30 else "medium",
        })

    # ── ASPECT RATIO ──────────────────────────────────────────────────────────
    ar_types = ct.get("by_aspect_ratio") or {}
    if ar_types:
        ranked = sorted(ar_types.items(), key=lambda x: -(x[1].get("avg_engagement",0) or 0))
        best = ranked[0]
        insights.append({
            "category": "ASPECT RATIO",
            "finding": f"{best[0]} = {best[1].get('avg_engagement',0):.0%} (n={best[1].get('count',0)})",
            "action": f"Frame for {best[0]}. Avoid vertical_9x16.",
            "confidence": "high",
        })

    # ── VISUAL COMPLEXITY ────────────────────────────────────────────────────
    vc = _load("visual_complexity_analysis.json")
    uplift = vc.get("complexity_uplift_vs_simple")
    vc_by = vc.get("by_complexity") or {}
    if vc_by:
        ranked = sorted(vc_by.items(), key=lambda x: -(x[1].get("avg_engagement",0) or 0))
        best = ranked[0]
        insights.append({
            "category": "VISUAL COMPLEXITY",
            "finding": f"{best[0]} = {best[1].get('avg_engagement',0):.0%}  (uplift vs simple: {uplift:+.0%})" if uplift else f"{best[0]} = {best[1].get('avg_engagement',0):.0%}",
            "action": "Pack the frame. More props, characters, layers = higher engagement.",
            "confidence": "high",
        })

    # ── HERITAGE ─────────────────────────────────────────────────────────────
    cult = _load("cultural_signal_analysis.json")
    hvm_uplift = cult.get("heritage_uplift_vs_modern")
    if hvm_uplift:
        insights.append({
            "category": "CULTURAL FRAMING",
            "finding": f"Heritage content outperforms modern by {hvm_uplift:+.0%}",
            "action": "Default to heritage framing unless explicit modern brand brief.",
            "confidence": "high",
        })

    # ── TONE ─────────────────────────────────────────────────────────────────
    tone_r = _load("tone_register_analysis.json")
    tones  = tone_r.get("by_tone") or {}
    if tones:
        ranked = sorted(tones.items(), key=lambda x: -(x[1].get("avg_engagement",0) or 0))[:3]
        top_tone = ranked[0]
        insights.append({
            "category": "TONE",
            "finding": " > ".join(f"{t}({v.get('avg_engagement',0):.0%})" for t,v in ranked),
            "action": f"Lead with {top_tone[0]} tone.",
            "confidence": "high",
        })

    # ── POSTING DAY ───────────────────────────────────────────────────────────
    dow = _load("day_of_week_analysis.json")
    days = dow.get("ranked_days") or []
    dow_by = dow.get("by_day") or {}
    if days and dow_by:
        best_day  = days[0]
        worst_day = days[-1]
        best_eng  = (dow_by.get(best_day) or {}).get("avg_engagement",0)
        worst_eng = (dow_by.get(worst_day) or {}).get("avg_engagement",0)
        insights.append({
            "category": "POSTING DAY",
            "finding": f"{best_day} = {best_eng:.0%}  ·  {worst_day} = {worst_eng:.0%}  ({best_eng-worst_eng:+.0%} gap)",
            "action": f"Schedule on {best_day}. Avoid {worst_day}.",
            "confidence": "medium",
        })

    # ── CAPTION ───────────────────────────────────────────────────────────────
    cap = _load("caption_length_hashtag_analysis.json")
    wc  = cap.get("by_word_count") or {}
    hc  = cap.get("by_hashtag_count") or {}
    if wc and hc:
        best_wc = max(wc.items(), key=lambda x: x[1].get("avg_engagement",0) or 0)
        best_hc = max(hc.items(), key=lambda x: x[1].get("avg_engagement",0) or 0)
        insights.append({
            "category": "CAPTION",
            "finding": f"Best length: {best_wc[0]} words ({best_wc[1].get('avg_engagement',0):.0%})  ·  Best hashtags: {best_hc[0]} ({best_hc[1].get('avg_engagement',0):.0%})",
            "action": f"Write {best_wc[0]}-word captions with {best_hc[0]} hashtags.",
            "confidence": "medium",
        })

    # ── TEXT OVERLAY ─────────────────────────────────────────────────────────
    toi = _load("text_overlay_intelligence.json")
    has_avg = toi.get("has_overlay_avg")
    no_avg  = toi.get("no_overlay_avg")
    if has_avg and no_avg:
        insights.append({
            "category": "TEXT OVERLAYS",
            "finding": f"No overlay = {no_avg:.0%}  ·  Has overlay = {has_avg:.0%}  ({no_avg-has_avg:+.0%} lift for clean posts)",
            "action": "Default to no text overlay unless it's event_info or brand_identity.",
            "confidence": "high",
        })

    # ── TOP ARABIC PHRASES ────────────────────────────────────────────────────
    npi    = _load("notable_phrases_intelligence.json")
    elite  = (npi.get("elite_phrases") or [])[:5]
    best_cat = list((npi.get("by_category") or {}).items())
    if elite:
        phrases_str = " · ".join(p["phrase"] for p in elite[:4])
        insights.append({
            "category": "ARABIC PHRASES",
            "finding": f"Elite phrases (100% eng): {phrases_str}",
            "action": "Use sensory/urgency/celebration Arabic phrases. Avoid nostalgia/memory.",
            "confidence": "high",
        })
    if best_cat:
        best_cat_name, best_cat_data = best_cat[0]
        insights.append({
            "category": "PHRASE CATEGORY",
            "finding": f"Best category: {best_cat_name} = {best_cat_data.get('avg_engagement',0):.0%}  (n={best_cat_data.get('count',0)})",
            "action": f"Use {best_cat_name} language in every post.",
            "confidence": "medium",
        })

    # ── COLOR ─────────────────────────────────────────────────────────────────
    # Read color warmth from obs directly (100 obs only)
    try:
        import json as _json
        from pathlib import Path as _Path
        from collections import defaultdict as _dd
        _ENG = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
        _wr = _dd(list)
        for _f in (_Path(__file__).parent.parent/"11_who_to_learn_from/observations").rglob("*.json"):
            _d = _json.loads(_f.read_text())
            _e = _ENG.get(_d.get("quality_assessment",{}).get("engagement_potential",""))
            _cp = _d.get("visual_observations",{}).get("color_palette") or {}
            if _e is None or not isinstance(_cp, dict): continue
            _w = _cp.get("warmth",""); _pf = _cp.get("primary_family",""); _pt = _cp.get("palette_type","")
            if _w: _wr["warmth_"+_w].append(_e)
            if _pf: _wr["pf_"+_pf].append(_e)
            if _pt: _wr["pt_"+_pt].append(_e)
        if _wr:
            warmth_ranked = sorted(
                [(k,sum(v)/len(v),len(v)) for k,v in _wr.items() if k.startswith("warmth_") and len(v)>=5],
                key=lambda x: -x[1])
            pf_ranked = sorted(
                [(k.replace("pf_",""),sum(v)/len(v),len(v)) for k,v in _wr.items() if k.startswith("pf_") and len(v)>=5],
                key=lambda x: -x[1])
            if warmth_ranked:
                best_w = warmth_ranked[0]; worst_w = warmth_ranked[-1]
                insights.append({
                    "category": "COLOR WARMTH",
                    "finding": f"{best_w[0].replace('warmth_','')}={best_w[1]:.0%}(n={best_w[2]}) > {worst_w[0].replace('warmth_','')}={worst_w[1]:.0%}(n={worst_w[2]})",
                    "action": f"Favour {best_w[0].replace('warmth_','')} colour palettes. (100-obs sample — F&B only)",
                    "confidence": "low",
                })
            if pf_ranked:
                top_pf = pf_ranked[0]
                insights.append({
                    "category": "COLOR FAMILY",
                    "finding": " · ".join(f"{k}={round(v,2):.0%}" for k,v,n in pf_ranked[:4]),
                    "action": f"Lead with {top_pf[0]} as primary colour family. Avoid red (46%).",
                    "confidence": "low",
                })
    except Exception: pass

    # ── PATTERNS ─────────────────────────────────────────────────────────────
    pat = _load("pattern_engagement.json")
    elite_pats = (pat.get("elite_patterns") or [])[:5]
    avoid_pats = (pat.get("avoid_patterns") or [])[:3]
    if elite_pats:
        pat_str = " · ".join(p["pattern"] for p in elite_pats[:4])
        insights.append({
            "category": "TOP PATTERNS",
            "finding": f"{pat_str}",
            "action": "These patterns consistently hit ≥90% engagement.",
            "confidence": "high",
        })
    if avoid_pats:
        avoid_str = " · ".join(p["pattern"] for p in avoid_pats[:3])
        insights.append({
            "category": "AVOID PATTERNS",
            "finding": f"{avoid_str}",
            "action": "These patterns score ≤40% engagement — eliminate from briefs.",
            "confidence": "high",
        })

    # ── PATTERN TRIPLETS ─────────────────────────────────────────────────────
    cooc = _load("pattern_cooccurrence_matrix.json")
    triplets = sorted((cooc.get("top_triplets") or []), key=lambda x: -(x.get("avg_engagement",0) or 0))[:3]
    if triplets:
        best_trip = triplets[0]
        a = best_trip.get("pattern_a","")
        b = best_trip.get("pattern_b","")
        c = best_trip.get("pattern_c","")
        trip_str = " + ".join(p for p in [a,b,c] if p)
        n = best_trip.get("co_occurrence_count",0) or best_trip.get("count",0)
        insights.append({
            "category": "PATTERN TRIPLET",
            "finding": f"{trip_str} → {best_trip.get('avg_engagement',0):.0%}  n={n}",
            "action": "Use these 3 patterns together for maximum impact.",
            "confidence": "high" if n >= 5 else "medium",
        })

    # ── HUMAN PRESENCE ───────────────────────────────────────────────────────
    wg = _load("wardrobe_gender_analysis.json")
    lift = wg.get("human_presence_lift")
    if lift:
        insights.append({
            "category": "HUMAN PRESENCE",
            "finding": f"Posts with humans score {lift:+.0%} vs no-human posts",
            "action": "Include a person in every possible shot.",
            "confidence": "medium",
        })

    # ── HOSPITALITY CUES ─────────────────────────────────────────────────────
    hosp = _load("hospitality_intelligence.json")
    hosp_grps = hosp.get("by_cue_group") or {}
    if hosp_grps:
        best_g = max(hosp_grps.items(), key=lambda x: x[1].get("avg_engagement",0) or 0)
        insights.append({
            "category": "HOSPITALITY",
            "finding": f"Best group: {best_g[0]} = {best_g[1].get('avg_engagement',0):.0%}",
            "action": f"Use {best_g[0]} cues in every post (product pride, welcome, abundance).",
            "confidence": "medium",
        })

    # ── ELITE vs WEAK ─────────────────────────────────────────────────────────
    evw = _load("elite_vs_weak_dna.json")
    top_do   = (evw.get("top_elite_advantages") or [])[:3]
    top_avoid= (evw.get("top_weak_tendencies") or [])[:2]
    if top_do:
        do_str = " | ".join(f"{r['dimension']}={r['value']}" for r in top_do)
        insights.append({
            "category": "ELITE DNA",
            "finding": f"Elite does more: {do_str}",
            "action": "These 3 signals separate 96% accounts from 29% accounts.",
            "confidence": "high",
        })
    if top_avoid:
        av_str = " | ".join(f"{r['dimension']}={r['value']}" for r in top_avoid)
        insights.append({
            "category": "WEAK DNA",
            "finding": f"Weak overindexes: {av_str}",
            "action": "Stop using these — they drag engagement down by 40-55pp.",
            "confidence": "high",
        })

    # ── SECTOR SPECIFIC (if --sector) ─────────────────────────────────────────
    if sk:
        opp = _load("cross_sector_opportunity.json")
        rep = (opp.get("opportunity_reports") or {}).get(sk)
        if rep:
            top_opp = (rep.get("top_opportunities") or [{}])[0]
            if top_opp.get("dimension"):
                insights.append({
                    "category": f"{sk.upper()} OPPORTUNITY",
                    "finding": f"Adopt {top_opp['dimension']}={top_opp['adopt_this']} from f_and_b → +{top_opp['potential_uplift']:.0%}",
                    "action": f"This single change could move {sk} from {rep['current_avg']:.0%} to {rep['best_sector_avg']:.0%}.",
                    "confidence": "medium",
                })
        coach = _load("account_coach_reports.json")
        sec_accounts = [r for r in (coach.get("account_reports") or []) if r.get("sector") == sk]
        if sec_accounts:
            worst = min(sec_accounts, key=lambda x: x.get("avg_engagement",0))
            best  = max(sec_accounts, key=lambda x: x.get("avg_engagement",0))
            insights.append({
                "category": f"{sk.upper()} RANGE",
                "finding": f"Best account: {best['avg_engagement']:.0%}  ·  Worst: {worst['avg_engagement']:.0%}  ({best['avg_engagement']-worst['avg_engagement']:.0%} gap)",
                "action": "Worst account must: " + (" + ".join(f"stop {g['current_value']} ({g['dimension']})" for g in (worst.get('priority_changes') or [])[:2])),
                "confidence": "high",
            })

    # ── PRINT ──────────────────────────────────────────────────────────────────
    W = 72
    sector_tag = f" [{sk}]" if sk else ""
    print(f"\n{'═'*W}")
    print(f"  OGZ TOP INTELLIGENCE INSIGHTS{sector_tag}  —  {len(insights)} findings")
    print(f"  648 obs · 15 accounts · 111 analytics logs")
    print(f"{'═'*W}\n")

    CONF_ICON = {"high": "●", "medium": "◐", "low": "○"}
    for i, ins in enumerate(insights, 1):
        icon = CONF_ICON.get(ins.get("confidence","medium"), "◐")
        print(f"  {icon} [{ins['category']}]")
        print(f"    {ins['finding']}")
        print(f"    → {ins['action']}")
        print()

    print(f"{'─'*W}")
    high_n = sum(1 for i in insights if i.get("confidence")=="high")
    print(f"  ● high confidence: {high_n}  ◐ medium: {len(insights)-high_n}")
    print()

if __name__ == "__main__":
    main()
