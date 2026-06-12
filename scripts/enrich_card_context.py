#!/usr/bin/env python3
"""ENRICH (June 12) — the rebuilt portal card has three new zones Mohamed asked for:
the bold WHY-line, and a summary of «المطلوب» (what we need) + «سوّاه النظام» (what the
system did). The renderer COLLAPSES any zone whose field is absent — never fabricates
filler (per the panel's anti-filler rule). So this fills those fields for the open cards
from content ALREADY in each card's desc (a split, not an invention). Idempotent.
"""
import json
from pathlib import Path

QUEUE = Path(__file__).parent.parent / "data" / "decision_queue.json"

# why / need / did / current / proposed — drawn from each card's own desc, nothing invented
EN = {
    "jurisha_q_voice": {
        "why": "كل كابشن لجريشة يحتاج صوتاً ثابتاً — لازم نعرف مين ينطق باسم البراند.",
        "need": "اختر صوت البراند الثابت.",
        "did": "النظام جاهز يكتب الكابشنات، لكنه واقف: بدون صوت محدّد ما يقدر يثبّت النبرة.",
    },
    "jurisha_q_goal": {
        "why": "هدف المحتوى يحدّد نسبة العروض في كل كابشن نكتبه.",
        "need": "ثبّت هدف المحتوى ونسبة البيع.",
        "did": "النظام الحالي يبيع يوماً من كل أربعة — بانتظار تثبيتك أو تغييرك.",
        "current": "بيع يوم من كل ٤ (٢٧٪).",
        "proposed": "اختر الاتجاه من الخيارات تحت.",
    },
    "pdpl_precedence": {
        "why": "تعارض قانوني حقيقي — وحكمك يدخل CONVENTIONS كقانون دائم.",
        "need": "احكم: حق المحو (PDPL) ضد قانوننا «حجر بلا حذف».",
        "did": "النظام رصد التعارض ووقف؛ التوصية: المحو القانوني الموثّق استثناء وحيد فوق الحجر.",
        "current": "قانوننا الداخلي: حجر بلا حذف (٩٠ يوماً).",
        "proposed": "⭐ المحو القانوني الموثّق = الاستثناء الوحيد، بتوقيعك أنت.",
    },
    "pilot_2_3_shortlist": {
        "why": "اختيارك يطلق استخراج عميلين جديدين وبناء الهرم الكامل لهما.",
        "need": "تبي تشوف المرشّحين الخمسة وتختار اثنين؟",
        "did": "النظام رشّح ٥ من الكوربس (SME تحت ١٠٠ألف، قطاعات متنوّعة) — جاهزين للاستخراج.",
    },
    "orchestrator_plist": {
        "why": "بدون التثبيت، روابطك والمنسّق يموتون مع أي إعادة تشغيل للجهاز.",
        "need": "الصق لصقة واحدة تثبّت ٣ خدمات حيوية ضد الريستارت.",
        "did": "النظام جهّز الـ plists الثلاثة (المنسّق + فحص الصحة كل ٣٠د + النفق) — تنتظر لصقتك.",
    },
    "team_link_share": {
        "why": "رابط واحد يُدخل أميرة والفريق كمصدر حقيقة بشرية لتصحيح النظام.",
        "need": "شارك رابط الفريق الموحّد.",
        "did": "النظام بنى رابطاً موحّداً بهوية لكل عضو — تصحيحاتهم توصلك مجمّعة باسم صاحبها.",
    },
}


def clean_desc(d: str) -> str:
    # the «⚠ اختَر زر…» trailing instruction is now redundant (options ARE the action)
    return d.split("⚠")[0].strip() if "⚠" in d else d


def main():
    q = json.loads(QUEUE.read_text())
    touched = []
    for it in q["items"]:
        e = EN.get(it["id"])
        if not e:
            continue
        for k, v in e.items():
            it[k] = v
        if it.get("desc"):
            it["desc"] = clean_desc(it["desc"])
        touched.append(it["id"])
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    for t in touched:
        print(f"  ✨ enriched {t}")
    print(f"\n{len(touched)} cards now carry why/need/did")


if __name__ == "__main__":
    main()
