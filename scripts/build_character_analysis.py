#!/usr/bin/env python3
"""
build_character_analysis.py
Analyse character presence vs engagement.
characters_visible stores {count: N} in obs — we use count > 0 as "has humans".
Also tracks character count buckets (0, 1, 2-3, 4+) vs engagement.
Output: logs/character_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0, "above_average": 0.75,
    "medium": 0.5, "low": 0.0, "below_average": 0.25
}


def agg(label=""):
    return {"label": label, "count": 0, "high": 0, "sum": 0.0}


def record(bucket, is_high, eng):
    bucket["count"] += 1
    bucket["high"]  += is_high
    bucket["sum"]   += eng


def summarise(bucket):
    n = bucket["count"]
    if n == 0:
        return {**bucket, "high_engagement_rate": 0, "avg_engagement": 0, "verdict": "no_data"}
    rate = round(bucket["high"] / n, 3)
    avg  = round(bucket["sum"] / n, 3)
    return {
        **bucket,
        "high_engagement_rate": rate,
        "avg_engagement": avg,
        "verdict": (
            "strong_positive" if rate >= 0.70 and n >= 5 else
            "positive"        if rate >= 0.55 and n >= 5 else
            "neutral"         if rate >= 0.40 else
            "weak"            if rate >= 0.25 else
            "avoid"
        )
    }


def main():
    has_chars   = agg("has_characters")
    no_chars    = agg("no_characters")

    count_buckets = {
        "0":   agg("0 characters"),
        "1":   agg("1 character"),
        "2-3": agg("2-3 characters"),
        "4+":  agg("4+ characters"),
    }

    # Cross: media_type + character presence
    media_char = defaultdict(lambda: {"with": agg(), "without": agg()})
    # Cross: sector + character presence
    sector_char = defaultdict(lambda: {"with": agg(), "without": agg()})
    # Cross: archetype pattern + character presence
    # Accounts with highest character use
    account_char = defaultdict(lambda: {"total": 0, "with_chars": 0, "eng_sum": 0.0, "high": 0})

    total = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        qa      = data.get("quality_assessment", {}) or {}
        eng_raw = str(qa.get("engagement_potential", "") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        vo = data.get("visual_observations", {}) or {}
        cv = vo.get("characters_visible")
        account = data.get("account_handle_normalized", "unknown")
        sector  = data.get("sector", "unknown") or "unknown"
        cr      = data.get("content_ref", {}) or {}
        mt      = str(cr.get("content_type", "unknown") or "unknown").lower().strip()

        # Extract character count
        char_count = 0
        if isinstance(cv, dict):
            char_count = int(cv.get("count", 0) or 0)
        elif isinstance(cv, list):
            char_count = len(cv)
        elif isinstance(cv, int):
            char_count = cv

        # Main buckets
        if char_count > 0:
            record(has_chars, is_high, eng)
            record(media_char[mt]["with"], is_high, eng)
            record(sector_char[sector]["with"], is_high, eng)
            account_char[account]["with_chars"] += 1
        else:
            record(no_chars, is_high, eng)
            record(media_char[mt]["without"], is_high, eng)
            record(sector_char[sector]["without"], is_high, eng)

        account_char[account]["total"] += 1
        account_char[account]["eng_sum"] += eng
        account_char[account]["high"] += is_high

        # Count bucket
        if char_count == 0:
            record(count_buckets["0"], is_high, eng)
        elif char_count == 1:
            record(count_buckets["1"], is_high, eng)
        elif char_count <= 3:
            record(count_buckets["2-3"], is_high, eng)
        else:
            record(count_buckets["4+"], is_high, eng)

    # Account-level character usage rate
    account_profile = []
    for acc, data in sorted(account_char.items()):
        n = data["total"]
        w = data["with_chars"]
        account_profile.append({
            "account": acc,
            "obs_count": n,
            "char_presence_rate": round(w / n, 3) if n else 0,
            "avg_engagement": round(data["eng_sum"] / n, 3) if n else 0,
            "high_engagement_rate": round(data["high"] / n, 3) if n else 0,
        })
    account_profile.sort(key=lambda x: -x["char_presence_rate"])

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total,
        "character_presence_vs_engagement": {
            "has_characters": summarise(has_chars),
            "no_characters":  summarise(no_chars),
        },
        "character_count_buckets": {k: summarise(v) for k, v in count_buckets.items()},
        "media_type_x_character_presence": {
            mt: {
                "with_characters":    summarise(vals["with"]),
                "without_characters": summarise(vals["without"]),
            }
            for mt, vals in sorted(media_char.items())
        },
        "sector_x_character_presence": {
            sector: {
                "with_characters":    summarise(vals["with"]),
                "without_characters": summarise(vals["without"]),
            }
            for sector, vals in sorted(sector_char.items())
        },
        "account_character_usage": account_profile,
        "key_findings": []
    }

    # Auto-findings
    h = summarise(has_chars)
    n = summarise(no_chars)
    out["key_findings"] = [
        f"Characters present: {int(h['high_engagement_rate']*100)}% high eng (n={h['count']}) — "
        f"{'characters HELP' if h['high_engagement_rate'] > n['high_engagement_rate'] else 'characters HURT'}",
        f"No characters: {int(n['high_engagement_rate']*100)}% high eng (n={n['count']})",
        f"Gap: {abs(round((h['high_engagement_rate'] - n['high_engagement_rate'])*100, 1))}pp {'in favour of human presence' if h['high_engagement_rate'] > n['high_engagement_rate'] else 'in favour of product-only'}",
    ]

    LOGS.mkdir(exist_ok=True)
    (LOGS / "character_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print(f"Character analysis: {total} obs")
    print(f"  Has characters: {has_chars['count']} obs | "
          f"high_eng={int(summarise(has_chars)['high_engagement_rate']*100)}%")
    print(f"  No characters:  {no_chars['count']} obs | "
          f"high_eng={int(summarise(no_chars)['high_engagement_rate']*100)}%")
    print(f"\n  Count buckets:")
    for bucket_name, bucket in count_buckets.items():
        s = summarise(bucket)
        print(f"    {bucket_name} chars: n={s['count']:3d} | "
              f"high_eng={int(s['high_engagement_rate']*100)}%")
    print(f"\n  Account character usage rates:")
    for prof in account_profile:
        bar = "█" * int(prof["char_presence_rate"] * 20)
        print(f"    {prof['account'][-25:]:<25} {int(prof['char_presence_rate']*100):3d}% | {bar}")
    print(f"\nOutput: logs/character_analysis.json")


if __name__ == "__main__":
    main()
