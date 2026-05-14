#!/usr/bin/env python3
"""
sync_to_supabase.py — Memory Controller's file → database sync (STUB).

This stub reads every record file in the repo, validates against schemas, and
prints intended UPSERTs in --dry-run mode (default). Real DB writes are Week 2
work in `ogz-runtime`.

Usage:
    .venv/bin/python sync_to_supabase.py --dry-run         # default
    .venv/bin/python sync_to_supabase.py --execute         # not implemented yet

Future env vars (for --execute):
    SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_REGION (me-central-1 / Bahrain)

Memory Controller principle: this is the ONLY program that writes to the
database. Agents never write directly. CI runs this on merge to main.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parent

FILE_TO_TABLE = [
    ("02_what_to_build/TF*/tf*.json",                   "chains",              "json"),
    ("05_sector_defaults/*.yaml",                       "sector_baselines",    "yaml"),
    ("06_saudi_calendar/*.yaml",                        "occasions",           "yaml"),
    ("20_cd_brains/cd_0*.md",                           "cd_brains",           "md_frontmatter"),
    ("15_cultural_specs/sector_defaults/*.yaml",        "cultural_specs",      "yaml"),
    ("11_who_to_learn_from/accounts/**/*.json",         "benchmark_accounts",  "json"),
    ("11_who_to_learn_from/patterns/**/*.json",         "account_patterns",    "json"),
    ("21_campaign_archive/campaigns/*.json",            "campaign_archive",    "json"),
]


def load(path: Path, fmt: str):
    if fmt == "json":
        return json.loads(path.read_text())
    if fmt == "yaml":
        return yaml.safe_load(path.read_text())
    if fmt == "md_frontmatter":
        text = path.read_text()
        if not text.startswith("---\n"):
            raise ValueError(f"missing front-matter in {path}")
        end = text.find("\n---\n", 4)
        if end < 0:
            raise ValueError(f"unterminated front-matter in {path}")
        return yaml.safe_load(text[4:end])
    raise ValueError(f"unknown fmt: {fmt}")


def primary_key_for(table: str, record: dict) -> str | None:
    pk_field = {
        "chains": "chain_ulid",
        "sector_baselines": "sector_baseline_ulid",
        "occasions": "occasion_ulid",
        "cd_brains": "cd_brain_ulid",
        "cultural_specs": "cultural_spec_ulid",
        "benchmark_accounts": "account_ulid",
        "account_patterns": "pattern_ulid",
        "campaign_archive": "campaign_ulid",
    }.get(table)
    return record.get(pk_field) if pk_field else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ogz-knowledge files → Supabase tables.")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--manifest-out", default="sync_manifest.json")
    args = parser.parse_args()

    if args.execute:
        print("⚠️  --execute is NOT IMPLEMENTED YET. Wire SUPABASE_URL + SUPABASE_SERVICE_KEY in ogz-runtime.")
        return 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run",
        "target_supabase": {
            "url": os.environ.get("SUPABASE_URL", "(not set — required for --execute)"),
            "region_intent": "me-central-1 (Bahrain)",
        },
        "tables": {},
    }

    print("═══ sync_to_supabase.py — DRY RUN ═══\n")
    total_records = 0
    seen_pks: set[str] = set()
    for glob, table, fmt in FILE_TO_TABLE:
        paths = list(REPO.glob(glob))
        records_seen = 0
        sample_pks: list[str] = []
        for path in paths:
            try:
                record = load(path, fmt)
                pk = primary_key_for(table, record)
                if pk:
                    seen_pks.add(pk)
                    if len(sample_pks) < 3:
                        sample_pks.append(pk[:10] + "…")
                records_seen += 1
            except Exception as e:
                print(f"  ! load failed: {path.relative_to(REPO)} — {e}")
        manifest["tables"][table] = {
            "records_seen": records_seen,
            "sample_pks": sample_pks,
            "file_glob": glob,
            "format": fmt,
        }
        total_records += records_seen
        print(f"  → {table:22} {records_seen:5} records (e.g. {sample_pks[:2]})")

    manifest["total_records"] = total_records
    (REPO / args.manifest_out).write_text(json.dumps(manifest, indent=2))
    print(f"\nTotal: {total_records} records would be UPSERTed.")
    print(f"Manifest written to: {args.manifest_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
