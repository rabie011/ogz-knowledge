-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0003_seed_benchmark_accounts.sql                                     ║
-- ║  Seed data for benchmark_accounts — active extraction accounts.      ║
-- ║  Source: 11_who_to_learn_from/accounts/ (15 active accounts).        ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

INSERT INTO benchmark_accounts (
  account_ulid, account_handle_normalized, account_handle_internal,
  sector, payload
)
VALUES

-- ── F&B — Complete (50/50) ───────────────────────────────────────────────────

('01KRKHS8R8SNJ8VJ56WKSQTS28', 'OGZ-F-AND-B-Reference-002', 'barnscoffee', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "<10k", "region": "najdi-primary",
  "engagement_tier": "average", "saudi_score": 9,
  "top_patterns": ["foodie_discovery_review","warm_najdi_invitational"],
  "archetype": "modern_premium"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS29', 'OGZ-F-AND-B-Reference-003', 'riyadhfood', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "strong", "saudi_score": 8,
  "top_patterns": ["foodie_discovery_review","hidden_gem_local_spotlight"],
  "archetype": "community_anchor"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS30', 'OGZ-F-AND-B-Reference-004', 'altazaj_fakieh', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "10k-50k", "region": "najdi-primary",
  "engagement_tier": "elite", "saudi_score": 10,
  "top_patterns": ["heritage_storytelling_hook","family_majlis_hierarchical","cultural_object_hero"],
  "archetype": "heritage_anchor"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS31', 'OGZ-F-AND-B-Reference-005', 'crumblcookiespr', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "50k-100k", "region": "najdi-primary",
  "engagement_tier": "strong", "saudi_score": 7,
  "top_patterns": ["product_hero_closeup","pattern_repeat_flatlay","limited_time_promo"],
  "archetype": "modern_premium"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS32', 'OGZ-F-AND-B-Reference-006', 'herfyfsc', 'f_and_b', '{
  "obs_count": 27, "status": "in_progress",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "weak", "saudi_score": 6,
  "top_patterns": ["product_honest_review","occasion_specific_greeting"],
  "archetype": "value_leader",
  "gap": 23
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS33', 'OGZ-F-AND-B-Reference-007', 'kuduksa', 'f_and_b', '{
  "obs_count": 28, "status": "in_progress",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "weak", "saudi_score": 7,
  "top_patterns": ["limited_time_promo","occasion_specific_greeting"],
  "archetype": "modern_premium",
  "gap": 22
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS34', 'OGZ-F-AND-B-Reference-008', 'albaik', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": ">100k", "region": "hejazi-primary",
  "engagement_tier": "elite", "saudi_score": 9,
  "top_patterns": ["cultural_object_hero","heritage_storytelling_hook","occasion_specific_greeting"],
  "archetype": "heritage_anchor"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS35', 'OGZ-F-AND-B-Reference-009', 'shawarmersa', 'f_and_b', '{
  "obs_count": 25, "status": "in_progress",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "weak", "saudi_score": 5,
  "top_patterns": ["product_honest_review","price_offer_graphic"],
  "archetype": "value_leader",
  "gap": 25
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS36', 'OGZ-F-AND-B-Reference-010', 'aseeb.najd', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "10k-50k", "region": "najdi-primary",
  "engagement_tier": "elite", "saudi_score": 10,
  "top_patterns": ["heritage_storytelling_hook","architectural_framing","cultural_object_hero"],
  "archetype": "heritage_anchor"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS37', 'OGZ-F-AND-B-Reference-011', 'alromansiahksa', 'f_and_b', '{
  "obs_count": 31, "status": "in_progress",
  "follower_bucket": "10k-50k", "region": "najdi-primary",
  "engagement_tier": "average", "saudi_score": 7,
  "top_patterns": ["limited_time_promo","occasion_specific_greeting","overhead_spread"],
  "archetype": "modern_premium",
  "gap": 19
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS38', 'OGZ-F-AND-B-Reference-038', 'pizzahutsaudi', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "average", "saudi_score": 6,
  "top_patterns": ["limited_time_promo","product_hero_closeup","entertainment_collab"],
  "archetype": "modern_premium"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS39', 'OGZ-F-AND-B-Reference-039', 'mcdonaldsksa', 'f_and_b', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": ">100k", "region": "najdi-primary",
  "engagement_tier": "average", "saudi_score": 6,
  "top_patterns": ["entertainment_collab","limited_time_promo","cultural_object_hero"],
  "archetype": "modern_premium"
}'::JSONB),

-- ── Beauty — Complete (50/50) ─────────────────────────────────────────────────

('01KRKHS8R8SNJ8VJ56WKSQTS41', 'OGZ-BEAUTY-Reference-001', 'asteribeautysa', 'beauty', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "10k-50k", "region": "najdi-primary",
  "engagement_tier": "average", "saudi_score": 8,
  "top_patterns": ["product_hero_closeup","pattern_repeat_flatlay","heritage_storytelling_hook"],
  "archetype": "modern_premium"
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSQTS42', 'OGZ-BEAUTY-Reference-002', 'prettynature.official', 'beauty', '{
  "obs_count": 50, "status": "complete",
  "follower_bucket": "10k-50k", "region": "hejazi-primary",
  "engagement_tier": "strong", "saudi_score": 8,
  "top_patterns": ["product_hero_closeup","natural_ingredient_hero","lifestyle_integrated"],
  "archetype": "modern_premium"
}'::JSONB),

-- ── Retail — In Progress ──────────────────────────────────────────────────────

('01KRKHS8R8SNJ8VJ56WKSQTS51', 'OGZ-RETAIL-Reference-001', 'aldeebajofficial', 'retail', '{
  "obs_count": 25, "status": "in_progress",
  "follower_bucket": "10k-50k", "region": "najdi-primary",
  "engagement_tier": "weak", "saudi_score": 7,
  "top_patterns": ["product_hero_closeup","occasion_specific_greeting"],
  "archetype": "modern_premium",
  "gap": 25
}'::JSONB)

ON CONFLICT (account_handle_normalized) DO UPDATE SET
  payload = EXCLUDED.payload,
  updated_at = NOW();
