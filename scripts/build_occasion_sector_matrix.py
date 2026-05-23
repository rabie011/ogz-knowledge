#!/usr/bin/env python3
"""
build_occasion_sector_matrix.py
Cross-tab 16 canonical occasions × 3 sectors.
Does Ramadan work the same way in F&B vs Beauty vs Retail?
Output: logs/occasion_sector_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
SECTOR_BASELINES = {"f_and_b": 0.60, "beauty": 0.18, "retail": 0.36}
CORPUS_BASELINE  = 0.54


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

    # (sector, occasion) → aggregation
    cells = defaultdict(lambda: {
        "count":0,"high":0,"sum":0.0,
        "patterns": Counter(),
        "media_types": Counter(),
        "settings": Counter(),
    })
    # sector totals
    sector_totals = defaultdict(lambda: {"count":0,"high":0})
    # occasion totals
    occ_totals = defaultdict(lambda: {"count":0,"high":0})

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cn     = data.get("cultural_notes",{}) or {}
        occ    = str(cn.get("occasion_relevance") or "evergreen").lower().strip() or "evergreen"
        sector = data.get("sector","unknown") or "unknown"

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        key = (sector, occ)
        cells[key]["count"]  += 1
        cells[key]["high"]   += is_high
        cells[key]["sum"]    += eng

        cr = data.get("content_ref",{}) or {}
        mt = str(cr.get("content_type","") or "").lower()
        if mt: cells[key]["media_types"][mt] += 1

        vv = data.get("visual_observations",{}) or {}
        if vv.get("setting"): cells[key]["settings"][vv["setting"]] += 1

        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: cells[key]["patterns"][slug] += 1

        sector_totals[sector]["count"] += 1
        sector_totals[sector]["high"]  += is_high
        occ_totals[occ]["count"]       += 1
        occ_totals[occ]["high"]        += is_high

    # All occasions and sectors seen
    all_occasions = sorted(set(k[1] for k in cells))
    all_sectors   = sorted(set(k[0] for k in cells))

    def top1(counter): return counter.most_common(1)[0][0] if counter else None

    # Build matrix
    matrix = []
    for occ in all_occasions:
        occ_row = {
            "occasion": occ,
            "total_obs": occ_totals[occ]["count"],
            "total_high_eng_rate": round(occ_totals[occ]["high"]/occ_totals[occ]["count"],3)
                                   if occ_totals[occ]["count"] else 0,
            "sectors": {}
        }
        for sec in all_sectors:
            d = cells.get((sec, occ))
            if not d or d["count"] == 0:
                occ_row["sectors"][sec] = {"count": 0}
                continue
            n = d["count"]
            rate = round(d["high"]/n, 3)
            base = SECTOR_BASELINES.get(sec, CORPUS_BASELINE)
            occ_row["sectors"][sec] = {
                "count": n,
                "high_eng_rate": rate,
                "lift_vs_sector_baseline": round(rate - base, 3),
                "top_pattern": pattern_names.get(top1(d["patterns"]), top1(d["patterns"])),
                "top_pattern_slug": top1(d["patterns"]),
                "top_media_type": top1(d["media_types"]),
                "top_setting": top1(d["settings"]),
            }
        matrix.append(occ_row)

    matrix.sort(key=lambda x: -x["total_obs"])

    # Biggest sector splits per occasion (occasions where sectors diverge most)
    sector_splits = []
    for occ in all_occasions:
        rates = []
        for sec in all_sectors:
            d = cells.get((sec, occ))
            if d and d["count"] >= 3:
                rates.append((sec, round(d["high"]/d["count"],3)))
        if len(rates) >= 2:
            rates.sort(key=lambda x: -x[1])
            gap = rates[0][1] - rates[-1][1]
            if gap >= 0.20:
                sector_splits.append({
                    "occasion": occ,
                    "best_sector": rates[0][0],
                    "best_rate": rates[0][1],
                    "worst_sector": rates[-1][0],
                    "worst_rate": rates[-1][1],
                    "gap": round(gap, 3),
                })
    sector_splits.sort(key=lambda x: -x["gap"])

    # Occasions unique to one sector (n=0 in others)
    sector_exclusive = defaultdict(list)
    for occ in all_occasions:
        present = [sec for sec in all_sectors if cells.get((sec,occ),{}).get("count",0) >= 2]
        if len(present) == 1:
            sector_exclusive[present[0]].append(occ)

    # Key findings
    findings = []
    if sector_splits:
        s = sector_splits[0]
        findings.append(
            f"Biggest sector split on '{s['occasion']}': "
            f"{s['best_sector']} {int(s['best_rate']*100)}% vs {s['worst_sector']} {int(s['worst_rate']*100)}% "
            f"({int(s['gap']*100)}pp gap)"
        )
    for sec, occs in sector_exclusive.items():
        if occs:
            findings.append(f"Occasions exclusive to {sec}: {', '.join(occs[:3])}")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs": total,
        "sector_baselines": SECTOR_BASELINES,
        "sectors": all_sectors,
        "occasions": all_occasions,
        "matrix": matrix,
        "biggest_sector_splits": sector_splits[:10],
        "sector_exclusive_occasions": dict(sector_exclusive),
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "occasion_sector_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Occasion × sector matrix: {total} obs, {len(all_occasions)} occasions × {len(all_sectors)} sectors")
    print(f"\n{'Occasion':<28} {'Total':>6}  ", end="")
    for sec in all_sectors:
        print(f"{sec[:8]:>10}", end="")
    print()
    print("  " + "─"*72)
    for row in matrix[:12]:
        print(f"  {row['occasion']:<26} {row['total_obs']:>6}  ", end="")
        for sec in all_sectors:
            sd = row["sectors"].get(sec, {})
            n  = sd.get("count", 0)
            r  = sd.get("high_eng_rate")
            if n == 0:   print(f"{'—':>10}", end="")
            elif r is None: print(f"{'?':>10}", end="")
            else: print(f"{int(r*100):>9}%", end="")
        print()
    if sector_splits:
        print(f"\nBiggest sector splits:")
        for s in sector_splits[:5]:
            print(f"  {s['occasion']:<28} {s['best_sector']}={int(s['best_rate']*100)}%  vs  {s['worst_sector']}={int(s['worst_rate']*100)}%  gap={int(s['gap']*100)}pp")
    print(f"\nOutput: logs/occasion_sector_matrix.json")


if __name__ == "__main__":
    main()
