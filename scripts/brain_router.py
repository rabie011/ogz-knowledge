#!/usr/bin/env python3
"""brain_router — the shared CD-brain routing module (B035, June 19 2026).

Extracted verbatim from render_client_slot.py so BOTH the render stage AND the
angle stage (build_angle_cards.py — B041) can route on the SAME logic without
the angle script importing the heavy render module (caption_filter, blackout_gate,
post_unit, urllib …). One source of truth for: which brain a slot routes to, and
the brain's full methodology body.

Root-hunt that birthed this (2026-06-14, see brain_method): the angle pen never
received the methodology BODY — only the YAML front-matter — so every brain
collapsed to the generic 'concrete scene' prompt → the brand-mean formula → the
#1 repetition cause. Sharing this module is the prerequisite for routing the full
methodologies into build_angle_cards (B041).
"""
import re
from pathlib import Path

BASE = Path(__file__).parent.parent

BRAIN_FILES = {"firaasa": "cd_01_firaasa_architect.md", "metaphor": "cd_02_metaphor_architect.md",
                "authenticity": "cd_03_authenticity_detective.md", "heritage": "cd_04_heritage_decoder.md",
                "paradox": "cd_05_paradox_hunter.md"}


def route_brain(slot: dict, alt: int = 0) -> str:
    """Deterministic CD-brain routing per slot type (Phase B, June 11 — Floward proved
    the full methodologies beat the salvaged one-liners). alt flips the pair for variety."""
    occ = slot.get("occasion") or ""
    if occ in ("saudi_national_day", "saudi_founding_day"):
        return "heritage"  # NOTE: make_angle falls back to firaasa when no root material — guard below
    if occ in ("ramadan", "eid_al_fitr", "eid_al_adha", "arab_mothers_day", "hajj_season"):
        return ("firaasa", "authenticity")[alt % 2]
    if slot.get("type") == "competitor_reference":
        return "paradox"
    # daily slots: spread across ALL FOUR non-occasion brains (June 14 — the *-11 batch came
    # out 100% paradox because the old 2-brain date-PARITY keyed identical for every date
    # ending in 1; a batch using one brain isn't using the 5-CD-brain range). Digit-sum%4
    # rotates brains even across same-parity / adjacent dates.
    DAILY = ("metaphor", "paradox", "firaasa", "authenticity")
    seed = sum(int(ch) for ch in str(slot.get("date", "")) if ch.isdigit()) or alt
    return DAILY[seed % 4]


def brain_method(brain: str) -> str:
    """The CD brain's actual METHODOLOGY BODY — not the YAML front-matter.
    (Root-hunt 2026-06-14: the old [:2800] returned ONLY the front-matter — the front-matter
    ends at char ~3395 — so the creative METHOD never reached the angle pen; every brain fell
    back to the generic 'concrete scene' prompt → captions collapsed to the brand-mean formula.
    THE #1 repetition cause. Now: skip the front-matter, inject the method body.)"""
    f = BASE / "20_cd_brains" / BRAIN_FILES[brain]
    if not f.exists():
        return ""
    t = f.read_text()
    marks = [m.start() for m in re.finditer(r"^---\s*$", t, re.M)]
    body = t[marks[1] + 3:] if len(marks) >= 2 else t   # content AFTER the YAML front-matter
    return body.strip()[:3200]   # the core methodology that makes this brain creative + distinct
