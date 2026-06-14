#!/usr/bin/env python3
"""CLIENT-RULES GATE — the single source (Rule #6) that makes the minds + gates CONSUME the
client's own CONFIRMED organs. Mohamed 2026-06-14 + RABIE NO-GO (1/5): the batch that passed the
deterministic gate "all green" carried 24 real OLD mistakes because nothing read the client's
truth. The organs exist; this reads them and refuses what they forbid:

  cultural_overrides.json:
    real_person_mentions=off       → no NAMED real person (الكابتن عادل، أبو بندر) in caption/visual
    family_voice_lines=blocked_*   → no words put in a family member's mouth (أختي تقول: …)
    face_visibility=never          → VISUAL must not direct visible faces/expressions
    family_member_visibility=never → VISUAL must not show family members/children
  truth_pack.format=cloud_kitchen  → no dine-in venue / no invented storefront-cart (delivery only)
  + cross-brand bleed (a food brand wearing a gym frame), brand-name register (English legal name/®)

Boundary-safe (Rule #9): titles need a real NAME after them — «الكابتن في جيبك» is NOT a person.
Imported by render_client_slot (gauntlet kill+regen), pre_ship_gate (HARD), post_audit (test).
"""
import json, re
from pathlib import Path

B = Path(__file__).parent.parent
_FUNC = {"في", "على", "مع", "من", "هو", "هي", "اللي", "الذي", "التي", "عندك", "معك", "بجيبك",
         "هنا", "اليوم", "دائماً", "دايم", "جاهز", "معاك", "وياك", "لك", "إلك", "بقلبك"}
# titles that, FOLLOWED BY A NAME, denote a real person
_TITLE = r"(?:الكابتن|الكوتش|المدرب|المدرّب|الشيف|الأستاذ|الأستاذة|الدكتور|الدكتورة|المعلم|الشيخ|الأمير|الأميرة|الكوتشة)"
NAMED_PERSON = re.compile(_TITLE + r"\s+([ء-ي]{3,})")
KUNYA = re.compile(r"(?<![ء-ي])(?:أبو|ابو|أم|ام)\s+([ء-ي]{3,})")
# family roles + a speech verb = a family voice line
_ROLE = r"(?:أخت[يكه]?|أخ[يوكه]?|الأخت|الأخ|جد[يهتك]?|الجد|الجدة|أم[يكه]?|الأم|أب[يوكه]?|الأب|الوالد[ةه]?|" \
        r"ابن[يكه]?|بنت[يكه]?|الطفل|الطفلة|الصغير|الصغيرة|الحفيد|الحفيدة|العم|الخال|الجيران?)"
_SAY = r"(?:تقول|يقول|قال[ت]?|يهمس|تهمس|همس[ت]?|يصيح|تصيح|ينادي|تنادي|يعلّ?ق|تعلّ?ق|يصرخ|تصرخ|يردّ?د|تردّ?د)"
FAMILY_VOICE = re.compile(_ROLE + r"[^.!؟\n]{0,30}?" + _SAY + r"\s*[:،]?|" + _SAY + r"[^.!؟\n]{0,15}?" + _ROLE)
# VISUAL face/expression + visible family/children directions
FACE_VIS = re.compile(r"وجوه|الوجه|الوجوه|ابتسام[ةات]|تبادل النظرات|نظرات دافئة|تعابير|ملامح|تعبير الوجه|ضحكات على الوج")
FAMILY_VIS = re.compile(r"الأطفال يلعب|الأطفال وهم|الجالسين|يجتمع الجميع|العائلة (?:تجلس|مجتمعة|حول|تتحلق)|أفراد العائلة|غرفة الجلوس|الأهل وهم")
# NEGATION/COMPLIANCE marker (Rule #9, June 14): the shot-cards correctly say «دون إظهار أي وجوه» /
# «التركيز على اليد فقط» — a face-WORD inside a no-faces instruction is COMPLIANT, not a violation.
NO_FACE_MARKER = re.compile(r"دون إظهار|بدون إظهار|بلا وجوه|دون وجوه|بدون وجوه|لا تظهر|دون ظهور|"
                            r"دون أشخاص|بدون أشخاص|اليد فقط|الأيدي فقط|الي[دّ]ين فقط|اليدين فقط|"
                            r"التركيز على الي|اليد والمنتج|دون أي أشخاص|بدون أي وجوه")
# cloud-kitchen forbidden: dine-in venue + invented storefront/cart
DINE_VENUE = re.compile(r"المطعم|مطعمنا|المقهى|الكافيه|صالة الطعام|صالة المطعم|طاولات المطعم|نجلس في المطعم|داخل المطعم")
STOREFRONT = re.compile(r"عرب[ةه] الطعام|عربة الأكل|الكشك|كشك|واجهة المحل|واجهة الفرع|أمام الفرع|الفرع الجديد|محلنا|دكان")
# cross-brand: a FOOD brand wearing a GYM frame (RABIE: albaik as post-workout gym reward)
GYM_FRAME = re.compile(r"(?:ال)?صالة\s+(?:ال)?رياضي|(?:ال)?نادٍ?ي?\s+(?:ال)?رياضي|الجيم|أجهزة\s+(?:ال)?رياضي|الأوزان|رفع الأثقال|كمال الأجسام")
GYM_SOFT = re.compile(r"بعد التمرين|بعد الرياضة|التمرين الطويل|تمرين طويل")
# brand-name register: English legal name / ® mark inside an Arabic caption
LEGAL_NAME = re.compile(r"®|Food Systems|Company|\bLLC\b|\bCo\.\b|\bEst\.\b|Trading Est")

FOOD_SECTORS = {"f_and_b"}


def _overrides(handle):
    f = B / "clients" / handle / "profile" / "cultural_overrides.json"
    return json.loads(f.read_text()) if f.exists() else {}


def _is_cloud_kitchen(handle):
    f = B / "clients" / handle / "profile" / "truth_pack.json"
    if not f.exists():
        return False
    fmt = json.loads(f.read_text()).get("format")
    val = fmt.get("value") if isinstance(fmt, dict) else fmt
    return val == "cloud_kitchen"


def _sector(handle):
    ym = B / "clients" / handle / "year_map.json"
    return json.loads(ym.read_text()).get("sector", "") if ym.exists() else ""


def _named_person(text):
    for m in NAMED_PERSON.finditer(text):
        if m.group(1) not in _FUNC:
            return m.group(0)
    for m in KUNYA.finditer(text):
        if m.group(1) not in _FUNC:
            return m.group(0)
    return None


def violations(post, handle):
    """Return list of (kind, severity, detail) for every confirmed-organ rule this post breaks."""
    out = []
    ov = _overrides(handle)
    caps = post.get("captions") or ([post.get("caption")] if post.get("caption") else [])
    vis = " ".join(str(x) for x in (post.get("visual") or {}).get("phone_shoot_card") or [])
    captext = " ".join(caps)
    allt = captext + " \n " + vis

    if ov.get("real_person_mentions") == "off":
        p = _named_person(allt)
        if p:
            out.append(("real_person", "block", f"named real person «{p}» but real_person_mentions=off"))
    if str(ov.get("family_voice_lines", "")).startswith("blocked"):
        for c in caps:
            if FAMILY_VOICE.search(c):
                out.append(("family_voice", "block", f"family member given a voice line (blocked): {c[:45]}"))
                break
    # a shot that explicitly avoids faces/people (دون إظهار وجوه / اليد فقط) is COMPLIANT —
    # don't flag the face-WORD inside its own negation (Rule #9 false-positive fix, June 14).
    compliant_vis = bool(NO_FACE_MARKER.search(vis))
    if ov.get("face_visibility") == "never" and FACE_VIS.search(vis) and not compliant_vis:
        out.append(("face_visibility", "block", "visual directs visible faces/expressions but face_visibility=never"))
    if ov.get("family_member_visibility") == "never" and FAMILY_VIS.search(vis) and not compliant_vis:
        out.append(("family_visibility", "block", "visual shows family members/children but family_member_visibility=never"))

    if _is_cloud_kitchen(handle):
        if DINE_VENUE.search(allt):
            out.append(("format_dinein", "block", "dine-in venue scene — brand is a delivery-only cloud kitchen"))
        if STOREFRONT.search(allt):
            out.append(("format_storefront", "block", "invented storefront/cart — cloud kitchen has no physical front"))

    if _sector(handle) in FOOD_SECTORS:
        if GYM_FRAME.search(allt):
            out.append(("cross_brand", "block", "gym/fitness SETTING on a food brand — cross-brand frame bleed"))
        elif GYM_SOFT.search(captext):
            out.append(("cross_brand", "warn", "post-workout framing on a food brand — off-positioning"))

    for c in caps:
        if LEGAL_NAME.search(c):
            out.append(("brand_register", "block", f"English legal name/® in an Arabic caption: {c[:45]}"))
            break
    return out


# ── within-BATCH trope repetition (batch-level, not per-post) ──
def device_tag(post):
    """A coarse 'creative device' signature, to catch a batch leaning on ONE trope."""
    c = " ".join(post.get("captions") or [])
    v = " ".join(str(x) for x in (post.get("visual") or {}).get("phone_shoot_card") or [])
    t = c + " " + v
    if re.search(r"يهمس|تهمس|أنا (?:ال|الـ)|تتساءل|يقول لي|أقول لنفسي|ينادي|صوت العلبة|العلبة تهمس|الكيس", t):
        return "personified_object"
    if GYM_FRAME.search(t) or GYM_SOFT.search(t):
        return "gym_scene"
    if FAMILY_VIS.search(t) or re.search(r"العائلة|حول الطاولة|لمة|السفرة", t):
        return "family_table"
    return None


def batch_trope_overconcentration(posts, ceiling=0.30):
    """posts: list of post dicts. Returns violations where one device > ceiling of the batch."""
    from collections import Counter
    n = len(posts) or 1
    tags = Counter(t for t in (device_tag(p) for p in posts) if t)
    cap = int(n * ceiling)
    return [{"device": d, "count": c, "pct": round(c / n * 100, 1)} for d, c in tags.items() if c > cap]
