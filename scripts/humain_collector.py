#!/usr/bin/env python3
"""
humain_collector.py — Automated HUMAIN/ALLaM 34B gold output collector
Playwright opens chat.humain.ai, sends each brief, captures response.
Mohamed picks the best output interactively → saved to GOLD_OUTPUTS_HUMAIN.md

Usage:
  python3 scripts/humain_collector.py              # run all 18 briefs
  python3 scripts/humain_collector.py --from 5     # resume from brief #5
  python3 scripts/humain_collector.py --dry-run    # print prompts only, no browser
  python3 scripts/humain_collector.py --id 3       # run single brief by id
"""

import asyncio
import argparse
import sys
import re
import json
from datetime import datetime
from pathlib import Path

BASE       = Path(__file__).parent.parent
INTEL_FILE = BASE / "11_who_to_learn_from/intelligence_layer.json"
GOLD_FILE  = BASE / "docs/consultations/GOLD_OUTPUTS_HUMAIN.md"
QUEUE_FILE = BASE / "logs/humain_queue.json"
LOG_FILE      = BASE / "logs/humain_collector.log"
LEARNING_FILE = BASE / "logs/prompt_learning.json"
HUMAIN        = "https://chat.humain.ai"
REVIEW_URL = "http://localhost:4100/humain-review"

# ── Sector display names ───────────────────────────────────────────────────────
SECTOR_AR = {
    "f_and_b":              "مطاعم وكافيهات",
    "fashion":              "أزياء وموضة",
    "real_estate":          "عقارات",
    "retail_lifestyle":     "تجزئة",
    "beauty_personal_care": "جمال وعناية",
    "healthcare_wellness":  "صحة ولياقة",
}

OCCASION_AR = {
    "new_product": "إطلاق منتج جديد",
    "weekly_offer": "عرض الأسبوع",
    "new_branch": "افتتاح فرع جديد",
    "daily_post": "منشور يومي عادي",

    "national_day":   "اليوم الوطني",
    "ramadan":        "رمضان",
    "eid_al_fitr":    "عيد الفطر",
    "eid_al_adha":    "عيد الأضحى",
    "founding_day":   "يوم التأسيس",
    "riyadh_season":  "موسم الرياض",
    "white_friday":   "الجمعة البيضاء",
    "singles_day":    "يوم العزاب",
}

MAX_CHARS = {
    "f_and_b":              140,
    "fashion":              220,
    "real_estate":          200,
    "retail_lifestyle":     160,
    "beauty_personal_care": 150,
    "healthcare_wellness":  150,
}

# ── All 5 CD brain techniques ─────────────────────────────────────────────────
TECHNIQUES_BLOCK = """أ. Paradox Hunter — قلب التوقع (استلهم الفكرة، لا تنسخ القالب)
← ناجح: "التوفير اللي ما يحتاج تفكر مرتين"
← ناجح (مختلف): "قهوة تصحيك — حتى قبل ما تشربها"
← فاشل: "استمتع" / "لا تفوت" / "أجواء مميزة" / "عرض لفترة محدودة"
← ممنوع: نسخ أي مثال كما هو مع تغيير الكلمات فقط
← ممنوع تماماً: قالب "[المنتج] اللي ما ينتظر [المناسبة] — [المناسبة] ينتظره/ها" بأي شكل
← ممنوع تماماً: وضع رمضان/العيد/اليوم الوطني/يوم التأسيس في موقع الانتظار — المناسبة لا تنتظر المنتج

ب. Heritage Decoder — جملة قصيرة تحمل كلمة بمعنيين في آنٍ واحد
← ناجح (مالية): الذكاء يستثمر فيك
← ناجح (أزياء): ترتدين المناسبة
← ناجح (غذاء): اللبن اللي يروبك
← فاشل وممنوع: اكتب الجملة فقط، بدون علامات اقتباس، بدون شرح للمعنى
← فاشل وممنوع: X معك في كل خطوة
← تجنب: "يشبك" — معناه الثاني "يعقّد/يُربك" يعكس المقصود
← تجنب: "يطمن قلبك" في سياق منتج — حميمية غير مقصودة

ج. Firaasa — ملاحظة سلوكية محددة لهذا المنتج تحديداً
← ناجح: "اللبن هو اللي يختارك — مو العكس"
← ناجح: "اللي يدور على صحة يدور على راحة بال"
← ممنوع تماماً: "الأم/الناس/الأسرة/العميل ما تدور/يدور على X — تدور/يدور على Y" — حتى مع تغيير الكلمات
← فاشل وممنوع: "في لحظة X، Y هو اللي..." أو "لحظة هدوء، تكتشف فيها..."
← الصحيح: لحظة سلوكية حقيقية خاصة بهذا المنتج تحديداً — مو قالب يصلح لأي منتج

د. Metaphor Architect — تشبيه معماري (الشيء المجرد يعيشه الناس كل يوم)
← الأداة: "إذا..." لبناء التشبيه / "بس" كمحور الدوران / "تخيل معي..." كمدخل
← ناجح: "إذا يومك طريق — القهوة هي اللي تحدد المسار"
← ناجح: "تخيل معي: كل عباءة اخترتيها كانت قرار قبل ما تقرري"
← فاشل: تشبيه ناقص — لازم كل عنصر في التشبيه يطابق عنصراً في الواقع
← فاشل: استعارة حرفية بدون عمق (المنتج = الحياة / العلامة = الحياة)
← الصحيح: اربط المنتج بشيء يومي سعودي محدد — مو صورة شاعرية عامة

هـ. Authenticity Detective — اللحظة الصادقة (لمّا ينكسر الأداء وتظهر الحقيقة)
← الأداة: "لمّا..." — المحفّز اللي يفتح اللحظة الحقيقية
← ناجح: "لمّا الكلمات تضيع — الطعم يقولها"
← ناجح: "لمّا الجوع أكبر من أي تفسير — البيك يفهم"
← ممنوع تماماً: وصف مشاهد بصرية (غرف، ملابس، لحظات خاصة) — كلمات فقط
← فاشل: مشاعر عامة (سعيد، حزين، مميز) — اكتب الحالة المحددة، مو اسمها
← الصحيح: لحظة إنسانية حقيقية خاصة بهذا المنتج — مو موقف يصلح لأي شيء"""

# ── Brief matrix — 18 briefs across 6 sectors ────────────────────────────────
BRIEFS = [
    # F&B (4) — Paradox Hunter wins here (+35% engagement)
    {"id": 1,  "sector": "f_and_b",             "brand": "AlBaik",           "product": "بروستد",            "occasion": "national_day",  "hashtags": "#انتم_والبيك_جيران #صنع_في_السعودية"},
    {"id": 2,  "sector": "f_and_b",             "brand": "Barns Coffee",      "product": "قهوة مثلجة",       "occasion": "ramadan",       "hashtags": "#بارنز #مننا_ويفهم_جونا"},
    {"id": 3,  "sector": "f_and_b",             "brand": "McDonald's KSA",    "product": "حفلة ماك",          "occasion": "eid_al_fitr",   "hashtags": "#ماكدونالدز #بحب_ماك"},
    {"id": 4,  "sector": "f_and_b",             "brand": "Al Romansiah",      "product": "مشاوي وكبسة",      "occasion": "founding_day",  "hashtags": "#الرومانسية"},
    # Fashion (3)
    {"id": 5,  "sector": "fashion",             "brand": "Max Fashion",       "product": "عباءة كلاسيكية",   "occasion": "eid_al_fitr",   "hashtags": "#إطلالاتmena"},
    {"id": 6,  "sector": "fashion",             "brand": "H&M KSA",           "product": "كوليكشن شتاء",     "occasion": "riyadh_season", "hashtags": "#hm"},
    {"id": 7,  "sector": "fashion",             "brand": "Level Shoes",       "product": "صبابيط عيد",        "occasion": "eid_al_adha",   "hashtags": "#level_shoes"},
    # Real Estate (3) — only ROSHN in our data
    {"id": 8,  "sector": "real_estate",         "brand": "ROSHN",             "product": "فيلا عائلية",      "occasion": "national_day",  "hashtags": "#روشن #رؤية_2030"},
    {"id": 9,  "sector": "real_estate",         "brand": "ROSHN",             "product": "شقق رؤية",         "occasion": "founding_day",  "hashtags": "#روشن #رؤية_2030"},
    {"id": 10, "sector": "real_estate",         "brand": "ROSHN",             "product": "موقع في قلب الرياض","occasion": "riyadh_season", "hashtags": "#روشن"},
    # Retail (3)
    {"id": 11, "sector": "retail_lifestyle",    "brand": "Panda",             "product": "عروض أسبوعية",     "occasion": "ramadan",       "hashtags": "#باندا #بياع_المسرة"},
    {"id": 12, "sector": "retail_lifestyle",    "brand": "Noon.com",          "product": "أجهزة إلكترونية",  "occasion": "white_friday",  "hashtags": "#نون"},
    {"id": 13, "sector": "retail_lifestyle",    "brand": "Tamimi Markets",    "product": "منتجات طازجة",     "occasion": "national_day",  "hashtags": "#تميمي"},
    # Beauty (3)
    {"id": 14, "sector": "beauty_personal_care","brand": "Mikyajy",           "product": "مجموعة عيد",       "occasion": "eid_al_fitr",   "hashtags": "#ميكياجي"},
    {"id": 15, "sector": "beauty_personal_care","brand": "Nice One",          "product": "عطور رمضانية",     "occasion": "ramadan",       "hashtags": "#نايس_ون"},
    {"id": 16, "sector": "beauty_personal_care","brand": "Gissah Perfumes",   "product": "عطر محلي فاخر",    "occasion": "national_day",  "hashtags": "#قصة_عطر"},
    # Healthcare (2)
    {"id": 17, "sector": "healthcare_wellness", "brand": "My Fitness",        "product": "اشتراك رمضان",     "occasion": "ramadan",       "hashtags": "#مايفتنس"},
    {"id": 18, "sector": "healthcare_wellness", "brand": "Fitness First",     "product": "برنامج لياقة",     "occasion": "national_day",  "hashtags": "#فتنس_فيرست"},
]


_REASON_LABELS_COLLECTOR = {
    "قالب_مكرر": "قالب مكرر", "معنى_مزدوج": "معنى مزدوج",
    "طويل": "طويل جداً",       "عام": "عام وغير محدد",
    "لهجة": "لهجة خاطئة",
}

def _build_learned_addition() -> str:
    """Read human-reviewed examples and return extra prompt lines."""
    try:
        if not LEARNING_FILE.exists():
            return ""
        ld = json.loads(LEARNING_FILE.read_text())
        lines = []
        for tech in ("أ", "ب", "ج", "د", "هـ"):
            for p in ld.get("positive", {}).get(tech, [])[-2:]:
                lines.append(f'[{tech}] ناجح (معتمد بشرياً): "{p["caption"]}"')
            for n in ld.get("negative", {}).get(tech, [])[-2:]:
                label = _REASON_LABELS_COLLECTOR.get(n.get("reason", ""), "ضعيف")
                lines.append(f'[{tech}] مرفوض ({label}): "{n["caption"]}"')
        if not lines:
            return ""
        return "\n\n## أمثلة متعلَّمة من مراجعة بشرية:\n" + "\n".join(lines)
    except Exception:
        return ""


def _build_brand_block(brief: dict, sector_ar: str, occasion_ar: str) -> str:
    """Build the <BRAND> block — enriched with KB data + occasion tension."""
    ctx = brief.get("brand_context", {})
    lines = [f"العلامة: {brief['brand']} | القطاع: {sector_ar} | المنتج: {brief['product']} | المناسبة: {occasion_ar}"]
    if brief.get("occasion_tension"):
        pass  # occasion_tension DEPRECATED 2026-06-11 — poetry seed poisoned generations (founding-day "أجداد" caption traced to it). Occasion FACTS injected via V5 path instead.

    if ctx.get("bio_tagline"):
        lines.append(f"شعار العلامة: \"{ctx['bio_tagline']}\"")

    if ctx.get("arabic_style"):
        style_map = {
            "colloquial_hejazi": "حجازية عامية",
            "saudi": "سعودية",
            "colloquial_gulf": "خليجية عامية",
            "formal_arabic": "فصحى",
            "modern_arabic": "عربية حديثة",
        }
        style = style_map.get(ctx["arabic_style"], ctx["arabic_style"])
        lines.append(f"اللهجة: {style}")

    if ctx.get("tone"):
        tone_map = {
            "playful": "مرح", "casual": "عفوي", "celebratory": "احتفالي",
            "informative": "معلوماتي", "warm": "دافئ", "urgent": "عاجل",
            "friendly": "ودّي", "aspirational": "طموح", "inspirational": "ملهم",
            "professional": "احترافي",
        }
        tones_ar = [tone_map.get(t, t) for t in ctx["tone"][:3]]
        lines.append(f"النبرة: {' | '.join(tones_ar)}")

    if ctx.get("signature_phrases"):
        # filter out generic red-line phrases before showing
        _GENERIC = {"لا تفوت", "اطلب الحين", "اشترك", "متوفر الآن", "منشن", "فولو"}
        clean = [p for p in ctx["signature_phrases"] if not any(g in p for g in _GENERIC)]
        if clean:
            phrases = " | ".join(f'"{p}"' for p in clean[:3])
            lines.append(f"عبارات مميزة: {phrases}")

    if ctx.get("proven_openers"):
        openers = " | ".join(f'"{o}"' for o in ctx["proven_openers"][:3])
        lines.append(f"افتتاحيات ناجحة: {openers}")

    if ctx.get("real_hooks"):
        lines.append("هوكات حقيقية من حسابهم:")
        for h in ctx["real_hooks"][:4]:
            lines.append(f"  - {h[:70]}")

    if ctx.get("high_engagement_style"):
        lines.append(f"ما ينجح: {ctx['high_engagement_style'][:100]}")

    if ctx.get("avoid_topics"):
        avoids = " | ".join(ctx["avoid_topics"][:3])
        lines.append(f"تجنب: {avoids}")

    lines.append(f"الهاشتاقات: {brief['hashtags']}")
    return "\n".join(lines)


_HERITAGE_SEEDS = {
    "f_and_b": [
        ("يروبك", "يعمّرك + يهدّئ روحك"),
        ("يسخّنك", "يدفّئ الأكل + يدفّئ قلبك"),
        ("يجمّعك", "يلمّ العيلة + يكمّل نفسك"),
        ("يشبعك", "يملأ بطنك + يرضي روحك"),
        ("يشرّبك", "يخلل المنتج فيك + يرسّخ الذوق"),
    ],
    "fashion": [
        ("ترتدين", "تلبسين الثوب + تحملين روح المناسبة"),
        ("تنسجين", "تختارين القماش + تُبدعين هويتك"),
        ("تُكمّلين", "تكتملين إطلالتك + تكتملين أنتِ"),
        ("تحيكين", "تُصمّمين + تُخطّطين لحياتك"),
    ],
    "beauty_personal_care": [
        ("تُجمّلين", "تزيّنين وجهك + تُكرّمين نفسك"),
        ("تُنضجين", "تصنعين لمسة ناضجة + تتطورين"),
        ("تُزيّنين", "تتحلّين بالمنتج + تُشرّفين اللحظة"),
        ("تكتملين", "يكتمل مكياجك + تكتملين أنتِ"),
    ],
    "real_estate": [
        ("تسكنين", "تسكنين البيت + تطمئن روحك"),
        ("تبنين", "تبنين منزلك + تبنين مستقبلك"),
        ("تؤسّسين", "تُنشئين بيتاً + تُؤسّسين إرثاً"),
        ("تجذّرين", "تتمسّكين بمكانك + تضربين جذوراً"),
    ],
    "retail_lifestyle": [
        ("تختارين", "تنتقين المنتج + تُقرّرين من أنتِ"),
        ("تجمعين", "تتسوّقين + تجمعين لحظات"),
        ("تملّكين", "تشترين + تتملّكين ثقتك"),
    ],
    "healthcare_wellness": [
        ("تنشّطين", "تُحرّكين جسدك + تُشعلين يومك"),
        ("تتعافين", "تُشفين + تُعيدين بناء نفسك"),
        ("تُحيّين", "تُحيّين جسدك + تعيشين بالفعل"),
    ],
}

def _build_heritage_block(sector: str) -> str:
    seeds = _HERITAGE_SEEDS.get(sector, [
        ("تُكمّل", "يُكمّل المنتج + يُكمّل نفسك"),
        ("يجمّع", "يلمّ الناس + يجمع المعاني"),
    ])
    seed_lines = "\n".join(
        f'← بذرة ({s[0]}): "{s[0]}..." — {s[1]}' for s in seeds[:3]
    )
    return f"""ب. Heritage Decoder — كلمة أو كلمتان تحمل معنيين في آنٍ واحد
← الافتتاح: الكلمة ذات المعنيين مباشرةً (ممنوع: اللي / لمّا / إذا كأولى الكلمات)
← الصحيح: ابدأ بالكلمة المزدوجة نفسها — الجملة تُفسَّر بمعنيين بدون شرح
{seed_lines}
← ناجح عام: "ترتدين المناسبة" — تلبسين + تحملين روح اليوم
← ناجح عام: "تسكنين التاريخ — يسكنك المستقبل"
← ممنوع تماماً: "اللي يختارك — مو العكس" — هذا قالب ج (Firaasa)، مو ب
← ممنوع تماماً: تبدأ بـ "لمّا" أو "إذا" أو "اللي"
← فاشل: "X معك في كل خطوة" — تعبير عام بدون معنى مزدوج
← فاشل: نسخ التعليمات نفسها كجملة — اكتب كابشن حقيقي"""


def _get_occasion_words(occasion: str) -> str:
    """Return comma-separated required words for this occasion from intelligence_layer."""
    try:
        intel = json.loads(INTEL_FILE.read_text())
        words = intel.get('occasion_required_words', {}).get(occasion, [])
        return '، '.join(words) if words else ''
    except Exception:
        return ''



def _load_brand_exemplars(brand_en: str, n: int = 6) -> list[dict]:
    """V4 feed-mind: the brand's REAL top-engagement captions from the raw archive.
    Engagement-first, then diversity (top 4 by likes + 2 mid-list), per consult 2026-06-10."""
    import glob as _glob
    base = Path(__file__).parent.parent / "11_who_to_learn_from" / "_raw_archive" / brand_en
    files = sorted(_glob.glob(str(base / "*" / "*apify_raw.jsonl")), reverse=True)
    if not files:
        return []
    posts = []
    for line in open(files[0], encoding="utf-8"):
        try:
            p = json.loads(line)
        except Exception:
            continue
        cap = (p.get("caption") or "").strip()
        if len(cap) < 6:
            continue
        # require real Arabic content
        if len(re.findall(r"[\u0600-\u06FF]{2,}", cap)) < 1:
            continue
        posts.append({"caption": cap[:220], "likes": int(p.get("likesCount") or 0)})
    posts.sort(key=lambda x: x["likes"], reverse=True)
    # dedupe near-identical (same first 25 chars)
    seen, out = set(), []
    for p in posts:
        k = p["caption"][:25]
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    top = out[:4]
    mid = out[len(out)//3 : len(out)//3 + max(0, n - len(top))]
    return (top + mid)[:n]


def build_prompt(brief: dict) -> str:
    """V4 — THE FEED MIND (2026-06-10, founder-approved redesign).
    Principle: stop teaching rhetoric, start cloning feeds. The brand's real
    top-engagement posts are the style spec; we own the structure (4 real post
    types); hard voice contract from the fingerprint; the em-dash aphorism is
    banned (documented AI-tell). Method: think→search→plan→check→consult→work.
    Output format unchanged (أ./ب./ج./د. + hashtags + الأفضل) — parser-compatible."""
    max_chars   = MAX_CHARS.get(brief["sector"], 160)
    sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
    brand_block = _build_brand_block(brief, sector_ar, occasion_ar)
    hashtags    = brief.get("hashtags", "")
    learned     = _build_learned_addition()
    ctx         = brief.get("brand_context", {}) or {}
    openers     = ctx.get("proven_openers", []) or []
    openers_line = "، ".join(f"«{o}»" for o in openers[:6]) if openers else ""

    # THE FEED — real exemplars, engagement-first
    exemplars = _load_brand_exemplars(brief.get("brand_en", ""))
    if exemplars:
        feed_lines = "\n".join(
            f"- ({e['likes']:,} إعجاب) {e['caption']}" for e in exemplars
        )
        feed_block = f"""<THE_FEED>
منشورات حقيقية من حساب {brief['brand']} — الأعلى تفاعلاً عند جمهوره الفعلي.
هذي هي الجودة والصوت والطول المطلوب. منشورك الجاي لازم يبدو أخوهم:
{feed_lines}
</THE_FEED>
"""
    else:
        feed_block = ""

    opener_rule = (
        f"\n- خيار واحد على الأقل يبدأ بافتتاحية مجرّبة من الحساب نفسه: {openers_line}"
        if openers_line else ""
    )

    return f"""<RED_LINES>
ممنوع: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس أو خوفهم.
ممنوع: وضع مناسبة دينية (رمضان، العيد) أو وطنية (اليوم الوطني، يوم التأسيس) في موقع الانتظار للمنتج.
دائماً: لهجة سعودية طبيعية. حد أقصى {max_chars} حرف للكابشن (بدون الهاشتاقات). بدون إنجليزي.
</RED_LINES>

{feed_block}<BRAND>
{brand_block}
</BRAND>

<BANNED_STRUCTURES>
أنت أدمن الحساب — مو كاتب إعلانات. كل سطر منك لازم يقدر ينزل على الفيد بكرة بدون ما أحد يحس إنه "إعلان مكتوب".
ممنوع نهائياً (هذي بصمة الذكاء الاصطناعي اللي نهرب منها):
- بنية الشرطة والقلب: «X — اللي/حتى/قبل ما Y» بكل صيغها
- الافتتاحيات الفلسفية: «لمّا...» / «إذا...» / «تخيل...»
- الكليشيهات: «أكبر من الكلام»، «الشوق»، «ما ينتهي»، «يحكي حكاية»، «حكاية أجدادنا»، «الطعم يقول»، «يكمّل اللحظة»
- أي جملة تصلح سكريبت إعلان تلفزيوني — إذا حسّيتها كذا، اكتبها من جديد كمنشور عادي
- نفس أول كلمة في خيارين{learned}
</BANNED_STRUCTURES>

<TASK>
اكتب 4 منشورات لحساب {brief['brand']} بمناسبة {occasion_ar} عن {brief.get('product','المنتج')} — كل واحد نوع منشور مختلف:

أ. إعلان/عرض مباشر — خبر أو عرض يُقال بصراحة وحماس، بأسلوب الحساب («الآن»، «جرب»، «وصل»...) مع دعوة فعل واضحة
ب. سؤال/نداء للجمهور — سؤال حقيقي قصير يخلي الناس تعلق (وش/مين/كم...)
ج. لحظة من الحياة — موقف يومي حقيقي محدد (مو فلسفة) يظهر فيه المنتج طبيعي، جملة أو جملتين
د. تهنئة بصوت البراند — تهنئة المناسبة كما ينزلها هذا الحساب فعلاً: قصيرة، دافئة، بإيموجيه وهاشتاقاته

قواعد:
- حد أقصى {max_chars} حرف للكابشن بدون الهاشتاقات — والأقصر أفضل (شوف أطوال THE_FEED){opener_rule}
- الإيموجي والهاشتاقات بنفس أسلوب الحساب الحقيقي
- اختبار ذاتي قبل ما تكتب أي خيار: «لو نزل هذا حرفياً على حساب {brief['brand']} بكرة — يمر كأنه منهم؟» إذا لا، أعد كتابته
- الشكل: ابدأ كل سطر بحرف النوع ثم نقطة (أ. / ب. / ج. / د.) ثم الكابشن مباشرة
- بعدها سطر الهاشتاقات: {hashtags}

في السطر الأخير اختر الأقوى وضعه بعد: الأفضل:
</TASK>"""


def load_gold() -> list[dict]:
    """Parse existing gold entries from GOLD_OUTPUTS_HUMAIN.md."""
    if not GOLD_FILE.exists():
        return []
    text = GOLD_FILE.read_text()
    rows = []
    for line in text.splitlines():
        # table rows: | # | Brand | ...
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7 and parts[1].isdigit():
            rows.append({
                "num": int(parts[1]),
                "brand": parts[2],
                "sector": parts[3],
                "occasion": parts[4],
                "technique": parts[5],
                "caption": parts[6],
            })
    return rows


def append_gold(num: int, brief: dict, caption: str, technique: str) -> None:
    """Append one approved output to GOLD_OUTPUTS_HUMAIN.md."""
    text = GOLD_FILE.read_text()
    # Update count
    count_match = re.search(r"## COUNT: (\d+) / 300", text)
    current = int(count_match.group(1)) if count_match else (num - 1)
    new_count = current + 1

    sector_ar  = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

    # Replace placeholder row or append after last data row
    new_row = f"| {num} | {brief['brand']} | {sector_ar} | {occasion_ar} | {technique} | {caption} |"
    text = re.sub(r"\| — \| — \| — \| — \| — \| — \|", new_row, text, count=1)

    # If no placeholder was replaced, insert before COUNT line
    if new_row not in text:
        text = text.replace(
            f"| {num-1} |",
            f"| {num-1} |",  # no-op, find insertion point differently
        )
        # append before the COUNT line
        text = re.sub(
            r"(---\n\n## COUNT:)",
            f"{new_row}\n\n---\n\n## COUNT:",
            text
        )

    text = re.sub(r"## COUNT: \d+ / 300", f"## COUNT: {new_count} / 300", text)
    GOLD_FILE.write_text(text)
    print(f"\n  ✅ Saved #{num} to GOLD_OUTPUTS_HUMAIN.md (total: {new_count}/300)")


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)


_TECH_PREFIXES = re.compile(
    r"^(Paradox Hunter|Heritage Decoder|Firaasa|Metaphor Architect|Authenticity Detective"
    r"|قلب التوقع|تشبيه معماري|لحظة صادقة|أ\.|ب\.|ج\.|د\.|هـ\.)"
    r"[\s\-—–:،.]*"
    r"(Paradox Hunter|Heritage Decoder|Firaasa|Metaphor Architect|Authenticity Detective)?"
    r"[\s\-—–:،.]*",
    re.IGNORECASE,
)
_QUOTE_STRIP = re.compile(r'^["\'""«»]+|["\'""«»]+$')


def _clean_caption(text: str) -> str:
    """Strip technique name prefixes, leading punctuation, surrounding quotes, and trailing hashtags."""
    text = text.strip()
    text = _TECH_PREFIXES.sub("", text).strip()
    text = _QUOTE_STRIP.sub("", text).strip()
    # Strip leading ". " or "- " artifacts from ALLaM double-punctuation
    text = re.sub(r"^[\.\-،]\s+", "", text).strip()
    # Strip trailing hashtag block (everything from first # to end, if # appears after caption text)
    # Keep captions where # appears mid-sentence (unlikely but safe)
    hash_match = re.search(r"\s#\S+(\s#\S+)*\s*$", text)
    if hash_match:
        text = text[:hash_match.start()].strip()
    return text


ALL_KEYS = ("أ", "ب", "ج", "د", "هـ")

# Generic red-line phrases that lower caption quality
_GENERIC_PHRASES = {
    "استمتع", "لا تفوت", "أجواء مميزة", "عرض لفترة محدودة",
    "اطلب الحين", "اشترك الحين", "متوفر الآن", "منشن صديقك",
    "عروض حصرية", "لمحبي", "لعشاق",
}

# Correct openers per technique — used for quality scoring
_CORRECT_OPENERS = {
    "أ": None,            # any NON-لمّا/إذا/تخيل starter
    "ب": None,            # double-meaning word (hard to verify automatically)
    "ج": ("اللي", ),
    "د": ("إذا", "تخيل"),
    "هـ": ("لمّا", "لما"),
}

_BANNED_FOR_TECH = {
    "أ": ("لمّا", "لما", "إذا", "تخيل"),
    "ب": ("لمّا", "لما", "إذا", "تخيل"),
    "ج": ("لمّا", "لما", "إذا"),
    "د": ("لمّا", "لما"),
    "هـ": ("إذا", "تخيل"),
}


def _auto_score(caption: str, technique: str, brand: str) -> int:
    """
    Score a caption 0-100.
    Higher = better for Instagram. Used to pick best when ALLaM doesn't.
    """
    if not caption or len(caption) < 5:
        return 0

    score = 50  # baseline

    # Length: sweet spot is 40-90 chars
    n = len(caption)
    if 40 <= n <= 90:
        score += 20
    elif n < 40:
        score += 10  # very short can be punchy
    elif n > 150:
        score -= 15
    elif n > 120:
        score -= 8

    # Technique adherence: starts with correct opener
    first_word = caption.split()[0].strip("؟!.،-") if caption.split() else ""
    banned = _BANNED_FOR_TECH.get(technique, ())
    correct = _CORRECT_OPENERS.get(technique)
    if any(caption.startswith(b) for b in banned):
        score -= 25   # wrong technique opener
    if correct and any(caption.startswith(c) for c in correct):
        score += 15   # correct technique opener

    # Doesn't start with brand name
    if brand and caption.startswith(brand):
        score -= 15

    # No generic phrases
    for phrase in _GENERIC_PHRASES:
        if phrase in caption:
            score -= 10
            break

    # Has a dash (—) — common in good Saudi captions
    if "—" in caption or " - " in caption:
        score += 5

    # Has Arabic verb (good sign of active voice)
    if re.search(r"[يتنا]\w{3,}", caption):
        score += 5

    return max(0, min(100, score))


def parse_response(raw: str) -> dict:
    """
    Extract the 5 technique options (أ, ب, ج, د, هـ) and الأفضل from ALLaM's response.
    Handles multiple output formats ALLaM uses:
      Format A: "أ. caption" ... "هـ. caption"
      Format B: Technique name labels (Paradox Hunter, etc.)
      Format C: unlabeled Arabic lines fallback
    """
    options = {k: "" for k in ALL_KEYS}
    best = ""
    best_key = ""  # technique key if ALLaM picked by key

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # Strip UI chrome
    start = 0
    for i, l in enumerate(lines):
        if any(x in l for x in ["Recent Chats", "Chat history", "MO\n", "New Chat"]):
            start = i + 1
    lines = lines[start:]

    # Note: extract الأفضل AFTER options so we can resolve "الأفضل: أ" by key
    best_line = next((l for l in lines if "الأفضل" in l), None)

    # Format A: أ. / ب. / ج. / د. / هـ. labels
    # Also handle multi-line captions: if next line is hashtag-only, skip it
    i = 0
    while i < len(lines):
        line = lines[i]
        matched = False
        for key in ALL_KEYS:
            if re.match(rf"^{key}[\.\-\:]\s*", line):
                text = _clean_caption(re.sub(rf"^{key}[\.\-\:]\s*", "", line))
                # If caption is empty and next line exists, try it (multi-line edge case)
                if not text and i + 1 < len(lines) and not any(
                    re.match(rf"^{k}[\.\-\:]\s*", lines[i+1]) for k in ALL_KEYS
                ):
                    text = _clean_caption(lines[i+1])
                if text and not options[key]:
                    options[key] = text
                matched = True
                break
        i += 1

    # Format B: English technique name labels
    if not any(options.values()):
        tech_map = {
            "Paradox Hunter": "أ",
            "Heritage Decoder": "ب",
            "Firaasa": "ج",
            "Metaphor Architect": "د",
            "Authenticity Detective": "هـ",
        }
        for line in lines:
            for tech, key in tech_map.items():
                if line.startswith(tech):
                    text = _clean_caption(re.sub(rf"^{tech}\s*:\s*", "", line))
                    if text and not options[key]:
                        options[key] = text
                    break

    # Format C: unlabeled Arabic lines fallback
    if not any(options.values()):
        arabic_lines = [
            _clean_caption(l) for l in lines
            if any("؀" <= c <= "ۿ" for c in l)
            and "الأفضل" not in l
            and "<" not in l
        ]
        arabic_lines = [l for l in arabic_lines if l and len(l) > 5]
        for i, key in enumerate(ALL_KEYS):
            if i < len(arabic_lines):
                options[key] = arabic_lines[i]

    # Resolve الأفضل line — handles both "الأفضل: أ" (key) and "الأفضل: full caption"
    if best_line:
        raw_best = re.sub(r"الأفضل\s*:\s*", "", best_line).strip()
        # If it's a single technique key, look up that option
        if raw_best in ALL_KEYS and options.get(raw_best):
            best = options[raw_best]
        else:
            cleaned = _clean_caption(raw_best)
            if len(cleaned) > 10:
                best = cleaned

    if not best:
        # Pick best by auto-score — prefer shorter, technique-adherent captions
        scored = {k: _auto_score(v, k, "") for k, v in options.items() if v and len(v) > 5}
        if scored:
            best_k = max(scored, key=scored.get)
            best = options[best_k]

    # Compute quality scores for each option
    scores = {k: _auto_score(v, k, "") for k, v in options.items() if v}

    return {"options": options, "best": best, "scores": scores}


def load_queue() -> dict:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return {"pending": [], "approved": []}


def _diversity_ok(options: dict) -> bool:
    """Return True if all non-empty captions start with different first words."""
    captions = [v for v in options.values() if v and len(v) > 5]
    first_words = [c.split()[0].strip("؟!.،-") for c in captions]
    return len(set(first_words)) == len(first_words)


def save_to_queue(brief: dict, raw_response: str) -> None:
    """Save a collected HUMAIN response to the review queue."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue = load_queue()

    parsed = parse_response(raw_response)
    sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
    div_ok = _diversity_ok(parsed["options"])
    n_opts = len([v for v in parsed["options"].values() if v and len(v) > 5])

    # Remove any existing entry for this brief_id (allow re-collection)
    queue["pending"] = [p for p in queue["pending"] if p.get("brief_id") != brief["id"]]

    queue["pending"].append({
        "brief_id":    brief["id"],
        "brand":       brief["brand"],
        "sector":      brief["sector"],
        "sector_ar":   sector_ar,
        "occasion":    brief["occasion"],
        "occasion_ar": occasion_ar,
        "product":     brief["product"],
        "hashtags":    brief["hashtags"],
        "raw":         raw_response,
        "options":     parsed["options"],
        "scores":      parsed.get("scores", {}),
        "best":        parsed["best"],
        "diversity_ok": div_ok,
        "options_count": n_opts,
        "collected_at": datetime.now().isoformat(),
        "status":      "pending",
    })
    if not div_ok:
        log(f"  ⚠️  Opener overlap for Brief #{brief['id']} ({n_opts} opts) — will retry")

    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    log(f"  💾 Saved to queue: Brief #{brief['id']} — {brief['brand']}")


# ── Playwright automation ──────────────────────────────────────────────────────
CHAT_INPUT_SELECTORS = [
    # Most specific first — "Ask me anything..." is the HUMAIN chat box
    "textarea[placeholder*='Ask me anything' i]",
    "textarea[placeholder*='message' i]",
    "textarea[placeholder*='اسأل' i]",
    "textarea[placeholder*='أرسل' i]",
    "[contenteditable='true']",
    "[role='textbox']",
    ".ProseMirror",
    "[data-placeholder*='message' i]",
    "input[type='text']:not([type='email']):not([type='password'])",
    ".chat-input",
    "#chat-input",
    "div[data-testid='chat-input']",
    # Fallback: any textarea that isn't the survey "Write your thoughts..." one
    "textarea:not([placeholder*='thoughts' i]):not([placeholder*='improve' i])",
]

SEND_BTN_SELECTORS = [
    "button[type='submit']",
    "button[aria-label*='send' i]",
    "button[aria-label*='إرسال']",
    "button[aria-label*='Submit' i]",
    "button svg[data-lucide='send']",
    ".send-button",
    "form button:last-child",
    "button:has(svg):last-of-type",
]

# Persistent session dir — so login is remembered between runs
SESSION_DIR = Path.home() / ".humain_playwright_session"


async def dismiss_modal(page) -> None:
    """Dismiss any onboarding/welcome modal that blocks the chat input."""
    modal_btns = [
        # HUMAIN survey modal — dismiss first
        "button:has-text('Cancel')",
        "button:has-text('إلغاء')",
        # Generic close patterns
        "button:has-text(\"Let's get started\")",
        "button:has-text('ابدأ')",
        "button:has-text('Continue')",
        "button:has-text('متابعة')",
        "button:has-text('Accept')",
        "button:has-text('موافق')",
        "[aria-label='Close']",
        "button.rounded-full svg[data-lucide='x']",
        # × button (any close button with × text)
        "button:has-text('×')",
        "[data-dismiss]",
    ]
    for sel in modal_btns:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                await asyncio.sleep(1)
                return
        except Exception:
            pass


async def find_chat_input(page):
    await dismiss_modal(page)
    for sel in CHAT_INPUT_SELECTORS:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1500):
                return el, sel
        except Exception:
            pass
    return None, None


async def wait_for_login(page, max_minutes: int = 20) -> bool:
    """
    Poll until chat input is found (login restored).
    Also tries navigating to the home URL every 2 minutes to help restore session.
    max_minutes: how long to wait total (default 20 — enough for Mohamed to see it).
    """
    log("🔐 HUMAIN requires login — open browser window and log in. Waiting up to 20 min...")
    log("   → Browser window should be visible. Log in via Google/Apple/Email.")

    total_polls = max_minutes * 30  # 2s sleep → 30 polls/minute
    nav_interval = 60   # re-navigate every 60 polls (2 minutes)

    for i in range(total_polls):
        await asyncio.sleep(2)

        # Try to find chat input
        chat_input, _ = await find_chat_input(page)
        if chat_input:
            log("✅ Login restored — chat input found.")
            return True

        # Every 2 minutes, try navigating to home (may restore session cookie)
        if i > 0 and i % nav_interval == 0:
            minutes_elapsed = (i * 2) // 60
            log(f"   Still waiting for login... {minutes_elapsed}m elapsed. Reloading HUMAIN...")
            try:
                await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(5)
                await dismiss_modal(page)
            except Exception:
                pass

    log("❌ Login wait timed out after 20 min — session could not be restored this batch.")
    return False


async def wait_for_response(page, timeout_s: int = 180) -> str | None:
    """
    Wait for HUMAIN to finish generating a response.
    Strategy: count messages before send, wait for count+1, then wait for stable text.
    """
    # Step 1 — snapshot message count before waiting
    async def count_messages():
        for sel in ["[data-role='assistant']", ".assistant-message", "article", ".message"]:
            try:
                els = page.locator(sel)
                n = await els.count()
                if n > 0:
                    return n, sel
            except Exception:
                pass
        return 0, None

    before_count, msg_sel = await count_messages()
    deadline = asyncio.get_event_loop().time() + timeout_s

    # Step 2 — wait for a new message to appear
    if msg_sel:
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(2)
            after_count, _ = await count_messages()
            if after_count > before_count:
                break
        else:
            pass  # timed out — still try to read

    # Step 3 — wait for text to stabilise (model stops generating)
    prev_text = ""
    stable_rounds = 0
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(3)

        current = ""
        # Try structured assistant message selectors first
        for sel in [
            "[data-role='assistant']",
            "[data-message-author-role='assistant']",
            ".assistant-message",
            "article",
            ".message",
            "div.group",
        ]:
            try:
                els = page.locator(sel)
                n = await els.count()
                if n > 0:
                    last = els.nth(n - 1)
                    if await last.is_visible(timeout=1000):
                        t = (await last.inner_text()).strip()
                        # Skip if it looks like the user's own prompt
                        if t and "<RED_LINES>" not in t and "<TECHNIQUES>" not in t:
                            current = t
                            break
            except Exception:
                pass

        if not current:
            # Fallback: grab visible body text, skip lines that look like our prompt
            try:
                body = await page.inner_text("body")
                lines = [
                    l.strip() for l in body.splitlines()
                    if l.strip()
                    and "<RED_LINES>" not in l
                    and "<TECHNIQUES>" not in l
                    and "<BRAND>" not in l
                    and "<TASK>" not in l
                ]
                # Take last 30 lines (response area)
                current = "\n".join(lines[-30:]) if lines else ""
            except Exception:
                pass

        if current and current == prev_text:
            stable_rounds += 1
            if stable_rounds >= 2:
                return current
        else:
            stable_rounds = 0
            prev_text = current

    return prev_text or None


async def run_browser(briefs: list[dict]) -> None:
    from playwright.async_api import async_playwright

    gold_entries = load_gold()
    done_ids = set()
    next_num = len(gold_entries) + 1

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        # Persistent context — login saved between runs
        ctx = await pw.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=False,
            slow_mo=80,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        log(f"\n{'='*60}")
        log(f"  HUMAIN Collector — {len(briefs)} briefs")
        log(f"  Gold so far: {len(gold_entries)}/300")
        log(f"{'='*60}\n")

        await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)  # extra wait for JS to hydrate

        # Check if login needed — wait up to 20 min for manual login
        chat_input, sel = await find_chat_input(page)
        if chat_input is None:
            ok = await wait_for_login(page)
            if ok:
                chat_input, sel = await find_chat_input(page)

        if chat_input is None:
            log("❌ Cannot find chat input after login. Exiting.")
            await ctx.close()
            return

        log(f"  Chat input found: {sel}\n")

        for brief in briefs:
            if brief["id"] in done_ids:
                continue

            prompt = build_prompt(brief)
            sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
            occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

            print(f"\n{'─'*60}")
            print(f"  Brief #{brief['id']}/{len(BRIEFS)} — {brief['brand']} / {brief['product']} / {occasion_ar}")
            print(f"  Sector: {sector_ar}")
            print(f"{'─'*60}")

            # Re-find chat input (may shift after navigation)
            chat_input, sel = await find_chat_input(page)
            if chat_input is None:
                log("  ⚠️  Lost chat input — reloading page...")
                await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                chat_input, sel = await find_chat_input(page)
                if chat_input is None:
                    log("  ❌  Still no input. Skipping.")
                    continue

            # Set clipboard and paste (most reliable across editor types)
            await page.evaluate(f"navigator.clipboard.writeText({json.dumps(prompt)})")
            await chat_input.click()
            await page.keyboard.press("Meta+a")   # select all (Mac)
            await asyncio.sleep(0.2)
            await page.keyboard.press("Meta+v")   # paste
            await asyncio.sleep(1)

            # Send — button first, fallback Enter
            sent = False
            for btn_sel in SEND_BTN_SELECTORS:
                try:
                    btn = page.locator(btn_sel).last
                    if await btn.is_enabled(timeout=1200):
                        await btn.click()
                        sent = True
                        break
                except Exception:
                    pass
            if not sent:
                await page.keyboard.press("Enter")

            log(f"  Prompt sent. Waiting for ALLaM 34B response (up to 3 min)...")
            response = await wait_for_response(page, timeout_s=180)

            if not response:
                log(f"  ❌  No response for Brief #{brief['id']} — skipping.")
                continue

            # Parse response and check diversity
            parsed_check = parse_response(response)
            n_opts = len([v for v in parsed_check["options"].values() if v and len(v) > 5])
            div_ok = _diversity_ok(parsed_check["options"])

            # Diversity retry: if openers overlap or too few options, try once more in same session
            if not div_ok or n_opts < 3:
                log(f"  ⚠️  Diversity issue ({n_opts} opts, div={div_ok}) — sending variation prompt...")
                openers_seen = []
                for cap in parsed_check["options"].values():
                    if cap and cap.split():
                        openers_seen.append(cap.split()[0].strip("؟!.،"))

                variation_note = ""
                if openers_seen:
                    variation_note = f"\nممنوع تبدأ أي كابشن بهذه الكلمات: {' / '.join(set(openers_seen))}"

                variation_prompt = (
                    f"اكتب مرة أخرى — هذه المرة لازم كل كابشن يبدأ بكلمة مختلفة تماماً.{variation_note}\n"
                    f"التزم بقواعد الافتتاح لكل تقنية:\n"
                    f"  أ: جملة خبرية مفاجئة (ممنوع: لمّا / إذا / تخيل)\n"
                    f"  ب: الكلمة ذات المعنيين (كلمة أو اثنتان)\n"
                    f"  ج: ابدأ بـ «اللي» أو فعل مضارع\n"
                    f"  د: ابدأ بـ «إذا» أو «تخيل معي»\n"
                    f"  هـ: ابدأ بـ «لمّا» (إلزامي)\n"
                    f"نفس الشكل السابق: أ. / ب. / ج. / د. / هـ. ثم الأفضل:"
                )
                try:
                    chat_input2, _ = await find_chat_input(page)
                    if chat_input2:
                        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(variation_prompt)})")
                        await chat_input2.click()
                        await page.keyboard.press("Meta+a")
                        await asyncio.sleep(0.2)
                        await page.keyboard.press("Meta+v")
                        await asyncio.sleep(0.5)
                        await page.keyboard.press("Enter")
                        retry_response = await wait_for_response(page, timeout_s=120)
                        if retry_response:
                            retry_parsed = parse_response(retry_response)
                            retry_opts = len([v for v in retry_parsed["options"].values() if v and len(v) > 5])
                            retry_div = _diversity_ok(retry_parsed["options"])
                            log(f"  🔄  Retry: {retry_opts} opts, div={retry_div}")
                            if retry_opts > n_opts or (retry_div and not div_ok):
                                response = retry_response  # use the better response
                                log(f"  ✅  Using retry response (better quality)")
                except Exception as e:
                    log(f"  ⚠️  Variation retry failed: {e}")

            # Save to queue
            save_to_queue(brief, response)
            done_ids.add(brief["id"])

            # Start new chat to avoid context contamination between briefs
            try:
                new_btn = page.locator(
                    "button[aria-label*='new chat' i], "
                    "button[title*='new' i], "
                    "a[href='/']:not([aria-label]), "
                    "button:has-text('New chat'), "
                    "button:has-text('محادثة جديدة')"
                ).first
                if await new_btn.is_visible(timeout=2000):
                    await new_btn.click()
                    await asyncio.sleep(2)
                else:
                    raise Exception("no new-chat button")
            except Exception:
                await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

        await ctx.close()
        queue = load_queue()
        pending = len([p for p in queue["pending"] if p["status"] == "pending"])
        gold    = len(load_gold())
        log(f"\n{'='*60}")
        log(f"  Collection complete!")
        log(f"  {pending} responses queued for review.")
        log(f"  Gold approved so far: {gold}/300")
        log(f"\n  ✨ Open review page: {REVIEW_URL}")
        log(f"{'='*60}\n")


def reparse_queue() -> None:
    """Re-run parse_response on all queue entries — fixes earlier parser bugs."""
    if not QUEUE_FILE.exists():
        print("No queue file found.")
        return
    q = load_queue()
    fixed = 0
    for item in q["pending"]:
        raw = item.get("raw", "")
        if raw:
            parsed = parse_response(raw)
            item["options"] = parsed["options"]
            item["best"]    = parsed["best"]
            fixed += 1
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2))
    print(f"Re-parsed {fixed} queue entries.")


def dry_run(briefs: list[dict]) -> None:
    """Print all prompts without opening browser — for review."""
    for brief in briefs:
        sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
        occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
        prompt = build_prompt(brief)
        print(f"\n{'='*70}")
        print(f"BRIEF #{brief['id']} — {brief['brand']} / {occasion_ar} / {sector_ar}")
        print(f"{'='*70}")
        print(prompt)
    print(f"\n\nTotal: {len(briefs)} briefs")


def print_quality_report() -> None:
    """Print a quality analysis of all pending queue items."""
    if not QUEUE_FILE.exists():
        print("No queue file.")
        return
    q = load_queue()
    pending = q.get("pending", [])
    if not pending:
        print("No pending items.")
        return

    total = len(pending)
    has_5_opts = sum(1 for p in pending if p.get("options_count", 0) == 5
                     or len([v for v in p.get("options",{}).values() if v]) == 5)
    div_ok = sum(1 for p in pending if p.get("diversity_ok", None) is True)
    div_fail = sum(1 for p in pending if p.get("diversity_ok", None) is False)
    div_unknown = total - div_ok - div_fail

    print(f"\n{'='*50}")
    print(f"  QUALITY REPORT — {total} pending items")
    print(f"{'='*50}")
    print(f"  5 options:       {has_5_opts}/{total} ({has_5_opts/total*100:.0f}%)")
    print(f"  diversity_ok=T:  {div_ok}")
    print(f"  diversity_ok=F:  {div_fail}")
    print(f"  not yet scored:  {div_unknown}")

    # Best technique picked by ALLaM
    from collections import Counter
    best_techs = Counter()
    for p in pending:
        best = p.get("best", "")
        for k, v in p.get("options", {}).items():
            if v and best == v:
                best_techs[k] += 1
                break
    if best_techs:
        print(f"\n  ALLaM best picks:")
        for k, n in best_techs.most_common():
            print(f"    {k}: {n}")

    # Score distribution
    all_scores = []
    for p in pending:
        for sc in (p.get("scores") or {}).values():
            if sc:
                all_scores.append(sc)
    if all_scores:
        avg = sum(all_scores) / len(all_scores)
        print(f"\n  Avg quality score: {avg:.1f}/100")

    print(f"{'='*50}\n")


def mark_for_recollect(min_options: int = 3, require_diversity: bool = True) -> int:
    """
    Remove bad pending items from the queue so the loop re-collects them.
    Returns count of items removed.
    """
    if not QUEUE_FILE.exists():
        return 0
    q = load_queue()
    pending = q.get("pending", [])
    keep = []
    removed = 0
    for item in pending:
        n_opts = len([v for v in item.get("options", {}).values() if v and len(v) > 5])
        div_ok = item.get("diversity_ok", True)  # unknown = assume ok
        if n_opts < min_options or (require_diversity and div_ok is False):
            print(f"  Removing Brief #{item['brief_id']} ({item['brand']}/{item['occasion']}) "
                  f"— opts={n_opts} div={div_ok}")
            removed += 1
        else:
            keep.append(item)
    q["pending"] = keep
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2))
    print(f"Removed {removed} bad items — loop will re-collect them.")
    return removed


def main():
    parser = argparse.ArgumentParser(description="HUMAIN gold output collector")
    parser.add_argument("--reparse",        action="store_true", help="Re-parse existing queue entries with improved parser")
    parser.add_argument("--quality-report", action="store_true", help="Print quality analysis of pending queue")
    parser.add_argument("--recollect-bad",  action="store_true", help="Remove low-quality items so loop re-collects them")
    parser.add_argument("--min-options",    type=int, default=3,  help="Min options required (default 3, for --recollect-bad)")
    parser.add_argument("--from",    dest="from_id", type=int, default=1,    help="Resume from brief id")
    parser.add_argument("--id",      type=int, default=None,                 help="Run single brief id")
    parser.add_argument("--dry-run", action="store_true",                    help="Print prompts only")
    parser.add_argument("--matrix",  action="store_true",                    help="Use full brief matrix (data/brief_matrix.json) instead of hardcoded 18 briefs")
    parser.add_argument("--sector",  default=None,                           help="Filter matrix by sector (e.g. f_and_b)")
    parser.add_argument("--occasion",default=None,                           help="Filter matrix by occasion (e.g. ramadan)")
    parser.add_argument("--batch",   type=int, default=None,                 help="Limit to N briefs (for batched runs)")
    args = parser.parse_args()

    if args.quality_report:
        print_quality_report()
        return

    if args.recollect_bad:
        mark_for_recollect(min_options=args.min_options, require_diversity=True)
        return

    # Choose brief source
    if args.matrix:
        matrix_file = BASE / "data" / "brief_matrix.json"
        if not matrix_file.exists():
            print("❌  data/brief_matrix.json not found. Run: python3 scripts/generate_brief_matrix.py")
            sys.exit(1)
        all_briefs = json.loads(matrix_file.read_text())
        # Skip briefs already in queue (pending review, approved, or stale)
        queue = load_queue()
        done_ids_queue = (
            {p["brief_id"] for p in queue.get("pending", [])}
            | {p["brief_id"] for p in queue.get("approved", [])}
            | {p["brief_id"] for p in queue.get("stale_v1", [])}
        )
        all_briefs = [b for b in all_briefs if b["id"] not in done_ids_queue]
        if args.sector:
            all_briefs = [b for b in all_briefs if b["sector"] == args.sector]
        if args.occasion:
            all_briefs = [b for b in all_briefs if b["occasion"] == args.occasion]
        source = all_briefs
    else:
        source = BRIEFS

    if args.id:
        briefs = [b for b in source if b["id"] == args.id]
    else:
        briefs = [b for b in source if b["id"] >= args.from_id]

    if args.batch:
        briefs = briefs[:args.batch]

    if not briefs:
        print(f"No briefs found for given arguments.")
        sys.exit(1)

    if args.dry_run:
        dry_run(briefs)
        return

    if args.reparse:
        reparse_queue()
        return

    asyncio.run(run_browser(briefs))


if __name__ == "__main__":
    main()
