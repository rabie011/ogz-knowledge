#!/usr/bin/env python3
"""
write_new_chain_families.py
Generate TF24 (Carousel Storytelling, 6 chains) +
         TF25 (Reels-First, 4 chains) +
         TF26 (UGC/Face-to-Cam, 3 chains)
Updates 02_what_to_build/INDEX.json.

Usage:
  python3 scripts/write_new_chain_families.py
  python3 scripts/write_new_chain_families.py --dry-run

Safe to re-run: skips files that already exist.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from ulid import ULID

BASE       = Path(__file__).parent.parent
CHAINS_DIR = BASE / "02_what_to_build"
INDEX_FILE = CHAINS_DIR / "INDEX.json"
NOW        = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
DRY_RUN    = "--dry-run" in sys.argv

# ── Chain definitions ──────────────────────────────────────────────────────────

TF24_CHAINS = [
    {
        "chain_id_short": "tf24_01",
        "name_en": "Heritage Journey Carousel",
        "name_ar": "كاروسيل رحلة التراث",
        "purpose": "Multi-slide brand story rooted in Saudi heritage. Slides progress from historical roots to modern expression. Highest-engagement format (74% high-eng in corpus).",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi heritage brand storytelling carousel slide {slide_number} of {total_slides}. Visual theme: {heritage_element}. Slide narrative: {slide_story_beat}. Color palette: warm amber, gold, deep brown. Typography: Arabic calligraphy accent on {brand_name}. No people visible. Clean editorial layout. {cultural_constraints_injection}",
        "input_schema": {
            "heritage_element": {"type": "string", "description": "Specific heritage reference: ingredient, tradition, landmark, craft", "required": True},
            "brand_name": {"type": "string", "description": "Brand name for caption/overlay", "required": True},
            "slide_story_beat": {"type": "string", "description": "What this specific slide communicates in the story arc", "required": True},
            "slide_number": {"type": "integer", "description": "Slide position (1-based)", "required": False, "default": 1},
            "total_slides": {"type": "integer", "description": "Total slide count in carousel (typically 5-7)", "required": False, "default": 5},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "primary_image_generation"},
            {"provider": "fal", "model_id": "fal-ai/ideogram/v2", "role": "text_overlay_variant"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.25,
        "latency_estimate_seconds": 60,
        "best_for_cd_brains": ["cd_01", "cd_02", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "scale",
        },
        "anti_patterns": ["Avoid generic stock imagery", "Avoid Western heritage references", "Avoid more than 8 slides"],
        "notes": "Top-performing format in corpus. Heritage framing adds +19% vs modern. Use 5-7 slides minimum for storytelling arc. Last slide must include brand CTA. Arabic calligraphy on slide 1 performs best.",
    },
    {
        "chain_id_short": "tf24_02",
        "name_en": "Product Range Reveal Carousel",
        "name_ar": "كاروسيل عرض منتجات المجموعة",
        "purpose": "Systematic product showcase: each slide = one hero product with name, key benefit, visual. Final slide = full range + CTA. Strong for launches.",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi product showcase carousel. Product: {product_name}. Hero shot on {background_color} background. Key benefit displayed: {product_benefit}. Minimalist layout, product centered, brand color accent. Professional studio quality. No lifestyle elements. {cultural_constraints_injection}",
        "input_schema": {
            "product_name": {"type": "string", "description": "Product name to feature on this slide", "required": True},
            "product_benefit": {"type": "string", "description": "Single key benefit or feature to highlight", "required": True},
            "background_color": {"type": "string", "description": "Background color direction", "required": False, "default": "white"},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "primary_image_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.15,
        "latency_estimate_seconds": 45,
        "best_for_cd_brains": ["cd_01", "cd_03", "cd_04"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": False,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "never",
        },
        "anti_patterns": ["Avoid more than 6 products per carousel", "Avoid busy backgrounds", "Avoid inconsistent visual style across slides"],
        "notes": "Best for product launches and seasonal collections. Each slide must follow identical visual template for brand consistency. Final slide should show full range in grid.",
    },
    {
        "chain_id_short": "tf24_03",
        "name_en": "Recipe Steps Carousel",
        "name_ar": "كاروسيل خطوات الوصفة",
        "purpose": "F&B step-by-step recipe: slide 1=ingredients flat lay, slides 2-5=prep steps, final=plated result. High save/share rates drive algorithmic reach.",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi recipe carousel slide. Step: {step_name} ({step_number} of {total_steps}). Scene: {step_visual_description}. Food styling: authentic Saudi presentation. Warm natural lighting. Hands may appear if showing technique. Arabic step number overlay: {arabic_step_number}. Brand color accent in corner. {cultural_constraints_injection}",
        "input_schema": {
            "step_name": {"type": "string", "description": "Name of this recipe step", "required": True},
            "step_visual_description": {"type": "string", "description": "What to show in this step: ingredients, action, tool", "required": True},
            "step_number": {"type": "integer", "description": "Step number (1-based)", "required": False, "default": 1},
            "total_steps": {"type": "integer", "description": "Total steps in recipe", "required": False, "default": 5},
            "arabic_step_number": {"type": "string", "description": "Arabic numeral for overlay e.g. الخطوة ١", "required": False},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "primary_image_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.18,
        "latency_estimate_seconds": 50,
        "best_for_cd_brains": ["cd_02", "cd_04"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "scale",
        },
        "anti_patterns": ["Avoid showing alcohol", "Avoid non-halal ingredients", "Avoid Western-style plating that conflicts with Saudi aesthetic"],
        "notes": "F&B only. Ramadan recipe carousels get 3x saves vs standard posts. Always show final plated result as last slide. Hand gestures must follow cultural guidance.",
    },
    {
        "chain_id_short": "tf24_04",
        "name_en": "Before / After Transformation Carousel",
        "name_ar": "كاروسيل قبل وبعد",
        "purpose": "Split journey: first half = before state, second half = after + brand transformation. Strong for beauty and F&B results-driven content.",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi {sector} transformation carousel. Stage: {stage} ({before_or_after}). Subject: {subject_description}. Visual treatment: {visual_style}. Consistent framing across before and after slides for direct comparison. Brand identity visible. Clean professional quality. {cultural_constraints_injection}",
        "input_schema": {
            "stage": {"type": "string", "description": "Transformation stage label e.g. 'Day 0' / 'Day 30'", "required": True},
            "before_or_after": {"type": "string", "description": "'before' or 'after'", "required": True},
            "subject_description": {"type": "string", "description": "What is being transformed", "required": True},
            "sector": {"type": "string", "description": "Sector context", "required": False, "default": "beauty"},
            "visual_style": {"type": "string", "description": "Visual treatment direction", "required": False, "default": "clinical editorial"},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "primary_image_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["beauty", "f_and_b"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 30,
        },
        "cost_estimate_usd": 0.12,
        "latency_estimate_seconds": 35,
        "best_for_cd_brains": ["cd_01", "cd_03"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid unrealistic results claims", "Avoid revealing face for female subjects without explicit approval", "Avoid inconsistent lighting between before/after slides"],
        "notes": "Beauty sector: enhancement framing outperforms transformation. Avoid claims that could trigger regulatory concerns. Saudi female subjects require abaya/modest styling unless brand has confirmed exception.",
    },
    {
        "chain_id_short": "tf24_05",
        "name_en": "Cultural Occasion Story Carousel",
        "name_ar": "كاروسيل قصة مناسبة ثقافية",
        "purpose": "Occasion-led narrative carousel: slide 1=greeting, slides 2-4=brand/cultural content, final=CTA. Eid Al-Fitr posts using this format hit 78% high-eng.",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi {occasion} occasion carousel slide {slide_number}. Visual theme: {occasion_visual_element}. Message: {slide_message}. Color palette: {occasion_colors}. Arabic typography dominant. Warm celebratory tone. Brand {brand_name} subtly integrated. No conflicting imagery. {cultural_constraints_injection}",
        "input_schema": {
            "occasion": {"type": "string", "description": "Cultural occasion: ramadan | eid_al_fitr | national_day | founding_day | eid_al_adha", "required": True},
            "occasion_visual_element": {"type": "string", "description": "Key visual symbol for this occasion", "required": True},
            "slide_message": {"type": "string", "description": "Message or story beat for this slide", "required": True},
            "occasion_colors": {"type": "string", "description": "Color palette for occasion", "required": False, "default": "gold, green, white"},
            "brand_name": {"type": "string", "description": "Brand name", "required": False},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/ideogram/v2", "role": "primary_image_generation"},
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "photographic_variant"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["ramadan", "eid_al_fitr", "eid_al_adha", "national_day", "founding_day"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.22,
        "latency_estimate_seconds": 55,
        "best_for_cd_brains": ["cd_01", "cd_02", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": True,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid mixing Eid Al-Fitr and Eid Al-Adha imagery (completely different energy)", "Avoid generic crescent moon without context", "Avoid non-Saudi cultural symbols"],
        "notes": "Eid Al-Fitr = 78% high-eng | Eid Al-Adha = 11% — treat completely differently. National Day slides must use Saudi green palette. Ramadan slides: warm amber + lantern motifs perform best.",
    },
    {
        "chain_id_short": "tf24_06",
        "name_en": "Education & Tips Carousel",
        "name_ar": "كاروسيل تعليمي ونصائح",
        "purpose": "5-7 tip slides on brand-adjacent topic. Positions brand as authority. High save rate drives long-tail algorithmic distribution.",
        "output_type": "carousel_slide",
        "target_dimensions": {"width": 1080, "height": 1080, "aspect_ratio_label": "1:1"},
        "prompt_template": "Saudi educational content carousel slide {slide_number}. Topic: {topic_title}. Tip number {tip_number}: {tip_text}. Layout: bold tip number in brand color, Arabic headline, supporting visual icon or graphic. Clean minimalist background: {background_style}. Brand {brand_name} in corner. No product hard sell. {cultural_constraints_injection}",
        "input_schema": {
            "topic_title": {"type": "string", "description": "Overall educational topic e.g. 'Skincare Routine for Saudi Climate'", "required": True},
            "tip_number": {"type": "integer", "description": "Tip number on this slide", "required": True},
            "tip_text": {"type": "string", "description": "The actual tip content (keep under 20 words)", "required": True},
            "background_style": {"type": "string", "description": "Background treatment: minimal | textured | gradient", "required": False, "default": "minimal"},
            "brand_name": {"type": "string", "description": "Brand name for corner placement", "required": False},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/ideogram/v2", "role": "primary_image_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.10,
        "latency_estimate_seconds": 30,
        "best_for_cd_brains": ["cd_02", "cd_04", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "never",
        },
        "anti_patterns": ["Avoid making the last slide feel like an ad", "Avoid more than 8 slides", "Avoid topics already covered by major media outlets without adding unique Saudi angle"],
        "notes": "Education carousels are the highest save-rate format. Topic should be genuinely useful. First slide = hook question or bold claim. Save CTA on last slide. Arabic content performs better than bilingual for this format.",
    },
]

TF25_CHAINS = [
    {
        "chain_id_short": "tf25_01",
        "name_en": "Dramatic Product Reveal Reel",
        "name_ar": "ريل كشف المنتج الدرامي",
        "purpose": "Reel: starts dark/obscured, dramatic reveal clears to hero product shot. 8-15 seconds. High thumb-stop rate.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi product reveal video sequence. Phase 1 (0-3s): {reveal_buildup} — dark or obscured product. Phase 2 (3-8s): dramatic reveal — {product_name} in full glory, {product_visual_description}. Phase 3 (8s+): beauty shot hold, {brand_color} accent animation. Music: {music_energy} beat. No voiceover. {cultural_constraints_injection}",
        "input_schema": {
            "product_name": {"type": "string", "description": "Product being revealed", "required": True},
            "product_visual_description": {"type": "string", "description": "How the product looks at peak reveal", "required": True},
            "reveal_buildup": {"type": "string", "description": "How the buildup looks before reveal e.g. fog, shadow, wrap", "required": False, "default": "fog dissipating"},
            "brand_color": {"type": "string", "description": "Brand primary color for accent", "required": False, "default": "gold"},
            "music_energy": {"type": "string", "description": "Music direction: subtle/dramatic/cinematic", "required": False, "default": "cinematic"},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/kling-video/v1.6/pro/text-to-video", "role": "primary_video_generation"},
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "keyframe_reference"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.45,
        "latency_estimate_seconds": 180,
        "best_for_cd_brains": ["cd_01", "cd_03", "cd_04"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid reveal longer than 5 seconds — kills thumb-stop", "Avoid human faces as the reveal subject without wardrobe check", "Avoid cluttered backgrounds post-reveal"],
        "notes": "Launches and new products. First 3 frames must create mystery. Kling v1.6 Pro gives best motion quality. Audio: no voiceover — music + sound design only.",
    },
    {
        "chain_id_short": "tf25_02",
        "name_en": "ASMR Texture Reel",
        "name_ar": "ريل نكهة وملمس ASMR",
        "purpose": "Sensory close-up reel: sound-forward, texture detail, pouring, cutting. No voiceover. 10-20 seconds. F&B and beauty. Triggers sensory engagement.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi sensory {sector} product ASMR reel. Subject: {subject}. Camera: extreme macro close-up, {texture_type} texture, {motion_type} motion. Lighting: {lighting}: soft diffuse, no harsh shadows. Sound: {asmr_sound}. No music track — pure ambient sound. Slow motion {slowmo_multiplier}x. {cultural_constraints_injection}",
        "input_schema": {
            "subject": {"type": "string", "description": "What to film: food item, beverage, product texture", "required": True},
            "texture_type": {"type": "string", "description": "Texture to highlight: crispy, smooth, melting, foamy, granular", "required": True},
            "motion_type": {"type": "string", "description": "Motion: pour, slice, swirl, drip, spread", "required": True},
            "sector": {"type": "string", "description": "Sector context", "required": False, "default": "f_and_b"},
            "lighting": {"type": "string", "description": "Lighting setup direction", "required": False, "default": "warm backlit"},
            "asmr_sound": {"type": "string", "description": "Sound design note for editor", "required": False, "default": "natural food texture sounds amplified"},
            "slowmo_multiplier": {"type": "integer", "description": "Slow motion multiplier", "required": False, "default": 4},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/kling-video/v1.6/pro/image-to-video", "role": "primary_video_generation"},
            {"provider": "fal", "model_id": "fal-ai/flux-pro/v1.1", "role": "keyframe_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.40,
        "latency_estimate_seconds": 150,
        "best_for_cd_brains": ["cd_02", "cd_04"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": False,
            "requires_arabic_text_validation": False,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "never",
        },
        "anti_patterns": ["Avoid music — pure ASMR sound only", "Avoid showing full product packaging (keep it sensory)", "Avoid Ramadan-sensitive food content during fasting hours"],
        "notes": "Best performing reel format for F&B (corpus: reels 65% high-eng). Winter season amplifies food ASMR +25%. No Arabic text needed — purely sensory.",
    },
    {
        "chain_id_short": "tf25_03",
        "name_en": "Behind The Scenes Reel",
        "name_ar": "ريل خلف الكواليس",
        "purpose": "Authentic BTS reel: kitchen/workshop/team in action. Fast cuts (1-2s each), real moments, builds trust and authenticity. 15-30 seconds.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi {sector} behind-the-scenes reel storyboard. Scene {scene_number}: {scene_description}. Location: {location_type}. Characters: {character_description}. Camera style: handheld authentic, not staged. Lighting: available light + practical sources. Energy: {energy_level}. Optional text overlay: {overlay_text}. {cultural_constraints_injection}",
        "input_schema": {
            "scene_description": {"type": "string", "description": "What happens in this BTS scene", "required": True},
            "location_type": {"type": "string", "description": "Where it happens: kitchen | workshop | office | store floor", "required": True},
            "character_description": {"type": "string", "description": "Who appears — role not name, e.g. head chef, store manager", "required": False},
            "sector": {"type": "string", "description": "Sector context", "required": False, "default": "f_and_b"},
            "scene_number": {"type": "integer", "description": "Scene number in sequence", "required": False, "default": 1},
            "energy_level": {"type": "string", "description": "Pace and mood: calm | energetic | intense", "required": False, "default": "energetic"},
            "overlay_text": {"type": "string", "description": "Optional text overlay in Arabic for this scene", "required": False},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/kling-video/v1.6/pro/text-to-video", "role": "primary_video_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 14,
        },
        "cost_estimate_usd": 0.35,
        "latency_estimate_seconds": 120,
        "best_for_cd_brains": ["cd_02", "cd_04", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid staged 'authentic' shots — must look real", "Avoid showing staff without consent protocols", "Avoid showing religious practice in commercial context"],
        "notes": "Transparency/BTS pattern = 0% high-eng when poorly executed but 56% when genuine. Real unpolished moments outperform produced. Wardrobe must follow sector norms. Show Saudi staff when possible — local pride driver.",
    },
    {
        "chain_id_short": "tf25_04",
        "name_en": "Occasion Motion Greeting Reel",
        "name_ar": "ريل تهنئة مناسبة متحركة",
        "purpose": "Cultural occasion greeting in reel format: motion graphics + brand logo + Arabic typography + occasion visual. 8-12 seconds. High share rate around key dates.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi {occasion} animated greeting video. Visual sequence: {animation_description}. Color palette: {occasion_colors}. Arabic greeting text animation: {greeting_text}. Brand logo: entrance at {logo_entrance_time}s. Particle effects: {particle_type}. Duration: {duration}s. Mood: {mood}. No product features — pure occasion celebration. {cultural_constraints_injection}",
        "input_schema": {
            "occasion": {"type": "string", "description": "Occasion: ramadan | eid_al_fitr | national_day | founding_day | eid_al_adha", "required": True},
            "greeting_text": {"type": "string", "description": "Arabic greeting text to animate", "required": True},
            "occasion_colors": {"type": "string", "description": "Color palette", "required": False, "default": "gold, green, white"},
            "animation_description": {"type": "string", "description": "Visual animation description", "required": False, "default": "particles forming crescent then exploding into brand identity"},
            "particle_type": {"type": "string", "description": "Particle effect: stars | lanterns | petals | geometric", "required": False, "default": "stars"},
            "logo_entrance_time": {"type": "integer", "description": "When brand logo appears in seconds", "required": False, "default": 6},
            "duration": {"type": "integer", "description": "Total duration in seconds", "required": False, "default": 10},
            "mood": {"type": "string", "description": "Overall mood direction", "required": False, "default": "celebratory warm"},
        },
        "models_used": [
            {"provider": "fal", "model_id": "fal-ai/kling-video/v1.6/pro/text-to-video", "role": "primary_video_generation"},
            {"provider": "fal", "model_id": "fal-ai/ideogram/v2", "role": "keyframe_with_arabic_text"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["ramadan", "eid_al_fitr", "eid_al_adha", "national_day", "founding_day"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 0,
        },
        "cost_estimate_usd": 0.50,
        "latency_estimate_seconds": 200,
        "best_for_cd_brains": ["cd_01", "cd_02", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": False,
            "requires_gesture_check": False,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": True,
            "high_gender_sensitivity": False,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid product features in occasion greeting — it reads as exploitative", "Avoid mixing Eid Al-Fitr and Eid Al-Adha visual language", "Avoid Western holiday aesthetic"],
        "notes": "Must post 1-2 days before occasion for maximum reach. Eid Al-Fitr = 78% high-eng vs Eid Al-Adha = 11% — completely different strategy required. National Day: Saudi green dominant. Ramadan: lantern + crescent + warm amber mandatory.",
    },
]

TF26_CHAINS = [
    {
        "chain_id_short": "tf26_01",
        "name_en": "Staff Pride Story",
        "name_ar": "قصة فخر الموظف",
        "purpose": "Employee facing camera shares authentic story about their role, pride, and brand love. UGC-style. 0% corpus high-eng when formulaic, 100% when genuine.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi {sector} employee pride video brief. Subject: {employee_role} sharing story about {story_topic}. Setting: {location} — on-brand background, clean. Tone: warm, genuine, unscripted feel. Camera: phone-quality acceptable. Duration: {duration}s. Arabic subtitles required: {subtitle_note}. Brand identifier: {brand_display}. {cultural_constraints_injection}",
        "input_schema": {
            "employee_role": {"type": "string", "description": "Employee role e.g. 'head chef', 'store manager', 'barista'", "required": True},
            "story_topic": {"type": "string", "description": "What the employee talks about: a moment of pride, a skill, their journey", "required": True},
            "location": {"type": "string", "description": "Where they film: kitchen, store floor, workshop", "required": True},
            "sector": {"type": "string", "description": "Sector context", "required": False, "default": "f_and_b"},
            "duration": {"type": "integer", "description": "Target duration in seconds (30-60 recommended)", "required": False, "default": 45},
            "subtitle_note": {"type": "string", "description": "Subtitle style direction", "required": False, "default": "Arabic subtitles, brand font, bottom third"},
            "brand_display": {"type": "string", "description": "How to show brand: logo corner | uniform | background signage", "required": False, "default": "uniform + logo corner"},
        },
        "models_used": [
            {"provider": "none", "model_id": "real_person_filming", "role": "primary_capture_no_ai_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 30,
        },
        "cost_estimate_usd": 0.02,
        "latency_estimate_seconds": 0,
        "best_for_cd_brains": ["cd_02", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid scripted corporate-speak — must feel genuine", "Avoid filming female employees without explicit consent and wardrobe approval", "Avoid employee_pride_campaign pattern (low-eng) in favor of genuine individual stories"],
        "notes": "This is the only chain with no AI generation — pure UGC. employee_pride_campaign pattern = 7 obs, 100% high-eng. Real person, real story. Arabic subtitles mandatory. Saudi staff when possible. Must get written consent.",
    },
    {
        "chain_id_short": "tf26_02",
        "name_en": "Customer Testimonial UGC",
        "name_ar": "تجربة العميل الحقيقية",
        "purpose": "Real customer (or brand ambassador) facing camera sharing genuine product experience. Peer validation drives conversion better than brand claims.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi customer testimonial video brief. Customer profile: {customer_profile}. Product/experience being reviewed: {product_name}. Key message: {key_testimonial_point}. Setting: natural environment — {setting}. Duration: {duration}s. Style: casual unscripted, phone-shot acceptable. Arabic subtitles. Brand overlay: {brand_display}. {cultural_constraints_injection}",
        "input_schema": {
            "customer_profile": {"type": "string", "description": "Customer type e.g. 'young Saudi mother', 'university student', 'professional man'", "required": True},
            "product_name": {"type": "string", "description": "Product or experience being reviewed", "required": True},
            "key_testimonial_point": {"type": "string", "description": "The core thing they should convey: taste, result, convenience, value", "required": True},
            "setting": {"type": "string", "description": "Where they film: home, cafe, workplace", "required": False, "default": "home living room"},
            "duration": {"type": "integer", "description": "Target duration in seconds", "required": False, "default": 30},
            "brand_display": {"type": "string", "description": "Brand display strategy", "required": False, "default": "lower-third name card + product in hand"},
        },
        "models_used": [
            {"provider": "none", "model_id": "real_person_filming", "role": "primary_capture_no_ai_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 14,
        },
        "cost_estimate_usd": 0.01,
        "latency_estimate_seconds": 0,
        "best_for_cd_brains": ["cd_03", "cd_04"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid scripted testimonials — audiences detect inauthenticity immediately", "Avoid influencer_review pattern (0% high-eng) in favor of genuine customers", "Avoid filming without explicit consent and location approval"],
        "notes": "influencer_review = 0% high-eng (4 obs). Genuine customer > paid influencer in Saudi market. Must get written consent. Arabic subtitles required. Product must be visible. Keep under 45 seconds.",
    },
    {
        "chain_id_short": "tf26_03",
        "name_en": "Expert Founder Tip",
        "name_ar": "نصيحة خبير أو مؤسس",
        "purpose": "Brand expert or founder shares one actionable tip related to brand expertise. Credibility-building, authority positioning. brand_values pattern = 4 obs, 100% high-eng.",
        "output_type": "video",
        "target_dimensions": {"width": 1080, "height": 1920, "aspect_ratio_label": "9:16"},
        "prompt_template": "Saudi brand expert tip video brief. Expert: {expert_role} at {brand_name}. Topic: one tip about {expertise_area}. Format: direct to camera, {duration}s, confident professional tone. Setting: {setting} — on-brand, clean, professional. Language: {language}. Arabic caption card required: {tip_in_arabic}. {cultural_constraints_injection}",
        "input_schema": {
            "expert_role": {"type": "string", "description": "Expert's role: founder | head chef | beauty expert | retail director", "required": True},
            "expertise_area": {"type": "string", "description": "Topic area of the tip", "required": True},
            "brand_name": {"type": "string", "description": "Brand name", "required": True},
            "tip_in_arabic": {"type": "string", "description": "The tip summarized in Arabic for the caption card (max 15 words)", "required": False},
            "setting": {"type": "string", "description": "Filming setting", "required": False, "default": "branded workspace"},
            "language": {"type": "string", "description": "Language for delivery: arabic | english | bilingual", "required": False, "default": "arabic"},
            "duration": {"type": "integer", "description": "Duration in seconds (20-45 optimal)", "required": False, "default": 30},
        },
        "models_used": [
            {"provider": "none", "model_id": "real_person_filming", "role": "primary_capture_no_ai_generation"},
        ],
        "eligibility_filters": {
            "sectors_allowed": ["f_and_b", "beauty", "retail"],
            "occasions_allowed": ["*"],
            "quality_tiers_allowed": ["growth", "scale"],
            "min_brand_maturity_days": 30,
        },
        "cost_estimate_usd": 0.02,
        "latency_estimate_seconds": 0,
        "best_for_cd_brains": ["cd_01", "cd_02", "cd_05"],
        "cultural_constraints": {
            "requires_wardrobe_check": True,
            "requires_gesture_check": True,
            "requires_cultural_coherence_check": True,
            "requires_arabic_text_validation": True,
            "high_religious_sensitivity": False,
            "high_gender_sensitivity": True,
            "human_review_recommended_above_quality_tier": "growth",
        },
        "anti_patterns": ["Avoid generic advice not tied to brand expertise", "Avoid more than one tip per video", "Avoid reading off a script — must be conversational"],
        "notes": "brand_values = 100% high-eng (4 obs). One tip, one video. Arabic delivery preferred. Founder face = authentic. Must follow wardrobe and gesture guidelines. Keep under 45 seconds. Arabic caption card = mandatory.",
    },
]

FAMILY_DEFINITIONS = {
    "TF24": {
        "name": "Carousel Storytelling",
        "rationale": "Carousel = 74% high-eng in corpus (#1 format). 0 carousel-native chains in TF01-TF23. Gap filled here.",
        "chains": TF24_CHAINS,
    },
    "TF25": {
        "name": "Reels-First Content",
        "rationale": "Reels = 65% high-eng. Only 5 reel chains in TF01-TF23. Adding 4 critical formats.",
        "chains": TF25_CHAINS,
    },
    "TF26": {
        "name": "UGC Face-to-Cam",
        "rationale": "0 UGC/face-to-cam chains. brand_values + employee_pride = 100% high-eng patterns. Filling gap.",
        "chains": TF26_CHAINS,
    },
}


# ── Write chains + update INDEX ────────────────────────────────────────────────

def _slug(name_en: str) -> str:
    return name_en.lower().replace(" ", "_").replace("/", "_").replace("&", "and")


def write_chains():
    index = json.loads(INDEX_FILE.read_text())
    existing_ids = {c.get("chain_id_short") for c in index.get("chains", [])}
    new_chains_written = 0
    new_index_entries  = []

    for family_id, fam_def in FAMILY_DEFINITIONS.items():
        tf_dir = CHAINS_DIR / family_id
        if not DRY_RUN:
            tf_dir.mkdir(exist_ok=True)

        chain_codes = []
        for chain_def in fam_def["chains"]:
            cid = chain_def["chain_id_short"]
            chain_codes.append(cid)

            filename = f"{cid}_{_slug(chain_def['name_en'])}.json"
            out_path  = tf_dir / filename

            if out_path.exists() and cid in existing_ids:
                print(f"  ⏭  {cid} already exists — skipping")
                continue

            ulid_val = str(ULID())
            chain_json = {
                "$schema": "../../12_data_shapes/chain_v1.schema.json",
                "chain_ulid": ulid_val,
                "chain_id_short": cid,
                "family": family_id,
                "schema_version": 1,
                "name_en": chain_def["name_en"],
                "name_ar": chain_def["name_ar"],
                "purpose": chain_def["purpose"],
                "models_used": chain_def["models_used"],
                "input_schema": chain_def["input_schema"],
                "prompt_template": chain_def["prompt_template"],
                "output_type": chain_def["output_type"],
                "target_dimensions": chain_def["target_dimensions"],
                "eligibility_filters": chain_def["eligibility_filters"],
                "cultural_constraints": chain_def["cultural_constraints"],
                "cost_estimate_usd": chain_def["cost_estimate_usd"],
                "latency_estimate_seconds": chain_def["latency_estimate_seconds"],
                "best_for_cd_brains": chain_def["best_for_cd_brains"],
                "anti_patterns": chain_def["anti_patterns"],
                "notes": chain_def["notes"],
                "provenance": {
                    "source": "ogz_knowledge_phase5_autonomous_system",
                    "date_added": NOW,
                    "confirmer": "claude_code_extraction",
                    "confidence": "experimental",
                    "scope": "saudi_instagram_corpus",
                },
            }

            if DRY_RUN:
                print(f"  DRY  [{cid}] → {family_id}/{filename}  (${chain_def['cost_estimate_usd']:.2f})")
            else:
                out_path.write_text(json.dumps(chain_json, ensure_ascii=False, indent=2))
                print(f"  ✅  [{cid}] {chain_def['name_en']} → {family_id}/{filename}")
                new_chains_written += 1

            ef = chain_def["eligibility_filters"]
            new_index_entries.append({
                "chain_ulid": ulid_val,
                "chain_id_short": cid,
                "family": family_id,
                "name_en": chain_def["name_en"],
                "name_ar": chain_def["name_ar"],
                "output_type": chain_def["output_type"],
                "filename": filename,
                "cost_estimate_usd": chain_def["cost_estimate_usd"],
                "quality_tiers_allowed": ef.get("quality_tiers_allowed", []),
                "sectors_allowed": ef.get("sectors_allowed", []),
                "occasions_allowed": ef.get("occasions_allowed", []),
                "best_for_cd_brains": chain_def["best_for_cd_brains"],
            })

        # Add/update family in families list
        fam_entry = {
            "family_id": family_id,
            "name": fam_def["name"],
            "chain_count": len(chain_codes),
            "chain_codes_in_family": chain_codes,
        }
        existing_families = [f["family_id"] for f in index.get("families", [])]
        if family_id in existing_families:
            idx = existing_families.index(family_id)
            index["families"][idx] = fam_entry
        else:
            index["families"].append(fam_entry)

    # Update index chains list
    if not DRY_RUN and new_index_entries:
        existing_chain_ids = {c["chain_id_short"] for c in index.get("chains", [])}
        for entry in new_index_entries:
            if entry["chain_id_short"] not in existing_chain_ids:
                index.setdefault("chains", []).append(entry)

        total = sum(f.get("chain_count", 0) for f in index["families"])
        index["total_chains"]   = total
        index["total_families"] = len(index["families"])
        index["generated_at"]   = NOW
        INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        print(f"\n  INDEX updated: {total} total chains across {index['total_families']} families")

    return new_chains_written


def main():
    if DRY_RUN:
        print("DRY RUN — no files will be written\n")

    total_planned = sum(len(fd["chains"]) for fd in FAMILY_DEFINITIONS.values())
    print(f"Writing {total_planned} new chains: TF24 (6) + TF25 (4) + TF26 (3)\n")

    written = write_chains()

    print(f"\n{'='*60}")
    if DRY_RUN:
        print(f"DRY RUN COMPLETE: would write {total_planned} chains")
    else:
        print(f"COMPLETE: Wrote {written} new chain files")
        print(f"\nNext step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
