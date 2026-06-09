"""
chain_router.py — CD brain → TF visual chain selector.

Given: cd_primary, sector, occasion, brand context
Returns: best matching chain + partially-filled prompt template

Usage:
    from lib.chain_router import select_chain, fill_prompt

    chain = select_chain(cd_primary='cd_01_firaasa_architect', sector='f_and_b', occasion='founding_day')
    prompt = fill_prompt(chain, brand='albaik', product='بروستد', sector='f_and_b', occasion='founding_day', brand_color='#1a5f30')
"""
from __future__ import annotations

import json
import os
import re
import psycopg2
import psycopg2.extras
from pathlib import Path

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge")

# ── CD technique → preferred TF families (primary, fallback, last_resort) ────
# Order matters — first match wins
_CD_TO_TF = {
    "cd_01": ["TF20", "TF13", "TF02", "TF01"],   # Firaasa (behavioral observation) → food gathering, lifestyle
    "cd_02": ["TF21", "TF14", "TF02", "TF01"],   # Metaphor Architect → dramatic reveal, conceptual, product hero
    "cd_03": ["TF13", "TF20", "TF02", "TF01"],   # Authenticity Detective → real food moment, lifestyle
    "cd_04": ["TF19", "TF04", "TF06", "TF01"],   # Heritage Decoder → heritage craft, texture, material
    "cd_05": ["TF01", "TF23", "TF12", "TF02"],   # Paradox Hunter → product hero, bold statement, contrast
}

# Sector-specific family overrides — some sectors need completely different visual treatment
# Real estate: architectural shots, not food/fragrance. Healthcare: clean wellness, not food.
_SECTOR_FAMILY_OVERRIDE = {
    "real_estate":        ["TF04", "TF02", "TF01", "TF06"],  # interior design, product hero, studio
    "healthcare_wellness": ["TF04", "TF01", "TF02", "TF23"], # clean aesthetic, hero product, bold
}

# Normalize cd_primary string → short cd key
def _cd_key(cd_primary: str) -> str:
    m = re.search(r"cd_0?(\d)", cd_primary or "")
    return f"cd_0{m.group(1)}" if m else "cd_01"

def select_chain(cd_primary: str, sector: str, occasion: str = "*") -> dict | None:
    """
    Select the best TF visual chain for a given CD technique + sector.
    Returns the chain row dict or None if DB is unavailable.
    """
    cd_key = _cd_key(cd_primary)
    # Sector override takes precedence — some sectors need specific visual families
    preferred_families = _SECTOR_FAMILY_OVERRIDE.get(sector) or _CD_TO_TF.get(cd_key, ["TF01", "TF02"])

    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        cur = conn.cursor()

        # Try each preferred family in order until we find a matching chain
        for family in preferred_families:
            cur.execute("""
                SELECT chain_id_short, family, name_en,
                       payload->>'name_ar' as name_ar,
                       output_type,
                       best_for_cd_brains, sectors_allowed, payload,
                       payload->>'latency_estimate_seconds' as latency_estimate_seconds
                FROM chains
                WHERE family = %s
                  AND best_for_cd_brains @> %s::jsonb
                  AND (
                    sectors_allowed @> %s::jsonb
                    OR sectors_allowed @> '["*"]'::jsonb
                  )
                ORDER BY
                    CASE output_type WHEN 'image' THEN 0 WHEN 'carousel' THEN 1 ELSE 2 END,
                    jsonb_array_length(COALESCE(best_for_cd_brains, '[]'::jsonb)) DESC
                LIMIT 1
            """, (family, f'["{cd_key}"]', f'["{sector}"]'))
            row = cur.fetchone()
            if row:
                cur.close()
                conn.close()
                return dict(row)

        # Fallback: any image chain for this CD + sector
        cur.execute("""
            SELECT chain_id_short, family, name_en,
                   payload->>'name_ar' as name_ar,
                   output_type,
                   best_for_cd_brains, sectors_allowed, payload,
                   payload->>'latency_estimate_seconds' as latency_estimate_seconds
            FROM chains
            WHERE best_for_cd_brains @> %s::jsonb
              AND (
                sectors_allowed @> %s::jsonb
                OR sectors_allowed @> '["*"]'::jsonb
              )
            ORDER BY
                CASE output_type WHEN 'image' THEN 0 ELSE 1 END
            LIMIT 1
        """, (f'["{cd_key}"]', f'["{sector}"]'))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None

    except Exception:
        return None


def _load_brand_context(brand: str) -> dict:
    """Load visual context for a brand from brand_visual_context.json."""
    ctx_path = Path(__file__).resolve().parent.parent.parent / "logs" / "brand_visual_context.json"
    try:
        with open(ctx_path) as f:
            ctx = json.load(f)
        return ctx.get(brand, ctx.get(brand.lower(), {}))
    except Exception:
        return {}


def fill_prompt(
    chain: dict,
    brand: str = "",
    product: str = "",
    sector: str = "",
    occasion: str = "",
    brand_color: str = "",
    brand_display: str = "",
    extra: dict | None = None,
) -> str:
    """
    Fill known variables in the chain's prompt_template.
    Loads brand visual context (colors, setting, lighting) automatically.
    Unknown variables are left as {VAR_NAME} so Hesham's platform can fill the rest.
    """
    payload = chain.get("payload", {})
    template = payload.get("prompt_template", "")
    if not template:
        return ""

    # Load brand visual context from brand_dna
    bctx = _load_brand_context(brand)

    # Cultural constraints injection — always applied for Saudi content
    cultural_inject = (
        "Saudi cultural adaptation: modest dress, no face close-ups (CS-24), "
        "warm golden lighting preferred, authentic Saudi settings"
    )

    # Occasion visual atmosphere mapping
    _occasion_atmosphere = {
        "national_day":    "Saudi national pride colors, green and white palette",
        "founding_day":    "warm heritage gold tones, Saudi heritage motifs",
        "ramadan":         "crescent moon motifs, warm amber evening light, lantern glow",
        "eid_al_fitr":     "celebratory gold and cream, festive warm atmosphere",
        "eid_al_adha":     "earthy tones, family gathering warmth",
        "white_friday":    "bold contrast, sale energy, high-impact composition",
        "summer_campaign": "bright natural light, warm Saudi outdoor setting",
        "evergreen":       "clean neutral backdrop, timeless composition",
    }

    # Brand display names
    _brand_ar = {
        "albaik": "البيك", "barnscoffee": "بارنز", "mcdonaldsksa": "ماكدونالدز",
        "pizzahutsaudi": "بيتزا هت", "tamimimarkets": "التميمي", "noon": "نون",
        "mikyajy": "مكياجي", "roshnksa": "روشن", "shawarmersa": "شاورمر",
        "aseeb.najd": "عسيب", "altazaj_fakieh": "الطازج", "herfyfsc": "هرفي",
        "maxfashionmena": "ماكس", "kiabiksa": "كيابي", "mumzworld": "ممزورلد",
        "niceonesa": "نايس ون", "ajmalperfumes": "عجمل", "pandasaudi": "بنده",
        "prettynature.official": "بريتي نيتشر", "asteribeautysa": "أستيري",
    }
    bd = brand_display or _brand_ar.get(brand.lower(), brand)

    # Known brand signatures — for food_descriptor / packaging_descriptor / product_descriptor vars
    _brand_food_sig = {
        # F&B
        "albaik":                 "بروستد الدجاج في علبة البيك الخضراء مع الصلصة",
        "barnscoffee":            "قهوة عربية مخصصة مع كرواسون محمر طازج",
        "mcdonaldsksa":           "برغر ماك مع البطاطس المقرمشة والصلصة الخاصة",
        "shawarmersa":            "شاورما لحم في خبز رقيق طازج مع الصلصات",
        "altazaj_fakieh":         "دجاج مشوي طازج مع الأرز وسلطة التبولة",
        "herfyfsc":               "وجبة هرفي من الدجاج المقلي المقرمش",
        "aseeb.najd":             "قهوة نجدية فاخرة محضّرة بالطريقة التقليدية مع تمر",
        "alromansiahksa":         "سمك طازج مشوي على الفحم مع الأرز والصلصة الحارة",
        "elixirbunn":             "قهوة إليكسير المختصة مع حلويات طازجة",
        "hashibasha":             "مشاوي حطابية مع أرز بخاري وخبز رقيق",
        "kuduksa":                "كبسة دجاج بيتية تقليدية بالتوابل السعودية",
        "pizzahutsaudi":          "بيتزا هت بالجبنة الموتزاريلا والإضافات الحصرية",
        "riyadhfood":             "أطباق الرياض الشهية والمطابخ المتنوعة",
        # Fashion
        "maxfashionmena":         "تشكيلة ماكس الموسمية الحصرية بأسعار مناسبة",
        "kiabiksa":               "قطع كيابي العائلية الملوّنة بأسعار مناسبة",
        # Beauty & Personal Care
        "mikyajy":                "مكياجي للمكياج الفاخر والعناية بالبشرة",
        "niceonesa":              "نايس ون لمنتجات الشعر والعناية اليومية",
        "ajmalperfumes":          "عطر عجمل الفاخر بنفحات عربية أصيلة",
        "asteribeautysa":         "أستيري للعناية بالبشرة بمكونات طبيعية فاخرة",
        "bathandbodyworksarabia": "باث آند بودي ووركس العطور وكريمات اليدين",
        "prettynature.official":  "بريتي نيتشر للعناية الطبيعية بالبشرة والعطور",
        # Retail & Lifestyle
        "noon":                   "منتجات نون بتوصيل سريع وأسعار تنافسية",
        "pandasaudi":             "منتجات بندة الطازجة والعروض اليومية",
        "tamimimarkets":          "مواد غذائية طازجة ومنتجات التميمي المختارة",
        "mumzworld":              "منتجات الأمومة والأطفال من ممزورلد",
    }

    # Sector-specific product fallbacks — used when product input = brand name or empty
    _sector_product_fallback = {
        "real_estate":          "مجتمعات سكنية فاخرة",
        "healthcare_wellness":  "باقة صحية متكاملة",
        "fashion":              "تشكيلة حصرية",
        "beauty_personal_care": "منتج تجميلي فاخر",
        "f_and_b":              "وجبة طازجة",
        "retail_lifestyle":     "منتج مميز",
    }
    # If product is empty or just the brand name, use the sector default
    effective_product = product if (product and product != bd and product != brand) \
                        else (_sector_product_fallback.get(sector, product or bd))

    # Brand color: explicit arg > brand_visual_context > known table
    resolved_color = (
        brand_color
        or bctx.get("brand_color", "")
        or "#1a5f30"
    )

    # Visual context from brand_dna
    b_setting   = bctx.get("dominant_setting", "studio")
    b_lighting  = bctx.get("dominant_lighting", "natural")
    b_archetype = bctx.get("archetype", "Modern Premium")

    # Sector-appropriate setting (more specific than b_setting)
    _sector_setting = {
        "f_and_b": "restaurant",
        "fashion": "retail_store",
        "beauty_personal_care": "studio",
        "retail_lifestyle": "retail_store",
        "real_estate": "outdoor Saudi residential community",
        "healthcare_wellness": "modern gym or wellness studio",
    }

    # Background color from brand palette
    bg_color = resolved_color

    # Resolve food/packaging descriptor: brand-specific > sector product fallback
    food_sig = _brand_food_sig.get(brand.lower(), effective_product)

    # Process descriptor for behind-the-scenes / cd_03 Authenticity Detective chains
    _sector_process = {
        "fashion":              "garment selection and styling preparation",
        "beauty_personal_care": "skincare and makeup preparation routine",
        "retail_lifestyle":     "product curation and sourcing selection",
        "f_and_b":              "fresh ingredient preparation and cooking",
        "real_estate":          "interior design and finishing walkthrough",
        "healthcare_wellness":  "trainer-led warmup and wellness preparation",
    }
    process_desc = _sector_process.get(sector, effective_product)

    vars_map = {
        "brand_name":                    bd,
        "brand_display":                 bd,
        "food_descriptor":               food_sig,
        "packaging_descriptor":          food_sig,
        "fragrance_descriptor":          effective_product,
        "material_descriptor":           effective_product,
        "texture_descriptor":            effective_product,
        "process_descriptor":            process_desc,
        "brand_product":                 food_sig,
        "featured_product":              food_sig,
        "product":                       food_sig,
        "product_descriptor":            food_sig,
        "product_name":                  food_sig,
        "hero_product":                  food_sig,
        "brand_color":                   resolved_color,
        "brand_color_primary":           resolved_color,
        "brand_color_palette":           resolved_color,
        "brand_color_accent":            resolved_color,
        "background_color":              bg_color,
        "background_tone":               b_archetype.lower().replace(" ", "_"),
        "background_style":              "clean gradient" if sector == "beauty_personal_care" else "contextual",
        "setting":                       b_setting or _sector_setting.get(sector, "studio"),
        "setting_descriptor":            b_setting or _sector_setting.get(sector, "studio"),
        "sector_appropriate_setting":    _sector_setting.get(sector, b_setting or "studio"),
        "lighting":                      b_lighting or "natural",
        "lighting_descriptor":           b_lighting or "warm natural",
        "sector":                        sector,
        "occasion":                      occasion,
        "occasion_atmosphere":           _occasion_atmosphere.get(occasion, "celebratory warm atmosphere"),
        "occasion_descriptor":           occasion.replace("_", " "),
        "occasion_visual_element":       _occasion_atmosphere.get(occasion, "seasonal motifs"),
        "occasion_colors":               _occasion_atmosphere.get(occasion, "warm palette"),
        "cultural_constraints_injection": cultural_inject,
        "brand_descriptor":              b_archetype,
        "sector_visual_style":           f"{sector.replace('_', ' ')} Saudi-native photography",
    }
    if extra:
        vars_map.update(extra)

    # Fill known vars, leave unknown as-is
    filled = template
    for k, v in vars_map.items():
        filled = filled.replace("{" + k + "}", str(v))

    return filled


def get_visual_direction(
    cd_primary: str,
    sector: str,
    occasion: str,
    brand: str,
    product: str,
    brand_color: str = "",
    brand_display: str = "",
) -> dict:
    """
    Main entry point. Returns the visual chain selection + filled prompt for the /api/create response.
    """
    chain = select_chain(cd_primary, sector, occasion)
    if not chain:
        return {
            "error": "no_chain_found",
            "cd_technique": _cd_key(cd_primary),
            "sector": sector,
        }

    prompt = fill_prompt(
        chain, brand=brand, product=product, sector=sector,
        occasion=occasion, brand_color=brand_color, brand_display=brand_display,
    )

    payload = chain.get("payload", {})
    models = payload.get("models_used", [])
    primary_model = next((m["model_id"] for m in models if m.get("role") == "primary_image_generation"), None)
    video_model = next((m["model_id"] for m in models if "video" in m.get("role", "")), None)

    # Count unfilled variables in the prompt
    unfilled = re.findall(r"\{([^}]+)\}", prompt)

    return {
        "chain_id": chain["chain_id_short"],
        "family": chain["family"],
        "name_en": chain["name_en"],
        "name_ar": chain.get("name_ar", ""),
        "output_type": chain["output_type"],
        "cd_technique": _cd_key(cd_primary),
        "primary_model": primary_model,
        "video_model": video_model,
        "prompt": prompt,
        "unfilled_vars": unfilled,
        "notes": payload.get("notes", ""),
        "anti_patterns": payload.get("anti_patterns", []),
        "latency_estimate_seconds": chain.get("latency_estimate_seconds", 15),
    }
