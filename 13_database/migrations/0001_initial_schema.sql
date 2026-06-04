-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0001_initial_schema.sql                                              ║
-- ║  Postgres/Supabase schema mirroring the file-first knowledge base.    ║
-- ║                                                                       ║
-- ║  Files-first principle (ADR-0001): every UPSERT below is driven by    ║
-- ║  sync_to_supabase.py reading the source-of-truth files in this repo.  ║
-- ║  Nothing in the application layer writes directly to these tables.    ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";   -- pgvector for distinctiveness + pattern similarity

-- ── ULID type — stored as TEXT (Crockford base32, 26 chars). We use a CHECK
--    constraint to validate format. ULIDs are minted by the file-first layer.
CREATE DOMAIN ulid AS TEXT
  CHECK (VALUE ~ '^[0-9A-HJKMNP-TV-Z]{26}$');

-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  Universal tables (read-only public knowledge — populated from repo)  ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── Chains (88 records from 02_what_to_build/)
CREATE TABLE chains (
  chain_ulid       ulid PRIMARY KEY,
  chain_id_short   TEXT UNIQUE NOT NULL,
  family           TEXT NOT NULL,
  name_en          TEXT NOT NULL,
  output_type      TEXT NOT NULL,
  cost_estimate_usd NUMERIC(8,4),
  quality_tiers_allowed JSONB NOT NULL,
  sectors_allowed  JSONB NOT NULL,
  occasions_allowed JSONB NOT NULL,
  best_for_cd_brains JSONB NOT NULL,
  payload          JSONB NOT NULL,
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chains_family ON chains(family);
CREATE INDEX idx_chains_sectors_gin ON chains USING GIN (sectors_allowed jsonb_path_ops);
CREATE INDEX idx_chains_occasions_gin ON chains USING GIN (occasions_allowed jsonb_path_ops);

-- ── Sector baselines (5 from 05_sector_defaults/)
CREATE TABLE sector_baselines (
  sector_baseline_ulid ulid PRIMARY KEY,
  sector_slug          TEXT UNIQUE NOT NULL,
  sector_name_en       TEXT NOT NULL,
  sector_name_ar       TEXT NOT NULL,
  payload              JSONB NOT NULL,
  provenance           JSONB NOT NULL,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ── Occasions (5 from 06_saudi_calendar/)
CREATE TABLE occasions (
  occasion_ulid    ulid PRIMARY KEY,
  occasion_slug    TEXT UNIQUE NOT NULL,
  name_en          TEXT NOT NULL,
  name_ar          TEXT NOT NULL,
  date_recurrence  JSONB NOT NULL,
  payload          JSONB NOT NULL,
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── CD brain methodologies (5 from 20_cd_brains/)
CREATE TABLE cd_brains (
  cd_brain_ulid    ulid PRIMARY KEY,
  cd_brain_slug    TEXT UNIQUE NOT NULL,
  name_internal    TEXT NOT NULL,
  name_external    TEXT NOT NULL,
  payload          JSONB NOT NULL,
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Cultural specs — sector × region defaults (8 from 15_cultural_specs/sector_defaults/)
CREATE TABLE cultural_specs (
  cultural_spec_ulid ulid PRIMARY KEY,
  scope_label        TEXT NOT NULL,
  payload            JSONB NOT NULL,
  provenance         JSONB NOT NULL,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ── Benchmark accounts (~108 from 11_who_to_learn_from/accounts/)
CREATE TABLE benchmark_accounts (
  account_ulid             ulid PRIMARY KEY,
  account_handle_normalized TEXT UNIQUE NOT NULL,
  account_handle_internal  TEXT,  -- never surfaced to client UI
  sector                   TEXT NOT NULL,
  sub_sector               TEXT,
  payload                  JSONB NOT NULL,
  provenance               JSONB NOT NULL,
  created_at               TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_benchmarks_sector ON benchmark_accounts(sector);

-- ── Observations (2730+ from 11_who_to_learn_from/observations/)
CREATE TABLE observations (
  observation_ulid         ulid PRIMARY KEY,
  account_ulid             ulid REFERENCES benchmark_accounts(account_ulid),
  account_handle_normalized TEXT NOT NULL,
  sector                   TEXT NOT NULL,
  content_type             TEXT NOT NULL CHECK (content_type IN ('image', 'video', 'carousel_slide', 'story', 'reel')),
  engagement_potential      TEXT NOT NULL CHECK (engagement_potential IN ('high', 'medium', 'low')),
  likes_count              INTEGER DEFAULT 0,
  comments_count           INTEGER DEFAULT 0,
  engagement_total         INTEGER DEFAULT 0,
  content_pillar           TEXT,
  emotion_primary          TEXT,
  occasion                 TEXT,
  voice_observations       JSONB NOT NULL,
  visual_observations      JSONB NOT NULL,
  cultural_notes           JSONB,
  quality_assessment       JSONB NOT NULL,
  pattern_matches          JSONB NOT NULL DEFAULT '[]'::jsonb,
  content_ref              JSONB NOT NULL,
  compliance_check         JSONB,
  provenance               JSONB NOT NULL,
  embedding                vector(1536),
  created_at               TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_obs_sector ON observations(sector);
CREATE INDEX idx_obs_account ON observations(account_handle_normalized);
CREATE INDEX idx_obs_content_type ON observations(content_type);
CREATE INDEX idx_obs_engagement ON observations(engagement_potential);
CREATE INDEX idx_obs_occasion ON observations(occasion);
CREATE INDEX idx_obs_patterns_gin ON observations USING GIN (pattern_matches jsonb_path_ops);

-- ── Account patterns (1255 from 11_who_to_learn_from/patterns/)
CREATE TABLE account_patterns (
  pattern_ulid     ulid PRIMARY KEY,
  pattern_slug     TEXT UNIQUE NOT NULL,
  pattern_name     TEXT NOT NULL,
  payload          JSONB NOT NULL,
  observed_in_sectors JSONB NOT NULL,
  embedding        vector(1536),    -- for similarity search
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_patterns_sectors_gin ON account_patterns USING GIN (observed_in_sectors jsonb_path_ops);

-- ── Campaign archive (38 from 21_campaign_archive/)
CREATE TABLE campaign_archive (
  campaign_ulid        ulid PRIMARY KEY,
  campaign_code_anonymized TEXT UNIQUE NOT NULL,
  sector               TEXT NOT NULL,
  year                 INTEGER,
  cd_brain_used        TEXT,
  cd_brain_used_secondary TEXT,
  payload              JSONB NOT NULL,
  embedding            vector(1536),   -- for RAG retrieval by CEO agent
  provenance           JSONB NOT NULL,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_campaigns_sector ON campaign_archive(sector);
CREATE INDEX idx_campaigns_year ON campaign_archive(year);

-- ── Frames + Motions (visual reference records; populated from 16_character_library/)
CREATE TABLE frames (
  frame_ulid       ulid PRIMARY KEY,
  payload          JSONB NOT NULL,
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE motions (
  motion_ulid      ulid PRIMARY KEY,
  payload          JSONB NOT NULL,
  provenance       JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  Brand-scoped tables (per-brand data; RLS-isolated in 0002)           ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

CREATE TABLE brands (
  brand_ulid       ulid PRIMARY KEY,
  brand_name_normalized TEXT NOT NULL,
  sector           TEXT NOT NULL,
  quality_tier     TEXT NOT NULL CHECK (quality_tier IN ('starter', 'growth', 'enterprise')),
  status           TEXT NOT NULL DEFAULT 'pending_intake' CHECK (status IN ('pending_intake', 'active', 'paused', 'archived')),
  owner_user_id    UUID NOT NULL,  -- references Supabase auth.users
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE brand_fingerprints (
  brand_ulid                ulid PRIMARY KEY REFERENCES brands(brand_ulid) ON DELETE CASCADE,
  schema_version            INTEGER NOT NULL DEFAULT 1,
  l1_strategy               JSONB NOT NULL,
  l2_voice                  JSONB NOT NULL,
  l3_visual                 JSONB,
  l4_cinematography         JSONB,
  l5_look_and_feel          JSONB,
  l6_production             JSONB,
  distinctiveness_current   NUMERIC(4,3),
  distinctiveness_last_computed TIMESTAMPTZ,
  embedding_fingerprint     vector(1536),
  provenance                JSONB NOT NULL,
  created_at                TIMESTAMPTZ DEFAULT NOW(),
  updated_at                TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE briefs (
  brief_ulid       ulid PRIMARY KEY,
  brand_ulid       ulid NOT NULL REFERENCES brands(brand_ulid) ON DELETE CASCADE,
  request_type     TEXT NOT NULL,
  intent           TEXT,
  occasion_flags   JSONB,
  confidence_mode  TEXT,
  payload          JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE generation_events (
  event_ulid       ulid PRIMARY KEY,
  brand_ulid       ulid NOT NULL REFERENCES brands(brand_ulid) ON DELETE CASCADE,
  brief_ulid       ulid REFERENCES briefs(brief_ulid),
  chain_ulid       ulid NOT NULL REFERENCES chains(chain_ulid),
  cd_brain_used    TEXT,
  confidence_score INTEGER,
  gate_result      TEXT,
  cco_arabic_qc_score INTEGER,
  payload          JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE outcome_events (
  event_ulid       ulid PRIMARY KEY,
  generation_event_ulid ulid REFERENCES generation_events(event_ulid),
  brand_ulid       ulid NOT NULL REFERENCES brands(brand_ulid) ON DELETE CASCADE,
  outcome_kind     TEXT NOT NULL,   -- e.g. 'engagement_24h', 'saves', 'shares', 'comments'
  metric_value     NUMERIC,
  payload          JSONB,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_outcome_events_brand ON outcome_events(brand_ulid);
CREATE INDEX idx_outcome_events_gen ON outcome_events(generation_event_ulid);

-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  Audit + Memory Controller events (append-only)                       ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

CREATE TABLE memory_events (
  event_ulid       ulid PRIMARY KEY,
  event_kind       TEXT NOT NULL,   -- field_update / decision_trace / cultural_review / quarantine
  brand_ulid       ulid REFERENCES brands(brand_ulid),
  payload          JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_memory_events_brand ON memory_events(brand_ulid);
CREATE INDEX idx_memory_events_kind ON memory_events(event_kind);
CREATE INDEX idx_memory_events_created ON memory_events(created_at DESC);
