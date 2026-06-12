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
# G8 SERVICE-CLAIM (June 12 — the consultation lie survived two regens): unverified
# service offerings die unless the corpus carries them — a fake service generates
# real phone calls to the client.
SERVICE_CLAIM = re.compile(
    r"(free\s+(?:\w+\s+)?(consultation|session|trial|delivery|gift)|"
    r"استشار(?:ة|ات)\s*مجاني|توصيل\s*مجاني|اشتراك\s*(?:تجريبي|مجاني)|"
    r"جلسة\s*مجانية|هدية\s*مع\s*كل|ضمان\s*(?:استرجاع|استرداد)|عرض\s*تجريبي)", re.I)
# MOHAMED RULING 2026-06-12 (portal): family-voice lines BLOCKED for all brands
FAMILY_VOICE = re.compile(r"(أمي|امي|أبوي|ابوي|والدتي|والدي|أمك|جدتي قالت لي)\s+(جاب|جابت|قال|قالت|طلب|طلبت)")
FILLER = re.compile(r"(journey|unleash|conquer|roar|new heights|stronger than ever|"
                     r"رحلة(?!\s+لسوق)|أطلق(?:وا)? العنان|نقهر|القمم الجديدة|أقوى من أي وقت|لحظات لا تُنسى)", re.I)
CTA = re.compile(r"[^.!؟\n]*\b(اطلب(?:وا|ها|وه)?|حمّ?ل التطبيق|اطلبيها?)\b[^.!؟\n]*[.!؟]?")
strip_punct = lambda s: re.sub(r"[^\wء-ي\s]", "", s).strip()
dedupe_words = lambda s: re.sub(r"\b(\S+)\s+\1\b", r"\1", s)


def ungrounded(text: str, corpus: str, documented: bool) -> str | None:
    for m in PERSON_AR.finditer(text):
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
