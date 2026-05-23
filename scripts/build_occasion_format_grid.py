#!/usr/bin/env python3
"""
build_occasion_format_grid.py
For each of the 16 canonical occasions, compute the optimal
pattern + media_type + setting + lighting combination.
Direct campaign planning tool.
Output: logs/occasion_format_grid.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"
PATTERNS = BASE / "11_who_to_learn_from" / "patterns"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

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

    # Per occasion aggregation
    occasions = defaultdict(lambda: {
        "obs_count": 0,
        "high_count": 0,
        "eng_sum": 0.0,
        "patterns": Counter(),
        "pattern_eng": defaultdict(lambda: {"count":0,"high":0,"sum":0.0}),
        "media_types": Counter(),
        "media_eng": defaultdict(lambda: {"count":0,"high":0}),
        "settings": Counter(),
        "lightings": Counter(),
        "compositions": Counter(),
        "accounts": set(),
        "sectors": Counter(),
        "tones": Counter(),
        "registers": Counter(),
    })

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        cn = data.get("cultural_notes", {}) or {}
        occ = str(cn.get("occasion_relevance") or "evergreen").lower().strip()
        if not occ or occ in ("null", "none", ""):
            occ = "evergreen"

        qa = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        o = occasions[occ]
        o["obs_count"] += 1
        o["high_count"] += is_high
        o["eng_sum"] += eng
        o["accounts"].add(data.get("account_handle_normalized","?"))
        o["sectors"][data.get("sector","?")] += 1

        cr = data.get("content_ref", {}) or {}
        mt = str(cr.get("content_type","") or "").lower()
        if mt:
            o["media_types"][mt] += 1
            o["media_eng"][mt]["count"] += 1
            o["media_eng"][mt]["high"] += is_high

        vv = data.get("visual_observations", {}) or {}
        if vv.get("setting"): o["settings"][vv["setting"]] += 1
        if vv.get("lighting"): o["lightings"][vv["lighting"]] += 1
        if vv.get("composition_style"): o["compositions"][vv["composition_style"]] += 1

        vo = data.get("voice_observations", {}) or {}
        if vo.get("tone"): o["tones"][vo["tone"]] += 1
        if vo.get("register"): o["registers"][vo["register"]] += 1

        for pm in data.get("pattern_matches", []):
            slug = pm.get("pattern_slug","") if isinstance(pm, dict) else pm
            if not slug: continue
            o["patterns"][slug] += 1
            o["pattern_eng"][slug]["count"] += 1
            o["pattern_eng"][slug]["high"] += is_high
            o["pattern_eng"][slug]["sum"] += eng

    # Build grid
    grid = []
    for occ, o in sorted(occasions.items(), key=lambda x: -x[1]["obs_count"]):
        n = o["obs_count"]
        if n == 0: continue
        avg_eng = round(o["eng_sum"] / n, 3)
        high_rate = round(o["high_count"] / n, 3)

        # Top patterns with engagement
        top_patterns = []
        for slug, count in o["patterns"].most_common(5):
            pe = o["pattern_eng"][slug]
            nn = pe["count"]
            rate = round(pe["high"] / nn, 3) if nn else 0
            top_patterns.append({
                "slug": slug,
                "name": pattern_names.get(slug, slug),
                "count": count,
                "high_engagement_rate": rate,
            })

        # Best media type by engagement
        best_media = None
        best_media_rate = -1
        for mt, me in o["media_eng"].items():
            if me["count"] >= 2:
                rate = me["high"] / me["count"]
                if rate > best_media_rate:
                    best_media_rate = rate
                    best_media = mt

        def top1(counter): return counter.most_common(1)[0][0] if counter else None
        def top3(counter): return [k for k, _ in counter.most_common(3)]

        grid.append({
            "occasion": occ,
            "obs_count": n,
            "account_count": len(o["accounts"]),
            "high_engagement_rate": high_rate,
            "avg_engagement_score": avg_eng,
            "top_sectors": dict(o["sectors"].most_common(3)),
            "recommended_recipe": {
                "best_media_type": best_media or top1(o["media_types"]),
                "best_media_high_eng_rate": round(best_media_rate, 3) if best_media_rate >= 0 else None,
                "dominant_setting": top1(o["settings"]),
                "dominant_lighting": top1(o["lightings"]),
                "dominant_composition": top1(o["compositions"]),
                "dominant_tone": top1(o["tones"]),
                "dominant_register": top1(o["registers"]),
            },
            "top_5_patterns": top_patterns,
            "media_type_breakdown": {
                mt: {
                    "count": o["media_types"][mt],
                    "high_eng_rate": round(o["media_eng"][mt]["high"] / o["media_eng"][mt]["count"], 3)
                    if o["media_eng"][mt]["count"] >= 2 else None
                }
                for mt in o["media_types"]
            },
        })

    grid.sort(key=lambda x: -x["high_engagement_rate"])

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_occasions": len(grid),
        "how_to_read": "Each occasion shows the top-performing pattern + format combination from corpus evidence. Use recommended_recipe as the starting point for campaign briefs.",
        "occasion_grid": grid,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "occasion_format_grid.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Occasion-format grid: {len(grid)} occasions")
    print(f"\n{'Occasion':<25} {'n':>4}  {'HighEng':>8}  {'BestFormat':<18}  TopPattern")
    print("─" * 90)
    for g in grid:
        rec = g["recommended_recipe"]
        top_pat = g["top_5_patterns"][0]["slug"] if g["top_5_patterns"] else "—"
        print(f"  {g['occasion']:<23} {g['obs_count']:>4}  {int(g['high_engagement_rate']*100):>7}%  "
              f"{(rec['best_media_type'] or '—'):<18}  {top_pat}")
    print(f"\nOutput: logs/occasion_format_grid.json")

if __name__ == "__main__":
    main()
