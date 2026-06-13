#!/usr/bin/env python3
"""CLIENT PASSPORT INTAKE (June 13 — Mohamed: «answer all questions for each client,
me and amira or elhareth on the same link»). Stages the 6 must-have questions per
client as free-text cards on the SAME feedback portal (one shared link, roster picker
already names who answered). Answers flow into the client's organs via apply_rulings
h_passport → the 6 RED organs go green and the client becomes production-ready.

The 6 map 1:1 to the must-haves only the client can give:
  identity · goals · red_lines · truth · audience · capacity
Sector-aware: F&B (orders/day, delivery) vs jewelry (custom orders, appointments).

Usage: python3 scripts/seed_passport_cards.py --handle eatjurisha [--sector food|jewelry]
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import queue_decision as qd
from feedback_lib import base

# (field, organ, question by sector). organ = where h_passport writes the confirmed answer.
QUESTIONS = {
    "identity": {
        "organ": "fingerprint",
        "food": "مين يتكلم باسم البراند؟ (البراند نفسه / صاحبه / شخصية محددة) — وايش الشي اللي يميزكم عن أي منافس بكلمة أو سطر (الـUSP)؟",
        "jewelry": "مين يتكلم باسم البراند؟ (البراند / صاحب المحل / شخصية) — وايش يميزكم: التصميم، التوثيق/الثقة، السعر، ولا الخدمة؟ (الـUSP بسطر)",
    },
    "goals": {
        "organ": "goals",
        "food": "هدف الحساب: مبيعات مباشرة، بناء براند، ولا الاثنين؟ وكم بوست عروض من كل ١٠ بوستات؟",
        "jewelry": "هدف الحساب: مبيعات، مكانة/براند، ولا الاثنين؟ (عروض الذهب حساسة — كم نسبة بوستات العروض من ١٠، لو فيه أصلاً؟)",
    },
    "red_lines": {
        "organ": "red_lines",
        "food": "وش الشي اللي ما ننشره أبداً؟ (خطوط حمراء خاصة فيكم، فوق الخطوط الثقافية)",
        "jewelry": "وش الشي اللي ما ننشره أبداً؟ (خطوط حمراء خاصة فيكم — مثلاً أسعار صريحة، مقارنة، ولا شي ثاني)",
    },
    "truth": {
        "organ": "truth_pack",
        "food": "وش المنتجات الأساسية الحقيقية اللي ننشر عنها؟ (بأسمائها الصح + الأسعار لو ممكن)",
        "jewelry": "وش التشكيلات/القطع الحقيقية اللي ننشر عنها؟ (خواتم، أطقم، ذهب/ألماس؟ + الفئات السعرية لو ممكن)",
    },
    "audience": {
        "organ": "audience_mirror",
        "food": "مين جمهوركم الأساسي؟ (الفئة العمرية + الفئة السعرية + مين يطلب فعلاً — أم البيت، الشباب، الموظفين؟)",
        "jewelry": "مين جمهوركم الأساسي؟ (عرسان؟ هدايا؟ الفئة العمرية + الفئة السعرية — هذي الأهم في المجوهرات)",
    },
    "capacity": {
        "organ": "goals",
        "food": "كم طلب باليوم تقدرون تستوعبون؟ (يحدد كم نقدر نضغط على الطلب في البوستات)",
        "jewelry": "تفصيل حسب الطلب؟ كم ياخذ وقت؟ وفيه معرض/مواعيد بالدمام نوجّه لها، ولا أونلاين بس؟",
    },
}
ORDER = ["identity", "goals", "truth", "audience", "red_lines", "capacity"]
NAMES = {"eatjurisha": "جريش الرياض", "albaik": "البيك", "alnasserjewelry": "مجوهرات الناصر"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--sector", choices=["food", "jewelry"], default="food")
    a = ap.parse_args()
    b = base()
    disp = NAMES.get(a.handle, a.handle)
    staged = []
    for i, field in enumerate(ORDER, 1):
        q = QUESTIONS[field]
        cid = f"passport_{a.handle}_{field}"
        qd.push_attributed({
            "id": cid,
            "title": f"📋 {disp} — سؤال {i}/6: {field}",
            "tag": "Passport", "clock": "", "priority": "normal",
            "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
            "kind": "text", "judge_lane": False, "lane": "strategy",
            "handle": a.handle, "organ": q["organ"], "field": field,
            "why": q[a.sector],
            "need": "اكتبوا الجواب بكلماتكم — يُحفظ حرفياً ويعبّي ملف العميل (يصير العضو أخضر).",
            "did": f"هذا السؤال يعبّي العضو «{q['organ']}» — واحد من ٦ يخلّون {disp} جاهز للإنتاج.",
            "placeholder": "جوابكم هنا…",
        }, made_by="claude", via="scripts/seed_passport_cards.py",
           reason=f"client passport intake — {a.handle} {field} (his 'same link' plan)")
        staged.append(cid)
    print(f"staged {len(staged)} passport cards for {a.handle} ({a.sector}): {staged}")


if __name__ == "__main__":
    main()
