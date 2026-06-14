#!/usr/bin/env python3
"""OCCASION ALIGNMENT — the single source (Rule #6) for "is this caption confirmed with its
occasion?" Mohamed (2026-06-14): "make sure the post is confirmed with occasion and everything
is aligned." Root cause it serves: year_map seeded DAILY slots with occasion-anchored hooks, so
captions invented Eid/Ramadan/National-Day on plain daily slots. This module:
  • detects occasion signals BOUNDARY-SAFE (عيد inside سعيد/يعيدني is NOT Eid — Rule #9 scar);
  • rules a post aligned or not (daily → no occasion words; occasion slot → must match, no other);
  • lists the calendar occasions year_map must keep OUT of the daily evergreen pool.
Imported by render_client_slot (gate+regen), pre_ship_gate (hard block), post_audit (test).
"""
import re

# clitic-aware boundaries: a ROOT matches only as a whole word (optionally with a Saudi clitic
# prefix و/ف/ب/ل/ال and a pronoun suffix) — never as a substring inside another word.
_PRE = r"(?<![ء-ي])(?:وال|فال|بال|لل|بال|ال|[وفبل])?"
_SUF = r"(?:كم|نا|هم|ها|ين|ية|ه)?(?![ء-ي])"

OCC_ROOTS = {
    "eid":          ["عيد", "أضحى", "عيدية"],
    "ramadan":      ["رمضان", "سحور", "إفطار", "صيام", "صائم", "تراويح", "قرقيعان", "مسحراتي"],
    "founding_day": ["التأسيس"],
    "hajj":         ["الحج", "حجاج", "عرفة", "الحجيج", "مزدلفة"],
}
OCC_PHRASES = {
    "eid":          ["عساكم من عواده", "كل عام وانتم بخير", "كل عام وأنتم", "تقبل الله", "عيد الفطر", "عيد الأضحى"],
    "ramadan":      ["شهر رمضان", "تقبل الله صيامكم", "ليالي رمضان"],
    "national_day": ["اليوم الوطني", "يوم الوطن", "يومنا الوطني", "اليوم_الوطني", "هلا بالسعودية", "ليوم الوطن"],
    "founding_day": ["يوم التأسيس", "يوم_التأسيس"],
    "mothers_day":  ["يوم الأم", "عيد الأم", "يوم_الأم"],
    "hajj":         ["ضيوف الرحمن", "يوم عرفة"],
}
OCC_RX = {k: [re.compile(_PRE + re.escape(r) + _SUF) for r in roots] for k, roots in OCC_ROOTS.items()}
ALL_KEYS = set(list(OCC_ROOTS) + list(OCC_PHRASES))

# year-map occasion slugs → our keys
SLUG2KEY = {"eid_al_fitr": "eid", "eid_al_adha": "eid", "ramadan": "ramadan",
            "saudi_national_day": "national_day", "saudi_founding_day": "founding_day",
            "arab_mothers_day": "mothers_day", "hajj_season": "hajj"}
DAILY_TYPES = {"daily", "evergreen", "ramadan_evergreen", None, ""}

# moment.occasion values that are CALENDAR occasions — year_map must keep these OUT of the
# daily/evergreen theme pool (a daily post must never inherit an Eid/Ramadan/National-Day hook).
CALENDAR_OCC_MOMENTS = {
    "eid", "عيد", "عيد الفطر", "عيد الأضحى", "احتفال بالعيد", "Eid Celebration",
    "ramadan", "الإفطار", "فطور", "ضيافة رمضان", "ramadan_service", "Ramadan Hosting",
    "national_day", "national_day_event", "founding_day", "summer", "winter",
    "earth_hour", "ساعة الأرض", "call to prayer", "taheed", "التأسيس",
}


def occ_hits(text: str) -> set:
    """Occasion keys present in text — boundary-safe (phrases as substring, roots clitic-bounded)."""
    keys = set()
    for k in ALL_KEYS:
        if any(p in text for p in OCC_PHRASES.get(k, [])) or any(rx.search(text) for rx in OCC_RX.get(k, [])):
            keys.add(k)
    return keys


def is_daily(slot: dict) -> bool:
    return (slot.get("type") in DAILY_TYPES) and not slot.get("occasion")


def slot_occ_key(slot: dict):
    occ = slot.get("occasion")
    return SLUG2KEY.get(occ) if occ else None


def caption_misaligned(slot: dict, caption: str):
    """Return a reason string if THIS caption is occasion-misaligned, else None.
       daily slot   → any occasion word is a fabrication.
       occasion slot→ a DIFFERENT occasion's words are a mismatch."""
    hits = occ_hits(caption)
    if not hits:
        return None
    if is_daily(slot):
        return f"daily slot, caption invents occasion {sorted(hits)}"
    key = slot_occ_key(slot)
    wrong = hits - {key} if key else hits
    if wrong:
        return f"slot occasion '{key}', caption says {sorted(wrong)}"
    return None
