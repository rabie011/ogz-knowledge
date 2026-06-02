-- Auto-generated seed: sectors
-- Source: 05_sector_defaults/ + observation sectors
-- Generated: 2026-06-02 | Count: 8

INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('BEAUTY00000000000000000000', 'beauty', 'Beauty', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('BEAUTY0PERSONAL0CARE000000', 'beauty_personal_care', 'Beauty Personal Care', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('F0AND0B0000000000000000000', 'f_and_b', 'F And B', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('FASHION0000000000000000000', 'fashion', 'Fashion', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('HEALTHCARE0WELLNESS0000000', 'healthcare_wellness', 'Healthcare Wellness', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('REAL0ESTATE000000000000000', 'real_estate', 'Real Estate', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('RETAIL00000000000000000000', 'retail', 'Retail', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug, sector_name_en, sector_name_ar, payload, provenance) VALUES ('RETAIL0LIFESTYLE0000000000', 'retail_lifestyle', 'Retail Lifestyle', '', '{}'::jsonb, '{"source":"ogz-knowledge seed"}'::jsonb) ON CONFLICT (sector_slug) DO NOTHING;
