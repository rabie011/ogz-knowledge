# Final Prompt Design — V3
# Date: 2026-06-07
# Based on: Round 1 (5 briefs) + Round 2 (5 new sectors) + Round 3 validation (3 briefs)
# Model: HUMAIN / ALLaM 34B (best performer)
# Status: READY TO DEPLOY

---

## THE CORE FINDING

The model's quality is directly controlled by the "فاشل وممنوع" list.
Every time a new template appears → add it to the banned list → model finds something more original.

This is a living prompt. The negative examples are the quality lever.

---

## WHAT WE LEARNED FROM 13 BRIEFS

### Paradox Hunter
- Copies the exemplar structure verbatim when only one example is given
- Fix: give 2 structurally DIFFERENT examples + say "استلهم الفكرة، لا تنسخ القالب"
- Best outputs: "اليوم الوطني ينتظره" / "الشتاء يسخن معاه" / "الفرصة تنتظرها"

### Heritage Decoder
- Falls into "X معك في كل خطوة — أنت الخطوة" across different brands
- Fix: sector-specific exemplars + ban the generic template explicitly
- Best outputs: "الذكاء يستثمر فيك" / "ترتدين المناسبة" / "اللبن اللي يروبك"

### Firaasa
- Goes through templates in order: "ما تدور على X → Y" → "مش بس لـ X، وسط الزحمة"
- Each blocked template forces the model deeper → more original output
- Best output came AFTER blocking two templates: "في لحظة هدوء، اللبن هو اللي يختارك"
- Fix: keep the banned template list growing each session

---

## FINAL PROMPT — COPY THIS TO server.py

```
<RED_LINES>
ممنوع: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس أو خوفهم.
دائماً: لهجة سعودية طبيعية. حد أقصى {max_chars} حرف. بدون إنجليزي.
</RED_LINES>

<TECHNIQUES>
أ. Paradox Hunter — قلب التوقع (استلهم الفكرة، لا تنسخ القالب)
← ناجح 1: "البروستد اللي ما ينتظره اليوم الوطني — اليوم الوطني ينتظره"
← ناجح 2 (مختلف تماماً): "التوفير اللي ما يحتاج تفكر مرتين"
← فاشل: "استمتع" / "لا تفوت" / "أجواء مميزة" / "عرض لفترة محدودة"
← ممنوع: نسخ أي مثال كما هو مع تغيير الكلمات فقط

ب. Heritage Decoder — جملة كاملة تحمل كلمة بمعنيين
← ناجح (مالية): "الذكاء يستثمر فيك" — تستثمر الفكرة + الفكرة تستثمر فيك
← ناجح (أزياء): "ترتدين المناسبة" — تلبسين + أنتِ هي المناسبة
← فاشل وممنوع: "X معك في كل خطوة — أنت الخطوة" — لا تستخدمه أبداً

ج. Firaasa — ملاحظة سلوكية محددة لهذا المنتج تحديداً
← ناجح: "في لحظة هدوء، اللبن هو اللي يختارك"
← ناجح: "الأم ما تدور على حليب — تدور على طمأنينة"
← فاشل وممنوع: "الناس ما تدور على X — تدور على Y"
← فاشل وممنوع: "مش بس لـ X، هي لحظة Y وسط الزحمة"
← الصحيح: لحظة حقيقية خاصة بهذا المنتج، مو جملة عامة لأي منتج
</TECHNIQUES>

<BRAND>
العلامة: {brand} | القطاع: {sector} | المنتج: {product} | المناسبة: {occasion}
الهاشتاقات: {hashtags}
</BRAND>

<TASK>
اكتب 3 كابشنات — كل واحد بتقنية مختلفة (أ، ب، ج).
كل كابشن: حد أقصى {max_chars} حرف.
ثم اختر الأقوى وضعه في السطر الأخير بعد كلمة: الأفضل:
</TASK>
```

---

## DEPLOYMENT INSTRUCTIONS FOR server.py

1. Replace the bloated 7-section Arabic prompt (line ~1141) with this template
2. Fill variables: brand, sector, product, occasion, hashtags, max_chars
3. Kill Authenticity Detective routing for captions — remove cd_03 from caption route
4. Keep max_tokens=200 (or raise to 300 since we now get 3 outputs + selection)
5. Temperature 0.8 (higher = more diverse across 3 options)
6. Parse the "الأفضل:" line as the final output to return

---

## MAX_CHARS PER SECTOR

| Sector | Max chars |
|---|---|
| f_and_b | 140 |
| fashion | 220 |
| real_estate | 200 |
| retail_lifestyle | 160 |
| beauty_personal_care | 150 |
| finance | 180 |
| government | 200 |
| food_manufacturing | 140 |
| electronics | 160 |
| telecom | 160 |

---

## LIVING RULES — ADD TO THIS LIST AFTER EVERY 5 SESSIONS

### Firaasa banned templates (grow this list)
- "الناس ما تدور على X — تدور على Y"
- "مش بس لـ X، هي لحظة Y وسط الزحمة"
- [add next one here when it appears]

### Heritage Decoder banned templates
- "X معك في كل خطوة — أنت الخطوة"
- [add next one here when it appears]

### Paradox Hunter banned patterns
- Copying exemplar with word substitution only
- [add next one here when it appears]

---

## BEST OUTPUTS OF THE ENTIRE SESSION (الأفضل من كل الجولات)

These are the benchmark — future outputs should reach this level:

1. AlBaik/يوم وطني: "البروستد اللي ما ينتظره اليوم الوطني — اليوم الوطني ينتظره" [H]
2. Barns/رمضان: "القهوة المثلجة اللي تَرِد القلب قبل العطش — رمضان مع بارنز غير" [H]
3. MaxFashion/عيد: "العباءة اللي تعكس أصالة العيد — أنت العيد بذاته" [H]
4. Finance/إطلاق: "الناس ما تدور على فلوس — تدور على مستقبل آمن" [H]
5. Almarai/يومي: "في لحظة هدوء، اللبن هو اللي يختارك" [H-V3]
6. Starbucks/رمضان: "في رمضان، القهوة مش بس للطعم، هي لحظة هدوء وسط الزحمة" [H-V3]

[H] = HUMAIN Round 2 | [H-V3] = HUMAIN Round 3 (V3 prompt)
