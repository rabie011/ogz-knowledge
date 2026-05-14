-- ╔═══════════════════════════════════════════════════════════════════════╗
-- ║  0002_rls_policies.sql                                                ║
-- ║  Row-Level Security: public knowledge (read-only) +                   ║
-- ║  brand-scoped data (per-brand isolation by brand_ulid).               ║
-- ╚═══════════════════════════════════════════════════════════════════════╝

-- ── Public knowledge tables: read-only for any authenticated user.
--    Writes restricted to service role (used by sync_to_supabase.py).

ALTER TABLE chains              ENABLE ROW LEVEL SECURITY;
ALTER TABLE sector_baselines    ENABLE ROW LEVEL SECURITY;
ALTER TABLE occasions           ENABLE ROW LEVEL SECURITY;
ALTER TABLE cd_brains           ENABLE ROW LEVEL SECURITY;
ALTER TABLE cultural_specs      ENABLE ROW LEVEL SECURITY;
ALTER TABLE benchmark_accounts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_patterns    ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_archive    ENABLE ROW LEVEL SECURITY;
ALTER TABLE frames              ENABLE ROW LEVEL SECURITY;
ALTER TABLE motions             ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'chains','sector_baselines','occasions','cd_brains','cultural_specs',
    'benchmark_accounts','account_patterns','campaign_archive','frames','motions'
  ]) LOOP
    EXECUTE format('
      DROP POLICY IF EXISTS %1$s_read_authenticated ON %1$s;
      CREATE POLICY %1$s_read_authenticated ON %1$s
        FOR SELECT
        TO authenticated
        USING (true);
    ', t);
  END LOOP;
END$$;

-- ── Internal-handle column on benchmark_accounts: NOT visible to authenticated users
--    (only to service role). Enforce via a redacting view.

CREATE OR REPLACE VIEW benchmark_accounts_public AS
SELECT
  account_ulid,
  account_handle_normalized,
  sector,
  sub_sector,
  payload,
  provenance,
  created_at
FROM benchmark_accounts;

GRANT SELECT ON benchmark_accounts_public TO authenticated;
REVOKE SELECT ON benchmark_accounts FROM authenticated;
GRANT  SELECT ON benchmark_accounts TO service_role;

-- ── Brand-scoped tables: per-brand isolation.

ALTER TABLE brands              ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_fingerprints  ENABLE ROW LEVEL SECURITY;
ALTER TABLE briefs              ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_events   ENABLE ROW LEVEL SECURITY;
ALTER TABLE outcome_events      ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_events       ENABLE ROW LEVEL SECURITY;

-- brands: user can only see brands they own
DROP POLICY IF EXISTS brands_select_own ON brands;
CREATE POLICY brands_select_own ON brands
  FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

DROP POLICY IF EXISTS brands_insert_own ON brands;
CREATE POLICY brands_insert_own ON brands
  FOR INSERT
  TO authenticated
  WITH CHECK (owner_user_id = auth.uid());

DROP POLICY IF EXISTS brands_update_own ON brands;
CREATE POLICY brands_update_own ON brands
  FOR UPDATE
  TO authenticated
  USING (owner_user_id = auth.uid())
  WITH CHECK (owner_user_id = auth.uid());

-- brand_fingerprints + briefs + generation_events + outcome_events + memory_events:
-- accessible only when brand_ulid belongs to a brand owned by the user.

DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'brand_fingerprints','briefs','generation_events','outcome_events','memory_events'
  ]) LOOP
    EXECUTE format('
      DROP POLICY IF EXISTS %1$s_select_own_brand ON %1$s;
      CREATE POLICY %1$s_select_own_brand ON %1$s
        FOR SELECT
        TO authenticated
        USING (
          brand_ulid IN (
            SELECT brand_ulid FROM brands WHERE owner_user_id = auth.uid()
          )
        );

      DROP POLICY IF EXISTS %1$s_insert_own_brand ON %1$s;
      CREATE POLICY %1$s_insert_own_brand ON %1$s
        FOR INSERT
        TO authenticated
        WITH CHECK (
          brand_ulid IN (
            SELECT brand_ulid FROM brands WHERE owner_user_id = auth.uid()
          )
        );
    ', t);
  END LOOP;
END$$;

-- Updates to event tables are forbidden (append-only invariant).
DROP POLICY IF EXISTS generation_events_no_update ON generation_events;
CREATE POLICY generation_events_no_update ON generation_events
  FOR UPDATE TO authenticated USING (false);
DROP POLICY IF EXISTS outcome_events_no_update ON outcome_events;
CREATE POLICY outcome_events_no_update ON outcome_events
  FOR UPDATE TO authenticated USING (false);
DROP POLICY IF EXISTS memory_events_no_update ON memory_events;
CREATE POLICY memory_events_no_update ON memory_events
  FOR UPDATE TO authenticated USING (false);

-- ── Service role has unrestricted access (used by sync_to_supabase.py + Memory Controller)
--    (Supabase's `service_role` bypasses RLS by default — this is documented intent.)
