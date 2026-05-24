#!/usr/bin/env python3
"""
fill_occasions.py
Parse cultural_notes.occasion_relevance free text → canonical occasion slug
and write it to the top-level `occasion` field for all 648 obs.

Safe to re-run: skips obs that already have a non-null, non-'?' occasion.

Output: logs/fill_occasions_report.json
"""
import json
import re
from pathlib import Path
from collections import Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"


# ── Canonical occasion map ────────────────────────────────────────────
# Order matters: more specific patterns first, catch-alls last.
OCCASION_RULES = [
    # Ramadan & Eid
    (r"ramadan",                   "ramadan"),
    (r"eid.al.fitr|eid al-fitr",   "eid_al_fitr"),
    (r"eid.al.adha|eid al-adha",   "eid_al_adha"),
    (r"\beid\b",                   "eid_al_fitr"),   # generic eid → fitr

    # Saudi national occasions
    (r"national.day",              "national_day"),
    (r"founding.day|foundation.day|يوم التأسيس", "founding_day"),
    (r"flag.day|يوم العلم",        "national_day"),   # flag day = national pride
    (r"vision.2030",               "vision_2030"),

    # Sports
    (r"national.sports.day|sports.day|sports.pride", "national_sports_day"),
    (r"kings.cup|champions.league|pro.league|al.nassr|sporting.event|football", "sporting_event"),
    (r"worldskills",               "sporting_event"),

    # Seasonal
    (r"winter",                    "winter_seasonal"),
    (r"summer|سمر",                "summer_campaign"),
    (r"back.to.school",            "back_to_school"),
    (r"school.holiday",            "summer_campaign"),
    (r"graduation",                "graduation_season"),

    # Cultural/religious
    (r"hajj",                      "hajj"),
    (r"friday.weekly|أسبوعي",      "evergreen"),

    # International days / awareness
    (r"womens.day|earth.hour|world.coffee.day|international", "brand_campaign"),

    # Brand/campaign specific
    (r"spacetoon|herfy|pepsi|campaign|giveaway|competition|activation|collab", "brand_campaign"),

    # Family/social
    (r"family.gathering|saudi.weekend", "evergreen"),

    # Explicit none / evergreen
    (r"^none$",                    "evergreen"),
    (r"^evergreen$",               "evergreen"),
    (r"evergreen",                 "evergreen"),
]

COMPILED_RULES = [(re.compile(pattern, re.IGNORECASE), slug) for pattern, slug in OCCASION_RULES]


def parse_occasion(text: str) -> str:
    """Map free-text occasion_relevance to a canonical slug."""
    t = (text or "").strip()
    if not t or t.lower() in ("", "none"):
        return "evergreen"
    for pattern, slug in COMPILED_RULES:
        if pattern.search(t):
            return slug
    # Fallback: return a slugified version of the text (keep it clean)
    slug = re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:40]
    return slug or "evergreen"


def main():
    all_obs   = sorted(OBS_ROOT.rglob("*.json"))
    updated   = 0
    skipped   = 0
    already   = 0
    slug_dist = Counter()
    mapping_log = []

    for obs_file in all_obs:
        d = json.loads(obs_file.read_text())

        # Skip if already filled
        existing = d.get("occasion")
        if existing and existing not in ("?", "none", "null"):
            already += 1
            slug_dist[existing] += 1
            continue

        cn       = d.get("cultural_notes") or {}
        occ_text = (cn.get("occasion_relevance") or "").strip()

        if not occ_text:
            slug = "evergreen"
            skipped += 1
        else:
            slug = parse_occasion(occ_text)
            updated += 1

        d["occasion"] = slug
        obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        slug_dist[slug] += 1
        mapping_log.append({"file": obs_file.name, "source_text": occ_text, "mapped_to": slug})

    # ── save report ───────────────────────────────────────────────────
    LOGS.mkdir(exist_ok=True)
    report = {
        "total_obs": len(all_obs),
        "updated": updated,
        "already_had_occasion": already,
        "no_text_set_evergreen": skipped,
        "occasion_distribution": dict(slug_dist.most_common()),
        "sample_mappings": mapping_log[:30],
    }
    (LOGS / "fill_occasions_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("OCCASION FILL COMPLETE")
    print(f"  Updated      : {updated}")
    print(f"  Already set  : {already}")
    print(f"  No text→evgr : {skipped}")
    print()
    print("  Occasion distribution:")
    for slug, cnt in slug_dist.most_common():
        print(f"    {slug:<30} {cnt:>4}")
    print()
    print("  Output → logs/fill_occasions_report.json")


if __name__ == "__main__":
    main()
