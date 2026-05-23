#!/usr/bin/env python3
"""
build_account_similarity.py
Compute pairwise account similarity using:
1. Jaccard similarity on pattern sets
2. Voice profile similarity (register, tone, dialect overlap)
3. Visual profile similarity (setting, media_type, color_family overlap)
Produces a similarity matrix and identifies competitive clusters.
Output: logs/account_similarity_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high": 1.0, "very_high": 1.0, "above_average": 0.75,
           "medium": 0.5, "low": 0.0, "below_average": 0.25}

COLOR_FAMILIES = [
    ("neutral_warm",  ["nude", "cream", "beige", "ivory", "skin", "linen", "sand", "wheat", "oat"]),
    ("warm_red",      ["red", "crimson", "scarlet", "berry", "maroon", "wine", "cherry", "rust"]),
    ("pink_rose",     ["pink", "rose", "blush", "peach", "coral", "salmon", "lilac", "mauve"]),
    ("amber_gold",    ["amber", "gold", "honey", "caramel", "mustard", "yellow", "saffron", "ochre", "tan", "bronze", "copper", "golden"]),
    ("brown_earth",   ["brown", "earth", "terracotta", "sienna", "umber", "chocolate", "mocha", "espresso", "coffee", "cocoa"]),
    ("green",         ["green", "sage", "olive", "mint", "emerald", "forest", "teal", "khaki", "lime"]),
    ("blue",          ["blue", "navy", "indigo", "cobalt", "royal", "sky", "cerulean", "denim"]),
    ("purple",        ["purple", "violet", "lavender", "plum", "aubergine"]),
    ("white_light",   ["white", "light", "bright", "pale", "soft", "clean", "airy", "fresh"]),
    ("black_dark",    ["black", "dark", "charcoal", "graphite", "deep", "noir", "onyx", "shadow"]),
    ("grey",          ["grey", "gray", "silver", "slate", "ash", "smoke", "stone"]),
    ("mixed_vibrant", ["vibrant", "bold", "colourful", "colorful", "rainbow", "multi", "rich"]),
]


def classify_color(color_str):
    v = color_str.lower().strip()
    for family, keywords in COLOR_FAMILIES:
        if any(k in v for k in keywords):
            return family
    return "other"


def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union        = len(set_a | set_b)
    return round(intersection / union, 3) if union else 0.0


def top_n(counter, n=3):
    return set(k for k, _ in counter.most_common(n))


def main():
    # Build per-account profile vectors
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "patterns": Counter(),
        "registers": Counter(),
        "tones": Counter(),
        "dialects": Counter(),
        "settings": Counter(),
        "media_types": Counter(),
        "color_families": Counter(),
        "lightings": Counter(),
        "compositions": Counter(),
        "avg_eng": 0.0,
        "eng_scores": [],
    })

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        sector  = data.get("sector", "unknown") or "unknown"
        accounts[account]["sector"] = sector
        accounts[account]["obs_count"] += 1

        qa     = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        accounts[account]["eng_scores"].append(eng)

        vo = data.get("voice_observations", {}) or {}
        if vo.get("register"):
            accounts[account]["registers"][vo["register"]] += 1
        if vo.get("tone"):
            accounts[account]["tones"][vo["tone"]] += 1
        if vo.get("dialect_detected"):
            accounts[account]["dialects"][vo["dialect_detected"]] += 1

        vv = data.get("visual_observations", {}) or {}
        if vv.get("setting"):
            accounts[account]["settings"][vv["setting"]] += 1
        if vv.get("lighting"):
            accounts[account]["lightings"][vv["lighting"]] += 1
        if vv.get("composition_style"):
            accounts[account]["compositions"][vv["composition_style"]] += 1

        cr = data.get("content_ref", {}) or {}
        mt = str(cr.get("content_type", "") or "").lower()
        if mt:
            accounts[account]["media_types"][mt] += 1

        colors = vv.get("color_palette_dominant") or []
        for color in colors:
            if isinstance(color, str) and color.strip():
                accounts[account]["color_families"][classify_color(color)] += 1

        for pm in data.get("pattern_matches", []):
            slug = pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
            if slug:
                accounts[account]["patterns"][slug] += 1

    # Compute avg engagement per account
    for acc, info in accounts.items():
        scores = info["eng_scores"]
        info["avg_eng"] = round(sum(scores) / len(scores), 3) if scores else 0

    acc_list = sorted(accounts.keys())
    n = len(acc_list)

    # Build similarity matrix
    matrix = {}
    for i, acc_a in enumerate(acc_list):
        info_a = accounts[acc_a]
        matrix[acc_a] = {}
        for j, acc_b in enumerate(acc_list):
            if i == j:
                matrix[acc_a][acc_b] = {
                    "pattern_jaccard": 1.0,
                    "voice_jaccard": 1.0,
                    "visual_jaccard": 1.0,
                    "composite_similarity": 1.0
                }
                continue
            info_b = accounts[acc_b]

            # Pattern Jaccard (all patterns, weighted by obs count threshold ≥2)
            pats_a = {slug for slug, c in info_a["patterns"].items() if c >= 2}
            pats_b = {slug for slug, c in info_b["patterns"].items() if c >= 2}
            pj = jaccard(pats_a, pats_b)

            # Voice Jaccard (top 3 register + tone + dialect)
            voice_a = top_n(info_a["registers"]) | top_n(info_a["tones"]) | top_n(info_a["dialects"])
            voice_b = top_n(info_b["registers"]) | top_n(info_b["tones"]) | top_n(info_b["dialects"])
            vj = jaccard(voice_a, voice_b)

            # Visual Jaccard (top 2 setting + media + color_family + lighting)
            visual_a = top_n(info_a["settings"], 2) | top_n(info_a["media_types"], 2) | top_n(info_a["color_families"], 2) | top_n(info_a["lightings"], 2)
            visual_b = top_n(info_b["settings"], 2) | top_n(info_b["media_types"], 2) | top_n(info_b["color_families"], 2) | top_n(info_b["lightings"], 2)
            visj = jaccard(visual_a, visual_b)

            composite = round(0.5 * pj + 0.25 * vj + 0.25 * visj, 3)

            matrix[acc_a][acc_b] = {
                "pattern_jaccard": pj,
                "voice_jaccard": vj,
                "visual_jaccard": visj,
                "composite_similarity": composite
            }

    # Top 3 most similar accounts per account
    account_profiles = []
    for acc in acc_list:
        info = accounts[acc]
        peers = sorted(
            [(other, matrix[acc][other]["composite_similarity"])
             for other in acc_list if other != acc],
            key=lambda x: -x[1]
        )
        top_similar   = [{"account": p, "similarity": s} for p, s in peers[:3]]
        top_different = [{"account": p, "similarity": s} for p, s in peers[-3:]]

        account_profiles.append({
            "account": acc,
            "sector": info["sector"],
            "obs_count": info["obs_count"],
            "avg_engagement": info["avg_eng"],
            "top_patterns": [slug for slug, _ in info["patterns"].most_common(5)],
            "most_similar_accounts": top_similar,
            "most_differentiated_from": top_different,
        })

    # Cluster-like groupings (accounts with composite_similarity > 0.4)
    clusters = []
    assigned = set()
    for acc in sorted(acc_list, key=lambda a: -accounts[a]["avg_eng"]):
        if acc in assigned:
            continue
        cluster = [acc]
        assigned.add(acc)
        for other in acc_list:
            if other not in assigned and matrix[acc][other]["composite_similarity"] >= 0.35:
                cluster.append(other)
                assigned.add(other)
        if len(cluster) > 1:
            clusters.append({
                "size": len(cluster),
                "accounts": cluster,
                "avg_composite_similarity": round(
                    sum(matrix[cluster[0]][c]["composite_similarity"] for c in cluster[1:]) / (len(cluster) - 1), 3
                )
            })
        else:
            clusters.append({"size": 1, "accounts": cluster, "avg_composite_similarity": 1.0})

    # Flat similarity matrix for cross-account comparison
    flat_matrix = []
    seen_pairs = set()
    for acc_a in acc_list:
        for acc_b in acc_list:
            if acc_a >= acc_b:
                continue
            pair = (acc_a, acc_b)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            sims = matrix[acc_a][acc_b]
            flat_matrix.append({
                "account_a": acc_a,
                "account_b": acc_b,
                "pattern_jaccard": sims["pattern_jaccard"],
                "voice_jaccard": sims["voice_jaccard"],
                "visual_jaccard": sims["visual_jaccard"],
                "composite_similarity": sims["composite_similarity"],
                "sector_a": accounts[acc_a]["sector"],
                "sector_b": accounts[acc_b]["sector"],
                "cross_sector": accounts[acc_a]["sector"] != accounts[acc_b]["sector"],
            })
    flat_matrix.sort(key=lambda x: -x["composite_similarity"])

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_accounts": len(acc_list),
        "how_to_read": {
            "pattern_jaccard": "Overlap of pattern sets used (threshold ≥2 uses). 0=no overlap, 1=identical.",
            "voice_jaccard": "Overlap of top register/tone/dialect values.",
            "visual_jaccard": "Overlap of top setting/media/color/lighting.",
            "composite_similarity": "Weighted: 50% pattern + 25% voice + 25% visual.",
        },
        "account_profiles": account_profiles,
        "similarity_clusters": clusters,
        "top_20_most_similar_pairs": flat_matrix[:20],
        "top_10_most_differentiated_pairs": flat_matrix[-10:],
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "account_similarity_matrix.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Similarity matrix: {len(acc_list)} accounts × {len(flat_matrix)} pairs")
    print(f"\nTop 10 most similar account pairs:")
    for p in flat_matrix[:10]:
        print(f"  {p['account_a'][-25:]:<27} ↔ {p['account_b'][-25:]:<27} "
              f"sim={p['composite_similarity']:.3f} (pat={p['pattern_jaccard']:.2f} "
              f"voice={p['voice_jaccard']:.2f} visual={p['visual_jaccard']:.2f})")
    print(f"\nClusters ({len(clusters)} groups):")
    for c in sorted(clusters, key=lambda x: -x["size"])[:5]:
        print(f"  [{c['size']} accounts]: {', '.join(a[-20:] for a in c['accounts'])}")
    print(f"\nOutput: logs/account_similarity_matrix.json")


if __name__ == "__main__":
    main()
