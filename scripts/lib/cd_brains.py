#!/usr/bin/env python3
"""
cd_brains.py — Route a brief to a Creative Director brain + build its prompt.

The 5 CD brains in 20_cd_brains/ are creative methodologies. Instead of a generic
"professional content writer" prompt, /api/create routes each brief to the
best-fit CD brain and writes IN THAT METHODOLOGY.

Routing (simplified from cd_router.md — we don't have per-brand fingerprint
weights yet, so we use even default weights + sector affinity + occasion boost):

    score(brain) = default_weight(0.2) × sector_affinity[sector] × occasion_factor

Usage:
    from lib.cd_brains import route, build_cd_prompt_block
    primary, secondary, scores = route('f_and_b', 'ramadan')
    block = build_cd_prompt_block(primary)   # Arabic methodology injection
"""
from __future__ import annotations
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO = Path(__file__).resolve().parent.parent.parent
CD_DIR = REPO / "20_cd_brains"

# Occasion boosts (from cd_brain_router_rules.yaml). Our occasion slugs vs theirs:
#   founding_day → saudi_founding_day, national_day → saudi_national_day
OCCASION_BOOSTS = {
    "ramadan":        {"cd_03_authenticity_detective": 1.2, "cd_04_heritage_decoder": 1.2},
    "eid_al_fitr":    {"cd_01_firaasa_architect": 1.15, "cd_03_authenticity_detective": 1.15},
    "eid_al_adha":    {"cd_04_heritage_decoder": 1.15, "cd_03_authenticity_detective": 1.15},
    "national_day":   {"cd_04_heritage_decoder": 1.2, "cd_02_metaphor_architect": 1.2},
    "founding_day":   {"cd_04_heritage_decoder": 1.3},
}

# Sector safety locks
SECTOR_FORBIDDEN = {
    "healthcare_wellness": {"cd_05_paradox_hunter"},
}

# Map our sector slugs to the CD brain affinity keys
SECTOR_KEY = {
    "f_and_b": "f_and_b",
    "retail_lifestyle": "retail",
    "fashion": "retail",
    "beauty_personal_care": "beauty",
    "real_estate": "real_estate",
    "healthcare_wellness": "healthcare_wellness",
}

# Curated technique exemplars — extracted from each brain's methodology body.
# Showing the LLM the technique done RIGHT (concrete) lifts adherence far more
# than abstract instructions. These are the heart of the few-shot improvement.
EXEMPLARS = {
    "cd_01_firaasa_architect": """أمثلة على التقنية (الحقيقة الإنسانية قبل المنتج):
  • شركة أمن: "السعودي يعرف إن بابه مفتوح — السؤال مش الوعي، السؤال إن الأمان يصير إحساس بيت" → "لا تفتح مجال"
  • اتصالات: "أقوى شبكة في السعودية تطلب منك تفصل — لأن التواصل الحقيقي في الغرفة، مش في التطبيق" → "خلك معهم"
  الطريقة: ابدأ بالحقيقة الإنسانية اللي تخلي الرسالة حتمية، مش اعتباطية.""",

    "cd_02_metaphor_architect": """أمثلة على التقنية (نظام إلى إنسان + لحظة "بس انتبه!"):
  • "لا تفتح مجال" = حرفياً لا تفتح حقل + لا تعطي فرصة + لا تفتح مجال للمخترقين — ثلاث طبقات في أربع كلمات
  الطريقة: ابنِ استعارة كاملة، ثم اقلب التوقع بلحظة "بس انتبه!" — كل شي كان يبدو كافي، فجأة مش كافي.""",

    "cd_03_authenticity_detective": """أمثلة على التقنية (تباين الأداء مقابل الواقع):
  • مشهد الأداء: المجلس الرسمي، الكل مرتب ومبتسم.
  • مشهد الواقع: نفس المجموعة بالبيجامات يأكلون بقايا العرس، وحدة تصيح: "خلوني أحكي لكم وش صار!"
  الطريقة: ما هي اللحظة اللي ينزل فيها القناع؟ المنتج يعطي الإذن تكون حقيقي. مش "قبل/بعد" — بل "أداء/حقيقة".""",

    "cd_04_heritage_decoder": """أمثلة على التقنية (كلمة بمعنيين كمفتاح هيكلي):
  • "ترتوي" = الأرض تُسقى (حرفي) + الحكايات تُروى/الرواية (ثقافي) — نفس الكلمة، معنيان، كلاهما صحيح
  • "مجاديف" = مجاديف السفينة (حرفي) + الإرادة والصمود (مجازي): "انكسرنا.. بس ما انكسرت مجاديفنا"
  • "الأصل" = المنشأ (حرفي) + الذات الأصيلة (ثقافي)
  الطريقة: جد كلمة عربية بمعنيين كلاهما صحيح للعلامة الآن. خلّها المفتاح اللي يحسّه الجمهور قبل ما يسمّيه. الكشف صوتي-دلالي.""",

    "cd_05_paradox_hunter": """أمثلة على التقنية (قلب مضاد للحدس):
  • "غلطان.. توّنا مابدينا" (Wrong.. we've only just begun) — يرفض افتراض الجمهور بكلمة وحدة
  • "مصدر فخر من أول عهد" — حاضر الحتمية
  الطريقة: ابدأ بقلب توقع الجمهور بثقة، ثم اجعل المنتج هو الآلية اللي تثبت القلب.""",
}

_BRAIN_CACHE: dict | None = None


def _parse_front_matter(text: str) -> dict:
    """Extract YAML front-matter between the first two --- markers."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m or not yaml:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def _load_brains() -> dict:
    """Load all 5 CD brain front-matters, cached."""
    global _BRAIN_CACHE
    if _BRAIN_CACHE is not None:
        return _BRAIN_CACHE
    brains = {}
    for f in sorted(CD_DIR.glob("cd_0*.md")):
        fm = _parse_front_matter(f.read_text())
        if fm.get("cd_brain_slug"):
            brains[fm["cd_brain_slug"]] = fm
    _BRAIN_CACHE = brains
    return brains


def route(sector: str, occasion: str = "evergreen") -> tuple[str, str | None, dict]:
    """
    Route a brief to primary (+ optional secondary) CD brain.
    Returns (primary_slug, secondary_slug_or_None, scores_by_brain).
    """
    brains = _load_brains()
    if not brains:
        return ("cd_01_firaasa_architect", None, {})

    sector_key = SECTOR_KEY.get(sector, sector)
    boosts = OCCASION_BOOSTS.get(occasion, {})
    forbidden = SECTOR_FORBIDDEN.get(sector, set())

    scores = {}
    for slug, fm in brains.items():
        if slug in forbidden:
            continue
        weight = 0.2  # even default — no brand fingerprint yet
        sector_aff = fm.get("sector_affinity", {}).get(sector_key, 0.5)
        if occasion and occasion != "evergreen":
            occ_aff = fm.get("occasion_affinity", {}).get(
                {"founding_day": "saudi_founding_day", "national_day": "saudi_national_day"}.get(occasion, occasion),
                0.5,
            )
        else:
            occ_aff = 1.0
        score = weight * sector_aff * occ_aff
        score *= boosts.get(slug, 1.0)
        scores[slug] = round(score, 4)

    if not scores:
        return ("cd_01_firaasa_architect", None, {})

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    primary = ranked[0][0]
    secondary = None
    if len(ranked) > 1 and (ranked[0][1] - ranked[1][1]) < 0.15:
        secondary = ranked[1][0]  # Two-CD Diagnostic
    return (primary, secondary, scores)


def build_cd_prompt_block(slug: str) -> str:
    """Build an Arabic prompt injection from a CD brain's methodology."""
    brains = _load_brains()
    fm = brains.get(slug)
    if not fm:
        return ""

    name = fm.get("name_external", fm.get("name_internal", slug))
    dq = fm.get("diagnostic_question", "")
    vr = fm.get("voice_register", {})
    register = vr.get("register_descriptor", "")
    arabic_register = vr.get("arabic_register", "")
    forbidden = vr.get("forbidden_vocabulary", [])
    preferred = vr.get("preferred_constructions", [])
    tech = fm.get("signature_technique", {})
    tech_name = tech.get("name", "")
    tech_desc = tech.get("description", "")
    anti = fm.get("anti_patterns", [])

    preferred_str = "\n".join(f"  - {p}" for p in preferred[:5])
    forbidden_str = "، ".join(forbidden[:5]) if forbidden else "لا يوجد"
    anti_str = "\n".join(f"  - {a}" for a in anti[:4])
    exemplar = EXEMPLARS.get(slug, "")

    return f"""═══ المنهجية الإبداعية: {name} ═══
السؤال التشخيصي (اسأل نفسك قبل الكتابة):
  {dq}

الأسلوب الصوتي: {register}
السجل العربي: {arabic_register}

التقنية المميزة — {tech_name}:
  {tech_desc}

{exemplar}

أساليب مفضّلة (استخدم منها):
{preferred_str}

ممنوع في هذه المنهجية: {forbidden_str}

تجنّب (أخطاء هذه المنهجية):
{anti_str}

⚡ مهم: لا تكتفِ بالدفء والسجل — طبّق التقنية المميزة فعلياً كما في الأمثلة أعلاه."""


# CLI test
if __name__ == "__main__":
    import sys
    sector = sys.argv[1] if len(sys.argv) > 1 else "f_and_b"
    occasion = sys.argv[2] if len(sys.argv) > 2 else "ramadan"
    p, s, scores = route(sector, occasion)
    print(f"Sector: {sector} | Occasion: {occasion}")
    print(f"Primary:   {p}")
    print(f"Secondary: {s}")
    print(f"Scores:    {scores}")
    print()
    print(build_cd_prompt_block(p))
