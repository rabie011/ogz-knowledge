#!/usr/bin/env python3
"""
build_setting_lighting_synergy.py
12 settings × 9 lightings = 108 possible combinations.
Which specific (setting, lighting) pair achieves the highest engagement?
Also: best lighting for each setting, best setting for each lighting.
Output: logs/setting_lighting_synergy.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def main():
    pairs  = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    by_setting  = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    by_lighting = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv  = data.get("visual_observations",{}) or {}
        setting  = vv.get("setting")  or None
        lighting = vv.get("lighting") or None
        if not setting or not lighting: continue

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        key = (setting, lighting)
        pairs[key]["count"] += 1
        pairs[key]["high"]  += is_high
        pairs[key]["sum"]   += eng

        by_setting[setting][lighting]["count"] += 1
        by_setting[setting][lighting]["high"]  += is_high
        by_lighting[lighting][setting]["count"] += 1
        by_lighting[lighting][setting]["high"]  += is_high

    # Full pair table
    pair_table = []
    for (setting, lighting), d in pairs.items():
        n = d["count"]
        if n == 0: continue
        rate = round(d["high"]/n, 3)
        pair_table.append({
            "setting": setting,
            "lighting": lighting,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    pair_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Best lighting per setting
    best_lighting_per_setting = {}
    for setting, lightings in by_setting.items():
        best = None; best_rate = -1
        rows = []
        for light, d in lightings.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            rows.append({"lighting":light,"count":n,"high_eng_rate":rate})
            if n >= 2 and rate > best_rate:
                best_rate = rate; best = light
        rows.sort(key=lambda x: -x["high_eng_rate"])
        best_lighting_per_setting[setting] = {
            "best_lighting": best,
            "best_rate": round(best_rate,3) if best_rate >= 0 else None,
            "all_lightings": rows,
        }

    # Best setting per lighting
    best_setting_per_lighting = {}
    for lighting, settings in by_lighting.items():
        best = None; best_rate = -1
        rows = []
        for setting, d in settings.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            rows.append({"setting":setting,"count":n,"high_eng_rate":rate})
            if n >= 2 and rate > best_rate:
                best_rate = rate; best = setting
        rows.sort(key=lambda x: -x["high_eng_rate"])
        best_setting_per_lighting[lighting] = {
            "best_setting": best,
            "best_rate": round(best_rate,3) if best_rate >= 0 else None,
            "all_settings": rows,
        }

    findings = []
    top_pairs = [p for p in pair_table if p["obs_count"] >= 3]
    if top_pairs:
        t = top_pairs[0]
        findings.append(
            f"Best pair (n≥3): {t['setting']} + {t['lighting']} = {int(t['high_engagement_rate']*100)}% high eng"
        )
    if top_pairs:
        worst = [p for p in pair_table if p["obs_count"] >= 3][-1]
        findings.append(
            f"Worst pair (n≥3): {worst['setting']} + {worst['lighting']} = {int(worst['high_engagement_rate']*100)}%"
        )
    for setting, info in best_lighting_per_setting.items():
        if info["best_lighting"] and info["best_rate"] and info["best_rate"] >= 0.80:
            findings.append(
                f"'{setting}' + '{info['best_lighting']}' = {int(info['best_rate']*100)}% — premium combo"
            )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "pair_table": pair_table,
        "top_20_pairs": [p for p in pair_table if p["obs_count"] >= 2][:20],
        "best_lighting_per_setting": best_lighting_per_setting,
        "best_setting_per_lighting": best_setting_per_lighting,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "setting_lighting_synergy.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Setting × lighting synergy: {total} obs, {len(pair_table)} unique pairs")
    print(f"\nTop pairs (n≥3):")
    print(f"  {'Setting':<24} {'Lighting':<22} {'HighEng':>8}  {'n':>4}  Lift")
    print("  " + "─"*75)
    for p in [x for x in pair_table if x["obs_count"] >= 3][:12]:
        lift = f"+{int(p['lift_vs_baseline']*100)}%" if p['lift_vs_baseline']>=0 else f"{int(p['lift_vs_baseline']*100)}%"
        print(f"  {p['setting']:<24} {p['lighting']:<22} {int(p['high_engagement_rate']*100):>7}%  {p['obs_count']:>4}  {lift}")
    print(f"\nBest lighting per setting:")
    for setting, info in sorted(best_lighting_per_setting.items(),
                                  key=lambda x: -(x[1]["best_rate"] or 0)):
        if info["best_lighting"]:
            print(f"  {setting:<26} → {info['best_lighting']:<24} {int((info['best_rate'] or 0)*100):>3}%")
    print(f"\nOutput: logs/setting_lighting_synergy.json")

if __name__ == "__main__":
    main()
