#!/usr/bin/env python3
"""
build_cta_language_signals.py
Two unmined voice dimensions with direct agency impact:
  1. call_to_action_present (True/False) × engagement — should we always add a CTA?
  2. language (arabic/english/bilingual/none) × engagement — which language wins?
Both crossed with sector, occasion, media_type, and register.
Output: logs/cta_language_signals.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def cross_tab(data_dict):
    """Summarise a dict[key][subkey] = {count, high} into sorted rows."""
    rows = []
    for k, sub in data_dict.items():
        for sk, d in sub.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            rows.append({"key": k, "sub_key": sk, "count": n,
                          "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)})
    rows.sort(key=lambda x: (-x["high_eng_rate"], -x["count"]))
    return rows


def main():
    # CTA trackers
    cta_base    = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    cta_sector  = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    cta_occ     = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    cta_media   = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    cta_register= defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    # Language trackers
    lang_base    = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    lang_sector  = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    lang_occ     = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    lang_media   = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    lang_register= defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vo  = data.get("voice_observations",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}
        cn  = data.get("cultural_notes",{}) or {}
        cr  = data.get("content_ref",{}) or {}

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        sector   = data.get("sector","unknown") or "unknown"
        occ      = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"
        media    = str(cr.get("content_type","") or "").lower() or "unknown"
        register = str(vo.get("register","") or "").lower() or "unknown"

        # CTA
        cta_raw = vo.get("call_to_action_present")
        if cta_raw is not None:
            cta_label = "cta_present" if str(cta_raw).lower() in ("true","1","yes") else "no_cta"
            cta_base[cta_label]["count"]  += 1
            cta_base[cta_label]["high"]   += is_high
            cta_base[cta_label]["sum"]    += eng
            cta_sector[cta_label][sector]["count"]   += 1
            cta_sector[cta_label][sector]["high"]    += is_high
            cta_occ[cta_label][occ]["count"]         += 1
            cta_occ[cta_label][occ]["high"]          += is_high
            cta_media[cta_label][media]["count"]     += 1
            cta_media[cta_label][media]["high"]      += is_high
            cta_register[cta_label][register]["count"] += 1
            cta_register[cta_label][register]["high"]  += is_high

        # Language
        lang_raw = str(vo.get("language","") or "").lower().strip()
        if lang_raw and lang_raw not in ("","null","none","unknown"):
            lang_base[lang_raw]["count"]  += 1
            lang_base[lang_raw]["high"]   += is_high
            lang_base[lang_raw]["sum"]    += eng
            lang_sector[lang_raw][sector]["count"]   += 1
            lang_sector[lang_raw][sector]["high"]    += is_high
            lang_occ[lang_raw][occ]["count"]         += 1
            lang_occ[lang_raw][occ]["high"]          += is_high
            lang_media[lang_raw][media]["count"]     += 1
            lang_media[lang_raw][media]["high"]      += is_high
            lang_register[lang_raw][register]["count"] += 1
            lang_register[lang_raw][register]["high"]  += is_high

    # CTA summary table
    cta_table = []
    for label, d in cta_base.items():
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        cta_table.append({
            "cta": label, "count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    cta_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Language summary table
    lang_table = []
    for lang, d in lang_base.items():
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        lang_table.append({
            "language": lang, "count": n,
            "high_engagement_rate": rate,
            "avg_engagement": round(d["sum"]/n, 3),
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
        })
    lang_table.sort(key=lambda x: -x["high_engagement_rate"])

    # CTA × sector breakdown
    cta_sector_rows = []
    for label, sectors in cta_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            cta_sector_rows.append({
                "cta": label, "sector": sector, "count": n,
                "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
            })
    cta_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Language × sector breakdown
    lang_sector_rows = []
    for lang, sectors in lang_sector.items():
        for sector, d in sectors.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            lang_sector_rows.append({
                "language": lang, "sector": sector, "count": n,
                "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
            })
    lang_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Language × occasion (strategic for national day, Ramadan etc)
    lang_occ_rows = []
    for lang, occs in lang_occ.items():
        for occ, d in occs.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            if n >= 2:
                lang_occ_rows.append({
                    "language": lang, "occasion": occ, "count": n,
                    "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
                })
    lang_occ_rows.sort(key=lambda x: -x["high_eng_rate"])

    # CTA × register (does CTA + casual = better?)
    cta_register_rows = []
    for label, regs in cta_register.items():
        for reg, d in regs.items():
            n = d["count"]
            rate = round(d["high"]/n, 3) if n else 0
            if n >= 3:
                cta_register_rows.append({
                    "cta": label, "register": reg, "count": n,
                    "high_eng_rate": rate, "lift": round(rate - CORPUS_BASELINE, 3)
                })
    cta_register_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Key findings
    findings = []
    cta_present = next((r for r in cta_table if r["cta"] == "cta_present"), None)
    cta_absent  = next((r for r in cta_table if r["cta"] == "no_cta"), None)
    if cta_present and cta_absent:
        diff = round(cta_present["high_engagement_rate"] - cta_absent["high_engagement_rate"], 3)
        direction = "helps" if diff > 0.05 else "hurts" if diff < -0.05 else "neutral"
        findings.append(
            f"CTA impact: present={int(cta_present['high_engagement_rate']*100)}% vs absent={int(cta_absent['high_engagement_rate']*100)}% "
            f"— CTA {direction} engagement ({'+' if diff>=0 else ''}{int(diff*100)}pp)"
        )
    if lang_table:
        best_lang = lang_table[0]
        worst_lang = lang_table[-1]
        findings.append(
            f"Best language: '{best_lang['language']}' = {int(best_lang['high_engagement_rate']*100)}% high eng (n={best_lang['count']})"
        )
        findings.append(
            f"Worst language: '{worst_lang['language']}' = {int(worst_lang['high_engagement_rate']*100)}% high eng (n={worst_lang['count']})"
        )
    # National day language insight
    nat_day_langs = [r for r in lang_occ_rows if r["occasion"] == "national_day"]
    if nat_day_langs:
        best_nd = nat_day_langs[0]
        findings.append(
            f"National Day: best language = '{best_nd['language']}' at {int(best_nd['high_eng_rate']*100)}% (n={best_nd['count']})"
        )
    # Ramadan language insight
    ram_langs = [r for r in lang_occ_rows if r["occasion"] == "ramadan"]
    if ram_langs:
        best_r = ram_langs[0]
        findings.append(
            f"Ramadan: best language = '{best_r['language']}' at {int(best_r['high_eng_rate']*100)}% (n={best_r['count']})"
        )

    # Agency rules derived
    agency_rules = []
    if cta_present and cta_absent:
        diff = cta_present["high_engagement_rate"] - cta_absent["high_engagement_rate"]
        if diff > 0.05:
            agency_rules.append("ALWAYS add a CTA — it lifts engagement across corpus")
        elif diff < -0.05:
            agency_rules.append("SKIP CTA for heritage/storytelling content — it hurts engagement")
        else:
            agency_rules.append("CTA is neutral corpus-wide — decide by content goal, not habit")
    if lang_table:
        top = lang_table[0]
        agency_rules.append(f"Default to '{top['language']}' captions — highest engagement rate at {int(top['high_engagement_rate']*100)}%")
    for r in lang_occ_rows[:3]:
        if r["count"] >= 3:
            agency_rules.append(f"{r['occasion'].replace('_',' ').title()}: use '{r['language']}' captions ({int(r['high_eng_rate']*100)}%)")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "cta_engagement_table": cta_table,
        "language_engagement_table": lang_table,
        "cta_by_sector": cta_sector_rows,
        "language_by_sector": lang_sector_rows,
        "language_by_occasion": lang_occ_rows,
        "cta_by_register": cta_register_rows,
        "agency_rules": agency_rules,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "cta_language_signals.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"CTA + Language signals: {total} obs")
    print(f"\nCTA impact:")
    for r in cta_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['cta']:<18} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['count']}")
    print(f"\nLanguage → engagement:")
    for r in lang_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['language']:<14} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/cta_language_signals.json")


if __name__ == "__main__":
    main()
