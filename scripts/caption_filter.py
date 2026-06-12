#!/usr/bin/env python3
"""The ban side of THE DOCTRINE (June 10): prompts stay positive-only —
all forbidden patterns live HERE, in code, after generation (pink-elephant safe).
Any caption matching a pattern is rejected; the collector regenerates or drops it."""
import re

# The dash-flip aphorism family (the documented AI-tell that killed V1-V3)
_DASH_FLIP = re.compile(r"—\s*(اللي|حتى|قبل\s*ما|قبل\s*لا|هو\s*اللي)")
_FLIP_TAIL = re.compile(r"(اللي|حتى)\s+\S+\s+(قبل|بعد)\s*ما\s")
# Philosophical openers
_PHILO_OPEN = re.compile(r"^\s*[\"«']?\s*(لمّا|لما|إذا|تخيل|تخيّل)\b")
# The cliché list (verbatim strings, checked literally)
_CLICHES = [
    "أكبر من الكلام", "ما ينتهي", "يحكي حكاية", "حكاية أجداد", "الطعم يقول",
    "يكمّل اللحظة", "يكمل اللحظة", "الشوق ل", "أكبر من أي", "ما يحتاج تعريف",
    "يقول اللي ما", "تقول اللي ما",
]
# The metaphor ad-trap (June 11, founder): brand-as-symbol abstractions read as TV-ad
# voiceover. "X جسر الفرح" / "رمز الأصالة" / "روح اللحظة".
_AD_METAPHOR = [
    "جسر الفرح", "جسر ", "رمز الأصالة", "رمز ", "روح اللحظة", "روح المكان",
    "عنوان ", "نكهة الوطن", "طعم الانتماء", "لغة الحب",
]


def check(caption: str) -> tuple[bool, list[str]]:
    """Returns (passes, reasons). Empty/short captions fail silently."""
    cap = (caption or "").strip()
    if len(cap) < 6:
        return False, ["empty"]
    reasons = []
    if _DASH_FLIP.search(cap):
        reasons.append("dash_flip")
    if _FLIP_TAIL.search(cap):
        reasons.append("flip_tail")
    if _PHILO_OPEN.search(cap):
        reasons.append("philosophical_opener")
    for c in _CLICHES:
        if c in cap:
            reasons.append(f"cliche:{c}")
            break
    for a in _AD_METAPHOR:
        if a in cap:
            reasons.append(f"ad_metaphor:{a.strip()}")
            break
    cult_ok, cult_hits = cultural_check(cap)
    if not cult_ok:
        reasons.extend(f"cultural:{h}" for h in cult_hits)
    return (len(reasons) == 0), reasons


def filter_options(options: dict) -> tuple[dict, dict]:
    """Split options into (survivors, dropped{key: reasons})."""
    ok, dropped = {}, {}
    for k, v in options.items():
        passes, reasons = check(v)
        if passes:
            ok[k] = v
        else:
            dropped[k] = reasons
    return ok, dropped

# ── Cultural gate (P2, June 11): the 80-field moat, connected ──────────────────
import json as _json
from pathlib import Path as _Path
_GATE_F = _Path(__file__).parent.parent / "data" / "cultural_gate.json"
_GATE = _json.loads(_GATE_F.read_text()) if _GATE_F.exists() else {"hard_block": []}
# Arabic surface terms that signal a hard-block topic IN TEXT (visual entries are
# enforced at the render stage, not here). Conservative — text captions rarely
# describe these, but red-line topics must never slip through.
_CULTURAL_TERMS = {
    "خمر": "alcohol", "بيرة": "alcohol", "نبيذ": "alcohol",
    "قمار": "gambling", "رهان": "gambling",
    "تدخين": "smoking_family_context", "سيجارة": "smoking_family_context",
    "عُري": "immodest", "عاري": "immodest",
}


# Brand tokens — the dua rule needs to know what a "brand mention" is
_BRAND_TOKENS = ("البيك", "جريشة", "جريّشة", "جريش", "ماي فتنس", "myfitness")
_ALLAH_TOKENS = ("اللهم", "الله ", "يا رب")
_CTA_WORDS = ("اطلب", "اطلبوا", "احجز", "عرضنا", "عرض ", "خصم", "مجانًا", "مجانا", "الآن من")
_RELIGIOUS_EMOTIONAL_OCC = ("ramadan", "eid", "arafah", "hajj", "founding", "national", "mothers")
_TEXT_OCCASION = ("رمضان", "عيد", "التأسيس", "اليوم الوطني", "يوم الأم")


def cultural_check(caption: str, occasion: str = "") -> tuple[bool, list[str]]:
    """EXECUTES the gate (June 12 zoom-out: _GATE was loaded and never read — a dua
    with a brand name inside it reached v5 while the exact hard_block sat on disk).
    Deterministic text rules, severity=kill:
      1. red-line topic terms (alcohol/gambling/smoking/immodest)
      2. Allah's name and a brand name NEVER share a caption (the gate's
         prayer_as_commercial_backdrop hard_block, finally enforced)
      3. CTA words on a religious/emotional occasion — keyed to the occasion arg
         AND to what the TEXT itself implies, so slot-laundering can't bypass it"""
    cap = caption or ""
    hits = [v for term, v in _CULTURAL_TERMS.items() if term in cap]
    if any(a in cap for a in _ALLAH_TOKENS) and any(b in cap for b in _BRAND_TOKENS):
        hits.append("prayer_as_commercial_backdrop")
    occ = (occasion or "").lower()
    text_implies = any(o in cap for o in _TEXT_OCCASION)
    if any(w in cap for w in _CTA_WORDS) and (
            any(o in occ for o in _RELIGIOUS_EMOTIONAL_OCC) or text_implies):
        hits.append("cta_on_religious_or_emotional_day")
    return (len(hits) == 0, hits)


# Offer-claims (law: no_invented_facts + prices_off_until_truth, June 12) —
# a public promise of a deal/price is a FACT claim; blocked unless the client's
# truth confirms a live offer. Product-noun entailment waits for keys.
_OFFER_WORDS = ("عرض ", "عروضنا", "خصم", "تخفيض", "مجانًا", "مجانا", "اشترِ", "بسعر", "ريال")


def offer_check(caption: str, has_confirmed_offer: bool = False) -> tuple[bool, list[str]]:
    cap = caption or ""
    if has_confirmed_offer:
        return True, []
    hits = ["invented_offer_or_price"] if any(w in cap for w in _OFFER_WORDS) else []
    return (len(hits) == 0, hits)
