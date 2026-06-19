#!/usr/bin/env python3
"""V5 — prompt built under THE DOCTRINE (June 10, 2026):
English control · Arabic soul · positive-only (bans live in caption_filter.py,
NEVER here) · true few-shot as message pairs · task last.
Returns OpenAI/Anthropic-style messages list, or None when the brand has no DNA v2
(caller falls back to V4 build_prompt)."""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
_FACTS_FILE = BASE / "data" / "occasion_facts.json"
_FACTS = json.loads(_FACTS_FILE.read_text()) if _FACTS_FILE.exists() else {}

POST_TYPES_AR = {
    "أ": "إعلان أو عرض مباشر مع دعوة واضحة للطلب",
    "ب": "سؤال قصير يخلي الجمهور يعلق",
    "ج": "لحظة يومية حقيقية يظهر فيها المنتج طبيعي",
    "د": "تهنئة بالمناسبة بأسلوب الحساب نفسه",
}


def load_dna(brand_en: str) -> dict | None:
    for v in ("v3", "v2"):  # v3 = the join (patterns + traits); v2 fallback
        f = BASE / "logs" / "brand_dna" / f"{brand_en}_dna_{v}.json"
        if f.exists():
            return json.loads(f.read_text())
    return None


# B050 (June 19): DNA-eligibility floor for the feed-cloner (v6) path.
# The backlog spec said ">=20 real captions", but the extractor caps exemplars at 10
# (audited 72 v2/v3 files: every brand has 7-10, max=10) — a literal 20 floor would kill
# the v6 path for 100% of brands (Rule #9: the spec number dies against the data). So the
# MECHANISM is data-driven and the floor is a named, tunable constant. Default 5 cleanly
# separates a real extraction (7-10 exemplars) from a stub/empty/missing one (0). Mohamed
# owns the final number — staged to his portal to confirm/override (don't re-litigate here).
MIN_DNA_EXEMPLARS = 5


def _ruled_floor() -> int:
    """Mohamed owns the floor (Rule #7: his tap must land somewhere). If he has ruled a
    `dna_exemplar_floor` on the live-rulings file, the gate reads it; else the default."""
    try:
        r = json.loads((BASE / "data" / "mohamed_rulings_live.json").read_text())
        v = r.get("dna_exemplar_floor")
        v = v.get("value") if isinstance(v, dict) else v
        return int(v) if v is not None else MIN_DNA_EXEMPLARS
    except Exception:
        return MIN_DNA_EXEMPLARS


def dna_eligibility(brand_en: str, min_exemplars: int | None = None) -> dict:
    """Single source of truth for whether a brand may use the feed-cloner (v6) path.
    Returns {eligible, exemplars, reason}. Eligible ⇔ DNA v2/v3 exists AND carries
    >= min_exemplars real feed captions (default = Mohamed's ruled floor, else 5). The
    reason is logged on fallback so the angle-brain path knows WHY (Rule #6: writer→reader)."""
    if min_exemplars is None:
        min_exemplars = _ruled_floor()
    dna = load_dna(brand_en)
    if dna is None:
        return {"eligible": False, "exemplars": 0,
                "reason": f"no_dna_file:{brand_en}"}
    n = len(dna.get("exemplars") or [])
    if n < min_exemplars:
        return {"eligible": False, "exemplars": n,
                "reason": f"thin_dna:{n}<{min_exemplars}"}
    return {"eligible": True, "exemplars": n, "reason": "ok"}


def build_messages_v5(brief: dict, occasion_ar: str, max_chars: int) -> list | None:
    dna = load_dna(brief.get("brand_en", ""))
    if not dna:
        return None
    brand = brief["brand"]
    emoji = dna.get("emoji_style", {})
    length = dna.get("length_profile", {})
    always = "\n".join(f"- {a}" for a in dna.get("always_does_en", []))
    openers = "، ".join(dna.get("proven_openers_ar", [])[:5])
    sigs = "، ".join(dna.get("signature_phrases_ar", [])[:5])

    # ENGLISH CONTROL — the model obeys best here (doctrine §1)
    system = f"""You are the real Instagram admin of {brand}, a Saudi brand. You have run this \
account for years. You write tomorrow's actual post — never ad-copy, never campaign poetry.

VOICE DNA (from the brand's real feed):
- Sound: {dna.get('voice_summary_en','')}
- Dialect: {dna.get('dialect','saudi')} — natural Saudi Arabic only
- Tone: {', '.join(dna.get('tone', []))}
- Emoji: {emoji.get('density','medium')} density, favorites {', '.join(emoji.get('favorites', [])[:6])}
- Length: FREE — match this feed's natural range (study the examples); typical ~{length.get('typical_chars', 80)} chars but real posts vary, never pad
- This feed always:
{always}

PROVEN OPENERS from this account (use one to open at least one option): {openers}
SIGNATURE PHRASES/TAGS: {sigs}

HARD RULES:
- Religious/national occasions are honored, never positioned as waiting for the product.
- Never reference beds, removal of clothing/hijab, or exploit fear/weakness.
- Every line must pass: "if posted on {brand}'s account tomorrow, followers would assume the brand wrote it."

OUTPUT FORMAT (exact — a parser reads it):
One line PER REQUESTED TYPE in the final task, each starting with its Arabic type letter + period, then the caption directly:
أ. ...
ب. ...
(etc — exactly the letters the task lists)
Then one line with the hashtags. Then the final line: الأفضل: <the strongest caption text>"""

    # TRUE FEW-SHOT — the model becomes the admin (doctrine §3)
    # GOLD first: founder-rated captions (>=4/5) outrank engagement-ranked exemplars
    gold_f = BASE / "logs" / "brand_gold" / f"{brief.get('brand_en','')}_gold.json"
    _all_gold = json.loads(gold_f.read_text()) if gold_f.exists() else []
    # ARMOR PORT step 3 (June 12): rotate gold by occasion-hash — tail-slice fed every
    # request the same 3 lines (the client-path top-6 staleness bug, main-API edition)
    if len(_all_gold) > 3:
        _h = sum(ord(c) for c in str(brief.get("occasion", "")))
        gold = [_all_gold[(_h + j) % len(_all_gold)] for j in range(3)]
    else:
        gold = _all_gold
    msgs = [{"role": "system", "content": system}]
    for g in gold:
        msgs.append({"role": "user", "content": f"اكتب منشور ({g.get('occasion','')}) لحساب {brand}"})
        msgs.append({"role": "assistant", "content": g["caption"]})
    for ex in dna.get("exemplars", [])[: max(3, 6 - len(gold))]:
        pt = ex.get("post_type", "post")
        msgs.append({"role": "user", "content": f"اكتب منشور ({pt}) لحساب {brand}"})
        msgs.append({"role": "assistant", "content": ex.get("caption", "")})

    # THE TASK — last (doctrine §5), Arabic data, positive-only (doctrine §2)
    types = dict(POST_TYPES_AR)
    pats = [str(p).lower() for p in dna.get("patterns_used", [])]
    if any("story" in p or "قصة" in p for p in pats):
        types["هـ"] = "قصة قصيرة (3-5 جمل): مشهد → إحساس → المنتج يحل → دعوة خفيفة — بأسلوب الحساب"
    types_block = "\n".join(f"{k}. {v}" for k, v in types.items())
    occ_facts = _FACTS.get(brief.get("occasion", ""), {})
    facts_block = ""
    if occ_facts:
        pts = (occ_facts.get("themes", [])[:4] + occ_facts.get("dos", [])[:3])
        if pts:
            facts_block = "OCCASION FACTS (real behaviors — ground the captions in these, never quote them):\n" + "\n".join(f"- {p}" for p in pts) + "\n\n"
    msgs.append({"role": "user", "content": f"""{facts_block}المناسبة: {occasion_ar}
المنتج: {brief.get('product', 'المنتج')}
الهاشتاقات: {brief.get('hashtags', '')}

اكتب منشوراً لكل نوع من الأنواع التالية لحساب {brand}:
{types_block}

بنفس صوت الحساب اللي كتبته فوق بالضبط — قصير، حي، طبيعي.
التزم بشكل الإخراج المحدد، وفي آخر سطر: الأفضل:"""})
    return msgs
