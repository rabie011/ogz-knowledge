#!/usr/bin/env python3
"""
build_compliance_risk_report.py
Per-account compliance risk stratification.
Risk score = (hard_blocks × 10) + soft_flags count
Categories: green (0-5), yellow (6-15), orange (16-30), red (31+)
Output: logs/compliance_risk_report.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

def main():
    account_data = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "hard_block_count": 0,
        "soft_flag_count": 0,
        "hard_block_types": defaultdict(int),
        "soft_flag_types": defaultdict(int),
        "flagged_shortcodes": []
    })

    total_hard = 0
    total_soft = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        shortcode = data.get("shortcode", obs_file.stem)
        sector = data.get("sector", "unknown")
        cc = data.get("compliance_check", {})

        account_data[account]["sector"] = sector
        account_data[account]["obs_count"] += 1

        hard_blocks = cc.get("hard_blocks_triggered", [])
        soft_flags = cc.get("soft_flags", [])

        if isinstance(hard_blocks, str):
            hard_blocks = [hard_blocks] if hard_blocks else []
        if isinstance(soft_flags, str):
            soft_flags = [soft_flags] if soft_flags else []

        # Handle soft_flags as list of objects or strings
        soft_flag_types = []
        for sf in soft_flags:
            if isinstance(sf, dict):
                ft = sf.get("flag_type") or sf.get("type") or str(sf)
            else:
                ft = str(sf)
            soft_flag_types.append(ft)

        hard_block_types = []
        for hb in hard_blocks:
            if isinstance(hb, dict):
                ft = hb.get("flag_type") or hb.get("type") or str(hb)
            else:
                ft = str(hb)
            hard_block_types.append(ft)

        n_hard = len(hard_block_types)
        n_soft = len(soft_flag_types)

        account_data[account]["hard_block_count"] += n_hard
        account_data[account]["soft_flag_count"] += n_soft
        total_hard += n_hard
        total_soft += n_soft

        for ht in hard_block_types:
            account_data[account]["hard_block_types"][ht] += 1
        for st in soft_flag_types:
            account_data[account]["soft_flag_types"][st] += 1

        if n_hard > 0 or n_soft > 0:
            account_data[account]["flagged_shortcodes"].append({
                "shortcode": shortcode,
                "hard_blocks": hard_block_types,
                "soft_flags": soft_flag_types
            })

    # Compute risk scores and categorize
    risk_profiles = {}
    for account, info in account_data.items():
        risk_score = (info["hard_block_count"] * 10) + info["soft_flag_count"]
        if risk_score <= 5:
            category = "green"
        elif risk_score <= 15:
            category = "yellow"
        elif risk_score <= 30:
            category = "orange"
        else:
            category = "red"

        # Hard block rate
        hb_rate = round(info["hard_block_count"] / info["obs_count"], 3) if info["obs_count"] else 0
        sf_rate = round(info["soft_flag_count"] / info["obs_count"], 3) if info["obs_count"] else 0

        top_hard = sorted(info["hard_block_types"].items(), key=lambda x: -x[1])[:5]
        top_soft = sorted(info["soft_flag_types"].items(), key=lambda x: -x[1])[:5]

        risk_profiles[account] = {
            "account": account,
            "sector": info["sector"],
            "obs_count": info["obs_count"],
            "risk_score": risk_score,
            "risk_category": category,
            "hard_block_count": info["hard_block_count"],
            "soft_flag_count": info["soft_flag_count"],
            "hard_block_rate_per_obs": hb_rate,
            "soft_flag_rate_per_obs": sf_rate,
            "top_hard_block_types": [{"type": t, "count": c} for t, c in top_hard],
            "top_soft_flag_types": [{"type": t, "count": c} for t, c in top_soft],
            "flagged_obs_count": len(info["flagged_shortcodes"]),
            "flagged_observations": info["flagged_shortcodes"]
        }

    # Sort by risk score desc
    risk_sorted = dict(sorted(risk_profiles.items(), key=lambda x: -x[1]["risk_score"]))

    # Category summaries
    by_category = {"green": [], "yellow": [], "orange": [], "red": []}
    for acc, info in risk_sorted.items():
        by_category[info["risk_category"]].append(acc)

    # Top violation types across all accounts
    all_hard_types = defaultdict(int)
    all_soft_types = defaultdict(int)
    for info in account_data.values():
        for t, c in info["hard_block_types"].items():
            all_hard_types[t] += c
        for t, c in info["soft_flag_types"].items():
            all_soft_types[t] += c

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "risk_scoring": {
            "formula": "(hard_blocks × 10) + soft_flag_count",
            "green": "0-5 (low risk)",
            "yellow": "6-15 (moderate risk)",
            "orange": "16-30 (elevated risk)",
            "red": "31+ (high risk)"
        },
        "fleet_summary": {
            "total_accounts": len(risk_sorted),
            "total_hard_blocks": total_hard,
            "total_soft_flags": total_soft,
            "by_category": {cat: {"accounts": accs, "count": len(accs)}
                            for cat, accs in by_category.items()},
            "top_hard_block_types_fleet": [{"type": t, "count": c}
                for t, c in sorted(all_hard_types.items(), key=lambda x: -x[1])[:10]],
            "top_soft_flag_types_fleet": [{"type": t, "count": c}
                for t, c in sorted(all_soft_types.items(), key=lambda x: -x[1])[:10]]
        },
        "accounts": risk_sorted
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "compliance_risk_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Analysed {len(risk_sorted)} accounts")
    print(f"Risk distribution: green={len(by_category['green'])}, yellow={len(by_category['yellow'])}, orange={len(by_category['orange'])}, red={len(by_category['red'])}")
    print(f"\nTop 5 highest-risk accounts:")
    for acc, info in list(risk_sorted.items())[:5]:
        print(f"  {acc}: score={info['risk_score']} ({info['risk_category']}) — {info['hard_block_count']} hard / {info['soft_flag_count']} soft")
    print(f"Output: logs/compliance_risk_report.json")

if __name__ == "__main__":
    main()
