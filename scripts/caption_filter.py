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


def cultural_check(caption: str) -> tuple[bool, list[str]]:
    cap = caption or ""
    hits = [v for term, v in _CULTURAL_TERMS.items() if term in cap]
    return (len(hits) == 0, hits)
