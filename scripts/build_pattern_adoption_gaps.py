#!/usr/bin/env python3
"""
build_pattern_adoption_gaps.py
Pattern × sector adoption matrix. Surfaces differentiation gaps.
Output: logs/pattern_adoption_gaps.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS_ROOT = BASE / "11_who_to_learn_from" / "patterns"
LOGS = BASE / "logs"

SECTORS = ["f_and_b", "beauty", "retail"]

def main():
    # Load all defined patterns
    defined_patterns = {}
    for pf in sorted(PATTERNS_ROOT.rglob("*.json")):
        try:
            p = json.loads(pf.read_text())
            slug = p.get("pattern_slug")
            if slug:
                defined_patterns[slug] = {
                    "name": p.get("pattern_name"),
                    "subcategory": pf.parent.name,
                    "defined_sectors": p.get("observed_in_sectors", [])
                }
        except Exception:
            continue

    # Scan all observations
    # pattern_slug → { sector → set(accounts) }
    usage = defaultdict(lambda: {s: set() for s in SECTORS})
    account_sector = {}   # account → sector

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        sector = data.get("sector", "unknown")
        account_sector[account] = sector

        patterns = data.get("pattern_matches", [])
        if not patterns:
            continue

        for pm in patterns:
            slug = pm if isinstance(pm, str) else pm.get("pattern_slug", "")
            if slug and sector in SECTORS:
                usage[slug][sector].add(account)

    # Build adoption matrix
    adoption = {}
    for slug, sector_accounts in usage.items():
        sector_counts = {s: len(accs) for s, accs in sector_accounts.items()}
        total_accounts = sum(sector_counts.values())
        present_in_sectors = [s for s, c in sector_counts.items() if c > 0]
        absent_from_sectors = [s for s in SECTORS if sector_counts.get(s, 0) == 0]

        # Categorize
        if total_accounts >= 10:
            reach = "universal"
        elif total_accounts >= 5:
            reach = "widespread"
        elif total_accounts >= 3:
            reach = "moderate"
        else:
            reach = "lonely"

        # Opportunity score: lonely patterns with high engagement (from pattern file)
        is_defined = slug in defined_patterns

        adoption[slug] = {
            "pattern_slug": slug,
            "pattern_name": defined_patterns.get(slug, {}).get("name", slug),
            "subcategory": defined_patterns.get(slug, {}).get("subcategory", "unknown"),
            "is_defined_in_library": is_defined,
            "total_accounts_using": total_accounts,
            "reach_category": reach,
            "sector_breakdown": {s: {
                "account_count": sector_counts.get(s, 0),
                "accounts": sorted(sector_accounts[s])
            } for s in SECTORS},
            "present_in_sectors": present_in_sectors,
            "absent_from_sectors": absent_from_sectors,
            "differentiation_opportunity": len(absent_from_sectors) > 0 and sector_counts.get("f_and_b", 0) >= 3
        }

    # Sort: differentiation opps first, then by total usage
    sorted_adoption = dict(sorted(adoption.items(),
        key=lambda x: (-int(x[1]["differentiation_opportunity"]), -x[1]["total_accounts_using"])))

    # Gap summary
    sector_exclusive = {s: [] for s in SECTORS}
    for slug, info in sorted_adoption.items():
        if len(info["present_in_sectors"]) == 1:
            sector_exclusive[info["present_in_sectors"][0]].append(slug)

    universal = [s for s, i in sorted_adoption.items() if i["reach_category"] == "universal"]
    lonely = [s for s, i in sorted_adoption.items() if i["reach_category"] == "lonely"]
    opportunities = [s for s, i in sorted_adoption.items() if i["differentiation_opportunity"]]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "summary": {
            "total_patterns_tracked": len(sorted_adoption),
            "universal_patterns_10plus_accounts": universal,
            "lonely_patterns_under_3_accounts": lonely,
            "sector_exclusive": sector_exclusive,
            "differentiation_opportunities": opportunities,
            "differentiation_opportunity_count": len(opportunities)
        },
        "patterns": sorted_adoption
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "pattern_adoption_gaps.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Patterns tracked: {len(sorted_adoption)}")
    print(f"Universal (10+ accounts): {len(universal)}")
    print(f"Lonely (<3 accounts): {len(lonely)}")
    print(f"Differentiation opportunities: {len(opportunities)}")
    print(f"Output: logs/pattern_adoption_gaps.json")

if __name__ == "__main__":
    main()
