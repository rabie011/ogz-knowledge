#!/usr/bin/env python3
"""TRUTH GUARDS (B032, June 12 — RABIE's first ownership pick).
Every caption-level law born in the 3-client pilot, extracted into ONE module so the
client pipeline (render_client_slot) and the main 41-brand API (api/server v6 path)
enforce the SAME truth. Guards may KILL, never PASS — the AI-judge scar is law.

Laws carried (each born from a real failure, see git log):
  G1 event-claim     — invented gatherings/challenges die (yoga session, تحدي رياضي)
  G2 offer-emotional — عرض/خصم energy on emotional occasions dies
  G3 noun-grounding  — promo names, Latin names, titled PERSONS must trace to corpus;
                       persons allowed only on documented-moment slots
  G4 bilingual filler— journey=رحلة twins die in both tongues
  G5 cta-density     — max ONE order-tail per option set
  G6 dedupe          — «جاهز جاهز» adjacent-word collisions collapse

Usage:
  from truth_guards import apply_guards
  survivors, kills = apply_guards(options, corpus_text, slot={"occasion":..., "documented_moment":...})
"""
import re

EVENT_CLAIM = re.compile(
    # zoom-r7 (June 12): invented PROGRAM/GRADUATION claims — «خريج برنامج البيك الصيفي،
    # شيف معتمد» fabricated a training program + certification + named person. A program
    # is an event-class claim: documented or dead. (معتمد scoped to titles — مشغلين
    # معتمدين/تطبيقات معتمدة are legit operations language.)
    r"(خريج|تخرج|خريجي)\s.{0,25}برنامج|برنامج\s.{0,20}(الصيفي|التدريبي|الشتوي)|"
    r"(شيف|طاهي|مدرب|كوتش)\s+معتمد|شهادة\s.{0,15}(معتمدة|تدريب)|"
    r"(join us|تعالوا|انضم|سجلوا?|احجز مقعد|نلتقي|حضور|invite you|تحدي|challenge)"
    r".{0,60}(session|event|class|workshop|gathering|جلسة|فعالية|ورشة|لقاء|تجمع)|"
    r"(session|class|جلسة|فعالية|ورشة)\s.{0,40}(في|at|@)\s|"
    r"(ابدأ|انضم|join)\s.{0,20}(التحدي|تحدي|challenge)", re.I)
EMOTIONAL = {"ramadan", "eid_al_fitr", "eid_al_adha", "saudi_national_day",
              "saudi_founding_day", "arab_mothers_day"}
OFFER = re.compile(r"عرض|خصم|تخفيض|كود|discount|offer|% ?off|promo", re.I)
PROMO_AR = re.compile(r"(التوأم|كومبو|دبل|ميجا|تريبل)\s+\S+")
LATIN_NAME = re.compile(r"\b([A-Za-z]+\.[A-Za-z]+|[A-Za-z]*\d+[A-Za-z]*|[A-Z]{3,})\b")
PERSON_AR = re.compile(r"(الأمير|الأميرة|الشيخ|الشيخة|الدكتور(?:ة)?|معالي|سمو)\s+\S+(?:\s+بن\s+\S+)*")
# B034 (June 18): EN-led feeds leak named people the Arabic guard never saw — a brand
# captioning "Prince Mohammed" or "HRH ..." in English is the same kill as الأمير in Arabic
# (June 14: named real people / English legal-name was 1 of RABIE's 24 old-mistakes). The
# title must lead a Capitalized name so generic words ("the doctor said") don't trip it.
PERSON_EN = re.compile(
    r"\b(HRH|HH|His Royal Highness|Her Royal Highness|Prince|Princess|"
    r"Sheikh|Sheikha|Sheik|Dr\.?)\s+[A-Z][a-z]+"
    r"(?:\s+(?:bin|bint|al|Al|Al-)?\s*[A-Z][a-z]+)*")
# G8 SERVICE-CLAIM (June 12 — the consultation lie survived two regens): unverified
# service offerings die unless the corpus carries them — a fake service generates
# real phone calls to the client.
SERVICE_CLAIM = re.compile(
    r"(free\s+(?:\w+\s+)?(consultation|session|trial|delivery|gift)|"
    r"استشار(?:ة|ات)\s*(?:مجاني|خبير|مع خبير)|توصيل\s*مجاني|اشتراك\s*(?:تجريبي|مجاني)|"
    r"جلسة\s*مجانية|هدية\s*مع\s*كل|ضمان\s*(?:استرجاع|استرداد)|عرض\s*تجريبي)", re.I)
# MOHAMED RULING 2026-06-12 (portal): family-voice lines BLOCKED for all brands
FAMILY_VOICE = re.compile(r"(أمي|امي|أبوي|ابوي|والدتي|والدي|أمك|جدتي قالت لي)\s+(جاب|جابت|قال|قالت|طلب|طلبت)")
# «رحلة» (journey) is the G4 fitness-filler twin. Bounded (B196 follow-up, 2026-06-22):
#  - (?<!م) so it does NOT fire inside «مرحلة/المرحلة» (phase/stage — legit, was a false kill)
#  - ت-suffix branch so it DOES catch «رحلتك/رحلتنا/رحلتي…» (journey+possessive — was leaking)
#  - the existing «رحلة لسوق» exception (a real trip-to-market) is preserved on the ة branch
FILLER = re.compile(r"(journey|unleash|conquer|roar|new heights|stronger than ever|"
                     r"(?<!م)رحل(?:ة(?!\s+لسوق)|ت(?:ك|نا|ي|ه|ها|كم|كن))|"
                     r"أطلق(?:وا)? العنان|نقهر|القمم الجديدة|أقوى من أي وقت|لحظات لا تُنسى)", re.I)
CTA = re.compile(r"[^.!؟\n]*\b(اطلب(?:وا|ها|وه)?|حمّ?ل التطبيق|اطلبيها?)\b[^.!؟\n]*[.!؟]?")
strip_punct = lambda s: re.sub(r"[^\wء-ي\s]", "", s).strip()
dedupe_words = lambda s: re.sub(r"\b(\S+)\s+\1\b", r"\1", s)


def en_share(text: str) -> float:
    """Fraction of a caption's ALPHABETIC chars that are ASCII (Latin) — the English-share
    signal. A hashtag or an English brand-name alone barely moves it; an English-led body
    pushes it past 0.5. (mcdonalds posts Arabic bodies with Latin hashtags → stays low.)"""
    letters = [c for c in text if c.isalpha()]
    return sum(c.isascii() for c in letters) / max(len(letters), 1)


def is_en_led(*, fingerprint: dict | None = None, exemplars: list | None = None,
              threshold: float = 0.5, majority: int = 3) -> bool:
    """ONE source of truth for "does this brand LEAD in English?" (B043).

    The EN-hook+AR-idea bilingual pattern is a CONFIRMED taste reward (Mohamed: "EN hook +
    AR idea, NOT translation"), and the en_led flag is the door that turns the bilingual
    language-bar on. Before this it was decided two different ways in two files — the exact
    "one boundary leaking through unguarded doors" scar. This is the single boundary both
    doors now call:
      • CLIENT brands carry a fingerprint — l2_voice.dialect == "non_arabic" is the
        confirmed signal (render_client_slot path).
      • MATRIX/exemplar brands have no fingerprint — fall back to the exemplar majority:
        >= `majority` of the first 6 exemplar captions are >`threshold` Latin
        (creative_line path; a lone hashtag is NOT English-led).
    Fingerprint wins when present; exemplars are the fallback; no signal → False (Saudi
    Arabic is the safe default, never English by accident)."""
    if fingerprint:
        return (fingerprint.get("l2_voice") or {}).get("dialect") == "non_arabic"
    if exemplars:
        caps = [(e.get("caption", "") if isinstance(e, dict) else str(e)) for e in exemplars[:6]]
        return sum(en_share(c) > threshold for c in caps) >= majority
    return False


def build_corpus(brand: str, base_dir=None) -> str:
    """B036 (June 13): the grounding corpus for a matrix brand — exemplars + signature
    phrases + proven openers from logs/brand_dna/{brand}_dna_v3.json, plus the brief's
    real hooks/hashtags/context. Until this, the v6 path ran G3 noun-grounding nearly
    BLIND (corpus = brand names + gold only; armor proof counted 34 ungrounded kills).
    Deterministic, on-disk only. Returns '' when nothing exists (guards stay strict)."""
    import json as _j
    from pathlib import Path as _P
    b = _P(base_dir) if base_dir else _P(__file__).parent.parent
    parts = [brand]
    dna_f = b / f"logs/brand_dna/{brand}_dna_v3.json"
    if dna_f.exists():
        d = _j.loads(dna_f.read_text())
        parts += [str(x) for x in (d.get("exemplars") or [])]
        parts += [str(x) for x in (d.get("signature_phrases_ar") or [])]
        parts += [str(x) for x in (d.get("proven_openers_ar") or [])]
    bm = b / "data/brief_matrix.json"
    if bm.exists():
        brief = next((x for x in _j.loads(bm.read_text())
                      if x.get("brand") == brand or x.get("brand_en") == brand), None)
        if brief:
            parts += [str(brief.get(k, "")) for k in
                      ("brand", "brand_en", "brand_context", "product", "real_hooks", "hashtags")]
    return " ".join(p for p in parts if p).lower()


def _norm_ar(s: str) -> str:
    """Normalize Arabic/Latin text for product matching: strip tatweel + diacritics, drop
    punctuation/emoji, collapse whitespace, lowercase. Keeps Arabic + word chars."""
    import re as _re
    s = _re.sub(r"[ـً-ْ]", "", s or "")     # tatweel ـ + harakat (diacritics)
    s = _re.sub(r"[^\wء-ي\s]", " ", s)            # punctuation/emoji → space
    return _re.sub(r"\s+", " ", s).strip().lower()


def product_truth_names(handle: str, base_dir=None) -> list[str]:
    """The client's CONFIRMED product identities, read STRUCTURED from product_truth.json ONLY —
    never a raw substring over every profile json (that was the moments_bank fail-open: a random
    narrative phrase like «عيد أضحى مبارك» passed as a 'product'). Two on-disk shapes are handled:
      • products under d["products"]  (eatjurisha, alnasserjewelry)
      • products as TOP-LEVEL keys beside "_meta"  (albaik)
    Returns the canonical product-name strings ([] if no product_truth on disk)."""
    import json as _j
    from pathlib import Path as _P
    b = _P(base_dir) if base_dir else _P(__file__).parent.parent
    f = b / f"clients/{handle}/profile/product_truth.json"
    if not f.exists():
        return []
    try:
        d = _j.loads(f.read_text())
    except Exception:
        return []
    prods = d.get("products")
    if isinstance(prods, dict):
        return [str(k) for k in prods]
    return [str(k) for k in d if not str(k).startswith("_")]


def product_is_real(handle: str, product: str, base_dir=None):
    """Rule #12 anti-hallucination — SHARED guard, one source for all render doors. A product must exist
    in the brand's REAL data before any FAL spend. Born June 29: the LLM product-picker invented 'تشكن بيك'
    for albaik (0 hits in their real IG / not in product_truth.json) and the cron rendered it via
    --allow-unconfirmed → $0.06 on a product that doesn't exist. Returns (is_real, evidence).

    HARDENED June 30 (DeepSeek+RABIE consult, Rule #19 consult-before-build) after two proven fail-opens:
      (1) step1 did a RAW substring over EVERY profile/*.json — «عيد أضحى مبارك» (a greeting in
          moments_bank.json) passed as a product;
      (2) step2 passed on ANY single ≥4-char token in captions — «أي منتج وهمي» passed for
          alnasserjewelry because the common word «منتج»=product is in its captions.
    The matcher now REQUIRES POSITIVE confirmation: (1) the product is COVERED BY a real name in the
    client's STRUCTURED product_truth.json (query ⊆ a real product's tokens, never the reverse — a fake
    can't ride a real name as a substring), OR (2) — only as a fallback for a brand not yet carrying
    product_truth — a HIGH-OVERLAP phrase in the real captions (full phrase, or ≥2 significant tokens ALL
    present). A single common token is NEVER enough. No positive evidence → refuse (Rule #8/#12)."""
    import glob
    import json as _j
    from pathlib import Path as _P
    b = _P(base_dir) if base_dir else _P(__file__).parent.parent
    p = (product or "").strip()
    if not p:
        return False, "empty product"
    p_norm = _norm_ar(p)
    p_tok = set(t for t in p_norm.split() if t)
    if not p_tok:
        return False, "product has no real tokens after normalization"

    # 1) STRUCTURED product_truth confirmation (the locked, client-confirmed product identities).
    #    Pass ONLY when the query is COVERED BY a real product name — exact, or every query token is a
    #    token of that name (query ⊆ name). NOT name ⊆ query: that would let «سوبر رول وهمي» ride the
    #    real «سوبر رول» (DeepSeek+RABIE ruling, June 30). A lone common word can't line up with a real
    #    product identity, so «أي منتج وهمي» finds no name to cover it here.
    names = product_truth_names(handle, base_dir=b)
    for name in names:
        n_tok = set(t for t in _norm_ar(name).split() if t)
        if not n_tok:
            continue
        if p_norm == _norm_ar(name) or p_tok <= n_tok:
            return True, f"confirmed in product_truth ({name})"

    # If the client HAS a confirmed product_truth, it is the AUTHORITY — no caption back-door. Captions
    # are marketing copy full of greetings/slogans («عيد أضحى مبارك» is a real full-phrase in alnasser's
    # captions but is NOT a product); confirming a product from them re-opens the fail-open. A real product
    # missing here must be ADDED to product_truth (the structured source), not back-doored via copy. Refuse.
    if names:
        return False, (f"'{product}' not covered by any of {handle}'s {len(names)} confirmed "
                       f"product_truth products — refusing (Rule #12; add it to product_truth if real)")

    # 2) CORPUS FALLBACK — a SAFETY NET only for a brand that has NO product_truth yet (un-onboarded).
    raws = sorted(glob.glob(str(b / f"clients/{handle}/raw/instagram/*/posts.jsonl")))
    if not raws:
        # C244 (June 29): no product_truth match + no IG corpus → cannot positively confirm → refuse.
        return False, "not in product_truth + no IG corpus — cannot confirm it's real, refusing (Rule #12)"
    corpus = _norm_ar(" ".join(_j.loads(l).get("caption", "") for l in open(raws[-1]) if l.strip()))
    # POSITIVE phrase-level evidence required — never a single common token (the «منتج» fail-open).
    if len(p_tok) >= 2 and p_norm in corpus:
        return True, "exact product phrase in real captions"
    sig = [t for t in p_tok if len(t) >= 4]               # ≥4 skips brand short-forms (e.g. بيك)
    present = [t for t in sig if t in corpus]
    if len(sig) >= 2 and len(present) == len(sig):
        return True, f"high-overlap product phrase in real captions: {present}"
    return False, (f"not in product_truth and no high-overlap phrase in {handle}'s captions "
                   f"(matched {present or 'none'}) — looks hallucinated, refusing (Rule #12)")


def ungrounded(text: str, corpus: str, documented: bool) -> str | None:
    for m in list(PERSON_AR.finditer(text)) + list(PERSON_EN.finditer(text)):
        if not documented:
            return m.group(0) + " (person in fictional scene)"
        if strip_punct(m.group(0)).lower() not in corpus:
            return m.group(0)
    for m in PROMO_AR.finditer(text):
        if strip_punct(m.group(0)).lower() not in corpus:
            return m.group(0)
    for m in LATIN_NAME.finditer(text):
        t = strip_punct(m.group(0)).lower()
        if t and t not in corpus and t not in {"x", "ksa"} and not t.isdigit():
            return m.group(0)
    return None


def apply_guards(options: list[str], corpus_text: str, slot: dict | None = None,
                  real_hashtags: set | None = None) -> tuple[list[str], list[dict]]:
    """Returns (survivors, kills). Never returns zero survivors if any option existed —
    the least-bad option survives with its kill noted (human eyes decide downstream)."""
    slot = slot or {}
    corpus = (corpus_text or "").lower()
    documented = bool(slot.get("documented_moment"))
    is_emotional = slot.get("occasion") in EMOTIONAL
    tags = real_hashtags or set()
    survivors, kills = [], []
    for o in options:
        o = re.sub(r"#([\wء-ي_]+)", lambda m: m.group(0) if m.group(1) in tags else "", o).strip()
        if not o:
            continue
        reason = None
        if FAMILY_VOICE.search(o):
            reason = ("family_voice_blocked", FAMILY_VOICE.search(o).group(0)[:40])
        elif SERVICE_CLAIM.search(o) and strip_punct(SERVICE_CLAIM.search(o).group(0)).lower() not in corpus:
            reason = ("service_claim", SERVICE_CLAIM.search(o).group(0)[:40])
        elif EVENT_CLAIM.search(o):
            reason = ("event_claim", EVENT_CLAIM.search(o).group(0)[:40])
        elif is_emotional and OFFER.search(o):
            reason = ("offer_on_emotional", OFFER.search(o).group(0))
        elif is_emotional and CTA.search(o) and len(CTA.sub("", o).strip()) > 15:
            # RABIE ruling June 12 (provisional): eid greetings ending in اطلبوا الآن =
            # generic-template smell — strip the CTA sentence, keep the greeting
            o = CTA.sub("", o).strip(" -–—·,،\n")
        elif FILLER.search(o):
            reason = ("bilingual_filler", FILLER.search(o).group(0))
        else:
            bad = ungrounded(o, corpus, documented)
            if bad:
                reason = ("ungrounded_name", bad[:40])
        if reason:
            kills.append({"option": o[:80], "guard": reason[0], "evidence": reason[1]})
            continue
        survivors.append(dedupe_words(o))
    # G5 cta-density: max one order-tail across the set
    kept_cta, final = False, []
    for o in survivors:
        if CTA.search(o):
            if kept_cta:
                stripped = CTA.sub("", o).strip(" -–—·,،\n")
                o = stripped if len(stripped) > 15 else o
            kept_cta = True
        final.append(o)
    if not final and options:
        final = [dedupe_words(options[0])]
        kills.append({"option": options[0][:80], "guard": "ALL_KILLED_kept_least_bad",
                       "evidence": "human eyes must judge"})
    return final, kills


if __name__ == "__main__":
    # unit gauntlet — every law against its birth case
    corpus = "البيك كرسبي التوأم كرسبي بيك دبل القرمشة بروست"
    cases = [
        ("Join us in the park for a yoga session!", "event_claim"),
        ("ابدأ التحدي الرياضي مع لياقتي", "event_claim"),
        ("عرض خاص لليوم الوطني!", "offer_on_emotional"),
        ("اللياقة ليست مجرد تمرين بل رحلة", "bilingual_filler"),
        ("بحضور الأمير سعود بن عبدالله بن جلوي", "ungrounded_name"),
        ("تابعونا على Liaqti.tu", "ungrounded_name"),
        ("Get your free fitness consultation on Snapchat!", "service_claim"),
        ("أمي جابت البيك اليوم", "family_voice_blocked"),
        ("جربوا وجبة MegaCrunch77 الجديدة!", "ungrounded_name"),  # B003 fixture: invented product
        ("عيدكم غير مع التوأم كرسبي بيك! دبل القرمشة", None),  # corpus-real survives
    ]
    fails = 0
    for text, expect in cases:
        surv, kills = apply_guards([text], corpus, {"occasion": "saudi_national_day"})
        got = kills[0]["guard"] if kills and kills[0]["guard"] != "ALL_KILLED_kept_least_bad" else None
        ok = got == expect
        fails += not ok
        print(f"  {'✅' if ok else '❌'} [{got or 'survived'}] {text[:50]}")
    print(f"\n{'✅ ALL GUARDS HOLD' if not fails else f'❌ {fails} guard failures'}")
    raise SystemExit(1 if fails else 0)
