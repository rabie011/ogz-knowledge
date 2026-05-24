#!/usr/bin/env python3
"""
build_tone_register_analysis.py
Tone × register × sector × occasion → voice direction for production briefs.
Output: logs/tone_register_analysis.json
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
    tone_eng   = defaultdict(list)
    reg_eng    = defaultdict(list)
    combo_eng  = defaultdict(list)   # (tone, register)
    sec_tone   = defaultdict(lambda: defaultdict(list))
    sec_reg    = defaultdict(lambda: defaultdict(list))
    occ_tone   = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        e    = _eng(d)
        if e is None: continue
        vo   = d.get("voice_observations", {})
        tone = (vo.get("tone") or "").strip().lower()[:40]
        reg  = (vo.get("register") or "").strip().lower()[:40]
        sec  = d.get("sector", "")
        occ  = d.get("occasion", "") or "evergreen"

        if tone: tone_eng[tone].append(e)
        if reg:  reg_eng[reg].append(e)
        if tone and reg: combo_eng[(tone, reg)].append(e)
        if tone and sec: sec_tone[sec][tone].append(e)
        if reg  and sec: sec_reg[sec][reg].append(e)
        if tone and occ: occ_tone[occ][tone].append(e)

    global_avg = sum(v for vals in tone_eng.values() for v in vals) / max(
        sum(len(v) for v in tone_eng.values()), 1)

    def _build(eng_dict, min_n=3):
        out = {}
        for k, vals in sorted(eng_dict.items(), key=lambda x: -(_avg(x[1]) or 0)):
            if len(vals) < min_n: continue
            avg = _avg(vals)
            out[k] = {
                "count": len(vals),
                "avg_engagement": avg,
                "lift_vs_avg": round(avg - global_avg, 3),
                "high_rate": round(sum(1 for v in vals if v >= 0.75) / len(vals), 3),
            }
        return out

    by_tone = _build(tone_eng, min_n=2)
    by_reg  = _build(reg_eng,  min_n=3)

    # Combo matrix min n=3
    combo_matrix = {}
    for (tone, reg), vals in combo_eng.items():
        if len(vals) < 3: continue
        avg = _avg(vals)
        combo_matrix[f"{tone}__{reg}"] = {
            "tone": tone, "register": reg,
            "count": len(vals), "avg_engagement": avg,
            "lift_vs_avg": round(avg - global_avg, 3),
        }

    # Best tone per sector
    best_tone_by_sector = {}
    for sec, tones in sec_tone.items():
        ranked = sorted(tones.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_tone_by_sector[sec] = [
            {"tone": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:4] if len(v) >= 2
        ]

    # Best register per sector
    best_reg_by_sector = {}
    for sec, regs in sec_reg.items():
        ranked = sorted(regs.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_reg_by_sector[sec] = [
            {"register": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:4] if len(v) >= 3
        ]

    # Best tone per occasion
    best_tone_by_occasion = {}
    for occ, tones in occ_tone.items():
        total = sum(len(v) for v in tones.values())
        if total < 5: continue
        ranked = sorted(tones.items(), key=lambda x: _avg(x[1]) or 0, reverse=True)
        best_tone_by_occasion[occ] = [
            {"tone": k, "avg_engagement": _avg(v), "n": len(v)}
            for k, v in ranked[:2] if len(v) >= 2
        ]

    best_combos = sorted(combo_matrix.values(), key=lambda x: -(x["avg_engagement"] or 0))

    rules = []
    if by_tone:
        best_t = list(by_tone.items())[0]
        worst_t= list(by_tone.items())[-1]
        rules.append(f"Best tone: '{best_t[0]}' ({best_t[1]['avg_engagement']:.0%}) "
                     f"— avoid: '{worst_t[0]}' ({worst_t[1]['avg_engagement']:.0%})")
    if by_reg:
        best_r = list(by_reg.items())[0]
        rules.append(f"Best register: '{best_r[0]}' ({best_r[1]['avg_engagement']:.0%})")
    if best_combos:
        bc = best_combos[0]
        rules.append(f"Best voice combo: tone='{bc['tone']}' + register='{bc['register']}' "
                     f"({bc['avg_engagement']:.0%}, n={bc['count']})")

    out = {
        "total_obs":             sum(len(v) for v in tone_eng.values()),
        "global_avg":            round(global_avg, 3),
        "by_tone":               by_tone,
        "by_register":           by_reg,
        "combo_matrix":          best_combos,
        "best_tone_by_sector":   best_tone_by_sector,
        "best_reg_by_sector":    best_reg_by_sector,
        "best_tone_by_occasion": best_tone_by_occasion,
        "agency_rules":          rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "tone_register_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Tone × register analysis — {out['total_obs']} obs  (global avg {global_avg:.0%})\n")
    print("Top tones:")
    for tone, data in list(by_tone.items())[:10]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {tone:<30}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nTop registers:")
    for reg, data in list(by_reg.items())[:8]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data["lift_vs_avg"] >= 0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {reg:<30}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for rule in rules:
        print(f"\n  ▸ {rule}")
    print("  Output → logs/tone_register_analysis.json")

if __name__ == "__main__":
    main()
