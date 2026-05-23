#!/usr/bin/env python3
"""
cluster_register_tone.py
Normalize freeform register (104 unique) and tone (211 unique) values
in all 474 observations into canonical taxonomies.

Canonical Registers (10):
  casual          — everyday relaxed, informal conversational
  formal          — structured MSA, proper, classical
  aspirational    — premium/luxury positioning
  promotional     — commercial offers, pricing, CTAs dominant
  educational     — informative, review-style, instructional
  visual_only     — no significant text, image/visual narrative only
  playful         — gamified, quiz, challenge, humour-forward
  celebratory     — occasion-specific festive/festive hybrid
  patriotic       — national pride, allegiance, prayerful
  professional    — corporate, brand identity, corporate comms

Canonical Tones (12):
  warm            — warm, welcoming, nurturing, caring, generous
  playful         — playful, fun, humorous, witty, teasing, cheeky
  proud           — proud, confident, bold, authoritative
  celebratory     — celebratory, festive, joyful
  excited         — excited, energetic, enthusiastic, anticipatory
  inviting        — inviting, appetizing, enticing, indulgent
  informative     — informative, educational, helpful, instructional
  aspirational    — aspirational, elegant, sophisticated, refined
  nostalgic       — nostalgic, heritage, reflective, bittersweet
  patriotic       — patriotic, spiritual, reverent, solemn, ceremonial
  storytelling    — storytelling, documentary, cinematic, poetic, atmospheric
  transactional   — transactional, promotional, urgent, direct
"""
import json, re
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

# ── Canonical register mapping ───────────────────────────────────────────────
# Order matters: first match wins. More specific patterns first.
REGISTER_RULES = [
    # visual_only — must come before casual/formal to catch "visual" variants
    ("visual_only",   lambda v: any(k in v for k in ("visual only", "visual_only", "visual-only",
                                                      "visual narrative", "visual service", "visual atmosphere",
                                                      "visual teaser", "visual food", "visual invitation",
                                                      "visual architecture", "visual welcome", "visual menu",
                                                      "visual storytelling", "candid moment", "atmospheric",
                                                      "architectural narrative", "event showcase",
                                                      "heritage showcase", "service visual"))),
    # patriotic
    ("patriotic",     lambda v: "patriot" in v or "allegiance" in v or "prayerful" in v),
    # celebratory (hybrid festive/formal etc.)
    ("celebratory",   lambda v: any(k in v for k in ("celebrat", "festive", "ramadan occasion",
                                                      "promotional ramadan", "ramadan"))),
    # formal — pure formal variants
    ("formal",        lambda v: v.startswith("formal") or v in ("formal", "formal classical",
                                                                  "formal corporate", "formal/proud",
                                                                  "formal/awareness", "celebratory/formal",
                                                                  "corporate")),
    # aspirational / premium
    ("aspirational",  lambda v: any(k in v for k in ("aspirational", "premium", "luxe", "discovery/curator",
                                                      "achievement announcement"))),
    # promotional / commercial
    ("promotional",   lambda v: any(k in v for k in ("promot", "commercial", "announcement",
                                                      "offer", "functional"))),
    # educational / informative
    ("educational",   lambda v: any(k in v for k in ("educat", "informativ", "review", "brief info",
                                                      "brief caption", "awareness", "personal"))),
    # playful / quiz / challenge
    ("playful",       lambda v: any(k in v for k in ("playful", "quiz", "challenge", "puzzle",
                                                      "humour", "humor", "humorous", "teaser",
                                                      "engagement", "youth", "witty"))),
    # professional / brand
    ("professional",  lambda v: any(k in v for k in ("professional", "brand", "corporate",
                                                      "brand professional", "brand-focused",
                                                      "brand identity", "brand_identity",
                                                      "conversational_friendly", "authentic",
                                                      "warm"))),
    # casual — catch-all informal
    ("casual",        lambda v: True),  # default fallback
]

# ── Canonical tone mapping ────────────────────────────────────────────────────
TONE_RULES = [
    # patriotic / spiritual (specific — before proud/celebratory)
    ("patriotic",     lambda v: any(k in v for k in ("patriot", "spiritual", "solemn", "reverent",
                                                      "prayerful", "condolence", "prayer",
                                                      "quranic", "royal", "health wishes",
                                                      "responsible", "respectful", "graceful",
                                                      "dignified", "ceremonial", "majestic"))),
    # storytelling / cinematic / poetic
    ("storytelling",  lambda v: any(k in v for k in ("storytell", "documentary", "cinematic",
                                                      "poetic", "atmospheric", "dramatic",
                                                      "reflective", "bittersweet", "artistic",
                                                      "relatable", "emotional", "empathetic",
                                                      "genuine", "authentic", "natural",
                                                      "nurturing", "caring", "gentle",
                                                      "reassuring", "refined", "graceful",
                                                      "mysterious", "heritage, cinematic",
                                                      "heritage, atmospheric", "sensory, meditative",
                                                      "occasion-driven"))),
    # nostalgic / heritage
    ("nostalgic",     lambda v: any(k in v for k in ("nostalgic", "nostalgia", "heritage",
                                                      "rooted", "traditional", "bittersweet"))),
    # transactional / promotional / urgent
    ("transactional", lambda v: any(k in v for k in ("transactional", "promotional", "urgent",
                                                      "matter-of-fact", "direct product push",
                                                      "direct command", "order the toast",
                                                      "commercial", "direct"))),
    # informative / educational
    ("informative",   lambda v: any(k in v for k in ("informative", "educat", "instruct",
                                                      "detail", "review", "recommendation with",
                                                      "helpful", "practical", "concise",
                                                      "brief positive", "announcement",
                                                      "discovery_focused", "discovery-focused",
                                                      "neutral discovery"))),
    # aspirational / elegant / sophisticated
    ("aspirational",  lambda v: any(k in v for k in ("aspirational", "elegant", "sophistic",
                                                      "refined", "premium", "luxurious",
                                                      "intimate, luxurious", "contemporary",
                                                      "minimalist", "grand, inviting",
                                                      "professional, premium", "professional_showcase",
                                                      "professional_premium", "aspirational_elegant",
                                                      "aspirational_premium", "aspirational_growth",
                                                      "aspirational, modern", "confident, premium",
                                                      "indulgent, premium"))),
    # excited / energetic / enthusiastic / anticipatory
    ("excited",       lambda v: any(k in v for k in ("excit", "energet", "enthusias", "anticipat",
                                                      "hype", "buzz", "launch", "opening",
                                                      "arrival", "coming", "we're closer",
                                                      "positive_energetic", "promotional_energetic",
                                                      "energetic_positive", "energetic_appetitive",
                                                      "excited_launch", "excited_and_urgent"))),
    # inviting / appetizing / enticing / indulgent
    ("inviting",      lambda v: any(k in v for k in ("invit", "appetiz", "appeti", "entic",
                                                      "indulg", "sensory", "fresh",
                                                      "appetizing_inviting", "appetizing_promotional",
                                                      "warm_approachable_indulgent",
                                                      "inviting_celebratory", "inviting_community",
                                                      "inviting, fresh", "grand, inviting",
                                                      "generous, inviting", "proud, inviting",
                                                      "warm, nocturnal, inviting"))),
    # celebratory / joyful / festive / abundant
    ("celebratory",   lambda v: any(k in v for k in ("celebrat", "festive", "joyful", "joyous",
                                                      "abundant", "warm, generous, joyful",
                                                      "warm, celebratory", "community celebratory",
                                                      "celebratory_warm", "celebratory_welcoming",
                                                      "playful_celebratory", "inviting_celebratory",
                                                      "celebratory, value-focused", "celebratory, proud",
                                                      "grand, celebratory", "playful_festive",
                                                      "abundant, festive", "abundant, ceremonial",
                                                      "warm_reverent_festive"))),
    # proud / confident / bold / authoritative / powerful
    ("proud",         lambda v: any(k in v for k in ("proud", "confident", "bold", "authoritative",
                                                      "powerful", "proud_affectionate", "proud, warm",
                                                      "proud, prestigious", "proud, authoritative",
                                                      "proud, inviting", "excited, proud",
                                                      "caring, empowering", "bold, playful",
                                                      "bold provocation", "competitive"))),
    # humorous → playful
    ("playful",       lambda v: any(k in v for k in ("playful", "humorous", "humor", "humour",
                                                      "witty", "teas", "cheeky", "ironic",
                                                      "gym culture humor", "quirky", "fun",
                                                      "playful/", "playful,", "playful_",
                                                      "calling out", "workplace humor",
                                                      "challenge", "curious", "curiosity",
                                                      "question", "quiz", "counting",
                                                      "anticipatory, playful", "friendly",
                                                      "playful, vibrant", "playful, summer",
                                                      "playful and aspirational", "playful_aspirational",
                                                      "playful_promotional", "playful_inviting",
                                                      "playful/engaging", "playful/energetic",
                                                      "playful, warm", "playful, cheeky",
                                                      "warm, nostalgic, playful", "mysterious",
                                                      "relatable", "conversational", "relaxed",
                                                      "community", "family-friendly",
                                                      "inclusive", "globally-minded"))),
    # warm — catch remaining warm variants
    ("warm",          lambda v: any(k in v for k in ("warm", "welcom", "caring", "nurtur",
                                                      "empath", "sincere", "personal",
                                                      "warm_pride_community", "warm_and_inviting",
                                                      "warm, direct", "warm, welcoming",
                                                      "warm, respectful", "warm, sophisticated",
                                                      "formal, hospitable", "ceremonial, warm",
                                                      "dignified, welcoming", "inclusive"))),
    # informative fallback
    ("informative",   lambda v: True),  # fallback
]


def match_register(raw: str) -> str:
    v = raw.lower().strip()
    for canonical, rule in REGISTER_RULES:
        if rule(v):
            return canonical
    return "casual"


def match_tone(raw: str) -> str:
    v = raw.lower().strip()
    for canonical, rule in TONE_RULES:
        if rule(v):
            return canonical
    return "informative"


def main():
    reg_before = Counter()
    reg_after  = Counter()
    tone_before = Counter()
    tone_after  = Counter()
    reg_mapping  = defaultdict(lambda: defaultdict(int))  # raw → canonical → count
    tone_mapping = defaultdict(lambda: defaultdict(int))

    updated_files = 0
    total_files   = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            text = obs_file.read_text()
            data = json.loads(text)
        except Exception:
            continue

        total_files += 1
        changed = False
        vo = data.get("voice_observations", {})

        raw_reg = vo.get("register")
        if raw_reg and isinstance(raw_reg, str):
            canonical_reg = match_register(raw_reg)
            reg_before[raw_reg] += 1
            reg_mapping[raw_reg][canonical_reg] += 1
            if raw_reg != canonical_reg:
                vo["register"] = canonical_reg
                data["voice_observations"] = vo
                changed = True
            reg_after[canonical_reg] += 1

        raw_tone = vo.get("tone")
        if raw_tone and isinstance(raw_tone, str):
            canonical_tone = match_tone(raw_tone)
            tone_before[raw_tone] += 1
            tone_mapping[raw_tone][canonical_tone] += 1
            if raw_tone != canonical_tone:
                vo["tone"] = canonical_tone
                data["voice_observations"] = vo
                changed = True
            tone_after[canonical_tone] += 1

        if changed:
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            updated_files += 1

    # ── Output mapping log ───────────────────────────────────────────────────
    LOGS.mkdir(exist_ok=True)

    mapping_log = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_obs_scanned": total_files,
        "obs_updated": updated_files,
        "register_taxonomy": {
            "canonical_values": ["casual", "formal", "aspirational", "promotional",
                                 "educational", "visual_only", "playful", "celebratory",
                                 "patriotic", "professional"],
            "before_unique_count": len(reg_before),
            "after_distribution": dict(sorted(reg_after.items(), key=lambda x: -x[1])),
            "mappings": {
                raw: dict(targets)
                for raw, targets in sorted(reg_mapping.items(), key=lambda x: -sum(x[1].values()))
                if list(targets.keys()) != [raw]  # only show changed mappings
            }
        },
        "tone_taxonomy": {
            "canonical_values": ["warm", "playful", "proud", "celebratory", "excited",
                                 "inviting", "informative", "aspirational", "nostalgic",
                                 "patriotic", "storytelling", "transactional"],
            "before_unique_count": len(tone_before),
            "after_distribution": dict(sorted(tone_after.items(), key=lambda x: -x[1])),
            "mappings": {
                raw: dict(targets)
                for raw, targets in sorted(tone_mapping.items(), key=lambda x: -sum(x[1].values()))
                if list(targets.keys()) != [raw]
            }
        }
    }

    (LOGS / "register_tone_normalization.json").write_text(
        json.dumps(mapping_log, ensure_ascii=False, indent=2)
    )

    # ── Print summary ────────────────────────────────────────────────────────
    print(f"Scanned: {total_files} obs files | Updated: {updated_files}")
    print(f"\nRegister: {len(reg_before)} unique → {len(reg_after)} canonical")
    print("  After distribution:")
    for k, v in sorted(reg_after.items(), key=lambda x: -x[1]):
        print(f"    {k:<20} {v:3d}")

    print(f"\nTone: {len(tone_before)} unique → {len(tone_after)} canonical")
    print("  After distribution:")
    for k, v in sorted(tone_after.items(), key=lambda x: -x[1]):
        print(f"    {k:<20} {v:3d}")

    print(f"\nLog: logs/register_tone_normalization.json")


if __name__ == "__main__":
    main()
