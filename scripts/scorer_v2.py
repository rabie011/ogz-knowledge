#!/usr/bin/env python3
"""Scorer v2 — the DNA-aligned judge (June 11, 2026).
Replaces _auto_score, which rewarded the em-dash (+5), the poetry openers (+15)
and epigram length (+20) — audit showed 46% of its picks failed the brand filter
while a clean option sat buried in the same set (240/240 cases).

Doctrine: a caption scores high when it fits THE BRAND'S OWN FEED —
its openers, its signatures, its lengths — and passes the code filter.
No structural bonuses. Ever. When founder GOLD ratings exist, they dominate upstream.
"""
import json
import re
from pathlib import Path

from caption_filter import check

BASE = Path(__file__).parent.parent
_DNA_CACHE: dict = {}

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF❤️]"
)


def _dna(brand_en: str) -> dict | None:
    if brand_en in _DNA_CACHE:
        return _DNA_CACHE[brand_en]
    for v in ("v3", "v2"):
        f = BASE / "logs" / "brand_dna" / f"{brand_en}_dna_{v}.json"
        if f.exists():
            _DNA_CACHE[brand_en] = json.loads(f.read_text())
            return _DNA_CACHE[brand_en]
    _DNA_CACHE[brand_en] = None
    return None


def score_v2(caption: str, brand_en: str = "", brand_ar: str = "") -> int:
    """0-100. Filter-fail = 0. DNA fit drives everything else."""
    cap = (caption or "").strip()
    passes, _ = check(cap)
    if not passes:
        return 0

    score = 50
    dna = _dna(brand_en)
    if not dna:
        return score  # neutral when we don't know the brand — no fake taste

    # Opens like the brand opens (+20)
    openers = [o.strip() for o in dna.get("proven_openers_ar", []) if o and len(o) < 30]
    if any(cap.startswith(o[:12]) for o in openers if o):
        score += 20

    # Carries a signature phrase/tag (+10)
    sigs = [s for s in dna.get("signature_phrases_ar", []) if s]
    if any(s in cap for s in sigs):
        score += 10

    # Fits the brand's own length band (+15) — band from the feed, not a rule
    typical = int(dna.get("length_profile", {}).get("typical_chars", 80) or 80)
    lo, hi = int(typical * 0.35), int(typical * 2.6)
    if lo <= len(cap) <= hi:
        score += 15

    # Emoji density matches the brand (+5)
    density = dna.get("emoji_style", {}).get("density", "medium")
    has = bool(_EMOJI.search(cap))
    if (density == "none" and not has) or (density != "none" and has):
        score += 5

    return max(0, min(100, score))


def pick_best(options: dict, brand_en: str = "", brand_ar: str = "") -> tuple[str, dict]:
    """Best = highest v2 score among filter-survivors. Returns (best_caption, scores)."""
    scores = {k: score_v2(v, brand_en, brand_ar) for k, v in options.items() if v}
    if not scores:
        return "", {}
    best_key = max(scores, key=scores.get)
    return options[best_key], scores
