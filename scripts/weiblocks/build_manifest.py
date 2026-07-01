#!/usr/bin/env python3
"""build_manifest.py — assemble the Weiblocks export MANIFEST.json (spec §7).

Scans exports/weiblocks_v1/*.json (and any *.ndjson), counts records per file, and emits
MANIFEST.json with the export-level contract fields + a per-file {format, records} block +
the carried-forward known_gaps[]. The manifest itself is EXCLUDED from the scan (a manifest
does not index itself). Counts come from a real read of each file — never guessed:
  - array  -> len(json.load(...))          (a top-level JSON list)
  - ndjson -> count of non-blank lines      (one JSON object per line)
Native Arabic is not written by this file (it emits only ASCII contract metadata), but we
still write with ensure_ascii=False so any Arabic in a future filename/gap survives raw.

Deterministic: exported_at is stamped (2026-07-01), files are sorted, so re-runs are stable.
Honesty (Rule #12): the record counts are the real on-disk numbers; if a file cannot be read
or a .json is not a top-level array, the script REFUSES to proceed (Rule #8) rather than
emitting a fabricated count.
"""
import glob
import json
import sys
from pathlib import Path

OUT_DIR = Path("/Users/abarihm/Desktop/ogz-knowledge/exports/weiblocks_v1")
MANIFEST = OUT_DIR / "MANIFEST.json"
EXPORTED_AT = "2026-07-01"  # stamped, deterministic (not now())

# Export-level contract (spec §7).
EXPORT_VERSION = "ogz-knowledge-v1"
SCHEMA_CONTRACT = "weiblocks-knowledge-spec-v1"
VOCAB_MAPPING_APPLIED = True

# known_gaps[] — carried forward verbatim from the W1 builder honesty ledger so the whole
# export declares its edges in one place. These are DATA gaps, not script bugs.
KNOWN_GAPS = [
    "healthcare_wellness + real_estate sectors HELD for validation — present in all source "
    "logs but not emitted; intelligence_depth 0 and no arabic_copywriting per_sector_analysis, "
    "so their voice/copy signals could not be grounded. Emit only after human validation.",
    "dialect, brand_observation, reference, cultural, and caption entities are later waves — "
    "not part of this v1 export (sector + visual_pattern + occasion only).",
    "visual_pattern records are confidence=experimental (observed_count=null) — chains are "
    "templates, not observed post outcomes; parsed/authored fields, not measured.",
    "occasion behavior fields (type, priority, lead_weeks, recommended_mix_shift, tone_shift, "
    "sector_applicability, hard_rules, soft_flags) are DERIVED from cultural_significance "
    "weights + day_specific_variations — curated inference, not observed campaign data.",
    "No tone->approval/engagement table exists in the corpus: sector voice.top/worst_performing_"
    "tones.approval_rate is a PREVALENCE proxy, not a measured approval rate.",
    "sector content_mix_default (product/lifestyle/occasion/brand_story/founder) is fully "
    "INFERRED — no observed content-mix split exists anywhere in the sources.",
    "common_hashtags_ar are occasion KEYWORDS (occasion_keyword_clusters), not scraped "
    "'#hashtag' tokens — the corpus has no hashtag text field.",
    "visual_pattern record count is 127 (all real chain files: INDEX.json total_chains=127), "
    "not the '88 canonical' figure — flagged, not silently trimmed.",
]


def count_array_json(path: Path) -> int:
    """A .json export must be a top-level JSON array; return its length. Refuse otherwise."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(
            f"{path.name}: expected a top-level JSON array, got {type(data).__name__}"
        )
    return len(data)


def count_ndjson(path: Path) -> int:
    """One JSON object per line; count non-blank lines and assert each parses."""
    n = 0
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path.name}: line {i} is not valid JSON: {e}") from e
            n += 1
    return n


def scan() -> dict:
    files: dict[str, dict] = {}
    paths = sorted(
        p
        for p in list(OUT_DIR.glob("*.json")) + list(OUT_DIR.glob("*.ndjson"))
        if p.name != MANIFEST.name
    )
    if not paths:
        print(f"REFUSE: no *.json/*.ndjson export files found in {OUT_DIR}", file=sys.stderr)
        sys.exit(2)
    for p in paths:
        if p.suffix == ".ndjson":
            fmt, records = "ndjson", count_ndjson(p)
        else:
            fmt, records = "array", count_array_json(p)
        files[p.name] = {"format": fmt, "records": records}
    return files


def main() -> None:
    try:
        files = scan()
    except (ValueError, json.JSONDecodeError, OSError) as e:
        # Rule #8 REFUSE, DON'T WARN: a bad count is worse than no manifest.
        print(f"REFUSE: cannot build manifest — {e}", file=sys.stderr)
        sys.exit(1)

    manifest = {
        "export_version": EXPORT_VERSION,
        "exported_at": EXPORTED_AT,
        "schema_contract": SCHEMA_CONTRACT,
        "vocab_mapping_applied": VOCAB_MAPPING_APPLIED,
        "files": files,
        "known_gaps": KNOWN_GAPS,
    }

    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    total = sum(f["records"] for f in files.values())
    print(f"wrote {MANIFEST} — {len(files)} files, {total} total records")
    for name, meta in files.items():
        print(f"  {name}: {meta['format']} · {meta['records']} records")


if __name__ == "__main__":
    main()
