#!/usr/bin/env python3
"""
curate_brand_profiles.py
========================
Replaces auto-extracted brand_profiles entries for 5 brands with hand-curated
profiles derived from the top 10 observations by likes_count.

Brands: barnscoffee, tamimimarkets, mcdonaldsksa, mikyajy, hashibasha

Run from repo root:
    python3 scripts/curate_brand_profiles.py

Prints before/after for each brand, then saves intelligence_layer.json.
"""

import json
import glob
import sys
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAIN_PATH = REPO_ROOT / "11_who_to_learn_from" / "intelligence_layer.json"
OBS_GLOB   = str(REPO_ROOT / "11_who_to_learn_from" / "observations" / "**" / "*.json")

BRANDS = ["barnscoffee", "tamimimarkets", "mcdonaldsksa", "mikyajy", "hashibasha"]


def load_top10(brand: str, n: int = 10) -> list[dict]:
    """Return top-n observations by likes_count for a brand."""
    obs = []
    for fpath in glob.glob(OBS_GLOB, recursive=True):
        try:
            with open(fpath, encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("account_handle_normalized") == brand:
                likes = data.get("content_ref", {}).get("likes_count", 0) or 0
                obs.append((likes, data))
        except Exception:
            pass
    obs.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in obs[:n]]


def extract_hashtags(caption: str) -> list[str]:
    return re.findall(r"#[\w؀-ۿ_]+", caption)


# ---------------------------------------------------------------------------
# Hand-curated profiles — derived from real obs analysis
# ---------------------------------------------------------------------------
#
# METHODOLOGY NOTES (per brand):
#
# barnscoffee
#   - 125 obs, top-10 likes 4711→1630
#   - Dominant hashtags: #بارنز (9/10), #مننا_ويفهم_جونا (8/10)
#   - Dialect: hijazi (7/10) — "شتاك أدفى", "جديدنا يخطفك", "امسح الباركود" —
#     clear Saudi-west colloquial. English brand names mixed in.
#   - Tone: playful (5/10) + celebratory (4/10). Giveaways/prizes dominate.
#   - Content: image (7/10), video (3/10). Static product shots + offer posts win.
#   - Voice: warm prize-mechanic energy, community-first (مننا_ويفهم_جونا = "one of us
#     who gets us"). Seasonal campaigns (tumbler, winter menu, women's day).
#   - best_format: image (majority of top-10)
#
# tamimimarkets
#   - 125 obs, top-10 likes 2522→429
#   - Dominant hashtags: #اسواق_التميمي + #tamimimarkets (bilingual pair used together)
#   - Dialect: mixed (5/10) + msa (5/10). Captions swing between recipe-style
#     colloquial ("اعشق الكبدة بهذي الطريقة") and near-MSA news copy.
#   - Tone: informative (5/10). Recipe videos + store opening announcements + athlete
#     interviews. Not promotional-heavy — content-first.
#   - Content: video (10/10 top-10). Reels strategy is clear.
#   - Voice: community content-creator energy; practical recipes, local sports tie-ins.
#   - best_format: video
#
# mcdonaldsksa
#   - 12 obs total (small set); top-10 covers all 12
#   - Dominant hashtags: #ماك_يعايدكم (4x in top-3), #حصرياً_عبر_تطبيق_ماكدونالدز,
#     #ماك_مع_ججك, #اكبر_من_جوعك
#   - Dialect: mixed (10/10) — standard Gulf/Saudi colloquial, not specifically hijazi.
#     "جاوب الحين", "لا تضيع الفرصة", "وش كانت افضل حلقة"
#   - Tone: playful (5/10) + celebratory (3/10). Heavy prize/competition mechanic.
#     iPhone giveaways, World Cup tie-ins.
#   - Content: image (4/10), video (4/10), carousel (2/10). Giveaway posts are images.
#   - Voice: urgent competition energy, casual Saudi colloquial, tech prizes bait.
#   - best_format: image (giveaway mechanic posts outperform)
#
# mikyajy
#   - 96 obs, top-10 likes 48464→195
#   - NOTE: top post (48k likes) is an Emirati Women's Day UGC spike — outlier.
#     Excluding it, organic engagement clusters 100–1100.
#   - Dominant hashtags: #Mikyajy (7/10), #HighPerformanceBeauty (7/10),
#     #SaudiBrand (7/10), #CleanBeauty (6/10), #SaudiBeauty (5/10)
#   - Dialect: mixed (7/10) — bilingual English+Arabic in same caption. Not hijazi
#     or MSA dominant; it's true English-Arabic code-switching.
#   - Tone: playful (4/10) + informative (4/10). Beauty tutorials, product comparisons,
#     UGC re-shares. One urgent sale post (25–75% off).
#   - Content: video (10/10). Exclusively video.
#   - Voice: aspirational Saudi beauty brand, feminine address ("بنات", "صبايا"),
#     English product names mixed with Arabic copy. Consistent brand hashtag stack.
#   - best_format: video
#
# hashibasha
#   - 102 obs, top-10 likes 1158→142
#   - Dominant hashtags: #حاشي_باشا (9/10), #نكهة_سعودية (4/10), campaign-specific
#     sets (#تريبل_دجاج_الباشا, #لمتنا_غير) appear in top-2
#   - Dialect: msa (9/10) — captions use formal/near-MSA Arabic. Short, declarative.
#     "عروض تكفي وتوفّي", "حاشي باشا.. يعرفك طعم الكبسة الصح"
#   - Tone: casual (4/10) + informative (3/10). No hype — direct value statements.
#   - Content: video (5/10) + image (5/10) tied.
#   - Voice: proud Saudi heritage food brand, traditional kabsa/rice dishes. Terse
#     captions, heritage pride cues (#نكهة_سعودية, #نكهة_التراث).
#   - best_format: video (highest single post is video; video+image split so video
#     slight edge on max engagement)
# ---------------------------------------------------------------------------

CURATED_PROFILES = {
    "barnscoffee": {
        "sector": "f_and_b",
        "voice": "Prize-mechanic community brand. Runs seasonal campaigns (tumbler drops, winter menu, Women's Day) with warm participatory energy. Captions are short and invitation-style, built around shared identity and offers.",
        "tone": ["playful", "celebratory", "warm"],
        "language": "arabic",
        "arabic_style": "saudi_colloquial",
        "signature_phrases": [
            "#بارنز",
            "#مننا_ويفهم_جونا",
            "لا تفوّتوا فرصتكم",
            "العرض ساري في جميع الفروع"
        ],
        "best_format": "image",
        "confidence": "curated_from_real_obs",
        "curation_notes": "Top-10 obs (4711–1630 likes). Hijazi dialect 7/10. Image 7/10. #بارنز + #مننا_ويفهم_جونا appear in 8–9 of top 10."
    },

    "tamimimarkets": {
        "sector": "retail_lifestyle",
        "voice": "Content-creator supermarket. Leads with recipes, athlete partnerships, and store-opening moments. Bilingual output (Arabic + English captions for bilingual audience). Practical and community-adjacent, not discount-heavy.",
        "tone": ["informative", "casual", "community"],
        "language": "arabic",
        "arabic_style": "bilingual",
        "signature_phrases": [
            "#اسواق_التميمي",
            "#التميمي_جاركم",
            "#tamimimarkets",
            "جربوها وعطوني رايكم"
        ],
        "best_format": "video",
        "confidence": "curated_from_real_obs",
        "curation_notes": "Top-10 obs (2522–429 likes). Video 10/10. Mixed/MSA dialect split 5-5. Recipe content + athlete collabs dominate."
    },

    "mcdonaldsksa": {
        "sector": "f_and_b",
        "voice": "Giveaway-engine brand. Drives engagement through interactive prize mechanics (iPhone giveaways, World Cup tie-ins). Casual Gulf colloquial. Calls to action are direct: follow, like, answer the question.",
        "tone": ["playful", "celebratory", "urgent"],
        "language": "arabic",
        "arabic_style": "saudi_colloquial",
        "signature_phrases": [
            "#ماك_يعايدكم",
            "#حصرياً_عبر_تطبيق_ماكدونالدز",
            "#اكبر_من_جوعك",
            "#ماك_مع_ججك",
            "جاوب الحين في التعليقات"
        ],
        "best_format": "image",
        "confidence": "curated_from_real_obs",
        "curation_notes": "12 total obs. Top-3 all giveaway posts (4238–3282 likes) are images. Playful 5/10, celebratory 3/10. All 10 obs tagged mixed dialect."
    },

    "mikyajy": {
        "sector": "beauty_personal_care",
        "voice": "Saudi beauty brand with bilingual code-switching. Addresses audience as بنات / صبايا. Mixes Arabic copy with English product names and brand hashtags (#HighPerformanceBeauty, #SaudiBrand). Tutorial-first, UGC-amplified.",
        "tone": ["playful", "informative", "aspirational"],
        "language": "arabic",
        "arabic_style": "bilingual",
        "signature_phrases": [
            "#Mikyajy",
            "#HighPerformanceBeauty",
            "#SaudiBrand",
            "#CleanBeauty",
            "#SaudiBeauty",
            "بنات!",
            "صباياااا"
        ],
        "best_format": "video",
        "confidence": "curated_from_real_obs",
        "curation_notes": "96 obs. Video 10/10 in top-10. Mixed (bilingual) dialect 7/10. Brand hashtag stack (#Mikyajy + #HighPerformanceBeauty + #SaudiBrand + #CleanBeauty) appears in 6–7 of top 10."
    },

    "hashibasha": {
        "sector": "f_and_b",
        "voice": "Heritage Saudi rice-dish brand. Terse declarative captions. Near-MSA Arabic — no dialect affectation. Leans on national pride and traditional food identity (#نكهة_سعودية). Campaign hashtags are product-name-based.",
        "tone": ["casual", "proud", "informative"],
        "language": "arabic",
        "arabic_style": "msa_formal",
        "signature_phrases": [
            "#حاشي_باشا",
            "#نكهة_سعودية",
            "#لمتنا_غير",
            "طعم يحبه قلبك",
            "حاشي باشا.. يعرفك طعم الكبسة الصح"
        ],
        "best_format": "video",
        "confidence": "curated_from_real_obs",
        "curation_notes": "102 obs. Dialect msa 9/10 in top-10. #حاشي_باشا in 9/10 posts. Top 2 posts are video (1158, 892 likes). Image/video tied in count but video edges on peak engagement."
    }
}


def main():
    # Load brain
    with open(BRAIN_PATH, encoding="utf-8") as fh:
        brain = json.load(fh)

    brand_profiles = brain.get("brand_profiles", {})

    for brand in BRANDS:
        old = brand_profiles.get(brand, {})
        new = CURATED_PROFILES[brand]

        # Print before/after
        print(f"\n{'='*60}")
        print(f"BRAND: {brand}")
        print(f"{'='*60}")
        print("BEFORE:")
        print(json.dumps(old, ensure_ascii=False, indent=2))
        print("\nAFTER:")
        print(json.dumps(new, ensure_ascii=False, indent=2))

        # Replace
        brand_profiles[brand] = new

    brain["brand_profiles"] = brand_profiles

    # Save
    with open(BRAIN_PATH, "w", encoding="utf-8") as fh:
        json.dump(brain, fh, ensure_ascii=False, indent=2)

    print(f"\n\nSaved: {BRAIN_PATH}")
    print(f"Curated profiles written for: {', '.join(BRANDS)}")


if __name__ == "__main__":
    main()
