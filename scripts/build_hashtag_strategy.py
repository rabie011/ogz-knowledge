#!/usr/bin/env python3
"""
build_hashtag_strategy.py
Analyse hashtag patterns from extracted caption_text.

Agency questions answered:
  - Optimal hashtag count × sector × engagement
  - Arabic hashtags vs English hashtags vs mixed
  - Branded hashtags vs category hashtags vs occasion hashtags
  - Top-performing individual hashtags by sector and engagement

Output: logs/hashtag_strategy.json
"""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75,
    "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}
CORPUS_BASELINE = 0.54

_HASHTAG_RE    = re.compile(r"#([\w؀-ۿ]+)")
_ARABIC_CHAR   = re.compile(r"[؀-ۿ]")
_ENGLISH_CHAR  = re.compile(r"[A-Za-z]")


def _classify_hashtag(tag: str) -> str:
    """Classify a single hashtag into type."""
    t = tag.lower()
    # Occasion markers
    occasion_kws = ["رمضان", "ramadan", "عيد", "eid", "وطني", "national", "تأسيس",
                    "founding", "رياضة", "sports", "حج", "hajj", "رمضان", "winter", "شتاء"]
    for kw in occasion_kws:
        if kw in t:
            return "occasion"
    # Location markers
    location_kws = ["رياض", "riyadh", "jeddah", "جدة", "ksa", "saudi", "سعودي",
                    "مكة", "مدينة", "الشرقية", "neom"]
    for kw in location_kws:
        if kw in t:
            return "location"
    # Category / sector markers
    fnb_kws = ["مطعم", "restaurant", "cafe", "قهوة", "coffee", "food", "طعام",
               "مطاعم", "برغر", "burger", "بيتزا", "pizza", "حلويات", "sweets",
               "فطور", "breakfast", "lunch", "غداء", "dinner", "عشاء"]
    for kw in fnb_kws:
        if kw in t:
            return "category_fnb"
    beauty_kws = ["makeup", "beauty", "skincare", "تجميل", "عناية", "بشرة", "مكياج",
                  "hair", "شعر", "perfume", "عطر"]
    for kw in beauty_kws:
        if kw in t:
            return "category_beauty"
    retail_kws = ["تسوق", "shop", "shopping", "sale", "خصم", "offer", "عروض", "store", "متجر"]
    for kw in retail_kws:
        if kw in t:
            return "category_retail"
    # Engagement bait
    viral_kws = ["explore", "instagood", "viral", "trending", "fyp", "foryou", "تريند"]
    for kw in viral_kws:
        if kw in t:
            return "engagement_bait"
    # Branded (contains @ or brand-like capitalized name — hard to detect without a brand list)
    # Simple heuristic: mixed-case English without common words → likely branded
    return "branded_or_other"


def _tag_language(tag: str) -> str:
    has_ar = bool(_ARABIC_CHAR.search(tag))
    has_en = bool(_ENGLISH_CHAR.search(tag))
    if has_ar and has_en:
        return "mixed"
    if has_ar:
        return "arabic"
    if has_en:
        return "english"
    return "other"


def _count_bucket(n: int) -> str:
    if n == 0:
        return "0"
    if n <= 5:
        return "1_5"
    if n <= 15:
        return "6_15"
    return "16plus"


def main():
    # Per-hashtag tracking
    tag_data = defaultdict(lambda: {"count": 0, "high": 0, "sectors": Counter(), "type": None})

    # Aggregate buckets
    by_count    = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_type     = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_tag_lang = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    count_sector = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))

    total = 0
    cap_filled = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        vo  = data.get("voice_observations") or {}
        qa  = data.get("quality_assessment")  or {}

        cap = vo.get("caption_text")
        if cap is None:
            continue

        cap_filled += 1
        cap_str = str(cap)
        sector  = data.get("sector") or "unknown"

        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        # Extract all hashtags
        tags = _HASHTAG_RE.findall(cap_str)
        n_tags = len(tags)

        # Hashtag count bucket
        cb = _count_bucket(n_tags)
        by_count[cb]["count"] += 1
        by_count[cb]["high"]  += is_high
        by_count[cb]["sum"]   += eng
        count_sector[cb][sector]["count"] += 1
        count_sector[cb][sector]["high"]  += is_high

        # Per-tag analysis
        seen_types = set()
        seen_langs = set()
        for tag in tags:
            t_type = _classify_hashtag(tag)
            t_lang = _tag_language(tag)
            tag_data[tag]["count"]          += 1
            tag_data[tag]["high"]           += is_high
            tag_data[tag]["sectors"][sector] += 1
            tag_data[tag]["type"]            = t_type   # last wins, good enough

            if t_type not in seen_types:
                seen_types.add(t_type)
                by_type[t_type]["count"] += 1
                by_type[t_type]["high"]  += is_high
                by_type[t_type]["sum"]   += eng

            if t_lang not in seen_langs:
                seen_langs.add(t_lang)
                by_tag_lang[t_lang]["count"] += 1
                by_tag_lang[t_lang]["high"]  += is_high
                by_tag_lang[t_lang]["sum"]   += eng

    def _rate(d):
        return round(d["high"] / d["count"], 3) if d["count"] else 0

    # Count table
    count_table = []
    for cb, d in by_count.items():
        n = d["count"]
        r = _rate(d)
        count_table.append({
            "hashtag_count": cb, "obs_count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"] / n, 3) if n else 0,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    count_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Type table
    type_table = []
    for t, d in by_type.items():
        n = d["count"]
        r = _rate(d)
        type_table.append({
            "hashtag_type": t, "obs_count": n,
            "high_engagement_rate": r,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    type_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Language table
    lang_table = []
    for lang, d in by_tag_lang.items():
        n = d["count"]
        r = _rate(d)
        lang_table.append({
            "hashtag_language": lang, "obs_count": n,
            "high_engagement_rate": r,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    lang_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Top individual hashtags (3+ appearances)
    top_tags = []
    for tag, d in tag_data.items():
        n = d["count"]
        if n < 3:
            continue
        r = round(d["high"] / n, 3)
        top_tags.append({
            "hashtag": f"#{tag}",
            "obs_count": n,
            "high_engagement_rate": r,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
            "type": d["type"],
            "top_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    top_tags.sort(key=lambda x: (-x["high_engagement_rate"], -x["obs_count"]))

    # Count × sector
    count_sector_rows = []
    for cb, sects in count_sector.items():
        for sect, d in sects.items():
            if d["count"] >= 3:
                r = round(d["high"] / d["count"], 3)
                count_sector_rows.append({
                    "hashtag_count": cb, "sector": sect,
                    "count": d["count"],
                    "high_eng_rate": r,
                    "lift": round(r - CORPUS_BASELINE, 3),
                })
    count_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Findings
    findings = []
    if count_table:
        best_c = count_table[0]
        findings.append(
            f"Optimal hashtag count: '{best_c['hashtag_count']}' = "
            f"{int(best_c['high_engagement_rate']*100)}% "
            f"({'+' if best_c['lift_vs_baseline']>=0 else ''}{int(best_c['lift_vs_baseline']*100)}pp)"
        )
        worst_c = count_table[-1]
        findings.append(
            f"Worst hashtag count: '{worst_c['hashtag_count']}' = "
            f"{int(worst_c['high_engagement_rate']*100)}%"
        )
    if type_table:
        best_t = type_table[0]
        findings.append(
            f"Best hashtag type: '{best_t['hashtag_type']}' = "
            f"{int(best_t['high_engagement_rate']*100)}%"
        )
    if lang_table:
        best_l = lang_table[0]
        findings.append(
            f"Best hashtag language: '{best_l['hashtag_language']}' = "
            f"{int(best_l['high_engagement_rate']*100)}%"
        )
    if top_tags:
        findings.append(
            f"Top individual hashtag: '{top_tags[0]['hashtag']}' = "
            f"{int(top_tags[0]['high_engagement_rate']*100)}% (n={top_tags[0]['obs_count']})"
        )

    agency_rules = []
    if count_table:
        agency_rules.append(
            f"Use {count_table[0]['hashtag_count']} hashtags per post — best engagement count"
        )
    if type_table:
        agency_rules.append(
            f"Prioritise '{type_table[0]['hashtag_type']}' hashtags — strongest performer"
        )
    if lang_table:
        agency_rules.append(
            f"Use '{lang_table[0]['hashtag_language']}' hashtags — highest engagement language"
        )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_caption": cap_filled,
        "hashtag_count_table": count_table,
        "hashtag_type_table": type_table,
        "hashtag_language_table": lang_table,
        "top_individual_hashtags": top_tags[:50],
        "hashtag_count_by_sector": count_sector_rows,
        "key_findings": findings,
        "agency_rules": agency_rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "hashtag_strategy.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Hashtag strategy: {cap_filled}/{total} obs with captions")
    print(f"\nHashtag count → engagement:")
    for r in count_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  #{r['hashtag_count']:<10} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['obs_count']}")
    print(f"\nHashtag type → engagement:")
    for r in type_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['hashtag_type']:<26} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['obs_count']}")
    print(f"\nHashtag language → engagement:")
    for r in lang_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['hashtag_language']:<14} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['obs_count']}")
    print(f"\nTop hashtags (n≥3):")
    for r in top_tags[:12]:
        print(f"  {r['hashtag']:<34} {int(r['high_engagement_rate']*100):>3}%  n={r['obs_count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/hashtag_strategy.json")


if __name__ == "__main__":
    main()
