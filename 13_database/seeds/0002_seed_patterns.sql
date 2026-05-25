-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0002_seed_patterns.sql                                               ║
-- ║  Seed data for account_patterns — elite and avoid patterns.          ║
-- ║  Derived from logs/pattern_engagement.json (636 obs corpus).         ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

INSERT INTO account_patterns (
  pattern_ulid, pattern_slug, pattern_name, schema_version, payload
)
VALUES

-- ── ELITE PATTERNS (100% high-eng) ──────────────────────────────────────────

('01KRKHS8R8SNJ8VJ56WKSPAT01', 'heritage_storytelling_hook', 'Heritage Storytelling Hook', 1, '{
  "category": "content_types",
  "high_engagement_rate": 1.0,
  "obs_count": 13,
  "lift_vs_avg": 0.28,
  "verdict": "elite",
  "description": "Opens with Saudi heritage, roots, or legacy framing. Connects brand identity to Saudi story.",
  "why_it_works": "Heritage is the highest-trust signal in Saudi culture. Brands that anchor to authentic Saudi roots earn immediate credibility and emotional resonance.",
  "structural_recipe": "Open with a heritage reference (historical context, traditional practice, origin story). Bridge to present-day brand expression. Close with hospitality or invitation.",
  "applicable_sectors": ["f_and_b","beauty","retail"],
  "applicable_occasions": ["founding_day","national_day","ramadan","evergreen"],
  "transplantation_caveats": ["Heritage must be authentic — fabricated or generic heritage reads as hollow","Najdi vs Hejazi heritage signals must match the brand region"],
  "agency_rule": "Use for any brand with Saudi roots. Works any week — no occasion required."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT02', 'occasion_specific_greeting', 'Occasion-Specific Greeting', 1, '{
  "category": "occasion_plays",
  "high_engagement_rate": 1.0,
  "obs_count": 7,
  "lift_vs_avg": 0.28,
  "verdict": "elite",
  "description": "Dedicated content for a Saudi calendar occasion — not product-pushed, primarily a cultural acknowledgment.",
  "why_it_works": "Saudi audience expects brands to participate in occasion culture. A sincere, well-designed occasion greeting earns goodwill and broad sharing.",
  "structural_recipe": "Occasion visual (appropriate cultural iconography). Brief Arabic greeting text. Brand presence understated. CTA optional.",
  "applicable_sectors": ["f_and_b","beauty","retail"],
  "applicable_occasions": ["eid_al_fitr","national_day","founding_day","ramadan","winter_seasonal"],
  "agency_rule": "Every major Saudi occasion should have a dedicated greeting post. Do not push product in the same visual."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT03', 'employee_pride_campaign', 'Employee Pride Campaign', 1, '{
  "category": "content_types",
  "high_engagement_rate": 1.0,
  "obs_count": 7,
  "lift_vs_avg": 0.28,
  "verdict": "elite",
  "description": "Content featuring team members, staff, or people behind the brand with authentic pride framing.",
  "why_it_works": "Humanizes the brand. Saudi audience responds to authenticity and people stories. Signals hospitality through the lens of the people who deliver it.",
  "structural_recipe": "Feature a real team member or team. Show craft, dedication, or pride in their role. Caption tells their story briefly. Brand is contextual, not dominant.",
  "applicable_sectors": ["f_and_b","beauty","retail"],
  "applicable_occasions": ["national_day","founding_day","evergreen"],
  "agency_rule": "Run 1-2x/month as part of evergreen cadence. Especially effective for F&B brands with service culture."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT04', 'limited_time_promo', 'Limited-Time Promotion', 1, '{
  "category": "content_types",
  "high_engagement_rate": 1.0,
  "obs_count": 5,
  "lift_vs_avg": 0.28,
  "verdict": "elite",
  "description": "A genuinely time-bound offer with authentic urgency — tied to an occasion or product launch.",
  "why_it_works": "Scarcity and real deadlines drive action. Distinct from generic discount — the limited-time must be believable and the product must be featured beautifully.",
  "structural_recipe": "Product hero visual at full quality. Urgency cue (visual timer, seasonal badge, occasion marker). Caption explains the offer. CTA to action.",
  "applicable_sectors": ["f_and_b","retail"],
  "applicable_occasions": ["eid_al_fitr","national_day","summer_campaign","winter_seasonal"],
  "transplantation_caveats": ["Urgency must be real — Saudi audience detects fake scarcity","Product visual quality must be high — cannot hide behind the offer"],
  "agency_rule": "Never use limited-time promo as a substitute for product storytelling. The offer amplifies great product content; it does not replace it."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT05', 'parallel_original_bilingual', 'Parallel Original Bilingual', 1, '{
  "category": "voice_techniques",
  "high_engagement_rate": 1.0,
  "obs_count": 7,
  "lift_vs_avg": 0.28,
  "verdict": "elite",
  "description": "Dual-language creative where Arabic and English are both original — not translation of each other.",
  "why_it_works": "Saudi bilingual audience feels seen when both languages are given equal creative weight. Translation feels lazy; parallel original feels intentional.",
  "structural_recipe": "Arabic creative direction → English creative direction. Both hit the same emotional note but in culturally distinct ways. Neither is primary.",
  "applicable_sectors": ["beauty","retail","f_and_b"],
  "applicable_occasions": ["evergreen","eid_al_fitr","national_day"],
  "agency_rule": "Do not translate Arabic captions to English. Write both independently from the same brief."
}'::JSONB),

-- ── AVOID PATTERNS (0–20% high-eng) ─────────────────────────────────────────

('01KRKHS8R8SNJ8VJ56WKSPAT10', 'discount_price_dominant', 'Discount/Price Dominant', 1, '{
  "category": "content_types",
  "high_engagement_rate": 0.0,
  "obs_count": 18,
  "lift_vs_avg": -0.69,
  "verdict": "avoid",
  "description": "Content where the price or discount is the visual headline. Number-first messaging.",
  "why_it_fails": "Signals brand desperation. Positions brand as commodity. Saudi audience disengages. Destroys brand equity even when the offer is genuine.",
  "agency_rule": "Price belongs in captions, never in the visual headline. If the brief asks for price-first creative, push back with product-first alternative."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT11', 'csr_brand_story', 'CSR / Brand Story', 1, '{
  "category": "content_types",
  "high_engagement_rate": 0.2,
  "obs_count": 5,
  "lift_vs_avg": -0.42,
  "verdict": "avoid",
  "description": "Standalone content about the brand doing good — charity, sustainability, community initiatives.",
  "why_it_fails": "Saudi audience does not engage with corporate virtue-signaling. No product, no hospitality, no occasion — just brand talking about itself.",
  "agency_rule": "Embed brand values into product and people content. Do not create standalone CSR posts."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT12', 'campaign_teaser', 'Campaign Teaser', 1, '{
  "category": "content_types",
  "high_engagement_rate": 0.2,
  "obs_count": 5,
  "lift_vs_avg": -0.42,
  "verdict": "avoid",
  "description": "Cryptic build-up content. Something big is coming. Countdown posts without substance.",
  "why_it_fails": "Saudi Instagram audience does not respond to withheld information. By the time the reveal lands, momentum is gone.",
  "agency_rule": "Launch with substance on Day 1. If you have something worth teasing, open with it directly."
}'::JSONB),

('01KRKHS8R8SNJ8VJ56WKSPAT13', 'lifestyle_embed', 'Lifestyle Embed', 1, '{
  "category": "content_types",
  "high_engagement_rate": 0.11,
  "obs_count": 9,
  "lift_vs_avg": -0.38,
  "verdict": "avoid",
  "description": "Product placed incidentally in a lifestyle scene — on a shelf, in a background, part of a larger scene but not the hero.",
  "why_it_fails": "Product loses visual authority. Brand appears to borrow someone else''s lifestyle rather than owning its own.",
  "agency_rule": "Make the product the clear visual hero OR make the person/occasion the clear hero. Never split the difference."
}'::JSONB)

ON CONFLICT (pattern_slug) DO UPDATE SET
  payload = EXCLUDED.payload,
  updated_at = NOW();
