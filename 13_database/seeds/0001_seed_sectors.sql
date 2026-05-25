-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0001_seed_sectors.sql                                                ║
-- ║  Seed data for sector_baselines, occasions, and cultural_specs.       ║
-- ║  Mirrors 05_sector_defaults/, 06_saudi_calendar/, 15_cultural_specs/  ║
-- ║                                                                       ║
-- ║  Files-first principle: this seed is a bootstrap convenience.        ║
-- ║  sync_to_supabase.py is the authoritative sync path for production.  ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── Sector Baselines ─────────────────────────────────────────────────────────

INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload)
VALUES

('01KRKHS8R8SNJ8VJ56WKSQTS01', 'f_and_b', 'Food & Beverage', 'الغذاء والمشروبات', '{
  "default_voice": {
    "register": "warm_conversational",
    "formality": "semi_formal",
    "dialect_preference": "najdi_primary",
    "msa_tolerance": "moderate",
    "codeswitching_tolerance": "low"
  },
  "default_visual": {
    "primary_palette": ["#8B4513","#D2691E","#F5DEB3","#2C1810"],
    "lighting_default": "warm_practical",
    "composition_default": "overhead_spread",
    "texture_emphasis": "food_texture_macro"
  },
  "default_occasions_priority": ["ramadan","eid_al_fitr","national_day","founding_day","summer_campaign","winter_seasonal"],
  "default_kpis_focus": ["footfall","order_frequency","brand_recall"],
  "engagement_baseline": 0.47,
  "top_patterns": ["heritage_storytelling_hook","overhead_spread","occasion_specific_greeting"],
  "avoid_patterns": ["discount_price_dominant","csr_brand_story","lifestyle_embed"]
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS02', 'beauty', 'Beauty & Personal Care', 'الجمال والعناية الشخصية', '{
  "default_voice": {
    "register": "warm_conversational",
    "formality": "informal",
    "dialect_preference": "bilingual_arabic_english",
    "msa_tolerance": "high",
    "codeswitching_tolerance": "high"
  },
  "default_visual": {
    "primary_palette": ["#F8F0E8","#D4A5A5","#C8B8A2","#2C2C2C"],
    "lighting_default": "cold_studio",
    "composition_default": "product_hero_closeup",
    "texture_emphasis": "skin_texture_skincare"
  },
  "default_occasions_priority": ["eid_al_fitr","graduation_season","national_day","winter_seasonal","summer_campaign"],
  "default_kpis_focus": ["brand_awareness","online_sales","repeat_purchase"],
  "engagement_baseline": 0.51,
  "top_patterns": ["product_hero_closeup","pattern_repeat_flatlay","cultural_object_hero"],
  "avoid_patterns": ["discount_price_dominant","gamified_content","educational_explainer"]
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS03', 'retail', 'Retail', 'التجزئة', '{
  "default_voice": {
    "register": "formal",
    "formality": "formal",
    "dialect_preference": "najdi_primary",
    "msa_tolerance": "high",
    "codeswitching_tolerance": "moderate"
  },
  "default_visual": {
    "primary_palette": ["#1A1A2E","#16213E","#C0C0C0","#FFFFFF"],
    "lighting_default": "cold_studio",
    "composition_default": "product_hero_closeup",
    "texture_emphasis": "fabric_material_detail"
  },
  "default_occasions_priority": ["eid_al_fitr","national_day","founding_day","graduation_season","white_friday"],
  "default_kpis_focus": ["footfall","basket_size","brand_loyalty"],
  "engagement_baseline": 0.43,
  "top_patterns": ["limited_time_promo","occasion_specific_greeting","community_pride_statement"],
  "avoid_patterns": ["price_offer_graphic","csr_brand_story","campaign_teaser"]
}'::JSONB)

ON CONFLICT (sector_slug) DO UPDATE SET
  payload = EXCLUDED.payload,
  updated_at = NOW();

-- ── Saudi Occasions ───────────────────────────────────────────────────────────

INSERT INTO occasions (occasion_ulid, occasion_slug, occasion_name_en, occasion_name_ar, payload)
VALUES

('01KRKHS8R8SNJ8VJ56WKSQTOA1', 'national_day', 'Saudi National Day', 'اليوم الوطني السعودي', '{
  "date_recurrence": {"type": "gregorian", "month": 9, "day": 23, "duration_days": 1},
  "high_engagement_rate": 0.75,
  "obs_count": 12,
  "lift_vs_baseline": 0.28,
  "lead_time_days": 21,
  "recommended_format": "carousel",
  "recommended_patterns": ["occasion_specific_greeting","heritage_storytelling_hook","community_pride_statement"],
  "avoid_patterns": ["discount_price_dominant","campaign_teaser"],
  "cultural_significance": {"patriotic_weight": "very_high", "family_centrality": "high", "commercial_activity": "high"}
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTOA2', 'founding_day', 'Saudi Founding Day', 'يوم التأسيس السعودي', '{
  "date_recurrence": {"type": "gregorian", "month": 2, "day": 22, "duration_days": 1},
  "high_engagement_rate": 0.86,
  "obs_count": 7,
  "lift_vs_baseline": 0.39,
  "lead_time_days": 14,
  "recommended_format": "video",
  "recommended_patterns": ["cultural_object_hero","heritage_storytelling_hook","occasion_specific_greeting"],
  "avoid_patterns": ["lifestyle_embed","price_offer_graphic"],
  "cultural_significance": {"heritage_weight": "very_high", "patriotic_weight": "very_high", "commercial_activity": "moderate"}
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTOA3', 'ramadan', 'Ramadan', 'رمضان المبارك', '{
  "date_recurrence": {"type": "hijri", "month": 9, "duration_days": 29},
  "high_engagement_rate": 0.62,
  "obs_count": 26,
  "lift_vs_baseline": 0.15,
  "lead_time_days": 21,
  "recommended_format": "carousel",
  "phases": ["early_ramadan","mid_ramadan","last_ten_days"],
  "recommended_patterns": ["occasion_specific_greeting","family_majlis_hierarchical","heritage_storytelling_hook"],
  "avoid_patterns": ["discount_price_dominant","food_imagery_during_fasting_hours"],
  "cultural_significance": {"religious_weight": "highest", "family_centrality": "very_high", "commercial_activity": "very_high"}
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTOA4', 'eid_al_fitr', 'Eid Al-Fitr', 'عيد الفطر المبارك', '{
  "date_recurrence": {"type": "hijri", "month": 10, "day": 1, "duration_days": 3},
  "high_engagement_rate": 0.78,
  "obs_count": 9,
  "lift_vs_baseline": 0.31,
  "lead_time_days": 21,
  "recommended_format": "image",
  "recommended_patterns": ["occasion_specific_greeting","limited_time_promo","family_majlis_hierarchical"],
  "avoid_patterns": ["discount_price_dominant","gamified_content"],
  "cultural_significance": {"religious_weight": "very_high", "family_centrality": "highest", "commercial_activity": "high"}
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTOA5', 'eid_al_adha', 'Eid Al-Adha', 'عيد الأضحى المبارك', '{
  "date_recurrence": {"type": "hijri", "month": 12, "day": 10, "duration_days": 3},
  "high_engagement_rate": 0.11,
  "obs_count": 9,
  "lift_vs_baseline": -0.36,
  "lead_time_days": 7,
  "warning": "LOWEST engagement occasion in corpus — reduce investment significantly vs Eid Al-Fitr",
  "recommended_format": "image",
  "recommended_patterns": ["occasion_specific_greeting"],
  "avoid_patterns": ["discount_price_dominant","product_launch","commercial_campaign"],
  "cultural_significance": {"religious_weight": "highest", "family_centrality": "highest", "commercial_activity": "low"}
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTOA6', 'winter_seasonal', 'Winter Season', 'الموسم الشتوي', '{
  "date_recurrence": {"type": "gregorian", "months": [12,1,2], "duration_days": 90},
  "high_engagement_rate": 1.0,
  "obs_count": 4,
  "lift_vs_baseline": 0.53,
  "lead_time_days": 7,
  "note": "Highest-performing season in corpus — 100% high-engagement",
  "recommended_format": "carousel",
  "recommended_patterns": ["seasonal_atmosphere","product_hero_closeup","lifestyle_integrated"],
  "cultural_significance": {"commercial_activity": "high", "family_centrality": "moderate"}
}'::JSONB)

ON CONFLICT (occasion_slug) DO UPDATE SET
  payload = EXCLUDED.payload,
  updated_at = NOW();
