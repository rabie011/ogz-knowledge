#!/usr/bin/env python3
"""
build_visual_decision_tree.py
Algorithmic shoot planner for agency production teams.
Input: sector + occasion → Output: recommended setting → lighting → composition
       + predicted engagement for each recommended combination.
Also: reverse lookup — given a setting, what lighting and composition are proven?
Output: logs/visual_decision_tree.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def best_option(counter_dict: dict, min_n: int = 2):
    """Given {value: {count, high}}, return best value by engagement rate (min n)."""
    best_val = None; best_rate = -1
    for val, d in counter_dict.items():
        n = d["count"]
        if n >= min_n:
            rate = d["high"] / n
            if rate > best_rate:
                best_rate = rate
                best_val = val
    return best_val, round(best_rate, 3) if best_rate >= 0 else None


def sorted_options(counter_dict: dict, min_n: int = 1):
    """Return sorted list of {value, count, high_eng_rate}."""
    rows = []
    for val, d in counter_dict.items():
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        rows.append({"value": val, "count": n, "high_eng_rate": rate})
    rows.sort(key=lambda x: (-x["high_eng_rate"], -x["count"]))
    return [r for r in rows if r["count"] >= min_n]


def main():
    # Triple: sector × occasion → {setting, lighting, composition} → engagement
    sect_occ_tree = defaultdict(lambda: defaultdict(lambda: {
        "count": 0, "high": 0,
        "settings":     defaultdict(lambda: {"count":0,"high":0}),
        "lightings":    defaultdict(lambda: {"count":0,"high":0}),
        "compositions": defaultdict(lambda: {"count":0,"high":0}),
        "formats":      defaultdict(lambda: {"count":0,"high":0}),
        "registers":    defaultdict(lambda: {"count":0,"high":0}),
        "tones":        defaultdict(lambda: {"count":0,"high":0}),
    }))

    # Setting → lighting → composition chains
    setting_tree = defaultdict(lambda: {
        "count": 0, "high": 0,
        "lightings":    defaultdict(lambda: {"count":0,"high":0}),
        "compositions": defaultdict(lambda: {"count":0,"high":0}),
    })
    light_tree = defaultdict(lambda: {
        "count": 0, "high": 0,
        "compositions": defaultdict(lambda: {"count":0,"high":0}),
    })

    total = 0
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        cn  = data.get("cultural_notes",{}) or {}
        cr  = data.get("content_ref",{}) or {}
        vv  = data.get("visual_observations",{}) or {}
        vo  = data.get("voice_observations",{}) or {}
        qa  = data.get("quality_assessment",{}) or {}

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        sector  = data.get("sector","unknown") or "unknown"
        occ     = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"
        sett    = str(vv.get("setting","") or "").lower() or "unknown"
        light   = str(vv.get("lighting","") or "").lower() or "unknown"
        comp    = str(vv.get("composition_style","") or "").lower() or "unknown"
        fmt_raw = str(cr.get("content_type","") or "").lower()
        reg     = str(vo.get("register","") or "").lower() or "unknown"
        tone    = str(vo.get("tone","") or "").lower() or "unknown"

        # Sector × Occasion tree
        node = sect_occ_tree[sector][occ]
        node["count"]  += 1
        node["high"]   += is_high
        node["settings"][sett]["count"]      += 1
        node["settings"][sett]["high"]       += is_high
        node["lightings"][light]["count"]    += 1
        node["lightings"][light]["high"]     += is_high
        node["compositions"][comp]["count"]  += 1
        node["compositions"][comp]["high"]   += is_high
        node["registers"][reg]["count"]      += 1
        node["registers"][reg]["high"]       += is_high
        node["tones"][tone]["count"]         += 1
        node["tones"][tone]["high"]          += is_high
        node["formats"][fmt_raw]["count"]    += 1
        node["formats"][fmt_raw]["high"]     += is_high

        # Setting tree
        setting_tree[sett]["count"]  += 1
        setting_tree[sett]["high"]   += is_high
        setting_tree[sett]["lightings"][light]["count"]    += 1
        setting_tree[sett]["lightings"][light]["high"]     += is_high
        setting_tree[sett]["compositions"][comp]["count"]  += 1
        setting_tree[sett]["compositions"][comp]["high"]   += is_high

        # Lighting → composition
        light_tree[light]["count"]  += 1
        light_tree[light]["high"]   += is_high
        light_tree[light]["compositions"][comp]["count"] += 1
        light_tree[light]["compositions"][comp]["high"]  += is_high

    # Build sector × occasion decision nodes
    decision_nodes = {}
    for sector, occs in sect_occ_tree.items():
        decision_nodes[sector] = {}
        for occ, node in occs.items():
            n = node["count"]
            if n < 3: continue
            rate = round(node["high"]/n, 3)

            best_sett,  best_sett_rate  = best_option(node["settings"], min_n=2)
            best_light, best_light_rate = best_option(node["lightings"], min_n=2)
            best_comp,  best_comp_rate  = best_option(node["compositions"], min_n=2)
            best_reg,   best_reg_rate   = best_option(node["registers"], min_n=2)
            best_tone,  best_tone_rate  = best_option(node["tones"], min_n=2)

            decision_nodes[sector][occ] = {
                "obs_count": n,
                "occasion_high_eng_rate": rate,
                "recommended_production": {
                    "setting":     best_sett,
                    "setting_eng_rate": best_sett_rate,
                    "lighting":    best_light,
                    "lighting_eng_rate": best_light_rate,
                    "composition": best_comp,
                    "composition_eng_rate": best_comp_rate,
                    "register":    best_reg,
                    "register_eng_rate": best_reg_rate,
                    "tone":        best_tone,
                    "tone_eng_rate": best_tone_rate,
                },
                "setting_options":     sorted_options(node["settings"], min_n=1)[:5],
                "lighting_options":    sorted_options(node["lightings"], min_n=1)[:5],
                "composition_options": sorted_options(node["compositions"], min_n=1)[:5],
            }

    # Build setting → lighting → composition chain guide
    setting_guide = {}
    for sett, d in sorted(setting_tree.items(), key=lambda x: -x[1]["count"]):
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        best_light, best_light_rate = best_option(d["lightings"], min_n=2)
        best_comp,  best_comp_rate  = best_option(d["compositions"], min_n=2)
        setting_guide[sett] = {
            "total_obs": n,
            "high_eng_rate": rate,
            "best_lighting": best_light,
            "best_lighting_rate": best_light_rate,
            "best_composition": best_comp,
            "best_composition_rate": best_comp_rate,
            "lighting_options":    sorted_options(d["lightings"], min_n=1)[:5],
            "composition_options": sorted_options(d["compositions"], min_n=1)[:5],
        }

    # Lighting → best composition
    lighting_guide = {}
    for light, d in sorted(light_tree.items(), key=lambda x: -x[1]["count"]):
        n = d["count"]
        rate = round(d["high"]/n, 3) if n else 0
        best_comp, best_comp_rate = best_option(d["compositions"], min_n=2)
        lighting_guide[light] = {
            "total_obs": n,
            "high_eng_rate": rate,
            "best_composition": best_comp,
            "best_composition_rate": best_comp_rate,
            "composition_options": sorted_options(d["compositions"], min_n=1)[:5],
        }

    # Key findings
    findings = []
    for sector, occs in decision_nodes.items():
        for occ, node in sorted(occs.items(), key=lambda x: -x[1]["obs_count"])[:2]:
            p = node["recommended_production"]
            findings.append(
                f"{sector.upper()} × {occ.replace('_',' ').title()} "
                f"(n={node['obs_count']}, eng={int(node['occasion_high_eng_rate']*100)}%): "
                f"→ {p['setting']} + {p['lighting']} + {p['composition']}"
            )
    best_setting = max(setting_guide.items(), key=lambda x: x[1]["high_eng_rate"], default=(None,{}))
    if best_setting[0]:
        sg = best_setting[1]
        findings.append(f"Best setting: '{best_setting[0]}' ({int(sg['high_eng_rate']*100)}%) → {sg['best_lighting']} light + {sg['best_composition']} frame")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "sector_occasion_decision_tree": decision_nodes,
        "setting_guide": setting_guide,
        "lighting_composition_guide": lighting_guide,
        "key_findings": findings,
        "how_to_use": (
            "Step 1: client sector + content occasion → look up sector_occasion_decision_tree "
            "→ get recommended_production (setting, lighting, composition, register, tone). "
            "Step 2: confirm with setting_guide — use best_lighting and best_composition for that setting. "
            "Step 3: cross-check lighting_composition_guide to ensure lighting+framing alignment."
        ),
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "visual_decision_tree.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Visual decision tree: {total} obs")
    print(f"\nSetting guide (best lighting + composition):")
    print(f"  {'Setting':<26} {'HighEng':>8}  Best lighting           Best comp")
    print("  " + "─"*90)
    for sett, sg in sorted(setting_guide.items(), key=lambda x: -x[1]["high_eng_rate"]):
        print(f"  {sett:<26} {int(sg['high_eng_rate']*100):>7}%  {str(sg['best_lighting']):<22}  {sg['best_composition']}")
    print(f"\nOutput: logs/visual_decision_tree.json")


if __name__ == "__main__":
    main()
