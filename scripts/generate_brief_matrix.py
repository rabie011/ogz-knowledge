#!/usr/bin/env python3
"""
generate_brief_matrix.py — Generate comprehensive brief matrix for HUMAIN collection.

Covers all OGZ-tracked brands × their most commercially relevant occasions.
Output: data/brief_matrix.json  (consumed by humain_collector.py --matrix flag)

Usage:
  python3 scripts/generate_brief_matrix.py           # generate and save
  python3 scripts/generate_brief_matrix.py --summary # show breakdown only
"""

import json
import sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent.parent

# ── Saudi marketing calendar ─────────────────────────────────────────────────
OCCASIONS_AR = {
    "national_day":      "اليوم الوطني",
    "founding_day":      "يوم التأسيس",
    "ramadan":           "رمضان",
    "eid_al_fitr":       "عيد الفطر",
    "eid_al_adha":       "عيد الأضحى",
    "riyadh_season":     "موسم الرياض",
    "white_friday":      "الجمعة البيضاء",
    "summer_campaign":   "الصيف",
    "back_to_school":    "العودة للمدارس",
    "winter_seasonal":   "الشتاء",
    "graduation_season": "موسم التخرج",
    "evergreen":         "محتوى دائم",
}

SECTORS_AR = {
    "f_and_b":              "مطاعم وكافيهات",
    "fashion":              "أزياء وموضة",
    "real_estate":          "عقارات",
    "retail_lifestyle":     "تجزئة",
    "beauty_personal_care": "جمال وعناية",
    "healthcare_wellness":  "صحة ولياقة",
}

# ── Brand registry ─────────────────────────────────────────────────────────
# Format: handle → {sector, ar, product, hashtags, occasions[]}
# One primary product per brand — the most representative brief.
# Occasions ordered by commercial relevance for that brand.

BRANDS = [

    # ═══ F & B ══════════════════════════════════════════════════════════════

    {"handle": "albaik",
     "sector": "f_and_b", "ar": "البيك",
     "product": "بروستد",
     "hashtags": "#انتم_والبيك_جيران #صنع_في_السعودية",
     "occasions": ["national_day", "founding_day", "eid_al_fitr", "eid_al_adha", "ramadan", "riyadh_season", "summer_campaign"]},

    {"handle": "alromansiahksa",
     "sector": "f_and_b", "ar": "الرومانسية",
     "product": "مشاوي وكبسة",
     "hashtags": "#الرومانسية #مشاوي_سعودية",
     "occasions": ["national_day", "founding_day", "eid_al_fitr", "eid_al_adha", "ramadan", "riyadh_season"]},

    {"handle": "barnscoffee",
     "sector": "f_and_b", "ar": "بارنز",
     "product": "قهوة مثلجة",
     "hashtags": "#بارنز #قهوتك_اليوم",
     "occasions": ["ramadan", "national_day", "founding_day", "summer_campaign", "riyadh_season", "white_friday", "evergreen"]},

    {"handle": "mcdonaldsksa",
     "sector": "f_and_b", "ar": "ماكدونالدز",
     "product": "حفلة ماك",
     "hashtags": "#ماكدونالدز_السعودية #ماك_دايم",
     "occasions": ["eid_al_fitr", "eid_al_adha", "national_day", "summer_campaign", "ramadan", "riyadh_season", "back_to_school"]},

    {"handle": "herfyfsc",
     "sector": "f_and_b", "ar": "هرفي",
     "product": "برغر هرفي",
     "hashtags": "#هرفي #برغر_سعودي",
     "occasions": ["national_day", "founding_day", "eid_al_fitr", "ramadan", "summer_campaign", "riyadh_season"]},

    {"handle": "kuduksa",
     "sector": "f_and_b", "ar": "كودو",
     "product": "برغر اللحم الطازج",
     "hashtags": "#كودو #لحم_طازج",
     "occasions": ["national_day", "founding_day", "eid_al_fitr", "riyadh_season", "summer_campaign"]},

    {"handle": "shawarmersa",
     "sector": "f_and_b", "ar": "شاورمر",
     "product": "شاورما",
     "hashtags": "#شاورمر #شاورما_سعودية",
     "occasions": ["national_day", "founding_day", "ramadan", "eid_al_fitr", "riyadh_season"]},

    {"handle": "crumblcookiespr",
     "sector": "f_and_b", "ar": "كرمبل كوكيز",
     "product": "كوكيز موسمي",
     "hashtags": "#كرمبل #كوكيز_العيد",
     "occasions": ["eid_al_fitr", "eid_al_adha", "riyadh_season", "national_day", "winter_seasonal", "white_friday"]},

    {"handle": "elixirbunn",
     "sector": "f_and_b", "ar": "إليكسير",
     "product": "مشروبات صحية",
     "hashtags": "#إليكسير #صحي_ولذيذ",
     "occasions": ["ramadan", "summer_campaign", "national_day", "riyadh_season", "evergreen"]},

    {"handle": "kyancafe",
     "sector": "f_and_b", "ar": "كيان كافيه",
     "product": "قهوة سعودية",
     "hashtags": "#كيان #قهوة_سعودية",
     "occasions": ["national_day", "founding_day", "ramadan", "riyadh_season", "evergreen"]},

    {"handle": "altazaj_fakieh",
     "sector": "f_and_b", "ar": "الطازج فاكيه",
     "product": "دجاج مشوي",
     "hashtags": "#الطازج #مشاوي_طازجة",
     "occasions": ["national_day", "eid_al_adha", "eid_al_fitr", "ramadan", "riyadh_season"]},

    {"handle": "aseeb.najd",
     "sector": "f_and_b", "ar": "عصيب نجد",
     "product": "أكلات نجدية",
     "hashtags": "#عصيب_نجد #أكل_نجدي",
     "occasions": ["national_day", "founding_day", "eid_al_adha", "riyadh_season", "evergreen"]},

    {"handle": "hashibasha",
     "sector": "f_and_b", "ar": "حاشي باشا",
     "product": "مشاوي عائلية",
     "hashtags": "#حاشي_باشا #لمة_العائلة",
     "occasions": ["eid_al_adha", "national_day", "founding_day", "ramadan"]},

    {"handle": "pizzahutsaudi",
     "sector": "f_and_b", "ar": "بيتزا هت",
     "product": "بيتزا عائلية",
     "hashtags": "#بيتزاهت_السعودية #لمة_بيتزا",
     "occasions": ["eid_al_fitr", "national_day", "summer_campaign", "riyadh_season", "white_friday"]},

    # ═══ FASHION ════════════════════════════════════════════════════════════

    {"handle": "maxfashionmena",
     "sector": "fashion", "ar": "ماكس",
     "product": "عباءة كلاسيكية",
     "hashtags": "#ماكس_فاشون #عباية_العيد",
     "occasions": ["eid_al_fitr", "eid_al_adha", "national_day", "founding_day", "back_to_school", "winter_seasonal"]},

    {"handle": "hmksa",
     "sector": "fashion", "ar": "H&M",
     "product": "كوليكشن موسمي",
     "hashtags": "#HM_السعودية #موضة_موسمية",
     "occasions": ["eid_al_fitr", "riyadh_season", "winter_seasonal", "summer_campaign", "white_friday", "back_to_school"]},

    {"handle": "levelshoes",
     "sector": "fashion", "ar": "ليفل شوز",
     "product": "صبابيط العيد",
     "hashtags": "#ليفل_شوز #أحذية_فاخرة",
     "occasions": ["eid_al_adha", "eid_al_fitr", "riyadh_season", "national_day", "white_friday", "winter_seasonal"]},

    {"handle": "mangome",
     "sector": "fashion", "ar": "مانغو",
     "product": "فستان مناسبات",
     "hashtags": "#مانغو_السعودية #موضة_نسائية",
     "occasions": ["eid_al_fitr", "riyadh_season", "winter_seasonal", "national_day", "graduation_season"]},

    {"handle": "ounass",
     "sector": "fashion", "ar": "أوناس",
     "product": "موضة فاخرة",
     "hashtags": "#أوناس #فاشون_فاخر",
     "occasions": ["eid_al_fitr", "riyadh_season", "white_friday", "winter_seasonal", "graduation_season"]},

    {"handle": "namshi",
     "sector": "fashion", "ar": "نمشي",
     "product": "ملابس أونلاين",
     "hashtags": "#نمشي #تسوق_اونلاين",
     "occasions": ["eid_al_fitr", "white_friday", "national_day", "back_to_school", "summer_campaign"]},

    {"handle": "lcwaikiki",
     "sector": "fashion", "ar": "LC Waikiki",
     "product": "ملابس للعائلة",
     "hashtags": "#LC_Waikiki #ملابس_عائلية",
     "occasions": ["eid_al_fitr", "eid_al_adha", "back_to_school", "white_friday", "national_day"]},

    {"handle": "kiabiksa",
     "sector": "fashion", "ar": "كيابي",
     "product": "ملابس الأطفال",
     "hashtags": "#كيابي #أزياء_أطفال",
     "occasions": ["eid_al_fitr", "back_to_school", "national_day", "winter_seasonal"]},

    {"handle": "centrepointstores",
     "sector": "fashion", "ar": "سنترپوينت",
     "product": "كوليكشن العائلة",
     "hashtags": "#سنتربوينت #عائلة_واحدة",
     "occasions": ["eid_al_fitr", "eid_al_adha", "back_to_school", "national_day", "white_friday"]},

    {"handle": "randbfashion",
     "sector": "fashion", "ar": "R&B",
     "product": "أزياء شبابية",
     "hashtags": "#RnB_فاشون #شباب_سعودي",
     "occasions": ["national_day", "founding_day", "riyadh_season", "summer_campaign", "white_friday"]},

    {"handle": "zara",
     "sector": "fashion", "ar": "زارا",
     "product": "كوليكشن الموسم",
     "hashtags": "#زارا_السعودية #موضة_عالمية",
     "occasions": ["riyadh_season", "eid_al_fitr", "white_friday", "winter_seasonal"]},

    {"handle": "lifestyleshops",
     "sector": "fashion", "ar": "لايف ستايل",
     "product": "هوم ديكور",
     "hashtags": "#لايف_ستايل #ديكور_البيت",
     "occasions": ["national_day", "riyadh_season", "eid_al_fitr", "white_friday", "winter_seasonal"]},

    # ═══ BEAUTY ══════════════════════════════════════════════════════════════

    {"handle": "mikyajy",
     "sector": "beauty_personal_care", "ar": "مكياجي",
     "product": "مجموعة المكياج",
     "hashtags": "#مكياجي #ميك_اب_عربي",
     "occasions": ["eid_al_fitr", "eid_al_adha", "national_day", "graduation_season", "riyadh_season", "white_friday"]},

    {"handle": "niceonesa",
     "sector": "beauty_personal_care", "ar": "نايس ون",
     "product": "عطور ومستلزمات بيوتي",
     "hashtags": "#نايس_ون #عطورك_هنا",
     "occasions": ["ramadan", "eid_al_fitr", "national_day", "white_friday", "riyadh_season", "founding_day"]},

    {"handle": "gissahperfumes",
     "sector": "beauty_personal_care", "ar": "قصة عطور",
     "product": "عطر محلي فاخر",
     "hashtags": "#قصة_عطور #عطر_سعودي_اصيل",
     "occasions": ["national_day", "founding_day", "ramadan", "eid_al_fitr", "riyadh_season", "evergreen"]},

    {"handle": "ajmalperfumes",
     "sector": "beauty_personal_care", "ar": "عجمل",
     "product": "عطر عود فاخر",
     "hashtags": "#عجمل_عطور #عود_اصيل",
     "occasions": ["ramadan", "eid_al_fitr", "national_day", "riyadh_season", "winter_seasonal"]},

    {"handle": "goldenscent",
     "sector": "beauty_personal_care", "ar": "جولدن سنت",
     "product": "عطر موسمي",
     "hashtags": "#جولدن_سنت #عطور_فاخرة",
     "occasions": ["eid_al_fitr", "white_friday", "riyadh_season", "national_day", "winter_seasonal"]},

    {"handle": "bathandbodyworksarabia",
     "sector": "beauty_personal_care", "ar": "باث آند بودي",
     "product": "عطور المنزل",
     "hashtags": "#باث_اند_بودي #رائحة_البيت",
     "occasions": ["ramadan", "eid_al_fitr", "winter_seasonal", "national_day", "white_friday"]},

    {"handle": "asteribeautysa",
     "sector": "beauty_personal_care", "ar": "أستيري",
     "product": "روتين العناية بالبشرة",
     "hashtags": "#أستيري #سكن_كير_سعودي",
     "occasions": ["national_day", "riyadh_season", "summer_campaign", "white_friday", "evergreen"]},

    {"handle": "overdose_sa",
     "sector": "beauty_personal_care", "ar": "أوفر دوز",
     "product": "مكياج عيد",
     "hashtags": "#اوفر_دوز #ميك_اب_العيد",
     "occasions": ["eid_al_fitr", "eid_al_adha", "national_day", "graduation_season"]},

    # ═══ RETAIL / LIFESTYLE ══════════════════════════════════════════════════

    {"handle": "noon",
     "sector": "retail_lifestyle", "ar": "نون",
     "product": "أجهزة إلكترونية",
     "hashtags": "#نون #عروض_نون",
     "occasions": ["white_friday", "national_day", "founding_day", "eid_al_fitr", "back_to_school", "ramadan", "summer_campaign"]},

    {"handle": "tamimimarkets",
     "sector": "retail_lifestyle", "ar": "التميمي",
     "product": "منتجات طازجة",
     "hashtags": "#التميمي #طازج_دايم",
     "occasions": ["ramadan", "national_day", "eid_al_fitr", "eid_al_adha", "back_to_school", "founding_day"]},

    {"handle": "pandasaudi",
     "sector": "retail_lifestyle", "ar": "باندا",
     "product": "عروض أسبوعية",
     "hashtags": "#باندا_السعودية #وفر_مع_باندا",
     "occasions": ["ramadan", "national_day", "eid_al_fitr", "back_to_school", "white_friday", "founding_day"]},

    {"handle": "mumzworld",
     "sector": "retail_lifestyle", "ar": "مامز وورلد",
     "product": "منتجات الأطفال والأمومة",
     "hashtags": "#مامز_وورلد #للأم_وطفلها",
     "occasions": ["eid_al_fitr", "back_to_school", "national_day", "white_friday", "summer_campaign"]},

    # ═══ REAL ESTATE ══════════════════════════════════════════════════════

    {"handle": "roshnksa",
     "sector": "real_estate", "ar": "روشن",
     "product": "فيلا عائلية",
     "hashtags": "#روشن #بيتك_السعودي",
     "occasions": ["national_day", "founding_day", "riyadh_season", "summer_campaign", "evergreen"]},

    # ═══ HEALTHCARE / WELLNESS ════════════════════════════════════════════

    {"handle": "fitnessfirstme",
     "sector": "healthcare_wellness", "ar": "فتنس فيرست",
     "product": "برنامج لياقة",
     "hashtags": "#فتنس_فيرست #لياقتك_أولوية",
     "occasions": ["national_day", "ramadan", "summer_campaign", "back_to_school", "founding_day", "graduation_season"]},

    {"handle": "myfitness.sa",
     "sector": "healthcare_wellness", "ar": "ماي فتنس",
     "product": "اشتراك رياضي",
     "hashtags": "#ماي_فتنس #صحتك_تستاهل",
     "occasions": ["ramadan", "national_day", "summer_campaign", "founding_day", "back_to_school"]},
]


def generate() -> list[dict]:
    briefs = []
    brief_id = 1
    for brand in BRANDS:
        for occ in brand["occasions"]:
            briefs.append({
                "id":          brief_id,
                "brand":       brand["ar"],
                "brand_en":    brand["handle"],
                "sector":      brand["sector"],
                "sector_ar":   SECTORS_AR.get(brand["sector"], brand["sector"]),
                "occasion":    occ,
                "occasion_ar": OCCASIONS_AR.get(occ, occ),
                "product":     brand["product"],
                "hashtags":    brand["hashtags"],
            })
            brief_id += 1
    return briefs


def main():
    briefs = generate()

    summary_only = "--summary" in sys.argv
    if not summary_only:
        out = BASE / "data" / "brief_matrix.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(briefs, ensure_ascii=False, indent=2))
        print(f"✅ Generated {len(briefs)} briefs → {out}")

    # Summary
    sec_counts = Counter(b["sector"] for b in briefs)
    occ_counts = Counter(b["occasion"] for b in briefs)
    brand_counts = Counter(b["brand"] for b in briefs)

    print(f"\n{'─'*40}")
    print(f"Total briefs: {len(briefs)}")
    print(f"\nBy sector:")
    for s, n in sorted(sec_counts.items(), key=lambda x: -x[1]):
        print(f"  {SECTORS_AR.get(s,s)}: {n}")
    print(f"\nBy occasion:")
    for o, n in sorted(occ_counts.items(), key=lambda x: -x[1]):
        print(f"  {OCCASIONS_AR.get(o,o)}: {n}")
    print(f"\nBrands: {len(brand_counts)} unique")
    print(f"{'─'*40}")


if __name__ == "__main__":
    main()
