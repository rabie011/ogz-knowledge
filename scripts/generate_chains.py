#!/usr/bin/env python3
"""
Generate 88 chain JSON files from the extracted raw chain data.
Maps each raw chain onto chain_v1.schema.json.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path("/home/claude/ogz-knowledge")
RAW_PATH = Path("/tmp/chains_raw.json")
CHAINS_DIR = REPO_ROOT / "02_what_to_build"

# Ulid alphabet (Crockford base32)
ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def deterministic_ulid(seed: str) -> str:
    """Deterministic 26-char ULID from a seed string. Same input always yields same ULID."""
    import hashlib
    h = hashlib.sha256(seed.encode()).hexdigest()
    # Use first 26 hex chars worth of entropy, mapped to Crockford base32
    out = []
    val = int(h[:32], 16)
    for _ in range(26):
        out.append(ULID_ALPHABET[val % 32])
        val //= 32
    return ''.join(reversed(out))

# Family-level metadata: cinematography defaults, output type defaults, sector affinity
FAMILY_META = {
    "TF01": {"output": "image", "best_cd": ["cd_01", "cd_04"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF02": {"output": "image", "best_cd": ["cd_02", "cd_05"], "duration": None, "sectors": ["f_and_b", "beauty", "retail"], "tiers": ["growth", "enterprise"]},
    "TF03": {"output": "image", "best_cd": ["cd_02", "cd_03"], "duration": None, "sectors": ["*"], "tiers": ["growth", "enterprise"]},
    "TF04": {"output": "image", "best_cd": ["cd_01", "cd_03"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF05": {"output": "image", "best_cd": ["cd_03"], "duration": None, "sectors": ["beauty", "retail", "f_and_b"], "tiers": ["starter", "growth", "enterprise"]},
    "TF06": {"output": "image", "best_cd": ["cd_02", "cd_04"], "duration": None, "sectors": ["*"], "tiers": ["growth", "enterprise"]},
    "TF07": {"output": "image", "best_cd": ["cd_03"], "duration": None, "sectors": ["beauty", "retail"], "tiers": ["starter", "growth", "enterprise"]},
    "TF08": {"output": "image", "best_cd": ["cd_02", "cd_04", "cd_05"], "duration": None, "sectors": ["*"], "tiers": ["growth", "enterprise"]},
    "TF09": {"output": "image", "best_cd": ["cd_03", "cd_04"], "duration": None, "sectors": ["retail", "beauty"], "tiers": ["growth", "enterprise"]},
    "TF10": {"output": "image", "best_cd": ["cd_01", "cd_04"], "duration": None, "sectors": ["*"], "tiers": ["growth", "enterprise"]},
    "TF11": {"output": "image", "best_cd": ["cd_02"], "duration": None, "sectors": ["beauty", "f_and_b"], "tiers": ["growth", "enterprise"]},
    "TF12": {"output": "image", "best_cd": ["cd_02"], "duration": None, "sectors": ["beauty", "f_and_b"], "tiers": ["growth", "enterprise"]},
    "TF13": {"output": "image", "best_cd": ["cd_03", "cd_01"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF14": {"output": "image", "best_cd": ["cd_02", "cd_04"], "duration": None, "sectors": ["beauty", "retail"], "tiers": ["growth", "enterprise"]},
    "TF15": {"output": "image", "best_cd": ["cd_01"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF16": {"output": "image", "best_cd": ["cd_04", "cd_01"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF17": {"output": "image", "best_cd": ["cd_03"], "duration": None, "sectors": ["beauty"], "tiers": ["starter", "growth", "enterprise"]},
    "TF18": {"output": "image", "best_cd": ["cd_01", "cd_03"], "duration": None, "sectors": ["beauty", "retail"], "tiers": ["starter", "growth", "enterprise"]},
    "TF19": {"output": "image", "best_cd": ["cd_03", "cd_04"], "duration": None, "sectors": ["retail"], "tiers": ["growth", "enterprise"]},
    "TF20": {"output": "image", "best_cd": ["cd_02", "cd_04"], "duration": None, "sectors": ["beauty", "f_and_b"], "tiers": ["growth", "enterprise"]},
    "TF21": {"output": "image", "best_cd": ["cd_01"], "duration": None, "sectors": ["*"], "tiers": ["starter", "growth", "enterprise"]},
    "TF22": {"output": "video", "best_cd": ["cd_01", "cd_02", "cd_03", "cd_04"], "duration": 6, "sectors": ["*"], "tiers": ["growth", "enterprise"]},
    "TF23": {"output": "video", "best_cd": ["cd_03", "cd_05"], "duration": 9, "sectors": ["retail", "f_and_b", "beauty"], "tiers": ["starter", "growth", "enterprise"]},
}

# Cost & latency tiers based on output type and family
def cost_latency(family: str, output: str) -> tuple:
    if output == "video":
        if family == "TF22":
            return 1.8, 75  # premium cinematic
        return 1.2, 60     # standard video
    return 0.05, 4        # image

def slugify(name: str) -> str:
    """Convert chain name to filename-safe slug."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s).strip("_")
    return s

def build_input_schema(family: str, output: str, has_video: bool):
    """Default input schema by family/output type."""
    base = {}
    if output == "image":
        base = {
            "subject_description": {
                "type": "string",
                "description": "What is being shown — product, scene, or subject",
                "required": True,
                "min_length": 10
            },
            "tone_descriptor": {
                "type": "string",
                "description": "Tone direction: contemplative, bold, warm, dignified, kinetic, etc.",
                "required": True
            },
            "brand_palette_override": {
                "type": "array",
                "description": "Optional palette override; otherwise pulled from brand fingerprint",
                "required": False
            }
        }
    else:  # video
        base = {
            "subject_description": {
                "type": "string",
                "description": "What is being shown — product, scene, or subject",
                "required": True,
                "min_length": 10
            },
            "setting_description": {
                "type": "string",
                "description": "Where this happens — must align with brand cultural spec",
                "required": True
            },
            "duration_seconds": {
                "type": "integer",
                "description": "Target video duration in seconds",
                "default": 6,
                "required": True
            },
            "first_frame_description": {
                "type": "string",
                "description": "What the first frame shows (generated as keyframe)",
                "required": True
            },
            "last_frame_description": {
                "type": "string",
                "description": "What the last frame shows",
                "required": False
            }
        }
    return base

def build_cultural_constraints(family: str, raw_chain: dict) -> dict:
    """Infer cultural constraint flags from family + saudi adaptation text."""
    sa = (raw_chain.get('saudi_adaptation') or '').lower()
    name = (raw_chain.get('chain_name') or '').lower()

    is_human_in_frame = any(t in name for t in ['model', 'hand', 'figure', 'portrait', 'lifestyle', 'thobe', 'hijab', 'man ', 'woman', 'family', 'mother', 'daughter', 'friend', 'workplace', 'beauty routine', 'grooming'])
    is_human_in_frame = is_human_in_frame or family in ['TF05', 'TF09', 'TF17', 'TF19', 'TF23']

    has_arabic_text = any(t in sa for t in ['arabic', 'text in arabic', 'msa', 'colloquial'])
    is_religious = any(t in sa for t in ['ramadan', 'eid', 'religious', 'prayer', 'iftar'])
    is_gender_sensitive = is_human_in_frame or 'gender' in sa or 'modest' in sa

    return {
        "requires_wardrobe_check": is_human_in_frame,
        "requires_gesture_check": is_human_in_frame,
        "requires_cultural_coherence_check": True,
        "requires_arabic_text_validation": has_arabic_text,
        "high_religious_sensitivity": is_religious,
        "high_gender_sensitivity": is_gender_sensitive,
        "human_review_recommended_above_quality_tier": "starter" if family in ['TF22', 'TF23'] or is_human_in_frame else "never"
    }

def derive_anti_patterns(raw_chain: dict, family: str) -> list:
    """Build sensible anti-patterns from family + chain context."""
    output = FAMILY_META[family]["output"]
    name = raw_chain.get('chain_name', '')
    sa = raw_chain.get('saudi_adaptation', '')

    base = []
    if output == "video":
        base.append(f"Do not use without locked first/last frame keyframes")
        base.append(f"Avoid for time-sensitive announcements when not paired with the right occasion")
    if family in ['TF09', 'TF19', 'TF23']:
        base.append("Mixed-gender intimate framing strictly forbidden")
        base.append("Modesty framing rules must be respected per brand cultural spec")
    if family == 'TF23':
        base.append("Never make this look 'produced' — defeats the UGC pretense")
        base.append("Studio lighting prompts disallowed")
    if family in ['TF05', 'TF17', 'TF19']:
        base.append("Face visibility rules must be honored per brand fingerprint")
    if family == 'TF16':
        base.append("Religious occasions require additional CCO review even at enterprise tier")
    if family in ['TF02', 'TF12']:
        base.append("Excessive motion/splash can read as Western fast-food — temper for premium Saudi brands")
    if not base:
        base.append("Maintain alignment with brand fingerprint L3 (visual) and L4 (cinematography) locks")
    return base

def build_chain_json(raw_chain: dict) -> dict:
    family = raw_chain['family_code']
    family_num = int(family[2:])
    code = raw_chain['chain_code']

    meta = FAMILY_META[family]
    output = meta["output"]
    chain_id_short = f"tf{family_num:02d}_{code}"  # e.g., tf01_U01 → not ideal

    # Better: numeric index within family
    # We'll renumber later in build loop; placeholder here
    chain_id_short_temp = code.lower()

    cost, latency = cost_latency(family, output)

    name_en = raw_chain['chain_name'].strip()

    # Construct prompt template by combining the image prompt or video motion prompt with placeholder injection
    image_prompt = raw_chain.get('image_prompt', '').strip()
    video_motion = raw_chain.get('video_motion_prompt', '').strip()
    negative_prompt = raw_chain.get('negative_prompt', '').strip()
    saudi_adaptation = raw_chain.get('saudi_adaptation', '').strip()

    if output == "video":
        # Combine image prompt (for first frame) + video motion
        if image_prompt and video_motion:
            pt = f"First frame keyframe: {image_prompt} Motion: {video_motion} Brand context: {{brand_palette_from_fingerprint}}, {{cinematography_lock_from_fingerprint}}. Cultural compliance: {{cultural_constraints_injection}}."
        elif video_motion:
            pt = f"Video generation: {video_motion} Brand context: {{brand_palette_from_fingerprint}}, {{cinematography_lock_from_fingerprint}}. Cultural compliance: {{cultural_constraints_injection}}."
        else:
            pt = f"Native video generation. Subject: {{subject_description}}. Setting: {{setting_description}}. Duration: {{duration_seconds}}s. Brand context: {{brand_palette_from_fingerprint}}, {{cinematography_lock_from_fingerprint}}. Cultural compliance: {{cultural_constraints_injection}}."
    else:
        if image_prompt:
            pt = f"{image_prompt} Brand context: {{brand_palette_from_fingerprint}}, {{composition_grammar_from_fingerprint}}, {{lighting_style_from_fingerprint}}. Cultural compliance: {{cultural_constraints_injection}}."
        else:
            pt = f"Image generation. Subject: {{subject_description}}. Tone: {{tone_descriptor}}. Brand context: {{brand_palette_from_fingerprint}}, {{composition_grammar_from_fingerprint}}, {{lighting_style_from_fingerprint}}. Cultural compliance: {{cultural_constraints_injection}}."

    # Dimensions
    if family == "TF22":  # premium cinematic
        target_dims = {"width": 1920, "height": 1080, "aspect_ratio_label": "16:9", "duration_seconds": meta["duration"]}
    elif family == "TF23":  # Saudi UGC vertical
        target_dims = {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16", "duration_seconds": meta["duration"]}
    elif family in ["TF10", "TF18"]:  # editorial / flat lay
        target_dims = {"width": 1080, "height": 1350, "aspect_ratio_label": "4:5"}
    else:
        target_dims = {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"}

    # Models
    if output == "video":
        if family == "TF22":
            models = [
                {"provider": "fal", "model_id": "fal-ai/kling-video/v2.1-pro", "role": "primary_video_generation"},
                {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1-ultra", "role": "primary_image_generation", "version_pinned": "v1.1"}
            ]
        else:
            models = [
                {"provider": "fal", "model_id": "fal-ai/kling-video/v2.1-standard", "role": "primary_video_generation"},
                {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "primary_image_generation"}
            ]
    else:
        models = [
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1-ultra", "role": "primary_image_generation", "version_pinned": "v1.1"}
        ]

    # Build the chain dict (placeholder chain_id_short — will be set in batch loop)
    return {
        "raw": raw_chain,
        "name_en": name_en,
        "purpose": raw_chain['description'] or f"{name_en}: {raw_chain.get('family_description', '')}",
        "models_used": models,
        "input_schema": build_input_schema(family, output, output == "video"),
        "prompt_template": pt,
        "negative_prompt_reference": negative_prompt,
        "output_type": output,
        "target_dimensions": target_dims,
        "eligibility_filters": {
            "sectors_allowed": meta["sectors"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": meta["tiers"],
            "min_brand_maturity_days": 14 if "growth" in meta["tiers"][:1] or family in ["TF22"] else 0
        },
        "cultural_constraints": build_cultural_constraints(family, raw_chain),
        "cost_estimate_usd": cost,
        "latency_estimate_seconds": latency,
        "best_for_cd_brains": meta["best_cd"],
        "anti_patterns": derive_anti_patterns(raw_chain, family),
        "saudi_adaptation_note": saudi_adaptation,
    }

# Build name_ar map — minimal Arabic versions for each family
FAMILY_NAMES_AR = {
    "TF01": "البطل النظيف للمنتج",
    "TF02": "الرذاذ والحركة",
    "TF03": "الإضاءة المسرحية والمشهد الداكن",
    "TF04": "البيئة الطبيعية",
    "TF05": "اللمسة البشرية",
    "TF06": "كشف استوديو الإنتاج",
    "TF07": "الباستيل ولعب الظلال",
    "TF08": "البيئة السينمائية",
    "TF09": "البورتريه والموديل",
    "TF10": "البوستر التحريري",
    "TF11": "الملمس والماكرو",
    "TF12": "اللحظة النشطة للمنتج",
    "TF13": "السياق الحياتي",
    "TF14": "المنصة الفاخرة",
    "TF15": "الترويج والنص",
    "TF16": "المناسبات والثقافة",
    "TF17": "التحول قبل/بعد",
    "TF18": "العرض المسطح للمنتج",
    "TF19": "الملابس على الموديل",
    "TF20": "العطر الفاخر والعود",
    "TF21": "دعوة لخدمة",
    "TF22": "الفيديو الأصلي",
    "TF23": "محتوى المستخدم السعودي الأصيل"
}

# Load raw data
with open(RAW_PATH) as f:
    chains_raw = json.load(f)

# Sort by family then by code order in the doc
chains_raw_sorted = sorted(chains_raw, key=lambda c: (int(c['family_code'][2:]), c['chain_code']))

# Track family chain numbering
family_counters = {}
all_built = []

now_iso = "2026-05-13T15:00:00Z"

for raw in chains_raw_sorted:
    family = raw['family_code']
    family_num = int(family[2:])
    family_counters.setdefault(family, 0)
    family_counters[family] += 1
    chain_idx = family_counters[family]
    chain_id_short = f"tf{family_num:02d}_{chain_idx:02d}"

    built = build_chain_json(raw)

    # Filename slug
    name_slug = slugify(built['name_en'])
    filename = f"{chain_id_short}_{name_slug}.json"

    # Now assemble final JSON record
    final = {
        "$schema": "../../12_data_shapes/chain_v1.schema.json",
        "chain_ulid": deterministic_ulid(f"chain:{family}:{raw['chain_code']}:v1"),
        "chain_id_short": chain_id_short,
        "family": family,
        "schema_version": 1,
        "name_en": built['name_en'],
        "name_ar": FAMILY_NAMES_AR.get(family, "") + " — " + raw['chain_code'],
        "purpose": built['purpose'],
        "models_used": built['models_used'],
        "input_schema": built['input_schema'],
        "prompt_template": built['prompt_template'],
        "output_type": built['output_type'],
        "target_dimensions": built['target_dimensions'],
        "eligibility_filters": built['eligibility_filters'],
        "cultural_constraints": built['cultural_constraints'],
        "cost_estimate_usd": built['cost_estimate_usd'],
        "latency_estimate_seconds": built['latency_estimate_seconds'],
        "best_for_cd_brains": built['best_for_cd_brains'],
        "anti_patterns": built['anti_patterns'],
        "notes": f"Source code in research corpus: {raw['chain_code']}. {built.get('saudi_adaptation_note', '')[:300]}",
        "provenance": {
            "source": f"internal_research_corpus/OGz_2_0_ChainLibrary_v2_Complete.docx#{family}#{raw['chain_code']}",
            "date_added": now_iso,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal"
        }
    }

    # Write file
    family_dir = CHAINS_DIR / family
    family_dir.mkdir(exist_ok=True)
    filepath = family_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
        f.write('\n')

    # Also save the negative_prompt reference as a sidecar file for fal.ai runtime
    if built.get('negative_prompt_reference'):
        np_path = family_dir / f"{chain_id_short}.negative_prompt.txt"
        with open(np_path, 'w', encoding='utf-8') as f:
            f.write(built['negative_prompt_reference'] + '\n')

    all_built.append({
        "chain_ulid": final['chain_ulid'],
        "chain_id_short": chain_id_short,
        "family": family,
        "name_en": final['name_en'],
        "output_type": final['output_type'],
        "filename": filename,
        "raw_code": raw['chain_code'],
    })

print(f"Generated {len(all_built)} chains")
print(f"Families: {len(set(c['family'] for c in all_built))}")

# Write index
index = {
    "schema_version": 1,
    "total_chains": len(all_built),
    "total_families": len(set(c['family'] for c in all_built)),
    "generated_at": now_iso,
    "chains": all_built
}
with open(CHAINS_DIR / "INDEX.json", 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)
    f.write('\n')

print(f"INDEX.json written to {CHAINS_DIR / 'INDEX.json'}")
