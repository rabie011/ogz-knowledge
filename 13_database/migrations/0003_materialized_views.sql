-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0003_materialized_views.sql                                          ║
-- ║  Pre-computed views for performance — refresh via cron / Sunday cycle ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── brand_eligible_chains_view: per-brand filtered chain list with scoring.
--    Used by CEO agent at routing time.

CREATE MATERIALIZED VIEW brand_eligible_chains_view AS
SELECT
  b.brand_ulid,
  c.chain_ulid,
  c.chain_id_short,
  c.family,
  c.name_en,
  c.cost_estimate_usd,
  c.quality_tiers_allowed,
  -- Allowed if chain accepts the brand's quality_tier
  (c.quality_tiers_allowed ? b.quality_tier) AS tier_allows,
  -- Allowed if chain accepts the brand's sector (wildcard '*' or specific)
  (c.sectors_allowed ? b.sector OR c.sectors_allowed ? '*') AS sector_allows
FROM brands b
CROSS JOIN chains c;

CREATE INDEX idx_brand_eligible_chains_brand ON brand_eligible_chains_view(brand_ulid);

-- ── brand_distinctiveness_view: current score per brand vs sector average.
--    Used by anti-convergence monitor + brand dashboard.

CREATE MATERIALIZED VIEW brand_distinctiveness_view AS
WITH sector_stats AS (
  SELECT
    b.sector,
    AVG(bf.distinctiveness_current) AS sector_avg,
    STDDEV(bf.distinctiveness_current) AS sector_stddev,
    COUNT(*) AS sector_brand_count
  FROM brands b
  JOIN brand_fingerprints bf ON bf.brand_ulid = b.brand_ulid
  WHERE b.status = 'active' AND bf.distinctiveness_current IS NOT NULL
  GROUP BY b.sector
)
SELECT
  b.brand_ulid,
  b.brand_name_normalized,
  b.sector,
  bf.distinctiveness_current,
  ss.sector_avg,
  ss.sector_stddev,
  ss.sector_brand_count,
  (bf.distinctiveness_current - ss.sector_avg) AS delta_from_sector_avg,
  bf.distinctiveness_last_computed
FROM brands b
JOIN brand_fingerprints bf ON bf.brand_ulid = b.brand_ulid
LEFT JOIN sector_stats ss ON ss.sector = b.sector
WHERE b.status = 'active';

CREATE INDEX idx_brand_distinct_brand ON brand_distinctiveness_view(brand_ulid);

-- ── sector_chain_recommendation_view: top-scored chains per sector.
--    Used by sector_to_chains routing reference.

CREATE MATERIALIZED VIEW sector_chain_recommendation_view AS
SELECT
  sb.sector_slug,
  ch.chain_ulid,
  ch.chain_id_short,
  ch.name_en,
  ch.cost_estimate_usd,
  (sb.payload->'default_eligible_chains')::JSONB AS sector_chain_scoring
FROM sector_baselines sb
JOIN chains ch ON ch.sectors_allowed ? sb.sector_slug OR ch.sectors_allowed ? '*';

-- ── Refresh schedule: run nightly via cron. Sunday cycle additionally rebuilds
--    distinctiveness scores via the Learning Agent before this view refreshes.

-- (Refresh statements; run via job scheduler in production)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY brand_eligible_chains_view;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY brand_distinctiveness_view;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY sector_chain_recommendation_view;
