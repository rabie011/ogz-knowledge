#!/usr/bin/env python3
"""
batch_extract.py — Autonomous batch extractor for ogz-knowledge observations.

Usage:
  python3 scripts/batch_extract.py --account barnscoffee --batch B2 --count 25
  python3 scripts/batch_extract.py --account aseeb.najd --batch B1 --count 25

Reads images from _inbox/@{account}/media/, calls Anthropic API (claude-haiku-4-5)
with vision to generate observation_v1 JSON records, saves to observations/f_and_b/.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import random
import sys
import time
from pathlib import Path

import anthropic

REPO = Path(__file__).resolve().parent.parent
OBS_DIR = REPO / "11_who_to_learn_from" / "observations" / "f_and_b"
SCHEMA_DIR = REPO / "12_data_shapes"

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ulid_ts_offset = 0

def make_ulid() -> str:
    global _ulid_ts_offset
    t = int(time.time() * 1000) + _ulid_ts_offset
    _ulid_ts_offset += 1
    t_part = ""
    v = t
    for _ in range(10):
        t_part = CROCKFORD[v & 0x1F] + t_part
        v >>= 5
    r = random.getrandbits(80)
    r_part = ""
    for _ in range(16):
        r_part = CROCKFORD[r & 0x1F] + r_part
        r >>= 5
    return t_part + r_part


ACCOUNT_META = {
    "barnscoffee": {
        "handle_norm": "OGZ-F-AND-B-Reference-002",
        "account_ulid": "01KRKHS8R8SNJ8VJ56WKSQTS28",
        "tier": 1,
        "description": "Top F&B coffee/cafe chain in Riyadh — 233K followers, Saudi Score 9",
        "what_to_watch": "Visual consistency, Saudi hospitality cues in cafe content",
    },
    "aseeb.najd": {
        "handle_norm": "OGZ-F-AND-B-Reference-010",
        "account_ulid": "01KRKHS8R9HB73WWWGKXVDMC3A",
        "tier": 1,
        "description": "Traditional Saudi Restaurant in Riyadh — 28K followers, Saudi Score 9, Engagement 6.7%",
        "what_to_watch": "Najdi cultural authenticity, traditional hospitality, qahwa service",
    },
    "riyadhfood": {
        "handle_norm": "OGZ-F-AND-B-Reference-004",
        "account_ulid": "01KRKHS8R8SNJ8VJ56WKSQTS2E",
        "tier": 2,
        "description": "Food Discovery/Community in Riyadh — 557K followers, Saudi Score 9",
        "what_to_watch": "Discovery-format content, Riyadh-specific food scenes",
    },
    "altazaj_fakieh": {
        "handle_norm": "OGZ-F-AND-B-Reference-005",
        "account_ulid": "01KRKHS8R8SNJ8VJ56WKSQTS2H",
        "tier": 2,
        "description": "Fast Food/Grills chain — 176K followers, Saudi Score 9",
        "what_to_watch": "How a Saudi fast food chain handles cultural content vs international chains",
    },
    "crumblcookiespr": {
        "handle_norm": "OGZ-F-AND-B-Reference-003",
        "account_ulid": "01KRKHS8R8SNJ8VJ56WKSQTS2G",
        "tier": 1,
        "description": "Dessert/Cookies — 97K followers (KSA local), Visual Score 9, Engagement 6.2%. Strong visual identity.",
        "what_to_watch": "High production quality, visual composition patterns, dessert food photography",
    },
    "herfyfsc": {
        "handle_norm": "OGZ-F-AND-B-Reference-006",
        "account_ulid": "01KS8MQHR0SVWGFRK2NDA3YT6P",
        "tier": 2,
        "description": "Herfy Food Services — Saudi fast food chain, 380K followers. Spacetoon nostalgia campaign + Champions League collab.",
        "what_to_watch": "How Saudi fast food brands run cultural nostalgia campaigns, Spacetoon IP usage, drive-through content format",
    },
    "kuduksa": {
        "handle_norm": "OGZ-F-AND-B-Reference-007",
        "account_ulid": "01KS5PYQ88T5AAR9PTC4NEWMPQ",
        "tier": 2,
        "description": "Kudu — Saudi burger chain, 533K followers. Breakfast campaign, kids meals, employee pride stories, sustainability CSR.",
        "what_to_watch": "Multi-pillar content strategy, breakfast daypart activation, Vision 2030 employee storytelling, CSR/sustainability content",
    },
    "albaik": {
        "handle_norm": "OGZ-F-AND-B-Reference-008",
        "account_ulid": "01KS5PZ5T50CY91R45QE57BT7P",
        "tier": 1,
        "description": "AlBaik — iconic Saudi fried chicken, 511K followers. Product-first strategy, extreme engagement (8K+ likes), Saudi occasion mastery.",
        "what_to_watch": "Ultra-minimal copy + product hero format, returning fan-favourite mechanic, Saudi national occasions, prayer-time service anchoring",
    },
    "shawarmersa": {
        "handle_norm": "OGZ-F-AND-B-Reference-009",
        "account_ulid": "01KS5PZ5T5YSN7GNCCVJ7AZ85T",
        "tier": 1,
        "description": "Shawarmer — Saudi shawarma chain, 310K followers. #إعرف_شاورمتك transparency series, 62g protein positioning, high nutritional/behind-scenes content.",
        "what_to_watch": "Ingredient transparency content, protein positioning, POV employee format, #KnowYourShawarma campaign mechanics",
    },
    "asteribeautysa": {
        "handle_norm": "OGZ-BEAUTY-Reference-001",
        "account_ulid": "01KS5PZ5T5J535JPWGJER6R2D1",
        "tier": 1,
        "sector": "beauty",
        "description": "Asteri Beauty — Saudi B Corp certified beauty brand. 'امتلاء أكثر بدون فيلر' (Fuller without Filler) campaign, Mira Lip Shine hero product.",
        "what_to_watch": "B Corp storytelling, ingredient transparency, influencer co-creation, shade range launches",
    },
}


EXTRACTION_SYSTEM = """You are an expert visual analyst for OGZ Studios, a Saudi Arabian creative agency.
Your job: analyze a food/cafe brand Instagram image and return a structured JSON observation record.

## Forbidden list (memorize — check every image):

### HARD BLOCKS (severe violations):
- left_hand_serving: Left hand used as PRIMARY serving hand (food/drink/gifts) → triggers hard_block
- sole_of_foot_visible: Soles of feet/shoes directed at a person → hard_block
- shoes_on_seating: Shoes on seating surfaces/majlis cushions → hard_block
- alcohol_product: Any alcohol bottle, wine glass, beer imagery → hard_block
- pork_product: Bacon, ham, pork imagery → hard_block
- gambling_imagery: Casino chips, slot machines, playing cards in gambling context → hard_block
- eating_during_ramadan_daylight: Eating/drinking in Ramadan daytime (Fajr to Maghreb) → hard_block
- cross_gender_physical_contact_non_mahram: Handshake/embrace/casual touch between unrelated opposite genders → hard_block
- prayer_as_commercial_backdrop: Prayer used as promotional set-dressing → hard_block
- saudi_flag_misuse: Saudi flag on disposable items, upside-down, overlaid on faces → hard_block
- kaaba_or_mecca_as_backdrop: Kaaba/Hajj imagery as brand backdrop → hard_block

### MODERATE violations (also blocked):
- western_palm_up_beckon: Curling finger "come here" gesture → moderate block
- pointing_finger_at_person: Index finger pointed directly at a person → moderate block
- thumbs_up_to_elder_or_religious: Thumbs up at religious/elder figures → moderate block
- ok_circle_gesture: Western "OK" circle hand gesture → moderate block
- other_faith_religious_symbols: Cross, Star of David, Buddha as decoration → moderate block
- smoking_family_context: Smoking in family-context content → moderate block

## 40 patterns (match if present):
Visual compositions: overhead_tabletop_spread, product_hero_close_up, pattern_repeat_flatlay, steam_and_texture_macro, architectural_framing, cultural_object_hero, lifestyle_environment_integration, behind_the_scenes_production, duo_product_comparison, storytelling_sequence_grid

Voice techniques: arabic_casual_mood_trigger, bilingual_brand_voice, heritage_storytelling_hook, curiosity_gap_question, community_pride_statement, urgency_without_pressure, user_generated_amplification, occasion_specific_greeting, poetic_phrasing_najdi, call_to_action_soft_invite

Content types: product_launch_reveal, seasonal_campaign_graphic, event_collab_announcement, giveaway_contest_post, behind_scenes_reel_teaser, educational_ingredient_spotlight, brand_milestone_post, menu_expansion_announcement, cultural_moment_tie_in, influencer_takeover_post

Occasion plays: national_day_93_94, ramadan_iftar_warmth, eid_premium_gift, expo_2030_pride, women_empowerment_day, global_event_saudi_lens, world_food_heritage_day, winter_comfort_cozy, founding_day_celebration, seasonal_summer_heat

## Output format (return ONLY valid JSON, no markdown):
{
  "composition_style": "string — e.g. overhead tabletop spread",
  "lighting": "string",
  "color_palette_dominant": ["color1", "color2"],
  "props_visible": ["prop1", "prop2"],
  "setting": "string",
  "characters": {
    "count": 0,
    "gender_presentation": null,
    "wardrobe_notes": null,
    "gesture_notes": null
  },
  "text_overlays": [{"language": "arabic", "content_summary": "summary"}],
  "notable_visual_elements": ["element1"],
  "voice": {
    "language": "arabic",
    "dialect_detected": null,
    "register": "casual",
    "tone": "warm",
    "notable_phrases": [],
    "call_to_action_present": false
  },
  "compliance": {
    "hard_blocks": [
      {"id": "01KRKH1N2YF8H7F60EGJYQS3EW", "name": "left_hand_serving", "severity": "severe", "evidence": "what was seen"}
    ],
    "soft_flags": [
      {"flag_type": "type", "description": "what was seen"}
    ]
  },
  "cultural_notes": {
    "regional_orientation": "Najdi | Hejazi | Eastern | general_saudi | null",
    "occasion_relevance": "null or string",
    "hospitality_cues": ["cue1"],
    "heritage_vs_modern": "heritage | modern | blended | neutral",
    "free_notes": "string or null"
  },
  "pattern_matches": [
    {"pattern_slug": "overhead_tabletop_spread", "confidence": "strong", "notes": "why"}
  ],
  "production_quality": "professional | semi_professional | ugc | low",
  "brand_consistency": "strong | moderate | weak",
  "engagement_potential": "high | medium | low"
}
"""

EXTRACTION_USER = """Account: @{handle} ({description})
Watch for: {what_to_watch}
Filename: {filename}
Caption (if available): {caption}

Analyze this image and return the JSON observation. Return ONLY the JSON, no text before or after."""


def detect_media_type(path: Path) -> str:
    with open(path, "rb") as f:
        header = f.read(12)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    elif header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"


def load_image_b64(path: Path) -> tuple[str, str]:
    with open(path, "rb") as f:
        data = f.read()
    return base64.standard_b64encode(data).decode("utf-8"), detect_media_type(path)


def get_existing_filenames(handle_norm: str) -> set[str]:
    used = set()
    for f in OBS_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized") == handle_norm:
                fn = d.get("content_ref", {}).get("filename", "")
                if fn:
                    sc = fn.rsplit(".", 1)[0].rstrip("_0123456789")
                    used.add(fn)
                    used.add(sc)
        except Exception:
            pass
    return used


def select_images(media_dir: Path, used: set[str], count: int, seed: int = 42) -> list[Path]:
    random.seed(seed)
    all_jpg = [f for f in media_dir.glob("*.jpg") if "_thumb" not in f.name]
    eligible = []
    for f in all_jpg:
        sc = f.stem.rstrip("_0123456789")
        if f.name not in used and sc not in used:
            eligible.append(f)

    random.shuffle(eligible)
    return eligible[:count]


def extract_one(
    client: anthropic.Anthropic,
    img_path: Path,
    meta: dict,
    caption: str,
    observation_ulid: str,
) -> dict:
    handle = img_path.parent.parent.name.lstrip("@")
    filename = img_path.name

    # Determine content type
    content_type = "image"
    if "_" in img_path.stem and img_path.stem.split("_")[-1].isdigit():
        content_type = "carousel_slide"

    img_b64, media_type = load_image_b64(img_path)

    user_msg = EXTRACTION_USER.format(
        handle=handle,
        description=meta["description"],
        what_to_watch=meta["what_to_watch"],
        filename=filename,
        caption=caption or "(no caption available)",
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=EXTRACTION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": user_msg},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip any markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    extracted = json.loads(raw)

    chars = extracted.get("characters", {})
    chars_out = {"count": chars.get("count", 0)}
    if chars.get("gender_presentation"):
        chars_out["gender_presentation"] = chars["gender_presentation"]
    if chars.get("wardrobe_notes"):
        chars_out["wardrobe_notes"] = chars["wardrobe_notes"]
    if chars.get("gesture_notes"):
        chars_out["gesture_notes"] = chars["gesture_notes"]

    voice = extracted.get("voice", {})
    _VALID_LANGS = {"arabic", "english", "bilingual", "none"}
    _VALID_CONF = {"strong", "moderate", "weak"}

    def _norm_lang(v: str) -> str:
        v = v.lower()
        if any(x in v for x in ("none", "visual", "no_text", "no text", "silent")):
            return "none"
        if any(x in v for x in ("mixed", "bilingual", "both")):
            return "bilingual"
        if "english" in v:
            return "english"
        return "arabic"

    def _norm_conf(v: str) -> str:
        v = v.lower()
        if v in ("high", "strong"):
            return "strong"
        if v in ("low", "weak"):
            return "weak"
        return "moderate"

    voice_out = {}
    if voice.get("language"):
        lang = voice["language"]
        voice_out["language"] = lang if lang in _VALID_LANGS else _norm_lang(lang)
    if voice.get("dialect_detected"):
        voice_out["dialect_detected"] = voice["dialect_detected"]
    if voice.get("register"):
        voice_out["register"] = voice["register"]
    if voice.get("tone"):
        voice_out["tone"] = voice["tone"]
    if voice.get("notable_phrases"):
        voice_out["notable_phrases"] = voice["notable_phrases"]
    if "call_to_action_present" in voice:
        voice_out["call_to_action_present"] = voice["call_to_action_present"]

    compliance = extracted.get("compliance", {})
    hard_blocks = []
    for hb in compliance.get("hard_blocks", []):
        hard_blocks.append({
            "forbidden_list_id": hb.get("id", ""),
            "entry_name": hb.get("name", ""),
            "severity": hb.get("severity", "moderate"),
            "evidence_description": hb.get("evidence", "observed violation"),
        })

    soft_flags = []
    for sf in compliance.get("soft_flags", []):
        soft_flags.append({
            "flag_type": sf.get("flag_type", "cultural_sensitivity"),
            "description": sf.get("description", ""),
        })

    overall = "clean"
    if hard_blocks:
        overall = "hard_blocked"
    elif soft_flags:
        overall = "soft_flagged"

    cn = extracted.get("cultural_notes", {})
    heritage_raw = cn.get("heritage_vs_modern", "neutral")
    valid_hvm = {"heritage", "modern", "blended", "neutral"}
    heritage_val = heritage_raw if heritage_raw in valid_hvm else "neutral"

    obs = {
        "observation_ulid": observation_ulid,
        "schema_version": 1,
        "account_handle_normalized": meta["handle_norm"],
        "account_ulid": meta["account_ulid"],
        "sector": "f_and_b",
        "content_ref": {
            "filename": filename,
            "platform": "instagram",
            "content_type": content_type,
        },
        "visual_observations": {
            "composition_style": extracted.get("composition_style", "unspecified"),
            "lighting": extracted.get("lighting"),
            "color_palette_dominant": extracted.get("color_palette_dominant", []),
            "props_visible": extracted.get("props_visible", []),
            "setting": extracted.get("setting"),
            "characters_visible": chars_out,
            "text_overlays": extracted.get("text_overlays", []),
            "notable_visual_elements": extracted.get("notable_visual_elements", []),
        },
        "voice_observations": voice_out if voice_out else None,
        "compliance_check": {
            "hard_blocks_triggered": hard_blocks,
            "soft_flags": soft_flags,
            "overall_compliance": overall,
        },
        "cultural_notes": {
            "regional_orientation_detected": cn.get("regional_orientation"),
            "occasion_relevance": cn.get("occasion_relevance"),
            "hospitality_cues": cn.get("hospitality_cues", []),
            "heritage_vs_modern": heritage_val,
            "free_notes": cn.get("free_notes"),
        },
        "pattern_matches": [
            {
                "pattern_slug": pm.get("pattern_slug", ""),
                "confidence": (lambda c: c if c in _VALID_CONF else _norm_conf(c))(pm.get("confidence", "moderate")),
                "notes": pm.get("notes"),
            }
            for pm in extracted.get("pattern_matches", [])
            if pm.get("pattern_slug")
        ],
        "quality_assessment": {
            "production_quality": extracted.get("production_quality", "semi_professional"),
            "brand_consistency_with_account": (lambda v: v if v in {"strong","moderate","weak"} else "moderate")(extracted.get("brand_consistency","moderate")),
            "engagement_potential": (lambda v: v if v in {"high","medium","low"} else "medium")(extracted.get("engagement_potential","medium")),
        },
        "provenance": {
            "source": f"instagram:@{handle}:{img_path.stem}",
            "date_added": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b",
        },
    }

    # Remove None voice_observations
    if obs["voice_observations"] is None:
        del obs["voice_observations"]

    # Remove None values from visual_observations
    vo = obs["visual_observations"]
    for k in ["lighting", "setting"]:
        if vo.get(k) is None:
            del vo[k]

    # Remove None from cultural_notes
    cn_out = obs["cultural_notes"]
    for k in ["regional_orientation_detected", "occasion_relevance", "free_notes"]:
        if cn_out.get(k) is None:
            del cn_out[k]

    return obs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True)
    parser.add_argument("--batch", default="B2")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    account = args.account
    meta = ACCOUNT_META.get(account)
    if not meta:
        print(f"ERROR: Unknown account '{account}'. Known: {list(ACCOUNT_META.keys())}")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Try loading from .abraham_env
        env_path = Path.home() / ".abraham_env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("ERROR: No ANTHROPIC_API_KEY found")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    media_dir = REPO / "11_who_to_learn_from" / "_inbox" / f"@{account}" / "media"
    if not media_dir.exists():
        print(f"ERROR: media dir not found: {media_dir}")
        sys.exit(1)

    OBS_DIR.mkdir(parents=True, exist_ok=True)

    used = get_existing_filenames(meta["handle_norm"])
    print(f"[{account}] Already extracted: {len(used)//2} files")

    images = select_images(media_dir, used, args.count, seed=args.seed)
    print(f"[{account}] Selected {len(images)} images for {args.batch}")
    for img in images:
        print(f"  {img.name}")

    captions: dict[str, str] = {}
    pass1_dir = REPO / "11_who_to_learn_from" / "_inbox" / f"@{account}" / "pass1"
    if pass1_dir.exists():
        for jf in pass1_dir.glob("*.json"):
            try:
                d = json.loads(jf.read_text())
                captions[jf.stem] = d.get("caption", "") or ""
            except Exception:
                pass

    success = 0
    failures = []

    for i, img_path in enumerate(images):
        ulid = make_ulid()
        sc = img_path.stem.rstrip("_0123456789")
        caption = captions.get(sc, "") or captions.get(img_path.stem, "")

        print(f"  [{i+1}/{len(images)}] Extracting {img_path.name} → {ulid}.json", end="", flush=True)

        try:
            obs = extract_one(client, img_path, meta, caption, ulid)
            out_path = OBS_DIR / f"{ulid}.json"
            out_path.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
            print(f" ✓ [{obs['compliance_check']['overall_compliance']}]")
            success += 1
        except Exception as e:
            print(f" ✗ ERROR: {e}")
            failures.append((img_path.name, str(e)))

        # Rate limiting: 1 image/sec
        time.sleep(1.0)

    print(f"\n[{account}] {args.batch} done: {success}/{len(images)} extracted")
    if failures:
        print(f"Failures ({len(failures)}):")
        for fn, err in failures:
            print(f"  {fn}: {err}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
