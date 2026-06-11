"""
3-Way Test: Current system vs New prompt vs ALLaM-7B
5 briefs. Mohamed rates all 15 outputs.
"""

import os, json, urllib.request, pathlib, time

ROOT = pathlib.Path(__file__).parent.parent

# Load keys
env = {}
with open(os.path.expanduser("~/.abraham_env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
OPENAI_KEY = env.get("OPENAI_API_KEY", "")

# ── 5 fixed briefs ───────────────────────────────────────────────
BRIEFS = [
    {"brand": "albaik",          "sector": "f_and_b",          "occasion": "national_day",  "product": "بروستد",       "hashtags": "#انتم_والبيك_جيران #صنع_في_السعودية"},
    {"brand": "barnscoffee",     "sector": "f_and_b",          "occasion": "ramadan",       "product": "قهوة مثلجة",   "hashtags": "#بارنز #مننا_ويفهم_جونا"},
    {"brand": "maxfashionmena",  "sector": "fashion",          "occasion": "eid_al_fitr",   "product": "عباءة كلاسيكية","hashtags": "#إطلالاتmena"},
    {"brand": "roshnksa",        "sector": "real_estate",      "occasion": "founding_day",  "product": "فيلا عائلية",  "hashtags": "#مجموعة_روشن #نبني_الفرق"},
    {"brand": "pandasaudi",      "sector": "retail_lifestyle", "occasion": "evergreen",     "product": "عرض أسبوعي",   "hashtags": "#بنده_معك_تفرق"},
]

# ── SYSTEM A: current prompt (bloated, Authenticity Detective wires) ─────────
CURRENT_SYSTEM_PROMPT = """أنت مخرج إبداعي سعودي تكتب لعلامة @{brand}.

═══ المنهجية الإبداعية ═══
استخدم تقنية الفراسة — ابدأ بحقيقة إنسانية قبل المنتج. الأسلوب الصوتي: ثقة هادئة + ملاحظة دقيقة.

═══ المنتج ═══
المنتج: {product}

═══ المناسبة ═══
{occasion}

═══ قواعد القطاع ═══
{sector_rule}

═══ أمثلة حقيقية (التزم بأسلوبها، لا تنسخ) ═══
{templates}

═══ خطوط حمراء صارمة ═══
⛔ ممنوع: السرير أو غرفة النوم.
⛔ ممنوع: خلع أو إزالة أي ملابس أو حجاب.
⛔ ممنوع: استغلال ضعف الناس.

═══ القواعد الذهبية ═══
1. قصير — حد أقصى {max_chars} حرف.
2. اللهجة السعودية: وش، الحين، يالله، حلو
3. ممنوع: شنو، جذي، زين، تفضلوا
4. هاشتاقات: {hashtags}

اكتب الكابشن فقط، بدون شرح:"""

SECTOR_RULES = {
    "f_and_b":              "الطول: 80-150 حرف. حسّي مباشر. ابدأ باسم المنتج.",
    "fashion":              "الطول: 150-250 حرف. طموح وأنيق. بدون إيموجي أو إيموجي واحد.",
    "beauty_personal_care": "الطول: 120-200 حرف. فائدة المنتج أولاً.",
    "retail_lifestyle":     "الطول: 80-150 حرف. عروض وتوفير. ابدأ بالفائدة.",
    "real_estate":          "الطول: 150-220 حرف. فخر وطني + جودة حياة.",
    "healthcare_wellness":  "الطول: 100-180 حرف. تحفيزي وصحي.",
}

SAMPLE_TEMPLATES = {
    "f_and_b":           ["طعم يجمعنا كل مرة 🍗 يالله اطلبها الحين", "النكهة اللي ما تنمل، مع {brand}"],
    "fashion":           ["إطلالة تعكس أناقتك في كل مناسبة", "تألّقي بتصميم يجمع بين الراحة والجمال"],
    "retail_lifestyle":  ["عروض ما تتوقعها، بأسعار ما تصدّقها", "استمتع بأفضل المنتجات بأسعار تنافسية"],
    "real_estate":       ["هنا تبدأ الحياة اللي تحلم بها", "منزلك الجديد ينتظرك في قلب المدينة"],
    "beauty_personal_care": ["بشرتك تستاهل الأفضل", "جمالك يبدأ من هنا"],
}

MAX_CHARS = {"f_and_b": 160, "fashion": 280, "real_estate": 250, "retail_lifestyle": 180, "beauty_personal_care": 220}

# ── SYSTEM B: new prompt (XML 4-block, exemplars not labels, no templates) ──
TECHNIQUE_EXEMPLARS = {
    "f_and_b": {
        "name": "Paradox Hunter — قلب التوقع",
        "example_good": '"الكيك اللي ما يحتاج مناسبة — هو المناسبة"\n"البيك مش أكل — البيك قرار"',
        "example_bad": '"لا تفوتون الفرصة" / "عرض لفترة محدودة" / "طعم لا يُنسى"'
    },
    "fashion": {
        "name": "Heritage Decoder — كلمة بمعنيين",
        "example_good": '"ترتدين المناسبة" (تلبسين اللي يليق + أنتِ هي المناسبة)\n"الأصل يظهر" (الخامة الحقيقية + الشخصية الأصيلة)',
        "example_bad": '"تألقي وكوني مركز الأنظار" / "إطلالة لا مثيل لها"'
    },
    "real_estate": {
        "name": "Heritage Decoder — كلمة بمعنيين",
        "example_good": '"أرضك تنتظرك" (الأرض الفعلية + جذورك + استثمارك)\n"نبني الفرق" (البناء الحرفي + الفارق في الحياة)',
        "example_bad": '"مشروع يجمع بين الجودة والفخامة" / "حياة مريحة في قلب المدينة"'
    },
    "retail_lifestyle": {
        "name": "Paradox Hunter — قلب التوقع",
        "example_good": '"بنده — وش تطلب أكثر؟" (سؤال بجواب داخله)\n"التوفير اللي ما تحتاج تشرحه"',
        "example_bad": '"استمتع بأفضل العروض" / "لا تفوتك الفرصة"'
    },
    "beauty_personal_care": {
        "name": "Paradox Hunter — قلب التوقع",
        "example_good": '"الروتين اللي ما يحس روتين"\n"بشرتك تعرف — حتى لو ما عرفتِ"',
        "example_bad": '"بشرتك تستاهل الأفضل" / "جمالك يبدأ من هنا"'
    },
}

NEW_PROMPT = """<RED_LINES>
ممنوع منعاً باتاً: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس.
دائماً: لهجة نجدية/سعودية خليجية. حد أقصى {max_chars} حرف. بدون إنجليزي.
</RED_LINES>

<TECHNIQUE>
التقنية: {technique_name}
مثال ناجح:
{example_good}
لا تكتب أبداً مثل:
{example_bad}
</TECHNIQUE>

<BRAND>
العلامة: {brand} | القطاع: {sector} | المنتج: {product} | المناسبة: {occasion}
الهاشتاقات: {hashtags}
</BRAND>

<TASK>
اكتب كابشن واحد فقط. لهجة سعودية. حد أقصى {max_chars} حرف.
</TASK>"""

# ── SYSTEM C: ALLaM-7B-Instruct via HuggingFace Inference API ──────────────
ALLAM_PROMPT = """أنت كاتب محتوى سعودي محترف. اكتب كابشن إنستغرام واحد باللهجة السعودية النجدية.

العلامة: {brand}
القطاع: {sector}
المنتج: {product}
المناسبة: {occasion}

القواعد:
- لهجة سعودية نجدية فقط (وش، الحين، يالله، حلو)
- حد أقصى {max_chars} حرف
- لا تكتب: شنو، جذي، زين، تفضلوا
- لا كلام عن السرير أو الملابس

اكتب الكابشن فقط:"""


def call_openai(prompt: str, system_label: str, brief_idx: int) -> str:
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.75,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip().strip('"\'')


def call_allam(prompt: str) -> str:
    payload = json.dumps({
        "inputs": prompt,
        "parameters": {"max_new_tokens": 120, "temperature": 0.75, "return_full_text": False}
    }).encode()
    req = urllib.request.Request(
        "https://api-inference.huggingface.co/models/humain-ai/ALLaM-7B-Instruct-preview",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict) and "error" in data:
            return f"[ALLaM ERROR: {data['error']}]"
        return str(data)
    except Exception as e:
        return f"[ALLaM TIMEOUT/ERROR: {e}]"


# ── RUN TEST ─────────────────────────────────────────────────────
results = []

for i, b in enumerate(BRIEFS):
    sector = b["sector"]
    print(f"\n{'='*60}")
    print(f"Brief {i+1}/5 — {b['brand']} | {b['occasion']} | {b['product']}")
    print('='*60)

    mx = MAX_CHARS.get(sector, 180)
    sr = SECTOR_RULES.get(sector, "الطول: 100-180 حرف.")
    tmpl = "\n".join(f"- {t}" for t in SAMPLE_TEMPLATES.get(sector, []))
    tech = TECHNIQUE_EXEMPLARS.get(sector, TECHNIQUE_EXEMPLARS["f_and_b"])

    # System A — current
    prompt_a = CURRENT_SYSTEM_PROMPT.format(
        brand=b["brand"], product=b["product"], occasion=b["occasion"],
        sector_rule=sr, templates=tmpl, hashtags=b["hashtags"], max_chars=mx
    )
    print("  [A] Current system...", end=" ", flush=True)
    out_a = call_openai(prompt_a, "A", i)
    print(f"done ({len(out_a)} chars)")
    print(f"      → {out_a}")

    time.sleep(1)

    # System B — new XML 4-block
    prompt_b = NEW_PROMPT.format(
        brand=b["brand"], product=b["product"], occasion=b["occasion"],
        sector=sector, hashtags=b["hashtags"], max_chars=mx,
        technique_name=tech["name"], example_good=tech["example_good"], example_bad=tech["example_bad"]
    )
    print("  [B] New prompt...", end=" ", flush=True)
    out_b = call_openai(prompt_b, "B", i)
    print(f"done ({len(out_b)} chars)")
    print(f"      → {out_b}")

    time.sleep(1)

    # System C — ALLaM
    prompt_c = ALLAM_PROMPT.format(
        brand=b["brand"], product=b["product"], occasion=b["occasion"],
        sector=sector, max_chars=mx
    )
    print("  [C] ALLaM-7B...", end=" ", flush=True)
    out_c = call_allam(prompt_c)
    print(f"done ({len(out_c)} chars)")
    print(f"      → {out_c}")

    results.append({
        "brief": i + 1,
        "brand": b["brand"],
        "sector": sector,
        "occasion": b["occasion"],
        "product": b["product"],
        "A_current": out_a,
        "B_new_prompt": out_b,
        "C_allam": out_c,
    })
    time.sleep(2)

# ── SAVE RESULTS ─────────────────────────────────────────────────
out_dir = ROOT / "docs" / "consultations"
out_dir.mkdir(parents=True, exist_ok=True)

# JSON
(out_dir / "test_3way_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))

# Human-readable review sheet
lines = ["# 3-Way Test Results — For Mohamed to Rate", "# Date: 2026-06-07", "# Rate each: ✅ Pass / ❌ Fail / ⚠️ Weak\n", ""]
for r in results:
    lines.append(f"## Brief {r['brief']} — {r['brand']} | {r['occasion']} | {r['product']}")
    lines.append(f"**[A] Current system (gpt-4o-mini, old prompt):**")
    lines.append(f"> {r['A_current']}")
    lines.append(f"Rate: [ ] ✅ [ ] ⚠️ [ ] ❌  Notes: ___\n")
    lines.append(f"**[B] New prompt (XML 4-block, exemplars, no templates):**")
    lines.append(f"> {r['B_new_prompt']}")
    lines.append(f"Rate: [ ] ✅ [ ] ⚠️ [ ] ❌  Notes: ___\n")
    lines.append(f"**[C] ALLaM-7B-Instruct (Saudi LLM, raw dialect test):**")
    lines.append(f"> {r['C_allam']}")
    lines.append(f"Rate: [ ] ✅ [ ] ⚠️ [ ] ❌  Notes: ___\n")
    lines.append("---\n")

(out_dir / "test_3way_review.md").write_text("\n".join(lines))

print("\n\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print(f"Saved: docs/consultations/test_3way_results.json")
print(f"Saved: docs/consultations/test_3way_review.md")
print("\nQUICK SUMMARY:")
for r in results:
    print(f"\nBrief {r['brief']} — {r['brand']}")
    print(f"  A (current):  {r['A_current'][:80]}...")
    print(f"  B (new):      {r['B_new_prompt'][:80]}...")
    c_preview = r['C_allam'][:80] if not r['C_allam'].startswith('[') else r['C_allam']
    print(f"  C (ALLaM):    {c_preview}...")
