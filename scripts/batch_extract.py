#!/usr/bin/env python3
"""
batch_extract.py — Autonomous batch extractor for ogz-knowledge observations.

Usage:
  python3 scripts/batch_extract.py --account crumblcookiespr --batch B2 --count 5 \
    --max-calls 5 --max-usd 0.15 --max-tokens 60000 --estimate-only

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
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from extraction_release_gate import assert_release_allowed  # B130 (Rule #8)
from extraction_budget import (
    MODEL,
    BudgetCaps,
    BudgetRefusal,
    BudgetRun,
    assert_writer_registered,
    build_plan,
    canonical_receipt_writer,
)

REPO = Path(__file__).resolve().parent.parent
OBS_DIR = REPO / "11_who_to_learn_from" / "observations" / "f_and_b"
SCHEMA_DIR = REPO / "12_data_shapes"
SYSTEM_ROOT = REPO.parents[2]
PRICING_PATH = SYSTEM_ROOT / "tools" / "model_router.json"
REGISTRY_PATH = SYSTEM_ROOT / "ledgers" / "REGISTRY.json"
MAX_OUTPUT_TOKENS = 2000

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


def get_existing_filenames(handle_norm: str, obs_dir: Path = OBS_DIR) -> set[str]:
    used = set()
    for f in obs_dir.glob("*.json"):
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


def build_user_message(img_path: Path, meta: dict, caption: str) -> str:
    return EXTRACTION_USER.format(
        handle=img_path.parent.parent.name.lstrip("@"),
        description=meta["description"],
        what_to_watch=meta["what_to_watch"],
        filename=img_path.name,
        caption=caption or "(no caption available)",
    )


def call_provider(
    client: Any,
    img_path: Path,
    meta: dict,
    caption: str,
) -> Any:
    img_b64, media_type = load_image_b64(img_path)
    return client.messages.create(
        model=MODEL,
        max_tokens=MAX_OUTPUT_TOKENS,
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
                    {"type": "text", "text": build_user_message(img_path, meta, caption)},
                ],
            }
        ],
    )


def observation_from_response(
    response: Any,
    img_path: Path,
    meta: dict,
    observation_ulid: str,
) -> dict:
    handle = img_path.parent.parent.name.lstrip("@")
    filename = img_path.name
    content_type = "image"
    if "_" in img_path.stem and img_path.stem.split("_")[-1].isdigit():
        content_type = "carousel_slide"

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
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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


def _positive_decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("must be a decimal") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True)
    parser.add_argument("--batch", default="B2")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-calls", type=int, required=True)
    parser.add_argument("--max-usd", type=_positive_decimal, required=True)
    parser.add_argument("--max-tokens", type=int, required=True)
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="print the bounded token/USD plan; no receipt, credential, provider, or observation write",
    )
    return parser.parse_args(argv)


def load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def default_client_factory(api_key: str) -> Any:
    import anthropic  # Lazy: estimate/refusal paths never import the provider SDK.

    return anthropic.Anthropic(api_key=api_key)


def load_captions(pass1_dir: Path) -> dict[str, str]:
    captions: dict[str, str] = {}
    if not pass1_dir.exists():
        return captions
    for path in pass1_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            captions[path.stem] = data.get("caption", "") or ""
        except (OSError, json.JSONDecodeError):
            continue
    return captions


def run_extraction(
    args: argparse.Namespace,
    *,
    repo: Path = REPO,
    system_root: Path = SYSTEM_ROOT,
    pricing_path: Path = PRICING_PATH,
    registry_path: Path = REGISTRY_PATH,
    receipt_writer: Callable[[dict[str, Any]], None] | None = None,
    key_loader: Callable[[], str] = load_api_key,
    client_factory: Callable[[str], Any] = default_client_factory,
    release_check: Callable[[], Any] = assert_release_allowed,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    try:
        release_check()
        if args.count <= 0 or args.max_calls <= 0 or args.max_tokens <= 0:
            raise BudgetRefusal("count and every numeric cap must be positive")
        meta = ACCOUNT_META.get(args.account)
        if not meta:
            raise BudgetRefusal(
                f"unknown account {args.account!r}; known={sorted(ACCOUNT_META)}"
            )
        media_dir = repo / "11_who_to_learn_from" / "_inbox" / f"@{args.account}" / "media"
        if not media_dir.is_dir():
            raise BudgetRefusal(f"media directory missing: {media_dir}")
        obs_dir = repo / "11_who_to_learn_from" / "observations" / "f_and_b"
        used = get_existing_filenames(meta["handle_norm"], obs_dir)
        images = select_images(media_dir, used, args.count, seed=args.seed)
        if not images:
            raise BudgetRefusal("no fresh eligible images selected")
        captions = load_captions(
            repo / "11_who_to_learn_from" / "_inbox" / f"@{args.account}" / "pass1"
        )
        prompts = []
        call_captions = []
        for image in images:
            stem = image.stem.rstrip("_0123456789")
            caption = captions.get(stem, "") or captions.get(image.stem, "")
            call_captions.append(caption)
            prompts.append(build_user_message(image, meta, caption))
        plan = build_plan(
            images,
            prompts,
            EXTRACTION_SYSTEM,
            MAX_OUTPUT_TOKENS,
            BudgetCaps(args.max_calls, args.max_usd, args.max_tokens),
            pricing_path,
        )
    except (BudgetRefusal, OSError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2

    plan_output = {
        "account": args.account,
        "batch": args.batch,
        "estimate_only": bool(args.estimate_only),
        **plan.as_dict(),
    }
    print(json.dumps(plan_output, indent=2, sort_keys=True))
    if args.estimate_only:
        return 0

    try:
        assert_writer_registered(registry_path)
        writer = receipt_writer or canonical_receipt_writer(system_root)
        run_id = "extract-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid4().hex[:8]
        budget = BudgetRun(plan, writer, run_id)
        budget.reserve()
    except (BudgetRefusal, OSError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2

    success = 0
    failures: list[tuple[str, str]] = []
    close_status = "parked"
    close_reason = "run did not complete"
    result_code = 1
    close_error: BudgetRefusal | None = None
    try:
        api_key = key_loader()
        if not api_key:
            close_reason = "credential unavailable after reservation"
            print(f"REFUSE: {close_reason}", file=sys.stderr)
            result_code = 2
            client = None
        else:
            try:
                client = client_factory(api_key)
            except Exception as exc:
                close_reason = f"provider client initialization failed: {type(exc).__name__}"
                print(f"REFUSE: {close_reason}", file=sys.stderr)
                result_code = 2
                client = None

        if client is not None:
            obs_dir.mkdir(parents=True, exist_ok=True)
            for call, caption in zip(plan.calls, call_captions):
                observation_ulid = make_ulid()
                print(
                    f"[{call.index}/{len(plan.calls)}] {call.image.name} -> {observation_ulid}.json",
                    flush=True,
                )
                try:
                    budget.authorize_call(call)
                except BudgetRefusal as exc:
                    failures.append((call.image.name, str(exc)))
                    close_reason = str(exc)
                    break
                try:
                    response = call_provider(client, call.image, meta, caption)
                except Exception as exc:
                    try:
                        budget.settle_error(call, exc)
                    except BudgetRefusal as ledger_exc:
                        failures.append((call.image.name, str(ledger_exc)))
                        close_reason = str(ledger_exc)
                        break
                    failures.append((call.image.name, str(exc)))
                    close_reason = f"provider call failed: {type(exc).__name__}"
                    break
                try:
                    budget.settle_success(call, response.usage)
                except BudgetRefusal as exc:
                    failures.append((call.image.name, str(exc)))
                    close_reason = str(exc)
                    break
                try:
                    observation = observation_from_response(
                        response, call.image, meta, observation_ulid
                    )
                    output_path = obs_dir / f"{observation_ulid}.json"
                    output_path.write_text(
                        json.dumps(observation, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    failures.append((call.image.name, str(exc)))
                    close_reason = f"post-settlement observation write failed: {type(exc).__name__}"
                    break
                success += 1
                sleep_fn(1.0)

            if success == len(plan.calls) and not failures:
                close_status = "done"
                close_reason = "all reserved calls settled and observations written"
                result_code = 0
            else:
                result_code = 1
            print(f"[{args.account}] {args.batch}: {success}/{len(plan.calls)} observations written")
    finally:
        try:
            budget.close(close_status, close_reason)
        except BudgetRefusal as exc:
            print(f"REFUSE: reservation close receipt failed: {exc}", file=sys.stderr)
            close_error = exc
    return 2 if close_error else result_code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_extraction(args)


if __name__ == "__main__":
    sys.exit(main())
