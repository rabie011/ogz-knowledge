#!/usr/bin/env python3
"""
build_occasion_playbook.py
Complete agency content recipe for each of 16 canonical Saudi occasions.
Per occasion: best format + setting + lighting + composition + register + tone
             + top patterns + hospitality cue count + predicted engagement.
The go-to pre-production planning document for client briefs.
Output: logs/occasion_playbook.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

FORMAT_NORM = {
    "video": "video", "reel": "video", "instagram_reel": "video",
    "carousel_slide": "carousel", "carousel": "carousel",
    "image": "image", "photo": "image", "static_image": "image",
    "story": "story", "graphic": "graphic", "infographic": "graphic",
}


def mode(counter: Counter):
    """Most common value, or None if empty."""
    return counter.most_common(1)[0][0] if counter else None


def modal_list(counter: Counter, top_n=3):
    return [k for k, _ in counter.most_common(top_n)]


def main():
    # Per occasion: collect all field values
    occ_data = defaultdict(lambda: {
        "count": 0, "high": 0, "sum": 0.0,
        "formats": Counter(), "settings": Counter(), "lightings": Counter(),
        "compositions": Counter(), "registers": Counter(), "tones": Counter(),
        "patterns": Counter(), "hosp_counts": [], "heritages": Counter(),
        "languages": Counter(), "ctas": Counter(),
    })

    # Also track: high-engagement obs only (to surface elite recipes)
    occ_high = defaultdict(lambda: {
        "patterns": Counter(), "settings": Counter(), "lightings": Counter(),
        "compositions": Counter(), "registers": Counter(), "tones": Counter(),
        "formats": Counter(), "languages": Counter(),
    })

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cn  = data.get("cultural_notes",{}) or {}
        cr  = data.get("content_ref",{}) or {}
        vv  = data.get("visual_observations",{}) or {}
        vo  = data.get("voice_observations",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}

        occ = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        fmt   = FORMAT_NORM.get(str(cr.get("content_type","") or "").lower(), "unknown")
        sett  = str(vv.get("setting","") or "").lower() or "unknown"
        light = str(vv.get("lighting","") or "").lower() or "unknown"
        comp  = str(vv.get("composition_style","") or "").lower() or "unknown"
        reg   = str(vo.get("register","") or "").lower() or "unknown"
        tone  = str(vo.get("tone","") or "").lower() or "unknown"
        lang  = str(vo.get("language","") or "").lower() or "unknown"
        hvm   = str(cn.get("heritage_vs_modern","") or "").lower() or "unknown"
        cta   = vo.get("call_to_action_present")
        cta_l = "yes" if str(cta).lower() in ("true","1") else "no" if cta is not None else "unknown"
        hosp  = len(cn.get("hospitality_cues") or [])

        slugs = [pm.get("pattern_slug","") if isinstance(pm,dict) else pm
                 for pm in data.get("pattern_matches",[]) if pm]
        slugs = [s for s in slugs if s]

        d = occ_data[occ]
        d["count"]  += 1
        d["high"]   += is_high
        d["sum"]    += eng
        d["formats"][fmt]    += 1
        d["settings"][sett]  += 1
        d["lightings"][light]+= 1
        d["compositions"][comp] += 1
        d["registers"][reg]  += 1
        d["tones"][tone]     += 1
        d["heritages"][hvm]  += 1
        d["languages"][lang] += 1
        d["ctas"][cta_l]     += 1
        d["hosp_counts"].append(hosp)
        for s in slugs:
            d["patterns"][s] += 1

        if is_high:
            h = occ_high[occ]
            h["patterns"].update(slugs)
            h["settings"][sett]      += 1
            h["lightings"][light]    += 1
            h["compositions"][comp]  += 1
            h["registers"][reg]      += 1
            h["tones"][tone]         += 1
            h["formats"][fmt]        += 1
            h["languages"][lang]     += 1

    # Build playbook entries
    playbook = []
    for occ, d in sorted(occ_data.items(), key=lambda x: -x[1]["count"]):
        n = d["count"]
        if n == 0: continue
        high_eng_rate = round(d["high"]/n, 3)
        avg_eng = round(d["sum"]/n, 3)
        avg_hosp = round(sum(d["hosp_counts"])/len(d["hosp_counts"]), 2) if d["hosp_counts"] else 0

        # Modal production values (all obs)
        overall_recipe = {
            "format":      mode(d["formats"]),
            "setting":     mode(d["settings"]),
            "lighting":    mode(d["lightings"]),
            "composition": mode(d["compositions"]),
            "register":    mode(d["registers"]),
            "tone":        mode(d["tones"]),
            "heritage_vs_modern": mode(d["heritages"]),
            "language":    mode(d["languages"]),
            "cta":         mode(d["ctas"]),
            "avg_hospitality_cues": avg_hosp,
            "top_patterns": modal_list(d["patterns"], 5),
        }

        # Elite recipe (high-eng obs only)
        h = occ_high[occ]
        elite_recipe = {
            "format":      mode(h["formats"]),
            "setting":     mode(h["settings"]),
            "lighting":    mode(h["lightings"]),
            "composition": mode(h["compositions"]),
            "register":    mode(h["registers"]),
            "tone":        mode(h["tones"]),
            "top_patterns": modal_list(h["patterns"], 5),
        } if d["high"] >= 3 else None

        # Avoid signals (most common in low-eng obs)
        avoid_note = None
        if high_eng_rate < 0.40:
            avoid_note = f"Low-performing occasion ({int(high_eng_rate*100)}%) — prioritise evergreen strategy"

        # Engagement verdict
        if high_eng_rate >= 0.75:
            verdict = "high_opportunity"
        elif high_eng_rate >= 0.55:
            verdict = "moderate_opportunity"
        elif high_eng_rate >= 0.35:
            verdict = "low_opportunity_use_caution"
        else:
            verdict = "poor_performer_reconsider"

        playbook.append({
            "occasion": occ,
            "obs_count": n,
            "high_engagement_rate": high_eng_rate,
            "avg_engagement": avg_eng,
            "lift_vs_baseline": round(high_eng_rate - CORPUS_BASELINE, 3),
            "engagement_verdict": verdict,
            "overall_recipe": overall_recipe,
            "elite_recipe": elite_recipe,
            "format_distribution": dict(d["formats"].most_common()),
            "setting_distribution": dict(d["settings"].most_common(5)),
            "lighting_distribution": dict(d["lightings"].most_common(5)),
            "top_patterns": modal_list(d["patterns"], 8),
            "avoid_note": avoid_note,
        })

    playbook.sort(key=lambda x: -x["high_engagement_rate"])

    # Summary table
    findings = []
    top3 = [p for p in playbook if p["obs_count"] >= 5][:3]
    for p in top3:
        r = p["overall_recipe"]
        findings.append(
            f"{p['occasion'].replace('_',' ').title()} ({p['obs_count']} obs): "
            f"{int(p['high_engagement_rate']*100)}% high eng — "
            f"{r['format']} + {r['setting']} + {r['lighting']} + {r['composition']}"
        )
    best = playbook[0] if playbook else None
    if best:
        findings.append(f"Highest-engagement occasion: '{best['occasion']}' at {int(best['high_engagement_rate']*100)}%")
    worst = min((p for p in playbook if p["obs_count"] >= 5), key=lambda x: x["high_engagement_rate"], default=None)
    if worst:
        findings.append(f"Lowest-engagement occasion (n≥5): '{worst['occasion']}' at {int(worst['high_engagement_rate']*100)}% — reconsider investment")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "occasion_count": len(playbook),
        "playbook": playbook,
        "key_findings": findings,
        "how_to_use": (
            "For each occasion: use 'elite_recipe' when planning high-priority content. "
            "Use 'overall_recipe' as a safe default. 'engagement_verdict' tells you how much "
            "budget to allocate. 'top_patterns' are the proven content patterns for this moment."
        ),
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "occasion_playbook.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Occasion playbook: {len(playbook)} occasions, {total} obs")
    print(f"\n  {'Occasion':<34} {'HighEng':>8}  {'Lift':>7}  {'n':>4}  Verdict")
    print("  " + "─"*80)
    for p in playbook:
        lift = f"+{int(p['lift_vs_baseline']*100)}%" if p['lift_vs_baseline']>=0 else f"{int(p['lift_vs_baseline']*100)}%"
        r = p["overall_recipe"]
        print(f"  {p['occasion'].replace('_',' '):<34} {int(p['high_engagement_rate']*100):>7}%  {lift:>7}  {p['obs_count']:>4}  {p['engagement_verdict']}")
    print(f"\nKey findings:")
    for f in findings:
        print(f"  ▸ {f}")
    print(f"\nOutput: logs/occasion_playbook.json")


if __name__ == "__main__":
    main()
