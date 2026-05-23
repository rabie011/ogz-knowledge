#!/usr/bin/env python3
"""
build_compliance_intelligence.py
Deep-dive into compliance risk across all observations.
Goes beyond the basic compliance_risk_report to break down:
  - Exact flag type frequency and engagement correlation
  - Account × flag type heat map
  - Sector risk profile
  - Patterns co-occurring with compliance flags (risky pattern combos)
Output: logs/compliance_intelligence.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}


def main():
    # Global counters
    hard_flag_counter = Counter()
    soft_flag_counter = Counter()

    # Per-flag engagement
    flag_eng = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"type":"soft"})

    # Per-account
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "hard_flags": Counter(),
        "soft_flags": Counter(),
        "risk_score": 0,
        "clean_obs": 0,
        "flagged_obs": 0,
        "eng_clean": {"count":0,"sum":0.0,"high":0},
        "eng_flagged": {"count":0,"sum":0.0,"high":0},
    })

    # Per-sector
    sectors = defaultdict(lambda: {
        "obs_count":0,"hard_count":0,"soft_count":0,"risk_total":0,
        "hard_types": Counter(), "soft_types": Counter(),
    })

    # Pattern × hard_flag co-occurrence
    pattern_flag_cooc = defaultdict(lambda: defaultdict(int))

    total = 0
    clean_obs = 0
    flagged_obs = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        account = data.get("account_handle_normalized","unknown")
        sector  = data.get("sector","unknown") or "unknown"
        accounts[account]["sector"] = sector
        accounts[account]["obs_count"] += 1
        sectors[sector]["obs_count"] += 1

        qa = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        cc = data.get("compliance_check",{}) or {}
        hard_blocks = cc.get("hard_blocks_triggered") or []
        soft_flags  = cc.get("soft_flags") or []

        is_flagged = bool(hard_blocks or soft_flags)

        if is_flagged:
            flagged_obs += 1
            accounts[account]["flagged_obs"] += 1
            accounts[account]["eng_flagged"]["count"] += 1
            accounts[account]["eng_flagged"]["sum"] += eng
            accounts[account]["eng_flagged"]["high"] += is_high
        else:
            clean_obs += 1
            accounts[account]["clean_obs"] += 1
            accounts[account]["eng_clean"]["count"] += 1
            accounts[account]["eng_clean"]["sum"] += eng
            accounts[account]["eng_clean"]["high"] += is_high

        for hb in hard_blocks:
            ft = hb.get("flag_type") if isinstance(hb, dict) else str(hb)
            if not ft: continue
            hard_flag_counter[ft] += 1
            accounts[account]["hard_flags"][ft] += 1
            accounts[account]["risk_score"] += 10
            sectors[sector]["hard_count"] += 1
            sectors[sector]["hard_types"][ft] += 1
            sectors[sector]["risk_total"] += 10
            flag_eng[f"HARD::{ft}"]["count"] += 1
            flag_eng[f"HARD::{ft}"]["high"] += is_high
            flag_eng[f"HARD::{ft}"]["sum"] += eng
            flag_eng[f"HARD::{ft}"]["type"] = "hard"
            # Pattern co-occurrence
            for pm in data.get("pattern_matches",[]):
                slug = pm.get("pattern_slug","") if isinstance(pm, dict) else pm
                if slug: pattern_flag_cooc[ft][slug] += 1

        for sf in soft_flags:
            ft = sf.get("flag_type") if isinstance(sf, dict) else str(sf)
            if not ft: continue
            soft_flag_counter[ft] += 1
            accounts[account]["soft_flags"][ft] += 1
            accounts[account]["risk_score"] += 1
            sectors[sector]["soft_count"] += 1
            sectors[sector]["soft_types"][ft] += 1
            sectors[sector]["risk_total"] += 1
            flag_eng[f"SOFT::{ft}"]["count"] += 1
            flag_eng[f"SOFT::{ft}"]["high"] += is_high
            flag_eng[f"SOFT::{ft}"]["sum"] += eng

    # Build flag table
    flag_table = []
    for key, data in sorted(flag_eng.items(), key=lambda x: -x[1]["count"]):
        n = data["count"]
        rate = round(data["high"]/n, 3) if n else 0
        avg  = round(data["sum"]/n, 3) if n else 0
        flag_type, flag_name = key.split("::", 1)
        flag_table.append({
            "flag_type": flag_type,
            "flag_name": flag_name,
            "frequency": n,
            "high_engagement_rate": rate,
            "avg_engagement": avg,
            "insight": "Flagged content still drives engagement" if rate > 0.5 else
                       "Compliance flags correlate with lower engagement",
        })
    flag_table.sort(key=lambda x: -x["frequency"])

    # Account risk profiles
    acc_profiles = []
    for acc, info in sorted(accounts.items()):
        n = info["obs_count"]
        risk_per_obs = round(info["risk_score"] / n, 2) if n else 0
        grade = "green" if info["risk_score"] <= 5 else \
                "yellow" if info["risk_score"] <= 15 else \
                "orange" if info["risk_score"] <= 30 else "red"

        # Clean vs flagged engagement
        c = info["eng_clean"]
        f = info["eng_flagged"]
        clean_eng = round(c["sum"]/c["count"],3) if c["count"] else None
        flag_eng_avg = round(f["sum"]/f["count"],3) if f["count"] else None

        acc_profiles.append({
            "account": acc,
            "sector": info["sector"],
            "obs_count": n,
            "risk_score": info["risk_score"],
            "risk_grade": grade,
            "risk_per_obs": risk_per_obs,
            "clean_obs": info["clean_obs"],
            "flagged_obs": info["flagged_obs"],
            "flagged_rate": round(info["flagged_obs"]/n, 3) if n else 0,
            "top_hard_flags": dict(info["hard_flags"].most_common(3)),
            "top_soft_flags": dict(info["soft_flags"].most_common(3)),
            "clean_avg_engagement": clean_eng,
            "flagged_avg_engagement": flag_eng_avg,
        })
    acc_profiles.sort(key=lambda x: -x["risk_score"])

    # Sector risk
    sector_profiles = {}
    for sec, s in sorted(sectors.items()):
        n = s["obs_count"]
        sector_profiles[sec] = {
            "obs_count": n,
            "total_hard_blocks": s["hard_count"],
            "total_soft_flags": s["soft_count"],
            "risk_score_total": s["risk_total"],
            "risk_per_obs": round(s["risk_total"]/n, 2) if n else 0,
            "top_hard_flag_types": dict(s["hard_types"].most_common(5)),
            "top_soft_flag_types": dict(s["soft_types"].most_common(5)),
        }

    # Pattern × flag co-occurrence (risky patterns)
    risky_pattern_combos = []
    for flag_type, pattern_counts in sorted(pattern_flag_cooc.items()):
        for slug, count in sorted(pattern_counts.items(), key=lambda x:-x[1])[:3]:
            if count >= 2:
                risky_pattern_combos.append({
                    "flag_type": flag_type,
                    "pattern_slug": slug,
                    "co_occurrence_count": count,
                    "warning": f"Pattern '{slug}' appears alongside hard block '{flag_type}' in {count} observations",
                })
    risky_pattern_combos.sort(key=lambda x: -x["co_occurrence_count"])

    # Clean vs flagged engagement delta
    clean_all = {"count":0,"sum":0.0,"high":0}
    flag_all  = {"count":0,"sum":0.0,"high":0}
    for info in accounts.values():
        for k in ("count","sum","high"):
            clean_all[k] += info["eng_clean"][k]
            flag_all[k]  += info["eng_flagged"][k]

    clean_rate = round(clean_all["high"]/clean_all["count"],3) if clean_all["count"] else 0
    flag_rate  = round(flag_all["high"]/flag_all["count"],3) if flag_all["count"] else 0

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_overview": {
            "total_obs": total,
            "clean_obs": clean_obs,
            "flagged_obs": flagged_obs,
            "flagged_rate": round(flagged_obs/total, 3) if total else 0,
            "unique_hard_flag_types": len(hard_flag_counter),
            "unique_soft_flag_types": len(soft_flag_counter),
        },
        "engagement_delta_clean_vs_flagged": {
            "clean_obs_high_engagement_rate": clean_rate,
            "flagged_obs_high_engagement_rate": flag_rate,
            "delta": round(clean_rate - flag_rate, 3),
            "insight": "Clean content has higher engagement rate" if clean_rate > flag_rate else
                       "Flagged content unexpectedly outperforms — review flag calibration",
        },
        "flag_frequency_table": flag_table,
        "top_hard_flags_fleet": [
            {"flag_type": ft, "count": c} for ft, c in hard_flag_counter.most_common(10)
        ],
        "top_soft_flags_fleet": [
            {"flag_type": ft, "count": c} for ft, c in soft_flag_counter.most_common(10)
        ],
        "account_risk_profiles": acc_profiles,
        "sector_risk_profiles": sector_profiles,
        "risky_pattern_combinations": risky_pattern_combos[:15],
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "compliance_intelligence.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Compliance intelligence: {total} obs | {flagged_obs} flagged ({round(flagged_obs/total*100)}%)")
    print(f"\nClean obs eng: {int(clean_rate*100)}% | Flagged obs eng: {int(flag_rate*100)}%")
    print(f"\nTop hard flags:")
    for ft, c in hard_flag_counter.most_common(8):
        print(f"  {c:3d}  {ft}")
    print(f"\nTop soft flags:")
    for ft, c in soft_flag_counter.most_common(8):
        print(f"  {c:3d}  {ft}")
    print(f"\nHighest-risk accounts:")
    for p in acc_profiles[:5]:
        print(f"  {p['account'][-30:]:<32} risk={p['risk_score']:3d} ({p['risk_grade']}) | "
              f"flagged={int(p['flagged_rate']*100)}% of posts")
    print(f"\nOutput: logs/compliance_intelligence.json")

if __name__ == "__main__":
    main()
