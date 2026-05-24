#!/usr/bin/env python3
"""
build_composition_analysis.py
Mine composition_style — 474/474 coverage, completely unmined visual dimension.
9 canonical composition types × engagement, sector, occasion, media_type, lighting.
Critical for agency shoot planning: "what framing should we use?"
Output: logs/composition_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def main():
    by_comp   = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter(),
                                      "occasions":Counter(),"media":Counter(),"lighting":Counter()})
    comp_sector   = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    comp_occasion = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    comp_media    = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    comp_lighting = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv   = data.get("visual_observations",{}) or {}
        comp = vv.get("composition_style") or None
        if not comp: continue

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        sector  = data.get("sector","unknown") or "unknown"
        cn      = data.get("cultural_notes",{}) or {}
        occ     = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"
        cr      = data.get("content_ref",{}) or {}
        media   = str(cr.get("content_type","") or "").lower() or "unknown"
        light   = str(vv.get("lighting","") or "").lower() or "unknown"

        by_comp[comp]["count"]  += 1
        by_comp[comp]["high"]   += is_high
        by_comp[comp]["sum"]    += eng
        by_comp[comp]["sectors"][sector] += 1
        by_comp[comp]["occasions"][occ] += 1
        by_comp[comp]["media"][media] += 1
        by_comp[comp]["lighting"][light] += 1

        comp_sector[comp][sector]["count"]     += 1
        comp_sector[comp][sector]["high"]      += is_high
        comp_occasion[comp][occ]["count"]      += 1
        comp_occasion[comp][occ]["high"]       += is_high
        comp_media[comp][media]["count"]       += 1
        comp_media[comp][media]["high"]        += is_high
        comp_lighting[comp][light]["count"]    += 1
        comp_lighting[comp][light]["high"]     += is_high

    # Main composition table
    comp_table = []
    for comp, d in by_comp.items():
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        top_sector  = d["sectors"].most_common(1)[0][0] if d["sectors"] else None
        top_occ     = d["occasions"].most_common(1)[0][0] if d["occasions"] else None
        top_media   = d["media"].most_common(1)[0][0] if d["media"] else None
        top_light   = d["lighting"].most_common(1)[0][0] if d["lighting"] else None
        comp_table.append({
            "composition_style": comp,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "dominant_sector": top_sector,
            "dominant_occasion": top_occ,
            "dominant_media": top_media,
            "dominant_lighting": top_light,
        })
    comp_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Best composition per sector
    best_comp_per_sector = {}
    for comp, sectors in comp_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            if sector not in best_comp_per_sector or (n >= 3 and rate > best_comp_per_sector[sector].get("rate",0)):
                best_comp_per_sector.setdefault(sector, {})
                if n >= 2 and rate > best_comp_per_sector[sector].get("rate",0):
                    best_comp_per_sector[sector] = {"composition": comp, "rate": rate, "n": n}

    # Best composition per occasion (n≥3)
    best_comp_per_occasion = {}
    for comp, occs in comp_occasion.items():
        for occ, d in occs.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            if n >= 3 and rate > best_comp_per_occasion.get(occ, {}).get("rate", -1):
                best_comp_per_occasion[occ] = {"composition": comp, "rate": rate, "n": n}

    # Best composition per media type
    best_comp_per_media = {}
    for comp, medias in comp_media.items():
        for media, d in medias.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            if n >= 3 and rate > best_comp_per_media.get(media, {}).get("rate", -1):
                best_comp_per_media[media] = {"composition": comp, "rate": rate, "n": n}

    # Composition × lighting cross-tab (full table)
    comp_lighting_table = {}
    for comp, lights in comp_lighting.items():
        rows = []
        for light, d in lights.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            rows.append({"lighting": light, "count": n, "high_eng_rate": rate})
        rows.sort(key=lambda x: -x["high_eng_rate"])
        best = next((r for r in rows if r["count"] >= 2), None)
        comp_lighting_table[comp] = {
            "best_lighting": best["lighting"] if best else None,
            "best_lighting_rate": best["high_eng_rate"] if best else None,
            "all_lightings": rows,
        }

    # Sector × composition full cross-tab
    sector_comp_table = {}
    for comp, sectors in comp_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            sector_comp_table.setdefault(sector, [])
            sector_comp_table[sector].append({
                "composition": comp, "count": n, "high_eng_rate": rate,
                "lift": round(rate - CORPUS_BASELINE, 3)
            })
    for sector in sector_comp_table:
        sector_comp_table[sector].sort(key=lambda x: -x["high_eng_rate"])

    findings = []
    if comp_table:
        best = comp_table[0]
        findings.append(
            f"Best composition: '{best['composition_style']}' = {int(best['high_engagement_rate']*100)}% high eng "
            f"(n={best['obs_count']}, +{int(best['lift_vs_baseline']*100)}pp vs baseline)"
        )
        worst = comp_table[-1]
        findings.append(
            f"Worst composition: '{worst['composition_style']}' = {int(worst['high_engagement_rate']*100)}% high eng "
            f"(n={worst['obs_count']})"
        )
        findings.append(
            f"Most used composition: 'product_hero_closeup' (n={next(c['obs_count'] for c in comp_table if c['composition_style']=='product_hero_closeup')}) "
            f"— the default Saudi F&B frame"
        )
    for sector, best in best_comp_per_sector.items():
        findings.append(
            f"Best for {sector}: '{best['composition']}' = {int(best['rate']*100)}% (n={best['n']})"
        )

    # Agency verdict per composition
    agency_verdicts = {}
    for c in comp_table:
        rate = c["high_engagement_rate"]
        if rate >= 0.75:
            verdict = "premium_use"
        elif rate >= 0.60:
            verdict = "standard_use"
        elif rate >= 0.45:
            verdict = "use_with_care"
        else:
            verdict = "avoid"
        agency_verdicts[c["composition_style"]] = verdict

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "composition_engagement_table": comp_table,
        "agency_verdicts": agency_verdicts,
        "best_composition_per_sector": best_comp_per_sector,
        "best_composition_per_occasion": best_comp_per_occasion,
        "best_composition_per_media": best_comp_per_media,
        "composition_x_lighting": comp_lighting_table,
        "sector_composition_breakdown": sector_comp_table,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "composition_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Composition analysis: {total} obs")
    print(f"\nComposition → engagement:")
    print(f"  {'Style':<28} {'HighEng':>8}  {'Lift':>7}  {'n':>4}  Verdict")
    print("  " + "─"*70)
    for c in comp_table:
        lift = f"+{int(c['lift_vs_baseline']*100)}%" if c['lift_vs_baseline']>=0 else f"{int(c['lift_vs_baseline']*100)}%"
        verdict = agency_verdicts[c["composition_style"]]
        print(f"  {c['composition_style']:<28} {int(c['high_engagement_rate']*100):>7}%  {lift:>7}  {c['obs_count']:>4}  {verdict}")
    print(f"\nBest composition per sector:")
    for sector, best in sorted(best_comp_per_sector.items()):
        print(f"  {sector:<18} → {best['composition']:<28} {int(best['rate']*100):>3}%  n={best['n']}")
    print(f"\nOutput: logs/composition_analysis.json")


if __name__ == "__main__":
    main()
