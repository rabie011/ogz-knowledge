#!/usr/bin/env python3
"""
build_hashtag_cooccurrence.py
Build a hashtag co-occurrence network from caption_text fields.

For each pair of hashtags that appear together: record frequency + avg engagement.
Also: top hashtag clusters, lone hashtags, Saudi-specific hashtag patterns.

Output: logs/hashtag_cooccurrence.json
"""
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75, "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}


def _extract_hashtags(caption: str) -> list[str]:
    if not caption:
        return []
    tags = re.findall(r'#([^\s#،,،؛]+)', caption)
    return [t.lower().strip('.,!؟?') for t in tags if len(t) > 1]


def main():
    tag_freq    = Counter()
    tag_eng     = defaultdict(list)
    pair_freq   = Counter()
    pair_eng    = defaultdict(list)
    sector_tags = defaultdict(Counter)
    occ_tags    = defaultdict(Counter)

    total_with_cap = 0

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        vo  = d.get("voice_observations") or {}
        cap = vo.get("caption_text")
        if not cap:
            continue

        qa  = d.get("quality_assessment") or {}
        eng = ENG_MAP.get(str(qa.get("engagement_potential") or "").lower(), 0.5)
        sector = d.get("sector", "unknown")
        occ    = d.get("occasion") or "evergreen"

        tags = _extract_hashtags(cap)
        if not tags:
            continue

        total_with_cap += 1
        tags_unique = list(dict.fromkeys(tags))  # dedupe preserving order

        for tag in tags_unique:
            tag_freq[tag] += 1
            tag_eng[tag].append(eng)
            sector_tags[sector][tag] += 1
            occ_tags[occ][tag] += 1

        for a, b in combinations(sorted(tags_unique), 2):
            pair = f"{a} + {b}"
            pair_freq[pair] += 1
            pair_eng[pair].append(eng)

    # ── Build outputs ────────────────────────────────────────────────
    corpus_baseline = 0.62

    top_tags = []
    for tag, freq in tag_freq.most_common(50):
        engs = tag_eng[tag]
        avg  = round(sum(engs) / len(engs), 3)
        top_tags.append({
            "hashtag": f"#{tag}",
            "frequency": freq,
            "avg_engagement": avg,
            "lift": round(avg - corpus_baseline, 3),
            "language": "arabic" if re.search(r'[؀-ۿ]', tag) else "english",
        })

    top_pairs = []
    for pair, freq in pair_freq.most_common(40):
        if freq < 2:
            continue
        engs = pair_eng[pair]
        avg  = round(sum(engs) / len(engs), 3)
        a, b = pair.split(" + ")
        top_pairs.append({
            "pair": [f"#{a}", f"#{b}"],
            "frequency": freq,
            "avg_engagement": avg,
            "lift": round(avg - corpus_baseline, 3),
        })

    # Sector top-5 hashtags
    sector_top = {}
    for sector, counts in sector_tags.items():
        sector_top[sector] = [f"#{t}" for t, _ in counts.most_common(5)]

    # Occasion top hashtags
    occ_top = {}
    for occ, counts in occ_tags.items():
        if counts:
            occ_top[occ] = [f"#{t}" for t, _ in counts.most_common(5)]

    # Arabic vs English hashtag engagement
    ar_tags = [v for t, engs in tag_eng.items()
               if re.search(r'[؀-ۿ]', t)
               for v in engs]
    en_tags = [v for t, engs in tag_eng.items()
               if not re.search(r'[؀-ۿ]', t)
               for v in engs]
    lang_comparison = {
        "arabic_hashtags": {
            "count": len(tag_freq) - sum(1 for t in tag_freq if not re.search(r'[؀-ۿ]', t)),
            "avg_engagement": round(sum(ar_tags) / len(ar_tags), 3) if ar_tags else None,
        },
        "english_hashtags": {
            "count": sum(1 for t in tag_freq if not re.search(r'[؀-ۿ]', t)),
            "avg_engagement": round(sum(en_tags) / len(en_tags), 3) if en_tags else None,
        },
    }

    out = {
        "meta": {
            "obs_with_captions": total_with_cap,
            "unique_hashtags": len(tag_freq),
            "unique_pairs": len(pair_freq),
            "corpus_baseline": corpus_baseline,
        },
        "top_hashtags": top_tags,
        "top_cooccurring_pairs": top_pairs,
        "hashtag_language_comparison": lang_comparison,
        "top_hashtags_by_sector": sector_top,
        "top_hashtags_by_occasion": occ_top,
        "key_findings": [],
    }

    # Findings
    best_tag  = max(top_tags, key=lambda x: x["lift"]) if top_tags else None
    worst_tag = min(top_tags, key=lambda x: x["lift"]) if top_tags else None
    ar_eng    = lang_comparison
    findings  = []
    if best_tag:
        findings.append(f"Best-performing hashtag: {best_tag['hashtag']} (lift={best_tag['lift']:+.2f}, n={best_tag['frequency']})")
    if worst_tag and worst_tag["frequency"] >= 3:
        findings.append(f"Worst-performing hashtag: {worst_tag['hashtag']} (lift={worst_tag['lift']:+.2f})")
    if ar_eng["arabic_hashtags"]["avg_engagement"] and ar_eng["english_hashtags"]["avg_engagement"]:
        diff = round(ar_eng["arabic_hashtags"]["avg_engagement"] - ar_eng["english_hashtags"]["avg_engagement"], 3)
        winner = "Arabic" if diff > 0 else "English"
        findings.append(f"{winner} hashtags outperform by {abs(diff):.2f} avg engagement")
    out["key_findings"] = findings

    LOGS.mkdir(exist_ok=True)
    (LOGS / "hashtag_cooccurrence.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    print("=" * 55)
    print("HASHTAG CO-OCCURRENCE ANALYSIS COMPLETE")
    print(f"  Captions analysed : {total_with_cap}")
    print(f"  Unique hashtags   : {len(tag_freq)}")
    print(f"  Unique pairs      : {len(pair_freq)}")
    print()
    print("  Top hashtags by engagement lift:")
    for t in sorted(top_tags, key=lambda x: -x["lift"])[:8]:
        sign = "+" if t["lift"] > 0 else ""
        print(f"    {t['hashtag']:<30} lift={sign}{t['lift']:.2f}  n={t['frequency']}")
    print()
    for f in findings:
        print(f"  ▸ {f}")
    print()
    print("  Output → logs/hashtag_cooccurrence.json")


if __name__ == "__main__":
    main()
