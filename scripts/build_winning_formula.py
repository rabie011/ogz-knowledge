#!/usr/bin/env python3
"""
build_winning_formula.py
Find complete multi-dimensional content formulas that consistently achieve high engagement.
Looks at all 6 dimensions simultaneously: pattern + media_type + setting + lighting + register + tone.
Unlike single-signal analysis — this finds the COMPLETE recipe.
Output: logs/winning_formula_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.65   # updated from 0.54 — live-calculated from 648 obs


def load_pattern_names():
    names = {}
    for pf in PATTERNS.rglob("*.json"):
        try:
            p = json.loads(pf.read_text())
            if p.get("pattern_slug"):
                names[p["pattern_slug"]] = p.get("pattern_name", p["pattern_slug"])
        except: pass
    return names


def main():
    pattern_names = load_pattern_names()

    # Per obs: extract full 6-dim fingerprint
    obs_records = []

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        cr  = data.get("content_ref",{}) or {}
        vv  = data.get("visual_observations",{}) or {}
        vo  = data.get("voice_observations",{}) or {}
        cn  = data.get("cultural_notes",{}) or {}

        media_type  = str(cr.get("content_type","") or "").lower().strip() or None
        setting          = vv.get("setting") or None
        lighting         = vv.get("lighting") or None
        composition      = vv.get("composition_style") or None
        visual_complexity= vv.get("visual_complexity") or None
        register         = str(vo.get("register","") or "").lower().strip() or None
        tone             = str(vo.get("tone","") or "").lower().strip() or None
        occasion         = str(cn.get("occasion_relevance","") or "evergreen").lower().strip() or "evergreen"
        sector           = data.get("sector","unknown") or "unknown"
        aspect_ratio     = cr.get("aspect_ratio") or None
        day_of_week      = cr.get("day_of_week") or None

        # All pattern slugs for this obs
        pattern_slugs = []
        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: pattern_slugs.append(slug)

        obs_records.append({
            "eng": eng,
            "is_high": is_high,
            "media_type": media_type,
            "setting": setting,
            "lighting": lighting,
            "composition": composition,
            "visual_complexity": visual_complexity,
            "aspect_ratio": aspect_ratio,
            "day_of_week": day_of_week,
            "register": register,
            "tone": tone,
            "occasion": occasion,
            "sector": sector,
            "patterns": pattern_slugs,
            "primary_pattern": pattern_slugs[0] if pattern_slugs else None,
        })

    total = len(obs_records)

    # ── 1. Full 6-dim formula (primary_pattern + media + setting + lighting + register + tone)
    formulas_6 = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"examples":[]})
    for rec in obs_records:
        key = (
            rec["primary_pattern"] or "none",
            rec["media_type"] or "unknown",
            rec["setting"] or "unknown",
            rec["lighting"] or "unknown",
            rec["register"] or "unknown",
            rec["tone"] or "unknown",
        )
        f = formulas_6[key]
        f["count"] += 1
        f["high"]  += rec["is_high"]
        f["sum"]   += rec["eng"]

    formula_6_table = []
    for key, f in formulas_6.items():
        n = f["count"]
        if n < 2: continue
        rate = round(f["high"]/n, 3)
        formula_6_table.append({
            "primary_pattern": key[0],
            "primary_pattern_name": pattern_names.get(key[0], key[0]),
            "media_type": key[1],
            "setting": key[2],
            "lighting": key[3],
            "register": key[4],
            "tone": key[5],
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(f["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    formula_6_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # ── 2. 5-dim visual formula (media + setting + lighting + composition + register)
    formulas_5 = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    for rec in obs_records:
        if not all([rec["media_type"], rec["setting"], rec["lighting"], rec["register"]]): continue
        key = (rec["media_type"], rec["setting"], rec["lighting"], rec["composition"] or "unknown", rec["register"])
        f = formulas_5[key]
        f["count"] += 1
        f["high"]  += rec["is_high"]
        f["sum"]   += rec["eng"]

    formula_5_table = []
    for key, f in formulas_5.items():
        n = f["count"]
        if n < 3: continue
        rate = round(f["high"]/n, 3)
        formula_5_table.append({
            "media_type": key[0],
            "setting": key[1],
            "lighting": key[2],
            "composition": key[3],
            "register": key[4],
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(f["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    formula_5_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # ── 3. Best occasion-specific formulas
    occ_formulas = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    for rec in obs_records:
        occ = rec["occasion"]
        key = (rec["media_type"] or "?", rec["setting"] or "?", rec["register"] or "?", rec["tone"] or "?")
        occ_formulas[occ][key]["count"] += 1
        occ_formulas[occ][key]["high"]  += rec["is_high"]

    best_occasion_formulas = {}
    for occ, formulas in occ_formulas.items():
        best = None
        best_rate = -1
        for key, f in formulas.items():
            n = f["count"]
            if n < 2: continue
            rate = f["high"] / n
            if rate > best_rate:
                best_rate = rate
                best = {"media_type":key[0],"setting":key[1],"register":key[2],"tone":key[3],
                        "count":n,"high_eng_rate":round(rate,3)}
        if best:
            best_occasion_formulas[occ] = best

    # ── 4. Sector-specific winning formulas
    sector_formulas = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    for rec in obs_records:
        sec = rec["sector"]
        key = (rec["primary_pattern"] or "none", rec["media_type"] or "?", rec["setting"] or "?")
        sector_formulas[sec][key]["count"] += 1
        sector_formulas[sec][key]["high"]  += rec["is_high"]

    sector_best = {}
    for sec, formulas in sector_formulas.items():
        rows = []
        for key, f in formulas.items():
            n = f["count"]
            if n < 2: continue
            rate = f["high"]/n
            rows.append({"pattern":key[0],"media_type":key[1],"setting":key[2],
                          "count":n,"high_eng_rate":round(rate,3)})
        rows.sort(key=lambda x: (-x["high_eng_rate"], -x["count"]))
        sector_best[sec] = rows[:5]

    # ── 5. Visual-complexity + format formula (new dimensions)
    vc_fmt = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    for rec in obs_records:
        if not (rec["media_type"] and rec["visual_complexity"]): continue
        key = (rec["media_type"], rec["visual_complexity"], rec["aspect_ratio"] or "unknown", rec["setting"] or "unknown")
        f = vc_fmt[key]
        f["count"] += 1
        f["high"]  += rec["is_high"]
        f["sum"]   += rec["eng"]

    vc_fmt_table = []
    for key, f in vc_fmt.items():
        n = f["count"]
        if n < 3: continue
        rate = round(f["high"]/n, 3)
        vc_fmt_table.append({
            "media_type": key[0],
            "visual_complexity": key[1],
            "aspect_ratio": key[2],
            "setting": key[3],
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(f["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    vc_fmt_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # ── Key findings
    findings = []
    top_6 = [f for f in formula_6_table if f["obs_count"] >= 3]
    if top_6:
        t = top_6[0]
        findings.append(
            f"Best 6-dim formula (n≥3): {t['primary_pattern']} + {t['media_type']} + "
            f"{t['setting']} + {t['lighting']} + {t['register']} + {t['tone']} "
            f"→ {int(t['high_engagement_rate']*100)}% high eng"
        )
    top_5 = [f for f in formula_5_table if f["obs_count"] >= 3]
    if top_5:
        t = top_5[0]
        findings.append(
            f"Best visual formula (n≥3): {t['media_type']} + {t['setting']} + "
            f"{t['lighting']} + {t['composition']} + {t['register']} "
            f"→ {int(t['high_engagement_rate']*100)}%"
        )
    findings.append(
        f"{len(formula_6_table)} unique 6-dim combinations found. "
        f"{len([f for f in formula_6_table if f['obs_count'] >= 3])} have 3+ observations."
    )

    out = {
        "schema_version": 2,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "top_6dim_formulas": formula_6_table[:20],
        "top_5dim_visual_formulas": formula_5_table[:20],
        "top_vc_format_formulas": vc_fmt_table[:15],
        "best_occasion_formulas": best_occasion_formulas,
        "sector_winning_formulas": sector_best,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "winning_formula_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Winning formula analysis: {total} obs")
    top3_6 = [f for f in formula_6_table if f["obs_count"] >= 3][:5]
    print(f"\nTop 6-dim formulas (n≥3):")
    print(f"  {'Pattern':<32} {'Format':<16} {'Setting':<20} {'Eng':>5}  n")
    print("  " + "─"*85)
    for f in top3_6:
        print(f"  {f['primary_pattern']:<32} {f['media_type']:<16} {f['setting']:<20} "
              f"{int(f['high_engagement_rate']*100):>4}%  {f['obs_count']}")

    top3_5 = [f for f in formula_5_table if f["obs_count"] >= 3][:5]
    print(f"\nTop 5-dim visual formulas (n≥3):")
    for f in top3_5:
        print(f"  {f['media_type']:<16} + {f['setting']:<22} + {f['lighting']:<20} "
              f"→ {int(f['high_engagement_rate']*100):>3}%  n={f['obs_count']}")

    print(f"\nBest formula by occasion:")
    for occ, f in sorted(best_occasion_formulas.items(), key=lambda x: -x[1]["high_eng_rate"])[:6]:
        print(f"  {occ:<28} {f['media_type']:<16} {f['register']:<14} → {int(f['high_eng_rate']*100):>3}%  n={f['count']}")

    print(f"\nOutput: logs/winning_formula_analysis.json")


if __name__ == "__main__":
    main()
