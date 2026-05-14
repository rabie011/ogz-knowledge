#!/usr/bin/env python3
"""
Day 2 / Task 2.2 — Generate 5 Saudi occasion YAML files.

Sources:
- Cultural weights + relevance + visual phase keywords: corpus xlsx "Saudi Occasions" sheet
- Hijri/Gregorian recurrence + lead times: same source + general Saudi calendar knowledge
- Recommended chains: pulled from 02_what_to_build/INDEX.json by chain_id_short

Each file validates against 12_data_shapes/occasion_v1.schema.json.

Idempotent: preserves existing occasion_ulid if file exists.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ulid import ULID

REPO = Path(__file__).resolve().parent.parent
INDEX = json.load(open(REPO / "02_what_to_build" / "INDEX.json"))
OUT_DIR = REPO / "06_saudi_calendar"
OUT_DIR.mkdir(exist_ok=True)

CHAIN_BY_SHORT = {c["chain_id_short"]: c for c in INDEX["chains"]}


def chain_pick(chain_id_short: str, reason: str) -> dict:
    if chain_id_short not in CHAIN_BY_SHORT:
        raise KeyError(f"chain not found: {chain_id_short}")
    c = CHAIN_BY_SHORT[chain_id_short]
    return {
        "chain_ulid": c["chain_ulid"],
        "chain_id_short": c["chain_id_short"],
        "reason": reason,
    }


def existing_ulid(yaml_path: Path) -> str | None:
    if not yaml_path.exists():
        return None
    try:
        return yaml.safe_load(yaml_path.read_text()).get("occasion_ulid")
    except Exception:
        return None


def mint_or_preserve(yaml_path: Path) -> str:
    return existing_ulid(yaml_path) or str(ULID())


NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance(source_ref: str, scope: str) -> dict:
    return {
        "source": source_ref,
        "date_added": NOW,
        "confirmer": "Mohamed",
        "confidence": "experimental",
        "scope": scope,
    }


# ───────────────────────────────────────────────────────────────────────────
# Ramadan — Holy month, 3 phases, Hijri month 9
# ───────────────────────────────────────────────────────────────────────────
def ramadan():
    path = OUT_DIR / "ramadan.yaml"
    return {
        "occasion_ulid": mint_or_preserve(path),
        "occasion_slug": "ramadan",
        "name_en": "Ramadan",
        "name_ar": "رمضان",
        "schema_version": 1,
        "date_recurrence": {
            "type": "hijri",
            "hijri_month": 9,
            "hijri_days": "1-30 (29 or 30 by moon sighting)",
            "duration_days": "29-30",
            "varies_by_moonsighting": True,
        },
        "cultural_significance": {
            "religious_weight": "highest",
            "family_centrality": "highest",
            "hospitality_intensity": "highest",
            "commercial_activity": "peak — F&B and retail spike 2-3x baseline",
            "patriotic_weight": "low",
            "heritage_weight": "high",
        },
        "content_focus_themes": [
            "family iftar gatherings (multi-generational)",
            "charity and giving (zakat al-fitr)",
            "post-iftar community moments",
            "Suhoor and pre-dawn preparation",
            "spiritual reflection and reading",
            "preparation rituals (table-setting, hospitality)",
            "Eid anticipation in the last 10 nights",
        ],
        "content_dos": [
            "show iftar gatherings with families of multiple generations together",
            "feature genuine traditional dishes (dates, qatayef, sambousa, harees) with Arabic naming",
            "depict charity (zakat, gifting, food distribution) without exploiting the recipient",
            "use warm golden-hour lighting and lantern-warm color palette in weeks 1-2",
            "shift to celebratory-anticipatory tone in last 10 nights",
            "respect prayer times: no posting during Maghreb prayer window (auto-quiet 18:00-18:30 AST during Ramadan)",
            "use Arabic-primary copy (80/20 minimum); English is sibling, not subtitle",
        ],
        "content_donts": [
            "do NOT show food or drink consumption during fasting hours (daylight)",
            "do NOT use aggressive promotional discount language in weeks 1-2 (commercial weight builds in last 10 days)",
            "do NOT feature inappropriate clothing or mixed-gender intimate proximity",
            "do NOT trivialize religious practices (no jokes about fasting, prayer, Quran recitation)",
            "do NOT use 'Happy Ramadan' as the standalone caption — Ramadan is contemplative-first, celebratory in phase 3 only",
            "do NOT depict charity recipients in identifiable or pitying framing",
            "do NOT post timed promotions during iftar window without explicit family-friendly framing",
        ],
        "day_specific_variations": {
            "first_10_days_contemplative": {
                "focus": "spiritual awakening, gentle anticipation, family preparation",
                "emotion": "contemplative, calm, reverent",
                "content_emphasis": "no aggressive sales; brand-as-presence; community welcome",
            },
            "middle_10_days_charity": {
                "focus": "giving, charity, community ritual",
                "emotion": "generous, warm, communal",
                "content_emphasis": "highlight giving programs, partner with charities, share customer stories of generosity",
            },
            "last_10_days_anticipation": {
                "focus": "Layla al-Qadr, Eid preparation, gift-giving ramp",
                "emotion": "anticipatory, celebratory-edge, joyful",
                "content_emphasis": "Eid product reveals OK from day 21; gift-giving content peaks; commercial activity legitimate",
            },
        },
        "recommended_chains": [
            chain_pick("tf16_01", "Ramadan Iftar Spread — anchor chain for iftar table imagery"),
            chain_pick("tf22_01", "Ramadan Atmosphere Clip — mood-piece video format"),
            chain_pick("tf22_04", "Occasion Announcement Video — kickoff and milestone moments"),
            chain_pick("tf23_09", "Saudi Mother & Daughter Moment — generational family scene"),
            chain_pick("tf04_02", "Kitchen Window Morning — Suhoor preparation aesthetic"),
            chain_pick("tf12_03", "Beverage Pour Stream — water/laban for iftar opening"),
        ],
        "anti_pattern_warnings": [
            "AVOID: 'Limited Time Ramadan Offer 50% OFF' aggressive language in weeks 1-2 — reads as commercializing the holy month",
            "AVOID: showing characters eating during daylight hours, even in stylized form — auto-block at content gate",
            "AVOID: collapsing all 30 days into one tonal register — the month has 3 phases; treating it as one piece is the most common failure mode",
            "AVOID: mixed-gender iftar scenes without family-context framing (extended family OK; cross-gender strangers eating together is off)",
            "AVOID: comedic/punchline humor — Ramadan voice is warm but not jokey; jokes age badly here",
            "AVOID: lone-individual iftar scenes that imply isolation — Ramadan is family-centric; lone scenes need explicit narrative framing",
        ],
        "preparation_lead_days": 21,
        "provenance": provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Saudi_Occasions+Saudi_calendar_2027",
            scope="occasion:ramadan",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Eid Al-Fitr — End of Ramadan, 3 days, Hijri month 10 days 1-3
# ───────────────────────────────────────────────────────────────────────────
def eid_al_fitr():
    path = OUT_DIR / "eid_al_fitr.yaml"
    return {
        "occasion_ulid": mint_or_preserve(path),
        "occasion_slug": "eid_al_fitr",
        "name_en": "Eid Al-Fitr",
        "name_ar": "عيد الفطر",
        "schema_version": 1,
        "date_recurrence": {
            "type": "hijri",
            "hijri_month": 10,
            "hijri_days": "1-3",
            "duration_days": "3",
            "varies_by_moonsighting": True,
        },
        "cultural_significance": {
            "religious_weight": "high",
            "family_centrality": "highest",
            "hospitality_intensity": "highest",
            "commercial_activity": "peak retail moment — Eid clothes, gifts, gift-card spend",
            "patriotic_weight": "low",
            "heritage_weight": "high",
        },
        "content_focus_themes": [
            "joy and celebration after the fast",
            "Eid clothes (new outfits, traditional thobes/abayas)",
            "family gatherings and hospitality (kahwa, dates, ma'amoul, ka'ak)",
            "gift-giving (Eidiya — cash gifts to children)",
            "community Eid prayers and post-prayer gatherings",
            "children's joy and intergenerational moments",
        ],
        "content_dos": [
            "lead with celebratory warmth — bright, joyful, family-centered framing",
            "show traditional Eid sweets (ma'amoul, ka'ak, basbousa) with Arabic naming",
            "feature multigenerational family scenes — grandparents, parents, children together",
            "use Eid Mubarak / كل عام وأنتم بخير openers respectfully and varied — don't repeat one phrase",
            "highlight new clothes and gift-giving genuinely; Eid clothes are a cultural ritual not just a sale",
            "show community: Eid prayer, post-prayer hugs, neighbor visits",
        ],
        "content_donts": [
            "do NOT use 'sale ends in 2 hours' urgency on Eid Day 1 — Eid Day 1 is family, not transactional",
            "do NOT depict alcohol, gambling, or any prohibited imagery (perennial; especially visible on Eid)",
            "do NOT show isolated celebration — Eid is communal; lone scenes feel off",
            "do NOT mix Eid Al-Fitr and Eid Al-Adha in the same creative without distinction — they are different events",
            "do NOT use 'Eid Mubarak' as the only caption text — bilingual sibling expected",
            "do NOT recycle Ramadan creative — Eid voice is celebratory-bright; Ramadan was contemplative-warm",
        ],
        "day_specific_variations": {
            "day_1_family_first": {
                "focus": "family gathering, Eid prayer, gift-giving",
                "emotion": "joyful, family-centered, hospitable",
                "content_emphasis": "non-transactional — brand as presence in the family moment, no aggressive promo",
            },
            "days_2_and_3_extended_celebration": {
                "focus": "extended family visits, outings, ongoing celebration",
                "emotion": "festive, social, generous",
                "content_emphasis": "commercial content acceptable; gift-giving narratives strong; outdoor/social scenes",
            },
        },
        "recommended_chains": [
            chain_pick("tf16_02", "Occasion Greeting — direct Eid Mubarak greeting format"),
            chain_pick("tf22_04", "Occasion Announcement Video"),
            chain_pick("tf23_09", "Saudi Mother & Daughter Moment — generational Eid scene"),
            chain_pick("tf22_05", "New Arrival Reveal Video — Eid product/collection launch"),
            chain_pick("tf21_02", "New Arrival / Launch — Eid collection drop"),
            chain_pick("tf04_03", "Bedroom Side Table Morning — Eidiya/gift placement"),
        ],
        "anti_pattern_warnings": [
            "AVOID: 'Eid Sale 70% OFF' as the day-1 hero — wrong day; runs on day 2-3",
            "AVOID: generic stock-feeling smiles — Saudi Eid scenes have specific cues (thobes, kahwa, kids running)",
            "AVOID: assuming Eid Al-Fitr and Eid Al-Adha share creative — they are tonally different (Fitr is joy-after-fast; Adha is sacrificial-reflective)",
            "AVOID: foreign cultural imagery (e.g., Western Christmas-style gift wrapping) for Eidiya — Eidiya is cash in envelopes, not wrapped boxes",
        ],
        "preparation_lead_days": 14,
        "provenance": provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Saudi_Occasions+Saudi_calendar_2027",
            scope="occasion:eid_al_fitr",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Eid Al-Adha — Hajj-aligned, Hijri month 12 days 10-13
# ───────────────────────────────────────────────────────────────────────────
def eid_al_adha():
    path = OUT_DIR / "eid_al_adha.yaml"
    return {
        "occasion_ulid": mint_or_preserve(path),
        "occasion_slug": "eid_al_adha",
        "name_en": "Eid Al-Adha",
        "name_ar": "عيد الأضحى",
        "schema_version": 1,
        "date_recurrence": {
            "type": "hijri",
            "hijri_month": 12,
            "hijri_days": "10-13",
            "duration_days": "4",
            "varies_by_moonsighting": False,
        },
        "cultural_significance": {
            "religious_weight": "highest",
            "family_centrality": "high",
            "hospitality_intensity": "high",
            "commercial_activity": "moderate — F&B (meat, hospitality) high; retail moderate; entertainment blacked out",
            "patriotic_weight": "low",
            "heritage_weight": "high",
        },
        "content_focus_themes": [
            "Hajj reverence and pilgrimage imagery (respectful, never staged)",
            "the story of Ibrahim — sacrifice, faith, family",
            "qurban (sacrifice) meat sharing with neighbors and the needy",
            "generosity and giving",
            "extended family hosting",
        ],
        "content_dos": [
            "frame the meat-sharing ritual (qurban) as community giving, not as a meal aesthetic",
            "show Hajj-aligned reverence (Mecca/Kaaba imagery only when authentic and respectful, never as backdrop)",
            "lean on extended-family hospitality scenes",
            "use a respectful, less-celebratory tone than Eid Al-Fitr — Adha is reflective-generous, not party-joyful",
            "Arabic-primary copy; MSA acceptable here given religious weight",
        ],
        "content_donts": [
            "do NOT show graphic slaughter or animal distress imagery — never; auto-block",
            "do NOT use Hajj imagery as a marketing backdrop (Kaaba, Mecca, pilgrim crowds) — these are reverent contexts, not stages",
            "do NOT depict alcohol, gambling, or entertainment — entire entertainment sector is blacked out from posting during Eid Al-Adha",
            "do NOT recycle Eid Al-Fitr creative — different occasion, different tone",
            "do NOT trivialize the sacrifice narrative with puns or wordplay",
            "do NOT push aggressive sales — this is a religious-reflective period",
        ],
        "day_specific_variations": {
            "day_1_arafat_qurban": {
                "focus": "reverence, qurban, family",
                "emotion": "reflective, generous, solemn-joyful",
                "content_emphasis": "no commercial promo; brand-as-presence, charity, hospitality",
            },
            "days_2_3_4_extended": {
                "focus": "family gatherings, hosting, generosity continues",
                "emotion": "warm, communal, hospitable",
                "content_emphasis": "soft commercial OK from day 2; hosting/F&B content strong",
            },
        },
        "recommended_chains": [
            chain_pick("tf16_02", "Occasion Greeting — respectful Eid Al-Adha greeting"),
            chain_pick("tf22_04", "Occasion Announcement Video"),
            chain_pick("tf23_09", "Saudi Mother & Daughter Moment — family hospitality"),
            chain_pick("tf04_02", "Kitchen Window Morning — preparation-aesthetic"),
            chain_pick("tf23_10", "Saudi Outdoor Lifestyle — Heritage Setting"),
        ],
        "anti_pattern_warnings": [
            "AVOID: any imagery suggesting animal suffering or graphic slaughter — auto-block, no exceptions",
            "AVOID: Hajj-related imagery for non-Hajj brands — too reverent for promotional context unless brand is a Hajj-services provider",
            "AVOID: entertainment-sector content during Adha — entertainment is in the blackout list",
            "AVOID: collapsing Adha with Fitr — they are tonally and theologically distinct",
        ],
        "preparation_lead_days": 14,
        "provenance": provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Saudi_Occasions+Saudi_calendar_2027",
            scope="occasion:eid_al_adha",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Saudi National Day — Sep 23 (Gregorian fixed)
# ───────────────────────────────────────────────────────────────────────────
def saudi_national_day():
    path = OUT_DIR / "saudi_national_day.yaml"
    return {
        "occasion_ulid": mint_or_preserve(path),
        "occasion_slug": "saudi_national_day",
        "name_en": "Saudi National Day",
        "name_ar": "اليوم الوطني السعودي",
        "schema_version": 1,
        "date_recurrence": {
            "type": "gregorian",
            "gregorian_month": 9,
            "gregorian_day": 23,
            "duration_days": "1",
            "varies_by_moonsighting": False,
        },
        "cultural_significance": {
            "religious_weight": "none",
            "family_centrality": "medium",
            "hospitality_intensity": "medium",
            "commercial_activity": "high — National Day collections, hospitality bookings, fashion drops",
            "patriotic_weight": "highest",
            "heritage_weight": "high",
        },
        "content_focus_themes": [
            "national pride and Vision 2030 (without becoming politically loaded)",
            "Saudi green palette + falcon + historic motifs",
            "modernity meets heritage — Riyadh skyline alongside heritage sites",
            "youth and ambition",
            "achievement narratives (sport, science, culture, business)",
        ],
        "content_dos": [
            "use the official Saudi green (#006C35) where palette permits; never tint or pastel-soften it",
            "feature both heritage and modernity in the same piece — neither alone is the moment",
            "highlight authentic Saudi cultural markers (thobe, ghutra, sadu pattern, falcon, Najdi or Hijazi architecture)",
            "lead with pride and aspiration, not nostalgia",
            "use Arabic-primary copy; English present but secondary",
            "official slogan of the year if released by GACA / KSA gov — verify before use",
        ],
        "content_donts": [
            "do NOT use stock 'desert + camel + sunset' clichés — Saudi National Day deserves specificity",
            "do NOT politicize beyond Vision 2030 framing — National Day is celebratory, not policy debate",
            "do NOT use the Saudi flag in casual/commercial decoration (e.g., on disposable items, party hats) — flag respect is law-level",
            "do NOT use foreign cultural imagery in the lead frame",
            "do NOT minimize the date with generic 'Happy Holidays' — it's a specific moment",
        ],
        "day_specific_variations": {
            "day_of": {
                "focus": "peak patriotic celebration, public events, family outings",
                "emotion": "proud, celebratory, ambitious",
                "content_emphasis": "real-time content, live coverage, community shots",
            },
        },
        "recommended_chains": [
            chain_pick("tf22_04", "Occasion Announcement Video — kickoff piece"),
            chain_pick("tf23_10", "Saudi Outdoor Lifestyle — Heritage Setting"),
            chain_pick("tf23_08", "Saudi Workplace Moment — Modern Office (modernity)"),
            chain_pick("tf16_02", "Occasion Greeting"),
            chain_pick("tf21_02", "New Arrival / Launch — National Day collection drop"),
            chain_pick("tf22_05", "New Arrival Reveal Video"),
        ],
        "anti_pattern_warnings": [
            "AVOID: flag misuse — Saudi flag has Quranic shahada; no use on disposables, no upside-down, no overlay on faces",
            "AVOID: 'Happy National Day' as the only caption — generic; not specific enough",
            "AVOID: borrowed Western patriotic motifs (fireworks-as-hero, marching-band aesthetics) — Saudi visual grammar is different",
            "AVOID: contrasting modern vs heritage as opposition — the brand voice is 'both, together, on purpose'",
        ],
        "preparation_lead_days": 21,
        "provenance": provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Saudi_Occasions+Saudi_calendar_2027",
            scope="occasion:saudi_national_day",
        ),
    }


# ───────────────────────────────────────────────────────────────────────────
# Saudi Founding Day — Feb 22 (Gregorian fixed since 2022)
# ───────────────────────────────────────────────────────────────────────────
def saudi_founding_day():
    path = OUT_DIR / "saudi_founding_day.yaml"
    return {
        "occasion_ulid": mint_or_preserve(path),
        "occasion_slug": "saudi_founding_day",
        "name_en": "Saudi Founding Day",
        "name_ar": "يوم التأسيس",
        "schema_version": 1,
        "date_recurrence": {
            "type": "gregorian",
            "gregorian_month": 2,
            "gregorian_day": 22,
            "duration_days": "1",
            "varies_by_moonsighting": False,
        },
        "cultural_significance": {
            "religious_weight": "none",
            "family_centrality": "medium",
            "hospitality_intensity": "medium",
            "commercial_activity": "moderate — heritage fashion, traditional food, art and craft",
            "patriotic_weight": "highest",
            "heritage_weight": "highest",
        },
        "content_focus_themes": [
            "the First Saudi State (1727 / 1139H) — three centuries of foundation",
            "Najdi heritage (Dir'iyah, mud-brick architecture, palm groves)",
            "traditional crafts (sadu weaving, calligraphy, palm-leaf work)",
            "founding fathers and the Al-Saud lineage",
            "historic dress (mishlah, agal, traditional women's dress)",
        ],
        "content_dos": [
            "lean heavily on Najdi heritage — Dir'iyah palette (terracotta, palm green, sand)",
            "feature traditional crafts authentically — sadu, calligraphy, palm-leaf weaving with real practitioners or artisan partners",
            "use historic-aesthetic imagery (mud-brick architecture, palm tree, falcon) with respect",
            "Arabic-primary, classical literary register acceptable here",
            "respect the founding date — 1727 (1139H) — and the three centuries narrative",
        ],
        "content_donts": [
            "do NOT confuse Founding Day with National Day — they have distinct meanings (Founding = three centuries; National = 1932 unification)",
            "do NOT use stock 'desert + camel' clichés — Founding Day is specifically Najdi-historical",
            "do NOT misuse the flag (same rules as National Day)",
            "do NOT make Founding Day about modern Vision 2030 — it's about the historical foundation",
            "do NOT use foreign historical-imagery aesthetics (e.g., American old-west, European-medieval)",
        ],
        "day_specific_variations": {
            "day_of": {
                "focus": "heritage celebration, family heritage outings, traditional dress",
                "emotion": "proud, rooted, dignified",
                "content_emphasis": "heritage-deep content; partner with cultural-heritage initiatives if possible",
            },
        },
        "recommended_chains": [
            chain_pick("tf16_02", "Occasion Greeting"),
            chain_pick("tf22_04", "Occasion Announcement Video"),
            chain_pick("tf23_10", "Saudi Outdoor Lifestyle — Heritage Setting"),
            chain_pick("tf04_05", "Retail Boutique Interior — heritage retail aesthetic"),
            chain_pick("tf06_03", "Gallery Pedestal Solo — artisan piece feature"),
        ],
        "anti_pattern_warnings": [
            "AVOID: conflation with National Day — Founding Day commemorates the FIRST Saudi State (1727); National Day commemorates the modern Kingdom (1932). They are different.",
            "AVOID: surface-level 'heritage' wallpaper — Founding Day rewards specificity (Dir'iyah, At-Turaif, Imam Mohammed bin Saud Al-Saud)",
            "AVOID: borrowed regional motifs (Gulf-pan, MENA-generic) — Founding Day is specifically Najdi-historical",
            "AVOID: framing it as 'just another national holiday' — the three-centuries narrative is the point",
        ],
        "preparation_lead_days": 14,
        "provenance": provenance(
            source_ref="internal_research_corpus/OGz_OpenClaw_Prompt_Requirements.xlsx#Saudi_Occasions+Saudi_calendar_2027",
            scope="occasion:saudi_founding_day",
        ),
    }


def write_yaml(data: dict, path: Path) -> None:
    header = f"# {path.name}\n# Schema: 12_data_shapes/occasion_v1.schema.json\n# Confidence: {data['provenance']['confidence']}\n# Scope: {data['provenance']['scope']}\n\n---\n"
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    path.write_text(header + body)


def main() -> int:
    occasions = [ramadan(), eid_al_fitr(), eid_al_adha(), saudi_national_day(), saudi_founding_day()]
    for o in occasions:
        path = OUT_DIR / f"{o['occasion_slug']}.yaml"
        write_yaml(o, path)
        print(f"✓ {path.relative_to(REPO)}  ({len(o['recommended_chains'])} chains · "
              f"{len(o['content_dos'])} dos / {len(o['content_donts'])} donts)")
    print(f"\nWrote {len(occasions)} occasions to {OUT_DIR.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
