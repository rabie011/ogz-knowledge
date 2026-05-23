#!/usr/bin/env python3
"""
build_pattern_cooccurrence.py
Mine pattern co-occurrences from 474 observations.
Outputs:
  logs/pattern_cooccurrence_matrix.json  — full pair matrix
  logs/content_recipe_combos.json        — human-readable top recipe combos
"""
import json
from pathlib import Path
from collections import defaultdict
from itertools import combinations

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS_ROOT = BASE / "11_who_to_learn_from" / "patterns"
LOGS = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}

def load_pattern_names():
    names = {}
    for pf in PATTERNS_ROOT.rglob("*.json"):
        try:
            p = json.loads(pf.read_text())
            if p.get("pattern_slug"):
                names[p["pattern_slug"]] = p.get("pattern_name", p["pattern_slug"])
        except Exception:
            pass
    return names

def main():
    pattern_names = load_pattern_names()

    # pair → {count, weighted_eng_sum}
    pairs = defaultdict(lambda: {"count": 0, "eng_sum": 0.0, "obs": []})
    # triplet → {count, eng_sum}
    triplets = defaultdict(lambda: {"count": 0, "eng_sum": 0.0})
    # single pattern → {count, eng_sum}
    singles = defaultdict(lambda: {"count": 0, "eng_sum": 0.0, "accounts": set()})

    total_obs = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total_obs += 1
        account = data.get("account_handle_normalized", "unknown")
        sector = data.get("sector", "unknown")
        shortcode = data.get("shortcode", obs_file.stem)

        qa = data.get("quality_assessment", {})
        eng_raw = qa.get("engagement_potential", "medium")
        eng = ENG_MAP.get(str(eng_raw).lower(), 0.5)

        pms = data.get("pattern_matches", [])
        slugs = list(dict.fromkeys(  # deduplicate while preserving order
            pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
            for pm in pms
        ))
        slugs = [s for s in slugs if s]

        for s in slugs:
            singles[s]["count"] += 1
            singles[s]["eng_sum"] += eng
            singles[s]["accounts"].add(account)

        # pairs
        for a, b in combinations(slugs, 2):
            pair = tuple(sorted([a, b]))
            pairs[pair]["count"] += 1
            pairs[pair]["eng_sum"] += eng
            if len(pairs[pair]["obs"]) < 5:
                pairs[pair]["obs"].append({"shortcode": shortcode, "account": account, "sector": sector})

        # triplets
        for combo in combinations(slugs, 3):
            trip = tuple(sorted(combo))
            triplets[trip]["count"] += 1
            triplets[trip]["eng_sum"] += eng

    # Build pair output
    pair_list = []
    for (a, b), data in pairs.items():
        n = data["count"]
        avg_eng = round(data["eng_sum"] / n, 3) if n else 0
        pair_list.append({
            "pattern_a": a,
            "pattern_b": b,
            "pattern_a_name": pattern_names.get(a, a),
            "pattern_b_name": pattern_names.get(b, b),
            "co_occurrence_count": n,
            "avg_engagement": avg_eng,
            "weighted_signal": round(n * avg_eng, 2),
            "sample_obs": data["obs"]
        })
    pair_list.sort(key=lambda x: -x["weighted_signal"])

    # Build triplet output (count >= 3)
    triplet_list = []
    for (a, b, c), data in triplets.items():
        n = data["count"]
        if n < 3:
            continue
        avg_eng = round(data["eng_sum"] / n, 3) if n else 0
        triplet_list.append({
            "pattern_a": a,
            "pattern_b": b,
            "pattern_c": c,
            "co_occurrence_count": n,
            "avg_engagement": avg_eng,
            "weighted_signal": round(n * avg_eng, 2)
        })
    triplet_list.sort(key=lambda x: -x["weighted_signal"])

    # Content recipe combos — human-readable top combos by sector signals
    recipes = []

    # Group by top pairs + sector to infer recipe context
    sector_pair_eng = defaultdict(lambda: defaultdict(lambda: {"count": 0, "eng_sum": 0.0}))
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue
        sector = data.get("sector", "unknown")
        qa = data.get("quality_assessment", {})
        eng = ENG_MAP.get(str(qa.get("engagement_potential", "medium")).lower(), 0.5)
        occasion = data.get("cultural_notes", {}).get("occasion_relevance", "evergreen") or "evergreen"
        pms = data.get("pattern_matches", [])
        slugs = list(dict.fromkeys(
            pm.get("pattern_slug", "") if isinstance(pm, dict) else pm for pm in pms
        ))
        slugs = [s for s in slugs if s]
        for a, b in combinations(slugs, 2):
            key = f"{sector}:{occasion}"
            pair = tuple(sorted([a, b]))
            sector_pair_eng[key][pair]["count"] += 1
            sector_pair_eng[key][pair]["eng_sum"] += eng

    # Build top recipes per sector:occasion
    seen_pairs = set()
    for context, pair_data in sorted(sector_pair_eng.items()):
        top_pairs = sorted(pair_data.items(), key=lambda x: -(x[1]["count"] * (x[1]["eng_sum"] / x[1]["count"])))[:3]
        for pair, pdata in top_pairs:
            n = pdata["count"]
            avg_eng = round(pdata["eng_sum"] / n, 3)
            if n < 2:
                continue
            sector_slug, occasion_slug = context.split(":", 1)
            recipes.append({
                "recipe_context": context,
                "sector": sector_slug,
                "occasion": occasion_slug,
                "core_patterns": list(pair),
                "core_pattern_names": [pattern_names.get(p, p) for p in pair],
                "co_occurrence_count": n,
                "avg_engagement": avg_eng,
                "engagement_verdict": "strong" if avg_eng >= 0.7 else "moderate" if avg_eng >= 0.4 else "weak"
            })

    recipes.sort(key=lambda x: -(x["co_occurrence_count"] * x["avg_engagement"]))

    # Also build named "master recipe" combos from top triplets
    master_recipes = []
    for t in triplet_list[:20]:
        patterns = [t["pattern_a"], t["pattern_b"], t["pattern_c"]]
        names = [pattern_names.get(p, p) for p in patterns]
        master_recipes.append({
            "combo": " + ".join(patterns),
            "combo_names": " + ".join(names),
            "count": t["co_occurrence_count"],
            "avg_engagement": t["avg_engagement"],
            "verdict": "proven" if t["avg_engagement"] >= 0.7 else "mixed"
        })

    LOGS.mkdir(exist_ok=True)

    # Matrix output
    matrix_out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_observations_scanned": total_obs,
        "total_unique_pairs": len(pair_list),
        "total_unique_triplets_3plus": len(triplet_list),
        "top_pairs": pair_list[:50],
        "top_triplets": triplet_list[:30],
        "all_pairs": pair_list
    }
    (LOGS / "pattern_cooccurrence_matrix.json").write_text(json.dumps(matrix_out, ensure_ascii=False, indent=2))

    # Recipe combos output
    recipe_out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "how_to_read": "These are pattern combinations that consistently appear together in the corpus. Higher avg_engagement = stronger signal. Use as creative recipe starting points.",
        "master_triplet_recipes": master_recipes,
        "context_recipes_by_sector_occasion": recipes[:60]
    }
    (LOGS / "content_recipe_combos.json").write_text(json.dumps(recipe_out, ensure_ascii=False, indent=2))

    print(f"Scanned {total_obs} observations")
    print(f"Unique pattern pairs: {len(pair_list)}")
    print(f"Unique triplets (3+ obs): {len(triplet_list)}")
    print(f"\nTop 10 pairs (by weighted signal):")
    for p in pair_list[:10]:
        print(f"  {p['pattern_a']} + {p['pattern_b']}: {p['co_occurrence_count']} obs, eng={p['avg_engagement']}")
    print(f"\nTop triplet recipes:")
    for t in triplet_list[:5]:
        print(f"  {t['pattern_a']} + {t['pattern_b']} + {t['pattern_c']}: {t['co_occurrence_count']} obs, eng={t['avg_engagement']}")
    print(f"\nOutputs: logs/pattern_cooccurrence_matrix.json + logs/content_recipe_combos.json")

if __name__ == "__main__":
    main()
