#!/usr/bin/env python3
"""
build_account_themes_index.py
Aggregate high/low engagement themes, distinctive visual/voice traits,
and anti-patterns from all 110 account profile JSON files.
Produces a cross-account intelligence index of what works and what fails.
Output: logs/account_themes_index.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE          = Path(__file__).parent.parent
ACCOUNTS_ROOT = BASE / "11_who_to_learn_from" / "accounts"
LOGS          = BASE / "logs"


def normalise(text: str) -> str:
    """Lowercase, strip punctuation edges, collapse whitespace."""
    return " ".join(text.lower().strip().split())


def main():
    high_eng_themes     = Counter()
    low_eng_themes      = Counter()
    distinctive_visual  = Counter()
    distinctive_voice   = Counter()
    anti_patterns       = Counter()

    # Per-sector groupings
    by_sector = defaultdict(lambda: {
        "high_eng_themes": Counter(),
        "low_eng_themes": Counter(),
        "distinctive_visual": Counter(),
        "distinctive_voice": Counter(),
        "anti_patterns": Counter(),
        "accounts_seen": 0
    })

    total = 0
    total_with_themes = 0

    for acct_file in sorted(ACCOUNTS_ROOT.rglob("*.json")):
        try:
            data = json.loads(acct_file.read_text())
        except Exception:
            continue

        total += 1
        sector = data.get("sector", "unknown") or "unknown"
        s = by_sector[sector]
        s["accounts_seen"] += 1

        # high_engagement_themes
        het = data.get("high_engagement_themes") or []
        if het:
            total_with_themes += 1
        for item in het:
            if isinstance(item, str) and item.strip():
                key = normalise(item)
                high_eng_themes[key] += 1
                s["high_eng_themes"][key] += 1

        # low_engagement_themes
        for item in (data.get("low_engagement_themes") or []):
            if isinstance(item, str) and item.strip():
                key = normalise(item)
                low_eng_themes[key] += 1
                s["low_eng_themes"][key] += 1

        # distinctive_visual_traits
        for item in (data.get("distinctive_visual_traits") or []):
            if isinstance(item, str) and item.strip():
                key = normalise(item)
                distinctive_visual[key] += 1
                s["distinctive_visual"][key] += 1

        # distinctive_voice_traits
        for item in (data.get("distinctive_voice_traits") or []):
            if isinstance(item, str) and item.strip():
                key = normalise(item)
                distinctive_voice[key] += 1
                s["distinctive_voice"][key] += 1

        # anti_patterns_observed
        for item in (data.get("anti_patterns_observed") or []):
            if isinstance(item, str) and item.strip():
                key = normalise(item)
                anti_patterns[key] += 1
                s["anti_patterns"][key] += 1

    # Build sector summaries
    sector_summaries = {}
    for sector, s in sorted(by_sector.items()):
        sector_summaries[sector] = {
            "accounts_in_sector": s["accounts_seen"],
            "top_high_engagement_themes": [
                {"theme": t, "account_count": c}
                for t, c in s["high_eng_themes"].most_common(10)
            ],
            "top_low_engagement_themes": [
                {"theme": t, "account_count": c}
                for t, c in s["low_eng_themes"].most_common(10)
            ],
            "top_distinctive_visual_traits": [
                {"trait": t, "account_count": c}
                for t, c in s["distinctive_visual"].most_common(10)
            ],
            "top_distinctive_voice_traits": [
                {"trait": t, "account_count": c}
                for t, c in s["distinctive_voice"].most_common(10)
            ],
            "top_anti_patterns": [
                {"pattern": t, "account_count": c}
                for t, c in s["anti_patterns"].most_common(10)
            ],
        }

    # Identify cross-sector constants (themes appearing in 2+ sectors)
    cross_sector_high = [
        {"theme": t, "total_accounts": c}
        for t, c in high_eng_themes.most_common(20)
        if c >= 2
    ]
    cross_sector_avoid = [
        {"theme": t, "total_accounts": c}
        for t, c in low_eng_themes.most_common(20)
        if c >= 2
    ]
    universal_anti = [
        {"pattern": t, "total_accounts": c}
        for t, c in anti_patterns.most_common(20)
        if c >= 2
    ]

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_account_files_scanned": total,
        "accounts_with_theme_data": total_with_themes,
        "fleet_wide": {
            "top_high_engagement_themes": [
                {"theme": t, "account_count": c}
                for t, c in high_eng_themes.most_common(25)
            ],
            "top_low_engagement_themes": [
                {"theme": t, "account_count": c}
                for t, c in low_eng_themes.most_common(25)
            ],
            "top_distinctive_visual_traits": [
                {"trait": t, "account_count": c}
                for t, c in distinctive_visual.most_common(20)
            ],
            "top_distinctive_voice_traits": [
                {"trait": t, "account_count": c}
                for t, c in distinctive_voice.most_common(20)
            ],
            "top_anti_patterns": [
                {"pattern": t, "account_count": c}
                for t, c in anti_patterns.most_common(20)
            ],
        },
        "cross_sector_constants": {
            "high_engagement_across_sectors": cross_sector_high,
            "low_engagement_across_sectors": cross_sector_avoid,
            "universal_anti_patterns": universal_anti,
        },
        "by_sector": sector_summaries,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "account_themes_index.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Scanned {total} account files ({total_with_themes} with theme data)")
    print(f"\nFleet-wide top high-engagement themes:")
    for item in out["fleet_wide"]["top_high_engagement_themes"][:10]:
        print(f"  ({item['account_count']:2d} accounts) {item['theme']}")
    print(f"\nFleet-wide top anti-patterns:")
    for item in out["fleet_wide"]["top_anti_patterns"][:10]:
        print(f"  ({item['account_count']:2d} accounts) {item['pattern']}")
    print(f"\nOutput: logs/account_themes_index.json")


if __name__ == "__main__":
    main()
