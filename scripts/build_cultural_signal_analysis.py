#!/usr/bin/env python3
"""
build_cultural_signal_analysis.py
The heritage × dialect × occasion cultural intelligence matrix.
heritage_vs_modern × dialect × regional_orientation × occasion → engagement.
Key finding: heritage beats modern by +18pp — package this for briefs.
Output: logs/cultural_signal_analysis.json
"""
import json
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d):
    return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""), None)

def _avg(vals):
    return round(sum(vals) / len(vals), 3) if vals else None

def main():
    hvm_eng    = defaultdict(list)   # heritage_vs_modern
    dial_eng   = defaultdict(list)   # dialect
    region_eng = defaultdict(list)   # regional_orientation
    hvm_occ    = defaultdict(lambda: defaultdict(list))
    hvm_sec    = defaultdict(lambda: defaultdict(list))
    dial_sec   = defaultdict(lambda: defaultdict(list))
    dial_occ   = defaultdict(lambda: defaultdict(list))
    hvm_dial   = defaultdict(list)   # combo (hvm, dialect)

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        e    = _eng(d)
        if e is None: continue
        cn   = d.get("cultural_notes", {})
        vo   = d.get("voice_observations", {})
        hvm  = cn.get("heritage_vs_modern", "")
        dial = (vo.get("dialect_detected") or "").strip().lower()
        reg  = (cn.get("regional_orientation_detected") or "").strip().lower()[:30]
        sec  = d.get("sector", "")
        occ  = d.get("occasion", "") or "evergreen"

        if hvm:  hvm_eng[hvm].append(e)
        if dial: dial_eng[dial].append(e)
        if reg:  region_eng[reg].append(e)
        if hvm and occ: hvm_occ[occ][hvm].append(e)
        if hvm and sec: hvm_sec[sec][hvm].append(e)
        if dial and sec: dial_sec[sec][dial].append(e)
        if dial and occ: dial_occ[occ][dial].append(e)
        if hvm and dial: hvm_dial[(hvm, dial)].append(e)

    global_avg = sum(v for vals in hvm_eng.values() for v in vals) / max(
        sum(len(v) for v in hvm_eng.values()), 1)

    def _build(eng_dict, min_n=3):
        return {
            k: {"count": len(v), "avg_engagement": _avg(v),
                "lift_vs_avg": round(_avg(v) - global_avg, 3),
                "high_rate": round(sum(1 for x in v if x >= 0.75) / len(v), 3)}
            for k, v in sorted(eng_dict.items(), key=lambda x: -(_avg(x[1]) or 0))
            if len(v) >= min_n
        }

    by_hvm    = _build(hvm_eng, min_n=3)
    by_dial   = _build(dial_eng, min_n=5)
    by_region = _build(region_eng, min_n=3)

    # hvm × dialect combo
    hvm_dial_matrix = {}
    for (hvm, dial), vals in hvm_dial.items():
        if len(vals) < 3: continue
        avg = _avg(vals)
        hvm_dial_matrix[f"{hvm}__{dial}"] = {
            "heritage_vs_modern": hvm, "dialect": dial,
            "count": len(vals), "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg, 3),
        }

    # hvm per occasion
    hvm_by_occasion = {}
    for occ, hvms in hvm_occ.items():
        total = sum(len(v) for v in hvms.values())
        if total < 5: continue
        ranked = sorted(hvms.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        hvm_by_occasion[occ] = [
            {"hvm": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked if len(v) >= 2
        ]

    # hvm per sector
    hvm_by_sector = {}
    for sec, hvms in hvm_sec.items():
        ranked = sorted(hvms.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        hvm_by_sector[sec] = [
            {"hvm": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked if len(v) >= 2
        ]

    # dial per sector
    dial_by_sector = {}
    for sec, dials in dial_sec.items():
        ranked = sorted(dials.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        dial_by_sector[sec] = [
            {"dialect": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:4] if len(v) >= 3
        ]

    # Best dialect per occasion
    dial_by_occasion = {}
    for occ, dials in dial_occ.items():
        total = sum(len(v) for v in dials.values())
        if total < 5: continue
        ranked = sorted(dials.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        dial_by_occasion[occ] = [
            {"dialect": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:2] if len(v) >= 2
        ]

    # Heritage uplift vs modern (key finding)
    h_avg = _avg(hvm_eng.get("heritage", []))
    m_avg = _avg(hvm_eng.get("modern", []))
    uplift = round(h_avg - m_avg, 3) if h_avg and m_avg else None

    rules = [
        f"Heritage beats modern by +{uplift:.0%} ({h_avg:.0%} vs {m_avg:.0%}) — use heritage cues in briefs"
    ] if uplift else []

    if by_dial:
        best_d = list(by_dial.items())[0]
        rules.append(f"Best dialect signal: '{best_d[0]}' ({best_d[1]['avg_engagement']:.0%})")

    best_combo = sorted(hvm_dial_matrix.values(), key=lambda x: -(x["avg_engagement"] or 0))
    if best_combo:
        bc = best_combo[0]
        rules.append(f"Best cultural combo: {bc['heritage_vs_modern']} + {bc['dialect']} "
                     f"({bc['avg_engagement']:.0%}, n={bc['count']})")

    out = {
        "total_obs":          sum(len(v) for v in hvm_eng.values()),
        "global_avg":         round(global_avg, 3),
        "heritage_uplift_vs_modern": uplift,
        "by_heritage_vs_modern": by_hvm,
        "by_dialect":         by_dial,
        "by_regional_orientation": by_region,
        "hvm_dialect_matrix": sorted(hvm_dial_matrix.values(), key=lambda x: -(x["avg_engagement"] or 0)),
        "hvm_by_occasion":    hvm_by_occasion,
        "hvm_by_sector":      hvm_by_sector,
        "dialect_by_sector":  dial_by_sector,
        "dialect_by_occasion":dial_by_occasion,
        "agency_rules":       rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "cultural_signal_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Cultural signal analysis — {out['total_obs']} obs  (global avg {global_avg:.0%})\n")
    print("Heritage vs Modern:")
    for k, data in by_hvm.items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {k:<12}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nDialect performance (n≥5):")
    for k, data in by_dial.items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {k:<25}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/cultural_signal_analysis.json")

if __name__ == "__main__":
    main()
