-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0004_indexes.sql                                                     ║
-- ║  Performance indexes — ULID lookups, JSONB GIN, pgvector, date range. ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── ULID lookup indexes (PK already covers most; add foreign-key indexes)
CREATE INDEX IF NOT EXISTS idx_briefs_brand ON briefs(brand_ulid);
CREATE INDEX IF NOT EXISTS idx_gen_events_brand ON generation_events(brand_ulid);
CREATE INDEX IF NOT EXISTS idx_gen_events_brief ON generation_events(brief_ulid);
CREATE INDEX IF NOT EXISTS idx_gen_events_chain ON generation_events(chain_ulid);

-- ── JSONB GIN indexes for commonly-queried payload fields
CREATE INDEX IF NOT EXISTS idx_brand_fp_l1_strategy_gin ON brand_fingerprints USING GIN (l1_strategy jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_brand_fp_l2_voice_gin ON brand_fingerprints USING GIN (l2_voice jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_brief_payload_gin ON briefs USING GIN (payload jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_gen_event_payload_gin ON generation_events USING GIN (payload jsonb_path_ops);

-- ── pgvector indexes for similarity search (HNSW for speed; IVFFlat for huge tables)
CREATE INDEX IF NOT EXISTS idx_brand_fp_embedding_hnsw
  ON brand_fingerprints
  USING hnsw (embedding_fingerprint vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_account_patterns_embedding_hnsw
  ON account_patterns
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_campaign_archive_embedding_hnsw
  ON campaign_archive
  USING hnsw (embedding vector_cosine_ops);

-- ── Date range / event indexes
CREATE INDEX IF NOT EXISTS idx_gen_events_created ON generation_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outcome_events_created ON outcome_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_events_created ON memory_events(created_at DESC);

-- ── Status + tier indexes
CREATE INDEX IF NOT EXISTS idx_brands_status ON brands(status);
CREATE INDEX IF NOT EXISTS idx_brands_tier ON brands(quality_tier);
CREATE INDEX IF NOT EXISTS idx_brands_sector ON brands(sector);
