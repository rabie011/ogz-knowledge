"""
generate_tensions.py — GPT-4o generates occasion_tension for every brief

For each brand × occasion in brief_matrix.json, produces one Arabic line:
the specific creative insight that makes THIS brand on THIS occasion unique.

Usage: python3 scripts/generate_tensions.py [--dry-run]
"""

import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent
BRIEFS_FILE = BASE / "data" / "brief_matrix.json"

OCCASION_AR = {
    "national_day":    "اليوم الوطني",
    "founding_day":    "يوم التأسيس",
    "ramadan":         "رمضان",
    "eid_al_fitr":     "عيد الفطر",
    "eid_al_adha":     "عيد الأضحى",
    "riyadh_season":   "موسم الرياض",
    "white_friday":    "الجمعة البيضاء",
    "back_to_school":  "العودة للمدارس",
    "summer":          "الصيف",
    "winter":          "الشتاء",
    "graduation":      "التخرج",
    "evergreen":       "محتوى دائم",
}

SECTOR_EN = {
    "f_and_b":              "Food & Beverage",
    "fashion":              "Fashion",
    "real_estate":          "Real Estate",
    "retail_lifestyle":     "Retail",
    "beauty_personal_care": "Beauty",
    "healthcare_wellness":  "Health & Fitness",
}


def _load_key() -> str:
    env_file = Path.home() / ".abraham_env"
    for line in env_file.read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("OPENAI_API_KEY not found in ~/.abraham_env")


def build_tension_prompt(brief: dict) -> str:
    ctx = brief.get("brand_context", {})
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

    lines = [f"العلامة: {brief['brand']}"]
    if ctx.get("bio_tagline"):
        lines.append(f'شعار حقيقي: "{ctx["bio_tagline"]}"')
    if ctx.get("real_hooks"):
        lines.append(f"أقوى هوكات: {' | '.join(ctx['real_hooks'][:2])}")
    if ctx.get("high_engagement_style"):
        lines.append(f"ما ينجح: {ctx['high_engagement_style'][:80]}")
    brand_block = "\n".join(lines)

    return f"""أنت مدير إبداعي يبحث عن الزاوية غير المتوقعة.

العلامة × المناسبة:
{brand_block}
المناسبة: {occasion_ar}

سؤال واحد: ما الحقيقة المفاجئة أو التناقض الذكي بين هذه العلامة تحديداً وهذه المناسبة تحديداً؟
مو وصف — زاوية. مو احتفال عام — توتر خاص.

أمثلة على المطلوب (لاحظ: قصيرة، مفاجئة، خاصة):
البيك / اليوم الوطني → "البيك نفسه رمز وطني — ما تحتاج يوم وطني عشان تحتفل بالبيك"
بارنز / رمضان → "الصايم أول ما يفطر يفكر في القهوة — بارنز يعرف ذا قبل الصايم نفسه"
روشن / يوم التأسيس → "تأسيس المملكة كان وعد بوطن — روشن هو البيت اللي يكمّل الوعد"
ماكدونالدز / عيد الأضحى → "كل العيلة عندها رأي في الأكل إلا ماكدونالدز — ذاك الوحيد اللي ما فيه خلاف"

الآن اكتب توتراً إبداعياً لـ {brief['brand']} في {occasion_ar}.
جملة واحدة، 10-20 كلمة، لهجة سعودية طبيعية، تبدأ بالزاوية مو باسم العلامة:"""


def generate_tension(brief: dict, client) -> str:
    prompt = build_tension_prompt(brief)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=120,
    )
    return resp.choices[0].message.content.strip()


def main():
    dry_run = "--dry-run" in sys.argv

    briefs = json.loads(BRIEFS_FILE.read_text())

    # Skip briefs that already have occasion_tension
    to_process = [b for b in briefs if not b.get("occasion_tension")]
    print(f"Briefs needing tension: {len(to_process)} / {len(briefs)}")

    if dry_run:
        for b in to_process[:3]:
            print(f"\n[DRY] #{b['id']} {b['brand']} / {b['occasion']}")
            print(build_tension_prompt(b)[-300:])
        return

    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib.openai_client import make_client  # B258: bounded timeout/retries
    client = make_client(_load_key())

    updated = 0
    errors = 0
    for i, brief in enumerate(to_process):
        print(f"  [{i+1}/{len(to_process)}] #{brief['id']} {brief['brand']} / {brief['occasion']} ...", end=" ", flush=True)
        try:
            tension = generate_tension(brief, client)
            # Write back to the full briefs list
            for b in briefs:
                if b["id"] == brief["id"]:
                    b["occasion_tension"] = tension
                    break
            print(f"✓ {tension[:60]}...")
            updated += 1
            # Save every 10 to avoid losing progress
            if updated % 10 == 0:
                BRIEFS_FILE.write_text(json.dumps(briefs, ensure_ascii=False, indent=2))
                print(f"    [saved {updated} so far]")
            time.sleep(0.3)  # gentle rate limiting
        except Exception as e:
            print(f"✗ {e}")
            errors += 1
            time.sleep(2)

    BRIEFS_FILE.write_text(json.dumps(briefs, ensure_ascii=False, indent=2))
    print(f"\nDone: {updated} tensions generated, {errors} errors")
    print(f"Run enrich_briefs.py again if needed (tension is already in brief_matrix.json)")


if __name__ == "__main__":
    main()
