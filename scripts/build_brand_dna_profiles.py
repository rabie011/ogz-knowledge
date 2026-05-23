#!/usr/bin/env python3
"""
build_brand_dna_profiles.py
Per-account brand DNA profile aggregating all corpus intelligence.
Outputs:
  logs/brand_dna/{account}.json    — one per account
  logs/brand_dna_index.json        — cross-account comparison table
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS_ROOT = BASE / "11_who_to_learn_from" / "patterns"
LOGS = BASE / "logs"

ENG_MAP = {"high": 1.0, "very_high": 1.0, "above_average": 0.75, "medium": 0.5, "low": 0.0, "below_average": 0.25}
HEALTH_WEIGHTS = {"engagement": 0.35, "production": 0.30, "brand": 0.25, "cultural": 0.10}

def load_existing_logs():
    logs = {}
    for log_name in ["content_health_scores", "compliance_risk_report", "voice_positioning_map",
                     "account_archetypes", "pattern_usage_analysis"]:
        path = LOGS / f"{log_name}.json"
        if path.exists():
            try:
                logs[log_name] = json.loads(path.read_text())
            except Exception:
                pass
    return logs

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
    logs = load_existing_logs()

    # Aggregate per-account from observations
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "dialects": [],
        "registers": [],
        "tones": [],
        "heritage_vs_modern": [],
        "hospitality_cue_counts": [],
        "occasions": [],
        "patterns": defaultdict(int),
        "phrases": [],
        "eng_scores": [],
        "compliance_hard": [],
        "compliance_soft": [],
        "production_quality": [],
        "brand_consistency": []
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
        cc = data.get("compliance_check", {})

        if vo.get("dialect_detected"):
            accounts[account]["dialects"].append(str(vo["dialect_detected"]).lower())
        if vo.get("register"):
            accounts[account]["registers"].append(str(vo["register"]).lower())
        if vo.get("tone"):
            accounts[account]["tones"].append(str(vo["tone"]).lower())
        for ph in (vo.get("notable_phrases") or []):
            accounts[account]["phrases"].append(str(ph))

        if cn.get("heritage_vs_modern"):
            accounts[account]["heritage_vs_modern"].append(str(cn["heritage_vs_modern"]).lower())
        accounts[account]["hospitality_cue_counts"].append(len(cn.get("hospitality_cues") or []))
        if cn.get("occasion_relevance"):
            accounts[account]["occasions"].append(str(cn["occasion_relevance"]).lower())

        for pm in data.get("pattern_matches", []):
            slug = pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
            if slug:
                accounts[account]["patterns"][slug] += 1

        eng = ENG_MAP.get(str(qa.get("engagement_potential", "")).lower(), 0.5)
        accounts[account]["eng_scores"].append(eng)

        prod = qa.get("production_quality", "")
        if prod:
            accounts[account]["production_quality"].append(str(prod).lower())
        brand = qa.get("brand_consistency_with_account", "")
        if brand:
            accounts[account]["brand_consistency"].append(str(brand).lower())

        hard_blocks = cc.get("hard_blocks_triggered") or []
        soft_flags = cc.get("soft_flags") or []
        for hb in hard_blocks:
            ft = hb.get("flag_type") if isinstance(hb, dict) else str(hb)
            if ft:
                accounts[account]["compliance_hard"].append(ft)
        for sf in soft_flags:
            ft = sf.get("flag_type") if isinstance(sf, dict) else str(sf)
            if ft:
                accounts[account]["compliance_soft"].append(ft)

    # Build profiles
    profiles = {}
    index_rows = []

    for account, info in accounts.items():
        n = info["obs_count"]
        if n == 0:
            continue

        # Top patterns
        top_patterns = sorted(info["patterns"].items(), key=lambda x: -x[1])[:5]
        top_pattern_data = [{"slug": s, "name": pattern_names.get(s, s), "obs_count": c} for s, c in top_patterns]

        # Dominant dialect/register/tone
        def top_val(lst):
            if not lst:
                return None
            counts = defaultdict(int)
            for v in lst:
                counts[v] += 1
            return max(counts, key=counts.get)

        # Heritage/modern split
        hvm_counts = defaultdict(int)
        for v in info["heritage_vs_modern"]:
            if "heritage" in v or "traditional" in v:
                hvm_counts["heritage"] += 1
            elif "modern" in v or "contemporary" in v:
                hvm_counts["modern"] += 1
            elif "blend" in v:
                hvm_counts["blended"] += 1
            else:
                hvm_counts["other"] += 1
        hvm_total = sum(hvm_counts.values()) or 1
        hvm_split = {k: round(v / hvm_total, 3) for k, v in hvm_counts.items()}

        # Engagement profile
        eng_scores = info["eng_scores"]
        avg_eng = round(sum(eng_scores) / len(eng_scores), 3) if eng_scores else 0
        high_eng_rate = round(sum(1 for e in eng_scores if e >= 0.75) / len(eng_scores), 3) if eng_scores else 0
        eng_profile = {
            "avg_score": avg_eng,
            "high_rate": high_eng_rate,
            "medium_rate": round(sum(1 for e in eng_scores if 0.25 < e < 0.75) / len(eng_scores), 3) if eng_scores else 0,
            "low_rate": round(sum(1 for e in eng_scores if e <= 0.25) / len(eng_scores), 3) if eng_scores else 0
        }

        # Health score (simplified)
        prod_map = {"professional": 1.0, "semi_professional": 0.7, "amateur": 0.3}
        brand_map = {"strong": 1.0, "moderate": 0.6, "weak": 0.2}
        avg_prod = sum(prod_map.get(p, 0.5) for p in info["production_quality"]) / max(1, len(info["production_quality"]))
        avg_brand = sum(brand_map.get(b, 0.5) for b in info["brand_consistency"]) / max(1, len(info["brand_consistency"]))
        avg_hosp = sum(info["hospitality_cue_counts"]) / max(1, len(info["hospitality_cue_counts"]))
        cultural_bonus = 0.1 if (hvm_split.get("heritage", 0) > 0 and avg_hosp > 0) else 0
        health = round((avg_eng * 0.35) + (avg_prod * 0.30) + (avg_brand * 0.25) + (cultural_bonus * 0.10), 3)
        health_grade = "A" if health >= 0.8 else "B" if health >= 0.65 else "C" if health >= 0.5 else "D"

        # Compliance risk
        n_hard = len(info["compliance_hard"])
        n_soft = len(info["compliance_soft"])
        risk_score = (n_hard * 10) + n_soft
        compliance_grade = "green" if risk_score <= 5 else "yellow" if risk_score <= 15 else "orange" if risk_score <= 30 else "red"

        # Occasion profile
        occ_counts = defaultdict(int)
        for occ in info["occasions"]:
            occ_counts[occ] += 1
        top_occasions = sorted(occ_counts.items(), key=lambda x: -x[1])[:5]
        evergreen_ratio = round(occ_counts.get("evergreen", 0) / n, 3)

        # Pull archetype from log if available
        archetype = "unclassified"
        archetype_log = logs.get("account_archetypes", {})
        acct_arch = archetype_log.get("accounts", {}).get(account, {})
        if acct_arch:
            archetype = acct_arch.get("archetype", "unclassified")

        # Voice fingerprint from voice positioning log
        voice_fp = "unknown"
        vp_log = logs.get("voice_positioning_map", {})
        acct_vp = vp_log.get("accounts", {}).get(account, {})
        if acct_vp:
            voice_fp = acct_vp.get("voice_fingerprint", "unknown")

        # Top phrases (first 5)
        top_phrases = list(dict.fromkeys(info["phrases"]))[:5]

        # Differentiation gap (patterns used by sector peers but not this account)
        sector_patterns = defaultdict(int)
        for acc2, info2 in accounts.items():
            if acc2 != account and info2["sector"] == info["sector"]:
                for slug, count in info2["patterns"].items():
                    sector_patterns[slug] += count
        my_patterns = set(info["patterns"].keys())
        diff_gaps = [s for s, c in sorted(sector_patterns.items(), key=lambda x: -x[1])
                     if s not in my_patterns and c >= 2][:5]

        profile = {
            "account": account,
            "sector": info["sector"],
            "archetype": archetype,
            "obs_count": n,
            "health_score": health,
            "health_grade": health_grade,
            "compliance_risk_grade": compliance_grade,
            "compliance_risk_score": risk_score,
            "voice_fingerprint": voice_fp,
            "dominant_dialect": top_val(info["dialects"]),
            "dominant_register": top_val(info["registers"]),
            "dominant_tone": top_val(info["tones"]),
            "heritage_vs_modern_split": hvm_split,
            "avg_hospitality_cues_per_post": round(avg_hosp, 2),
            "engagement_profile": eng_profile,
            "top_5_patterns": top_pattern_data,
            "top_occasions": [{"occasion": occ, "count": c} for occ, c in top_occasions],
            "evergreen_content_ratio": evergreen_ratio,
            "top_phrases": top_phrases,
            "compliance_flags": {
                "hard_block_types": list(set(info["compliance_hard"])),
                "soft_flag_types": list(set(info["compliance_soft"]))[:5]
            },
            "differentiation_gaps": [{"slug": s, "name": pattern_names.get(s, s)} for s in diff_gaps]
        }
        profiles[account] = profile

        index_rows.append({
            "account": account,
            "sector": info["sector"],
            "archetype": archetype,
            "obs_count": n,
            "health_score": health,
            "health_grade": health_grade,
            "compliance_grade": compliance_grade,
            "voice_fingerprint": voice_fp,
            "dominant_dialect": top_val(info["dialects"]),
            "top_pattern": top_pattern_data[0]["slug"] if top_pattern_data else None,
            "avg_engagement": avg_eng,
            "high_engagement_rate": high_eng_rate
        })

    # Write per-account files
    dna_dir = LOGS / "brand_dna"
    dna_dir.mkdir(parents=True, exist_ok=True)

    for account, profile in profiles.items():
        safe_name = account.replace("/", "_").replace("@", "").strip()
        (dna_dir / f"{safe_name}.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2))

    # Write index
    index_rows.sort(key=lambda x: -x["health_score"])
    index_out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_accounts": len(index_rows),
        "accounts": index_rows
    }
    (LOGS / "brand_dna_index.json").write_text(json.dumps(index_out, ensure_ascii=False, indent=2))

    print(f"Created {len(profiles)} brand DNA profiles")
    print(f"Files: logs/brand_dna/*.json + logs/brand_dna_index.json")
    print(f"\nTop 5 accounts by health score:")
    for row in index_rows[:5]:
        print(f"  {row['account']}: {row['health_score']} ({row['health_grade']}) | {row['archetype']} | {row['voice_fingerprint']}")

if __name__ == "__main__":
    main()
