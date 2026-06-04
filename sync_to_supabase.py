#!/usr/bin/env python3
"""
sync_to_supabase.py — Sync ogz-knowledge files → Postgres/Supabase.

Usage:
    python3 sync_to_supabase.py --dry-run          # count files, no DB writes
    python3 sync_to_supabase.py --execute           # load all data into Postgres
    python3 sync_to_supabase.py --execute --table observations  # sync one table only

Env vars (for --execute):
    DATABASE_URL  (default: postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge)
    SUPABASE_URL + SUPABASE_SERVICE_KEY  (for Supabase — future)
"""
from __future__ import annotations
import argparse, json, os, sys, glob, re
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent

DEFAULT_DB_URL = "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge"

FILE_TO_TABLE = [
    ("02_what_to_build/TF*/tf*.json",                   "chains",              "json",  "chain_ulid"),
    ("05_sector_defaults/*.yaml",                        "sector_baselines",    "yaml",  "sector_baseline_ulid"),
    ("06_saudi_calendar/*.yaml",                         "occasions",           "yaml",  "occasion_ulid"),
    ("20_cd_brains/cd_0*.md",                            "cd_brains",           "md",    "cd_brain_ulid"),
    ("15_cultural_specs/sector_defaults/*.yaml",         "cultural_specs",      "yaml",  "cultural_spec_ulid"),
    ("11_who_to_learn_from/accounts/*/*.json",           "benchmark_accounts",  "json",  "account_ulid"),
    ("11_who_to_learn_from/patterns/*/*.json",           "account_patterns",    "json",  "pattern_ulid"),
    ("21_campaign_archive/campaigns/*.json",             "campaign_archive",    "json",  "campaign_ulid"),
    ("11_who_to_learn_from/observations/*/*.json",       "observations",        "json",  "observation_ulid"),
]


def load_file(path: Path, fmt: str) -> dict:
    if fmt == "json":
        return json.loads(path.read_text())
    if fmt == "yaml":
        return yaml.safe_load(path.read_text())
    if fmt == "md":
        text = path.read_text()
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end > 0:
                return yaml.safe_load(text[4:end])
        return {"raw_content": text}
    raise ValueError(f"unknown format: {fmt}")


def upsert_chain(cur, record):
    ef = record.get("eligibility_filters", {})
    cur.execute("""
        INSERT INTO chains (chain_ulid, chain_id_short, family, name_en, output_type,
            cost_estimate_usd, quality_tiers_allowed, sectors_allowed, occasions_allowed,
            best_for_cd_brains, payload, provenance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chain_ulid) DO UPDATE SET
            payload = EXCLUDED.payload, updated_at = NOW()
    """, (
        record["chain_ulid"], record["chain_id_short"], record["family"],
        record["name_en"], record.get("output_type", "image"),
        record.get("cost_estimate_usd"), json.dumps(ef.get("quality_tiers_allowed", [])),
        json.dumps(ef.get("sectors_allowed", [])), json.dumps(ef.get("occasions_allowed", ["*"])),
        json.dumps(record.get("best_for_cd_brains", [])), json.dumps(record),
        json.dumps(record.get("provenance", {}))
    ))


def upsert_pattern(cur, record):
    cur.execute("""
        INSERT INTO account_patterns (pattern_ulid, pattern_slug, pattern_name,
            payload, observed_in_sectors, provenance)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (pattern_ulid) DO UPDATE SET
            payload = EXCLUDED.payload
    """, (
        record["pattern_ulid"], record["pattern_slug"], record["pattern_name"],
        json.dumps(record), json.dumps(record.get("observed_in_sectors", [])),
        json.dumps(record.get("provenance", {}))
    ))


def upsert_observation(cur, record):
    cr = record.get("content_ref", {})
    qa = record.get("quality_assessment", {})
    cur.execute("""
        INSERT INTO observations (observation_ulid, account_ulid, account_handle_normalized,
            sector, content_type, engagement_potential, likes_count, comments_count, engagement_total,
            content_pillar, emotion_primary,
            occasion, voice_observations, visual_observations, cultural_notes,
            quality_assessment, pattern_matches, content_ref, compliance_check, provenance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (observation_ulid) DO UPDATE SET
            voice_observations = EXCLUDED.voice_observations,
            visual_observations = EXCLUDED.visual_observations,
            pattern_matches = EXCLUDED.pattern_matches,
            likes_count = EXCLUDED.likes_count,
            comments_count = EXCLUDED.comments_count,
            engagement_total = EXCLUDED.engagement_total
    """, (
        record["observation_ulid"], record.get("account_ulid"),
        record.get("account_handle_normalized", ""),
        record.get("sector", ""), cr.get("content_type", ""),
        qa.get("engagement_potential", "medium"),
        cr.get("likes_count", 0), cr.get("comments_count", 0), cr.get("engagement_total", 0),
        record.get("content_pillar"), record.get("emotion_primary"),
        record.get("occasion"),
        json.dumps(record.get("voice_observations", {})),
        json.dumps(record.get("visual_observations", {})),
        json.dumps(record.get("cultural_notes")),
        json.dumps(qa),
        json.dumps(record.get("pattern_matches", [])),
        json.dumps(cr),
        json.dumps(record.get("compliance_check")),
        json.dumps(record.get("provenance", {}))
    ))


def upsert_generic(cur, table, pk_field, record):
    pk = record.get(pk_field)
    if not pk:
        return

    if table == "benchmark_accounts":
        cur.execute("""
            INSERT INTO benchmark_accounts (account_ulid, account_handle_normalized,
                sector, payload, provenance)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (account_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("handle_normalized", record.get("account_handle_normalized", "")),
            record.get("sector", ""), json.dumps(record),
            json.dumps(record.get("provenance", {}))
        ))
    elif table == "sector_baselines":
        cur.execute("""
            INSERT INTO sector_baselines (sector_baseline_ulid, sector_slug,
                sector_name_en, sector_name_ar, payload, provenance)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (sector_baseline_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("sector_slug", ""),
            record.get("sector_name_en", ""), record.get("sector_name_ar", ""),
            json.dumps(record), json.dumps(record.get("provenance", {}))
        ))
    elif table == "occasions":
        cur.execute("""
            INSERT INTO occasions (occasion_ulid, occasion_slug, name_en, name_ar,
                date_recurrence, payload, provenance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (occasion_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("occasion_slug", ""),
            record.get("name_en", ""), record.get("name_ar", ""),
            json.dumps(record.get("date_recurrence", {})),
            json.dumps(record), json.dumps(record.get("provenance", {}))
        ))
    elif table == "cd_brains":
        cur.execute("""
            INSERT INTO cd_brains (cd_brain_ulid, cd_brain_slug, name_internal,
                name_external, payload, provenance)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (cd_brain_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("cd_brain_slug", record.get("slug", "")),
            record.get("name_internal", record.get("name", "")),
            record.get("name_external", record.get("name", "")),
            json.dumps(record), json.dumps(record.get("provenance", {}))
        ))
    elif table == "cultural_specs":
        cur.execute("""
            INSERT INTO cultural_specs (cultural_spec_ulid, scope_label, payload, provenance)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cultural_spec_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("scope_label", record.get("scope", "")),
            json.dumps(record), json.dumps(record.get("provenance", {}))
        ))
    elif table == "campaign_archive":
        cur.execute("""
            INSERT INTO campaign_archive (campaign_ulid, campaign_code_anonymized,
                sector, year, cd_brain_used, payload, provenance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (campaign_ulid) DO UPDATE SET payload = EXCLUDED.payload
        """, (
            pk, record.get("campaign_code_anonymized", ""),
            record.get("sector", ""), record.get("year"),
            record.get("cd_brain_used"),
            json.dumps(record), json.dumps(record.get("provenance", {}))
        ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--table", help="sync only this table")
    args = parser.parse_args()

    print("═══ sync_to_supabase.py ═══\n")

    totals = {}
    errors = {}

    for file_glob, table, fmt, pk_field in FILE_TO_TABLE:
        if args.table and args.table != table:
            continue
        paths = sorted(REPO.glob(file_glob))
        totals[table] = len(paths)
        errors[table] = 0
        print(f"  {table:22} {len(paths):5} files", end="")

        if not args.execute:
            print(" (dry-run)")
            continue

        print(" → syncing...", end="", flush=True)

    if not args.execute:
        print(f"\nTotal: {sum(totals.values())} records across {len(totals)} tables (dry-run)")
        return 0

    import psycopg2
    db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    for file_glob, table, fmt, pk_field in FILE_TO_TABLE:
        if args.table and args.table != table:
            continue
        paths = sorted(REPO.glob(file_glob))
        loaded = 0
        errs = 0
        for path in paths:
            try:
                record = load_file(path, fmt)
                if table == "chains":
                    upsert_chain(cur, record)
                elif table == "account_patterns":
                    upsert_pattern(cur, record)
                elif table == "observations":
                    upsert_observation(cur, record)
                else:
                    upsert_generic(cur, table, pk_field, record)
                loaded += 1
            except Exception as e:
                errs += 1
                if errs <= 3:
                    print(f"\n    ! {path.name}: {e}")
        conn.commit()
        errors[table] = errs
        print(f"\r  {table:22} {loaded:5} loaded, {errs} errors")

    # Print summary
    print(f"\n{'─' * 40}")
    cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC")
    print("  DB row counts:")
    for row in cur.fetchall():
        print(f"    {row[0]:25} {row[1]:6} rows")

    cur.close()
    conn.close()

    total_errors = sum(errors.values())
    if total_errors:
        print(f"\n⚠️  {total_errors} errors during sync")
        return 1
    print(f"\n✅ Sync complete — {sum(totals.values())} records loaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
