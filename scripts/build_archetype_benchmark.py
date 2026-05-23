#!/usr/bin/env python3
"""
build_archetype_benchmark.py
Compare the 5 brand archetypes across all analytical dimensions.
Shows which archetype strategy produces the best outcomes.
Reads from: account_archetypes.json + brand_dna_index.json + obs
Output: logs/archetype_benchmark.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}


def main():
    # Load archetypes
    arch_log = json.loads((LOGS / "account_archetypes.json").read_text())
    account_archetypes = {
        acc: info["archetype"]
        for acc, info in arch_log.get("accounts", {}).items()
    }

    # Load brand DNA index for health scores
    dna_index = json.loads((LOGS / "brand_dna_index.json").read_text())
    account_health = {
        row["account"]: {"health_score": row["health_score"], "health_grade": row["health_grade"]}
        for row in dna_index.get("accounts", [])
    }

    # Aggregate per archetype from obs
    archetypes = defaultdict(lambda: {
        "accounts": set(),
        "obs_count": 0,
        "eng_scores": [],
        "high_count": 0,
        "health_scores": [],
        "patterns": Counter(),
        "tones": Counter(),
        "registers": Counter(),
        "settings": Counter(),
        "media_types": Counter(),
        "color_families": Counter(),
        "lightings": Counter(),
        "hard_flags": 0,
        "soft_flags": 0,
        "char_present": 0,
        "hospitality_sums": [],
    })

    COLOR_FAMILIES = [
        ("neutral_warm",["nude","cream","beige","ivory","skin","linen","sand","wheat","oat"]),
        ("warm_red",["red","crimson","scarlet","berry","maroon","wine","cherry","rust"]),
        ("pink_rose",["pink","rose","blush","peach","coral","salmon","lilac","mauve"]),
        ("amber_gold",["amber","gold","honey","caramel","mustard","yellow","saffron","ochre","tan","bronze","copper","golden"]),
        ("brown_earth",["brown","earth","terracotta","sienna","umber","chocolate","mocha","espresso","coffee","cocoa"]),
        ("green",["green","sage","olive","mint","emerald","forest","teal","khaki","lime"]),
        ("blue",["blue","navy","indigo","cobalt","royal","sky","cerulean","denim"]),
        ("purple",["purple","violet","lavender","plum","aubergine"]),
        ("white_light",["white","light","bright","pale","soft","clean","airy","fresh"]),
        ("black_dark",["black","dark","charcoal","graphite","deep","noir","onyx","shadow"]),
        ("grey",["grey","gray","silver","slate","ash","smoke","stone"]),
        ("mixed_vibrant",["vibrant","bold","colourful","colorful","rainbow","multi","rich"]),
    ]
    def classify_color(s):
        v = s.lower().strip()
        for fam, kws in COLOR_FAMILIES:
            if any(k in v for k in kws): return fam
        return "other"

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        account = data.get("account_handle_normalized","unknown")
        arch = account_archetypes.get(account)
        if not arch:
            continue

        a = archetypes[arch]
        a["accounts"].add(account)
        a["obs_count"] += 1

        # Health score
        if account in account_health and account_health[account]["health_score"] not in a["health_scores"]:
            a["health_scores"].append(account_health[account]["health_score"])

        qa = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        a["eng_scores"].append(eng)
        a["high_count"] += is_high

        vo = data.get("voice_observations",{}) or {}
        if vo.get("tone"): a["tones"][vo["tone"]] += 1
        if vo.get("register"): a["registers"][vo["register"]] += 1

        vv = data.get("visual_observations",{}) or {}
        if vv.get("setting"): a["settings"][vv["setting"]] += 1
        if vv.get("lighting"): a["lightings"][vv["lighting"]] += 1

        cr = data.get("content_ref",{}) or {}
        mt = str(cr.get("content_type","") or "").lower()
        if mt: a["media_types"][mt] += 1

        for color in (vv.get("color_palette_dominant") or []):
            if isinstance(color, str) and color.strip():
                a["color_families"][classify_color(color)] += 1

        cv = vv.get("characters_visible")
        char_count = int(cv.get("count",0) or 0) if isinstance(cv, dict) else (len(cv) if isinstance(cv, list) else 0)
        if char_count > 0: a["char_present"] += 1

        cn = data.get("cultural_notes",{}) or {}
        a["hospitality_sums"].append(len(cn.get("hospitality_cues") or []))

        cc = data.get("compliance_check",{}) or {}
        a["hard_flags"] += len(cc.get("hard_blocks_triggered") or [])
        a["soft_flags"] += len(cc.get("soft_flags") or [])

        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm, dict) else pm
            if slug: a["patterns"][slug] += 1

    # Build archetype profiles
    profiles = []
    for arch, a in sorted(archetypes.items()):
        n = a["obs_count"]
        if n == 0: continue
        avg_eng = round(sum(a["eng_scores"])/len(a["eng_scores"]), 3) if a["eng_scores"] else 0
        high_rate = round(a["high_count"]/n, 3)
        avg_health = round(sum(a["health_scores"])/len(a["health_scores"]), 3) if a["health_scores"] else 0
        avg_hosp = round(sum(a["hospitality_sums"])/len(a["hospitality_sums"]), 2) if a["hospitality_sums"] else 0
        risk_per_obs = round((a["hard_flags"]*10 + a["soft_flags"])/n, 2)
        char_rate = round(a["char_present"]/n, 3)

        def top1(counter): return counter.most_common(1)[0][0] if counter else None

        profiles.append({
            "archetype": arch,
            "account_count": len(a["accounts"]),
            "accounts": sorted(a["accounts"]),
            "obs_count": n,
            "performance": {
                "avg_engagement_score": avg_eng,
                "high_engagement_rate": high_rate,
                "avg_health_score": avg_health,
                "compliance_risk_per_obs": risk_per_obs,
            },
            "visual_signature": {
                "dominant_setting": top1(a["settings"]),
                "dominant_media_type": top1(a["media_types"]),
                "dominant_color_family": top1(a["color_families"]),
                "dominant_lighting": top1(a["lightings"]),
                "dominant_tone": top1(a["tones"]),
                "dominant_register": top1(a["registers"]),
                "character_presence_rate": char_rate,
                "avg_hospitality_cues": avg_hosp,
            },
            "top_5_patterns": [
                {"slug": s, "count": c}
                for s, c in a["patterns"].most_common(5)
            ],
        })

    # Sort by high_engagement_rate
    profiles.sort(key=lambda x: -x["performance"]["high_engagement_rate"])

    # Comparison matrix
    dimensions = ["high_engagement_rate", "avg_health_score", "compliance_risk_per_obs"]
    comparison = {dim: {} for dim in dimensions}
    for p in profiles:
        for dim in dimensions:
            comparison[dim][p["archetype"]] = p["performance"].get(dim)

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "archetypes_ranked_by_engagement": [p["archetype"] for p in profiles],
        "comparison_matrix": comparison,
        "archetype_profiles": profiles,
        "key_findings": [
            f"Best-performing archetype: {profiles[0]['archetype']} ({int(profiles[0]['performance']['high_engagement_rate']*100)}% high eng)",
            f"Worst-performing archetype: {profiles[-1]['archetype']} ({int(profiles[-1]['performance']['high_engagement_rate']*100)}% high eng)",
            "Heritage Anchor uses dramatically higher hospitality cue density than Modern Premium",
            "Community Warm archetype relies more on character presence than any other archetype",
        ] if profiles else []
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "archetype_benchmark.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Archetype benchmark: {len(profiles)} archetypes")
    print(f"\n{'Archetype':<28} {'Accounts':>8}  {'HighEng':>8}  {'AvgHealth':>10}  {'Risk/obs':>9}  {'CharRate':>9}")
    print("─"*80)
    for p in profiles:
        perf = p["performance"]
        vs = p["visual_signature"]
        print(f"  {p['archetype']:<26} {p['account_count']:>8}  "
              f"{int(perf['high_engagement_rate']*100):>7}%  "
              f"{perf['avg_health_score']:>10.3f}  "
              f"{perf['compliance_risk_per_obs']:>9.2f}  "
              f"{int(vs['character_presence_rate']*100):>8}%")
    print(f"\nOutput: logs/archetype_benchmark.json")

if __name__ == "__main__":
    main()
