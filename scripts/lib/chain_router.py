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
    preferred_families = _CD_TO_TF.get(cd_key, ["TF01", "TF02"])

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
    Unknown variables are left as {VAR_NAME} so Hesham's platform can fill the rest.
    """
    payload = chain.get("payload", {})
    template = payload.get("prompt_template", "")
    if not template:
        return ""

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

    vars_map = {
        "brand_name":                    bd,
        "brand_display":                 bd,
        "brand_product":                 product or bd,
        "featured_product":              product or bd,
        "product":                       product or bd,
        "product_descriptor":            product or bd,
        "product_name":                  product or bd,
        "brand_color":                   brand_color or "#1a5f30",
        "brand_color_primary":           brand_color or "#1a5f30",
        "sector":                        sector,
        "occasion":                      occasion,
        "occasion_atmosphere":           _occasion_atmosphere.get(occasion, "celebratory warm atmosphere"),
        "occasion_descriptor":           occasion.replace("_", " "),
        "occasion_visual_element":       _occasion_atmosphere.get(occasion, "seasonal motifs"),
        "cultural_constraints_injection": cultural_inject,
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
