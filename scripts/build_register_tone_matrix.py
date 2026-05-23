#!/usr/bin/env python3
"""
build_register_tone_matrix.py
Cross-tab register × tone with engagement outcomes.
Shows which voice combination drives the best engagement.
Output: logs/register_tone_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def verdict(rate, n):
    if n < 3: return "insufficient_data"
    if rate >= 0.75: return "strong_positive"
    if rate >= 0.60: return "positive"
    if rate >= 0.45: return "neutral"
    return "avoid"


def main():
    combos       = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"register":"","tone":""})
    registers    = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    tones        = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    combo_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        vo   = data.get("voice_observations", {}) or {}
        reg  = str(vo.get("register") or "").lower().strip()
        tone = str(vo.get("tone") or "").lower().strip()
        if not reg or not tone: continue

        qa      = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector","unknown") or "unknown"

        total += 1
        key = f"{reg}::{tone}"
        combos[key]["count"]    += 1
        combos[key]["high"]     += is_high
        combos[key]["sum"]      += eng
        combos[key]["register"]  = reg
        combos[key]["tone"]      = tone

        registers[reg]["count"] += 1
        registers[reg]["high"]  += is_high
        registers[reg]["sum"]   += eng

        tones[tone]["count"] += 1
        tones[tone]["high"]  += is_high
        tones[tone]["sum"]   += eng

        combo_sector[key][sector]["count"] += 1
        combo_sector[key][sector]["high"]  += is_high

    # Build combo table
    combo_table = []
    for key, d in combos.items():
        n    = d["count"]
        rate = round(d["high"] / n, 3) if n else 0
        avg  = round(d["sum"]  / n, 3) if n else 0
        sector_breakdown = {}
        for sec, sd in combo_sector[key].items():
            sn = sd["count"]
            sector_breakdown[sec] = {
                "count": sn,
                "high_eng_rate": round(sd["high"] / sn, 3) if sn else 0,
            }
        combo_table.append({
            "register": d["register"],
            "tone": d["tone"],
            "combo": key,
            "obs_count": n,
            "high_engagement_rate": rate,
            "avg_engagement_score": avg,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "verdict": verdict(rate, n),
            "sector_breakdown": sector_breakdown,
        })
    combo_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Register table
    reg_table = sorted([
        {
            "register": reg,
            "obs_count": d["count"],
            "high_engagement_rate": round(d["high"]/d["count"],3) if d["count"] else 0,
            "lift_vs_baseline": round(d["high"]/d["count"] - CORPUS_BASELINE, 3) if d["count"] else 0,
            "verdict": verdict(round(d["high"]/d["count"],3) if d["count"] else 0, d["count"]),
        }
        for reg, d in registers.items()
    ], key=lambda x: -x["high_engagement_rate"])

    # Tone table
    tone_table = sorted([
        {
            "tone": tone,
            "obs_count": d["count"],
            "high_engagement_rate": round(d["high"]/d["count"],3) if d["count"] else 0,
            "lift_vs_baseline": round(d["high"]/d["count"] - CORPUS_BASELINE, 3) if d["count"] else 0,
            "verdict": verdict(round(d["high"]/d["count"],3) if d["count"] else 0, d["count"]),
        }
        for tone, d in tones.items()
    ], key=lambda x: -x["high_engagement_rate"])

    top_combos    = [c for c in combo_table if c["obs_count"] >= 3]
    bottom_combos = [c for c in reversed(combo_table) if c["obs_count"] >= 3]

    # Key findings
    findings = []
    if reg_table:
        best_reg  = reg_table[0]
        worst_reg = [r for r in reg_table if r["obs_count"] >= 5]
        findings.append(f"Best register: {best_reg['register']} ({int(best_reg['high_engagement_rate']*100)}% high eng, n={best_reg['obs_count']})")
        if worst_reg:
            findings.append(f"Worst register (n≥5): {worst_reg[-1]['register']} ({int(worst_reg[-1]['high_engagement_rate']*100)}%)")
    if tone_table:
        best_tone = tone_table[0]
        findings.append(f"Best tone: {best_tone['tone']} ({int(best_tone['high_engagement_rate']*100)}% high eng, n={best_tone['obs_count']})")
    if top_combos:
        c = top_combos[0]
        findings.append(f"Best combo: {c['register']} × {c['tone']} ({int(c['high_engagement_rate']*100)}% high eng, n={c['obs_count']})")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline_high_eng_rate": CORPUS_BASELINE,
        "total_obs_with_both_fields": total,
        "unique_combos": len(combo_table),
        "register_performance": reg_table,
        "tone_performance": tone_table,
        "combo_matrix": combo_table,
        "top_10_combos": top_combos[:10],
        "bottom_5_combos": bottom_combos[:5],
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "register_tone_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Register × tone matrix: {total} obs, {len(combo_table)} unique combos")
    print(f"\n{'Register':<22} {'HighEng':>8}  {'Lift':>7}  {'n':>5}  Verdict")
    print("─" * 62)
    for r in reg_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['register']:<20} {int(r['high_engagement_rate']*100):>7}%  {lift:>7}  {r['obs_count']:>5}  {r['verdict']}")

    print(f"\n{'Tone':<22} {'HighEng':>8}  {'Lift':>7}  {'n':>5}  Verdict")
    print("─" * 62)
    for t in tone_table:
        lift = f"+{int(t['lift_vs_baseline']*100)}%" if t['lift_vs_baseline'] >= 0 else f"{int(t['lift_vs_baseline']*100)}%"
        print(f"  {t['tone']:<20} {int(t['high_engagement_rate']*100):>7}%  {lift:>7}  {t['obs_count']:>5}  {t['verdict']}")

    print(f"\nTop combos (n≥3):")
    print(f"\n{'Register × Tone':<38} {'HighEng':>8}  {'n':>5}  Verdict")
    print("─" * 68)
    for c in top_combos[:10]:
        label = f"{c['register']} × {c['tone']}"
        print(f"  {label:<36} {int(c['high_engagement_rate']*100):>7}%  {c['obs_count']:>5}  {c['verdict']}")

    print(f"\nOutput: logs/register_tone_matrix.json")


if __name__ == "__main__":
    main()
