#!/usr/bin/env python3
"""V5 — prompt built under THE DOCTRINE (June 10, 2026):
English control · Arabic soul · positive-only (bans live in caption_filter.py,
NEVER here) · true few-shot as message pairs · task last.
Returns OpenAI/Anthropic-style messages list, or None when the brand has no DNA v2
(caller falls back to V4 build_prompt)."""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent

POST_TYPES_AR = {
    "أ": "إعلان أو عرض مباشر مع دعوة واضحة للطلب",
    "ب": "سؤال قصير يخلي الجمهور يعلق",
    "ج": "لحظة يومية حقيقية يظهر فيها المنتج طبيعي",
    "د": "تهنئة بالمناسبة بأسلوب الحساب نفسه",
}


def load_dna(brand_en: str) -> dict | None:
    f = BASE / "logs" / "brand_dna" / f"{brand_en}_dna_v2.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())


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
- Typical length: ~{length.get('typical_chars', 80)} chars, {length.get('style','one-liner')} — shorter wins
- This feed always:
{always}

PROVEN OPENERS from this account (use one to open at least one option): {openers}
SIGNATURE PHRASES/TAGS: {sigs}

HARD RULES:
- Religious/national occasions are honored, never positioned as waiting for the product.
- Never reference beds, removal of clothing/hijab, or exploit fear/weakness.
- Max {max_chars} characters per caption (hashtags excluded).
- Every line must pass: "if posted on {brand}'s account tomorrow, followers would assume the brand wrote it."

OUTPUT FORMAT (exact — a parser reads it):
Four lines, each starting with the type letter + period, then the caption directly:
أ. ...
ب. ...
ج. ...
د. ...
Then one line with the hashtags. Then the final line: الأفضل: <the strongest caption text>"""

    # TRUE FEW-SHOT — the model becomes the admin (doctrine §3)
    msgs = [{"role": "system", "content": system}]
    for ex in dna.get("exemplars", [])[:6]:
        pt = ex.get("post_type", "post")
        msgs.append({"role": "user", "content": f"اكتب منشور ({pt}) لحساب {brand}"})
        msgs.append({"role": "assistant", "content": ex.get("caption", "")})

    # THE TASK — last (doctrine §5), Arabic data, positive-only (doctrine §2)
    types_block = "\n".join(f"{k}. {v}" for k, v in POST_TYPES_AR.items())
    msgs.append({"role": "user", "content": f"""المناسبة: {occasion_ar}
المنتج: {brief.get('product', 'المنتج')}
الهاشتاقات: {brief.get('hashtags', '')}

اكتب 4 منشورات لحساب {brand} — كل واحد نوع مختلف:
{types_block}

بنفس صوت الحساب اللي كتبته فوق بالضبط — قصير، حي، طبيعي.
التزم بشكل الإخراج المحدد، وفي آخر سطر: الأفضل:"""})
    return msgs
