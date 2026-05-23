#!/usr/bin/env python3
"""
normalize_occasions.py
Canonicalize the 131 raw occasion values in obs JSON files to ~18 slug values.
Writes in-place and outputs logs/occasion_calendar_v2.json.
"""
import json, os, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

# Canonical mapping: keywords → canonical slug
# Order matters — first match wins
OCCASION_MAP = [
    # Ramadan/Eid first (most distinctive)
    (r"eid.*fitr|fitr",                 "eid_al_fitr"),
    (r"eid.*adha|adha",                 "eid_al_adha"),
    (r"eid(?!.*adha|.*fitr)",           "eid_al_fitr"),   # generic 'eid' → fitr
    (r"ramadan|رمضان",                  "ramadan"),
    (r"iftar",                          "ramadan"),
    (r"suhoor",                         "ramadan"),
    (r"hajj|حج",                        "hajj"),
    (r"muharram|new.*hijri|hijri.*new", "islamic_new_year"),
    (r"mawlid|prophet.*birth",          "mawlid"),
    # Saudi national occasions
    (r"national.*day|يوم.*وطني|saudi.*national|اليوم_الوطني", "national_day"),
    (r"founding.*day|يوم.*تأسيس",       "founding_day"),
    (r"vision.*2030|2030",              "vision_2030_moment"),
    (r"national.*sport|sport.*day|يوم.*رياضة", "national_sports_day"),
    # Seasonal
    (r"summer|صيف",                     "summer_campaign"),
    (r"winter|شتاء",                    "winter_seasonal"),
    (r"back.*school|school.*season",    "back_to_school"),
    # Commercial occasions
    (r"white.*friday|black.*friday",    "white_friday"),
    (r"singles.*day|11.11",             "singles_day"),
    (r"mother.*day|mothers.*day|يوم.*أم", "mothers_day"),
    (r"father.*day|fathers.*day",       "fathers_day"),
    (r"valentine|love.*day|عيد.*حب",    "valentines"),
    (r"women.*day|international.*women|يوم.*المرأة", "international_womens_day"),
    (r"world.*coffee|coffee.*day",      "world_coffee_day"),
    (r"world.*chocolate|chocolate.*day","world_chocolate_day"),
    (r"graduation|تخرج",                "graduation_season"),
    (r"new.*year|رأس.*سنة|new.*year",   "new_year"),
    (r"friday|جمعة",                    "friday_weekly"),
    # Evergreen
    (r"everyday|daily|general|product.*launch|launch|promo|offer|sale|regular|no.*occasion|none|brand", "evergreen"),
]

def canonicalize(raw: str) -> str:
    if not raw:
        return "evergreen"
    val = str(raw).lower().strip()
    for pattern, slug in OCCASION_MAP:
        if re.search(pattern, val):
            return slug
    return "evergreen"  # fallback

def main():
    changes = 0
    skipped = 0
    by_canonical = defaultdict(list)   # slug → list of {account, shortcode, raw}
    raw_to_canonical = {}

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            skipped += 1
            continue

        if "cultural_notes" not in data:
            continue

        raw = data["cultural_notes"].get("occasion_relevance")
        if raw is None:
            continue

        canonical = canonicalize(raw)
        raw_to_canonical[str(raw)] = canonical

        account = data.get("account_handle_normalized", "unknown")
        shortcode = data.get("shortcode", obs_file.stem)

        by_canonical[canonical].append({
            "account": account,
            "shortcode": shortcode,
            "raw_value": raw
        })

        # Write back normalized value
        if str(raw) != canonical:
            data["cultural_notes"]["occasion_relevance"] = canonical
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            changes += 1

    # Build calendar output
    calendar = {}
    for slug in sorted(by_canonical.keys()):
        entries = by_canonical[slug]
        accounts = sorted(set(e["account"] for e in entries))
        raw_values = sorted(set(e["raw_value"] for e in entries if str(e["raw_value"]) != slug))
        calendar[slug] = {
            "canonical_slug": slug,
            "observation_count": len(entries),
            "account_count": len(accounts),
            "accounts": accounts,
            "raw_values_normalized": raw_values,
            "observations": entries
        }

    # Sort by observation_count desc
    calendar_sorted = dict(sorted(calendar.items(), key=lambda x: -x[1]["observation_count"]))

    LOGS.mkdir(exist_ok=True)
    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_observations_processed": sum(len(v["observations"]) for v in calendar_sorted.values()),
        "canonical_occasion_count": len(calendar_sorted),
        "raw_values_normalized": len(raw_to_canonical),
        "obs_changed": changes,
        "calendar": calendar_sorted
    }
    (LOGS / "occasion_calendar_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Normalized {changes} obs values → {len(calendar_sorted)} canonical occasions")
    print(f"Output: logs/occasion_calendar_v2.json")
    for slug, data in calendar_sorted.items():
        print(f"  {slug}: {data['observation_count']} obs, {data['account_count']} accounts")

if __name__ == "__main__":
    main()
