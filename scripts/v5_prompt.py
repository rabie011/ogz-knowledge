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
    gold = json.loads(gold_f.read_text())[-3:] if gold_f.exists() else []
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
