#!/usr/bin/env python3
"""
build_account_archetypes.py
Assigns each extracted account to one of 5 brand archetypes based on corpus evidence.
Output: logs/account_archetypes.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

ENG_MAP = {"high": 1.0, "very_high": 1.0, "above_average": 0.75, "medium": 0.5, "low": 0.0, "below_average": 0.25}

# Archetype definitions
ARCHETYPES = {
    "Heritage Anchor": "Deeply rooted in Saudi/regional cultural identity. Heritage-first visual and voice. Najdi/Hejazi dialect dominant. High hospitality cue density. Identity is inseparable from product.",
    "Modern Premium": "Aspirational, polished, cool-toned. English-Arabic mixed or MSA. Minimal hospitality cues. High production quality. Speaks to upward mobility and contemporary taste.",
    "Community Warm": "Audience-first. UGC, giveaways, engagement mechanics dominant. Warm, playful, casual voice. High comment engagement. Brand is the hub of a social community.",
    "Occasion Specialist": "Content calendar is heavily occasion-driven. >40% of posts tied to specific occasions (Ramadan, National Day, sports). Pattern repertoire changes dramatically by season.",
    "Mass Market Functional": "Volume-driven. Price offers, product bundles, delivery CTAs dominate. Low cultural signal. Broad audience targeting. Conversions > connections."
}

def score_archetype(account_data):
    """Return {archetype: score} dict based on evidence."""
    scores = {k: 0.0 for k in ARCHETYPES}
    obs = account_data["obs"]
    n = len(obs)
    if n == 0:
        return scores

    heritage_count = sum(1 for o in obs if "heritage" in str(o.get("heritage_vs_modern", "")).lower())
    modern_count = sum(1 for o in obs if "modern" in str(o.get("heritage_vs_modern", "")).lower())
    blended_count = sum(1 for o in obs if "blend" in str(o.get("heritage_vs_modern", "")).lower())
    heritage_ratio = heritage_count / n

    dialects = [str(o.get("dialect", "")).lower() for o in obs if o.get("dialect")]
    najdi_hejazi = sum(1 for d in dialects if d in ("najdi", "hejazi"))
    najdi_hejazi_ratio = najdi_hejazi / len(dialects) if dialects else 0

    hosp_counts = [o.get("hospitality_cue_count", 0) for o in obs]
    avg_hosp = sum(hosp_counts) / len(hosp_counts) if hosp_counts else 0

    registers = [str(o.get("register", "")).lower() for o in obs if o.get("register")]
    msa_formal = sum(1 for r in registers if r in ("formal", "msa", "semi_formal"))
    msa_formal_ratio = msa_formal / len(registers) if registers else 0

    prod_quality = [str(o.get("production_quality", "")).lower() for o in obs if o.get("production_quality")]
    professional = sum(1 for p in prod_quality if p == "professional")
    professional_ratio = professional / len(prod_quality) if prod_quality else 0

    # Pattern usage
    all_patterns = []
    for o in obs:
        all_patterns.extend(o.get("patterns", []))
    price_offer_count = sum(1 for p in all_patterns if "price" in p or "offer" in p or "bundle" in p or "delivery" in p)
    ugc_giveaway_count = sum(1 for p in all_patterns if "ugc" in p or "giveaway" in p or "comment_to_win" in p or "poll" in p)
    heritage_pattern_count = sum(1 for p in all_patterns if "heritage" in p or "cultural" in p or "community_pride" in p)

    # Occasion diversity
    occasions = [str(o.get("occasion", "evergreen")).lower() for o in obs]
    non_evergreen = sum(1 for occ in occasions if occ not in ("evergreen", "null", "", "none"))
    occasion_ratio = non_evergreen / n

    # Heritage Anchor signals
    if heritage_ratio >= 0.5:
        scores["Heritage Anchor"] += 3.0
    if najdi_hejazi_ratio >= 0.5:
        scores["Heritage Anchor"] += 2.0
    if avg_hosp >= 2.5:
        scores["Heritage Anchor"] += 2.0
    if heritage_pattern_count >= 5:
        scores["Heritage Anchor"] += 1.5

    # Modern Premium signals
    if professional_ratio >= 0.8:
        scores["Modern Premium"] += 2.0
    if modern_count / n >= 0.4:
        scores["Modern Premium"] += 2.5
    if msa_formal_ratio >= 0.3:
        scores["Modern Premium"] += 1.5
    if avg_hosp < 1.0:
        scores["Modern Premium"] += 1.0

    # Community Warm signals
    if ugc_giveaway_count >= 3:
        scores["Community Warm"] += 3.0
    tones = [str(o.get("tone", "")).lower() for o in obs if o.get("tone")]
    warm_tones = sum(1 for t in tones if any(w in t for w in ("warm", "playful", "communal", "celebratory")))
    if warm_tones / len(tones) >= 0.5 if tones else 0:
        scores["Community Warm"] += 2.0
    if avg_hosp >= 2.0:
        scores["Community Warm"] += 1.0

    # Occasion Specialist signals
    if occasion_ratio >= 0.4:
        scores["Occasion Specialist"] += 3.0
    if occasion_ratio >= 0.6:
        scores["Occasion Specialist"] += 2.0

    # Mass Market Functional signals
    if price_offer_count >= 3:
        scores["Mass Market Functional"] += 3.0
    if occasion_ratio < 0.2 and heritage_ratio < 0.2 and ugc_giveaway_count < 2:
        scores["Mass Market Functional"] += 2.0

    return scores

def main():
    # Aggregate per-account data
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "obs": []
    })

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        accounts[account]["sector"] = data.get("sector")
        accounts[account]["obs_count"] += 1

        vo = data.get("voice_observations", {})
        cn = data.get("cultural_notes", {})
        qa = data.get("quality_assessment", {})

        obs_summary = {
            "dialect": vo.get("dialect_detected"),
            "register": vo.get("register"),
            "tone": vo.get("tone"),
            "heritage_vs_modern": cn.get("heritage_vs_modern"),
            "hospitality_cue_count": len(cn.get("hospitality_cues") or []),
            "occasion": cn.get("occasion_relevance"),
            "production_quality": qa.get("production_quality"),
            "engagement_potential": qa.get("engagement_potential"),
            "patterns": [
                pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
                for pm in data.get("pattern_matches", [])
            ]
        }
        accounts[account]["obs"].append(obs_summary)

    # Score each account
    archetype_assignments = {}
    for account, info in accounts.items():
        if info["obs_count"] < 3:
            continue
        scores = score_archetype(info)
        top_archetype = max(scores, key=scores.get)
        top_score = scores[top_archetype]
        runner_up = sorted(scores, key=scores.get, reverse=True)[1]

        # Confidence: gap between top and runner-up
        confidence = round((scores[top_archetype] - scores[runner_up]) / max(1, top_score), 2)
        confidence_label = "high" if confidence >= 0.3 else "medium" if confidence >= 0.1 else "low"

        archetype_assignments[account] = {
            "account": account,
            "sector": info["sector"],
            "obs_count": info["obs_count"],
            "archetype": top_archetype,
            "archetype_description": ARCHETYPES[top_archetype],
            "confidence": confidence_label,
            "scores": {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
            "runner_up_archetype": runner_up
        }

    # Fleet summary
    by_archetype = defaultdict(list)
    for acc, info in archetype_assignments.items():
        by_archetype[info["archetype"]].append(acc)

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "archetypes_defined": ARCHETYPES,
        "fleet_distribution": {arch: {"accounts": accs, "count": len(accs)}
                               for arch, accs in sorted(by_archetype.items(), key=lambda x: -len(x[1]))},
        "accounts": archetype_assignments
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "account_archetypes.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Classified {len(archetype_assignments)} accounts")
    print(f"\nArchetype distribution:")
    for arch, info in sorted(by_archetype.items(), key=lambda x: -len(x[1])):
        print(f"  {arch}: {len(info)} accounts — {info}")
    print(f"Output: logs/account_archetypes.json")

if __name__ == "__main__":
    main()
