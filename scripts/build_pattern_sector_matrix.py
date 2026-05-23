#!/usr/bin/env python3
"""
build_pattern_sector_matrix.py
For each pattern, break down engagement by sector.
Shows where patterns work and where they fail across F&B / Beauty / Retail.
Output: logs/pattern_sector_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
# Sector baselines from cross_sector_benchmark
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

    # pattern → {total, sectors: {sector → {count, high, sum}}}
    store = defaultdict(lambda: {
        "total": {"count":0,"high":0,"sum":0.0},
        "sectors": defaultdict(lambda: {"count":0,"high":0,"sum":0.0}),
    })
    # sector → pattern → {count, high, sum}
    sector_store = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0,"sum":0.0}))

    total_obs = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total_obs += 1
        sector  = data.get("sector","unknown") or "unknown"
        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if not slug: continue
            d = store[slug]
            d["total"]["count"] += 1
            d["total"]["high"]  += is_high
            d["total"]["sum"]   += eng
            d["sectors"][sector]["count"] += 1
            d["sectors"][sector]["high"]  += is_high
            d["sectors"][sector]["sum"]   += eng
            sector_store[sector][slug]["count"] += 1
            sector_store[sector][slug]["high"]  += is_high
            sector_store[sector][slug]["sum"]   += eng

    # Build pattern profiles
    pattern_profiles = []
    for slug, d in store.items():
        tn = d["total"]["count"]
        if tn == 0: continue
        total_rate = round(d["total"]["high"] / tn, 3)

        sector_breakdown = {}
        best_sector  = None; best_rate  = -1.0
        worst_sector = None; worst_rate =  2.0
        sectors_with_data = 0

        for sec, sd in d["sectors"].items():
            sn   = sd["count"]
            rate = round(sd["high"] / sn, 3) if sn else 0
            base = SECTOR_BASELINES.get(sec, CORPUS_BASELINE)
            sector_breakdown[sec] = {
                "count": sn,
                "high_eng_rate": rate,
                "lift_vs_sector_baseline": round(rate - base, 3),
            }
            if sn >= 2:
                sectors_with_data += 1
                if rate > best_rate:  best_rate  = rate; best_sector  = sec
                if rate < worst_rate: worst_rate = rate; worst_sector = sec

        pattern_profiles.append({
            "slug": slug,
            "name": pattern_names.get(slug, slug),
            "total_count": tn,
            "overall_high_eng_rate": total_rate,
            "overall_lift_vs_baseline": round(total_rate - CORPUS_BASELINE, 3),
            "appears_in_n_sectors": sectors_with_data,
            "best_sector": best_sector,
            "best_sector_rate": round(best_rate, 3) if best_rate >= 0 else None,
            "worst_sector": worst_sector,
            "worst_sector_rate": round(worst_rate, 3) if worst_rate <= 1.0 else None,
            "sector_breakdown": sector_breakdown,
        })

    pattern_profiles.sort(key=lambda x: (-x["total_count"], -x["overall_high_eng_rate"]))

    # Per-sector top patterns (n≥3 in that sector)
    sector_top = {}
    for sec, pats in sector_store.items():
        rows = []
        for slug, sd in pats.items():
            n    = sd["count"]
            rate = round(sd["high"] / n, 3) if n else 0
            base = SECTOR_BASELINES.get(sec, CORPUS_BASELINE)
            rows.append({
                "slug": slug,
                "name": pattern_names.get(slug, slug),
                "count": n,
                "high_eng_rate": rate,
                "lift_vs_sector_baseline": round(rate - base, 3),
            })
        qualified = [r for r in rows if r["count"] >= 3]
        sector_top[sec] = {
            "baseline": SECTOR_BASELINES.get(sec, CORPUS_BASELINE),
            "top_10_by_engagement": sorted(qualified, key=lambda x: -x["high_eng_rate"])[:10],
            "top_10_by_volume":     sorted(rows, key=lambda x: -x["count"])[:10],
            "avoid": [r for r in qualified if r["high_eng_rate"] < 0.30],
        }

    # Cross-sector transfer patterns — high in one sector, low in another
    transfer = [
        p for p in pattern_profiles
        if p["appears_in_n_sectors"] >= 2
        and p["best_sector_rate"] is not None
        and p["worst_sector_rate"] is not None
        and (p["best_sector_rate"] - p["worst_sector_rate"]) >= 0.30
    ]
    transfer.sort(key=lambda x: -(x["best_sector_rate"] - (x["worst_sector_rate"] or 0)))

    # Key findings
    findings = []
    if transfer:
        t = transfer[0]
        findings.append(
            f"Biggest sector split: '{t['slug']}' — {t['best_sector']} {int(t['best_sector_rate']*100)}% "
            f"vs {t['worst_sector']} {int(t['worst_sector_rate']*100)}% (gap {int((t['best_sector_rate']-t['worst_sector_rate'])*100)}pp)"
        )
    for sec, data in sector_top.items():
        top = data["top_10_by_engagement"]
        if top:
            findings.append(f"{sec} best pattern: '{top[0]['slug']}' ({int(top[0]['high_eng_rate']*100)}%, lift {int(top[0]['lift_vs_sector_baseline']*100):+}pp vs sector baseline)")
        avoid = data["avoid"]
        if avoid:
            findings.append(f"{sec} avoid: '{avoid[0]['slug']}' ({int(avoid[0]['high_eng_rate']*100)}% — well below {int(data['baseline']*100)}% baseline)")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs": total_obs,
        "sector_baselines": SECTOR_BASELINES,
        "corpus_baseline": CORPUS_BASELINE,
        "sector_top_patterns": sector_top,
        "cross_sector_transfer_patterns": transfer[:15],
        "pattern_sector_profiles": pattern_profiles,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "pattern_sector_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Pattern × sector matrix: {len(pattern_profiles)} patterns, {total_obs} obs")
    for sec, data in sector_top.items():
        print(f"\n  {sec.upper()} (baseline {int(data['baseline']*100)}%) — top by engagement (n≥3):")
        for r in data["top_10_by_engagement"][:5]:
            lift = f"+{int(r['lift_vs_sector_baseline']*100)}pp" if r['lift_vs_sector_baseline'] >= 0 else f"{int(r['lift_vs_sector_baseline']*100)}pp"
            print(f"    {r['slug']:<42} {int(r['high_eng_rate']*100):>3}%  {lift}  n={r['count']}")
        if data["avoid"]:
            print(f"  AVOID:")
            for r in data["avoid"][:3]:
                print(f"    {r['slug']:<42} {int(r['high_eng_rate']*100):>3}%  n={r['count']}")

    if transfer:
        print(f"\n  Cross-sector transfer patterns (≥30pp gap):")
        for t in transfer[:5]:
            print(f"    {t['slug']:<42} best={t['best_sector']}({int(t['best_sector_rate']*100)}%)  worst={t['worst_sector']}({int(t['worst_sector_rate']*100)}%)")

    print(f"\nOutput: logs/pattern_sector_matrix.json")


if __name__ == "__main__":
    main()
