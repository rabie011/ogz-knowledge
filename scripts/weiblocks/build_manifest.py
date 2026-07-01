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

OUT_DIR = Path(__file__).resolve().parents[2] / "exports" / "weiblocks_v1"
MANIFEST = OUT_DIR / "MANIFEST.json"
# extensions beyond the 8-entity spec — listed separately so a strict loader can ignore them
EXTENSION_FILES = {"creative_methods.json", "routing_rules.json", "scorecard_weights.json"}
EXPORTED_AT = "2026-07-01"  # stamped, deterministic (not now())

# Export-level contract (spec §7).
EXPORT_VERSION = "ogz-knowledge-v1"
SCHEMA_CONTRACT = "weiblocks-knowledge-spec-v1"
VOCAB_MAPPING_APPLIED = True

# known_gaps[] — carried forward verbatim from the W1 builder honesty ledger so the whole
# export declares its edges in one place. These are DATA gaps, not script bugs.
KNOWN_GAPS = [
    "EXTENSIONS beyond the 8-entity spec (§0/§4.7 invited the fill): creative_methods, routing_rules, "
    "scorecard_weights — the Creative-Direction + scorecard KNOWLEDGE, versioned so it is not hardcoded "
    "in runtime code. BrandDNA method 'vulnerability' has NO OGz creative_method (a gap, not force-fit); "
    "cd_06 feed_cloner is OGz-proprietary. scorecard_weights are GUIDE-SOURCED, not measured.",
    "sectors.extra.observed_rhythm: REAL measured posting rhythm from the raw archive (recent >=2024 "
    "posts, AST hours, per-source-slug — fashion kept separate from retail_lifestyle to avoid "
    "distortion); comments_per_like is directional only, never a KPI.",
    "TYPING CONTRACT provenance.observed_count: integer when a real count exists, null when never "
    "counted — never 0-for-unknown (that would fabricate a measurement). Loaders must accept "
    "int|null on this field (DeepSeek final-verify note, release round 10).",
    "healthcare_wellness + real_estate sector BASELINES are HELD for validation (Mohamed's ruling: "
    "their voice profiles are extrapolated, not observed). Note: real_estate DOES have arabic "
    "per_sector_analysis in the corpus (healthcare does not) — the hold is a validation decision, "
    "not a data-absence claim. Observed BRAND DATA from held sectors still ships: retagged "
    "sector_key=Other with extra.provisional_sector=true + the real slug in extra.source_label "
    "(panel-ruled: real market observations are kept, flagged, never silently deleted).",
    "caption_patterns: descriptive prevalence ONLY ('used by N accounts') — the corpus's engagement "
    "label was retired as signal-free, so NO lift/engagement claims anywhere; Arabic fields are "
    "verbatim-source or null+translation_needed (never machine-written).",
    "dialect_variants: avoid_phrases_ar is [] on EVERY record — zero per-dialect avoid-phrase source "
    "exists in the corpus; any value would be fabrication. Occasion-generic greetings are excluded "
    "from signature phrases (extra.occasion_generic). Thin cells flagged extra.thin_cell.",
    "cultural_rule.description_ar is null on EVERY record — source rules are English-only and cultural "
    "rules are NEVER machine-translated (authenticity is the moat); each carries "
    "extra.translation_needed=true for a human Arabic pass.",
    "10 arabic_text_rule records carry domain='visual' with extra.enum_mismatch=true + "
    "true_domain='language_text' — the spec §5.4 domain enum has no language/text value, so they ship as "
    "advisory (nothing dropped, §4.7), flagged for a future enum extension.",
    "80/84 culturalspec_field records include held-sector (healthcare_wellness/real_estate) values in "
    "sector_defaults, flagged extra.is_held — informational FIELD defaults from existing cultural-spec "
    "files, NOT the held sector BASELINE records.",
    "reference_accounts (110) vs brand_observations (45) are LARGELY DISJOINT populations: only "
    "15 brands appear in both, so only 15/110 reference_accounts carry observation_ids and 30 "
    "brand_observations have no matching reference_account. The benchmark reference pool and the "
    "scraped observation pool were built from different account sets.",
    "brand_observations: 45 brands aggregated from 6,888 real observations. 95% of the source obs "
    "were keyed by REAL Instagram handles (not the anon scheme); those are hash-anonymized to "
    "OGZ-<SECTOR>-OBS-<sha256(handle)[:8]> (one-way, no reverse map stored). PRIVACY WARRANTY "
    "(exact): all @-handles — the brand's own AND third parties' — are replaced with [mention] in "
    "example_captions and recurring_phrases_ar; brand names may still appear as ordinary words "
    "inside verbatim caption text — that is the content itself, not an identifier leak.",
    "ENGAGEMENT UPGRADED FROM THE RAW LAYER (reextract_raw.py over 11_who_to_learn_from/_raw_archive, "
    "5,834 raw Apify posts): 40/45 brand_observations now carry REAL avg_likes (mean of >=5 non-giveaway "
    "scraped like-counts; giveaways excluded — they inflate averages) with metrics_source='apify_scrape' "
    "and verified=true + engagement_sample_size; the remaining 5 keep the honest null/qualitative shape.",
    "reference_account.trust: 63 verified / 47 unverified (46 dead IG handles from xlsx prefix-"
    "mangling + 1 unmatched). Engine must filter trust=verified before using the fallback pool.",
    "international brands present in brand_observations (e.g. global retail/fragrance active in the "
    "Saudi market) are NOT flagged is_international — deferred: no verified international-brand list "
    "exists to ground the flag, so it is left unset rather than guessed.",
    "visual_pattern records are confidence=experimental (observed_count=null) — chains are "
    "templates, not observed post outcomes; parsed/authored fields, not measured.",
    "occasion behavior fields (type, priority, lead_weeks, recommended_mix_shift, tone_shift, "
    "sector_applicability, hard_rules, soft_flags) are DERIVED from cultural_significance "
    "weights + day_specific_variations — curated inference, not observed campaign data.",
    "No tone->approval/engagement table exists in the corpus: sector voice.top/worst_performing_"
    "tones.approval_rate is a PREVALENCE proxy, not a measured approval rate.",
    "sector content_mix_default (product/lifestyle/occasion/brand_story/founder) is fully "
    "INFERRED — no observed content-mix split exists anywhere in the sources.",
    "common_hashtags_ar are REAL scraped '#hashtags' from the raw archive for the 3 observed sectors "
    "(hashtag_source='apify_scrape' per entry); keyword_cluster entries only as a declared fallback. "
    "Occasion recovery from raw captions reconnected mothers_day (9 brands) and esports_world_cup (2); "
    "soundstorm + singles_day remain honestly zero-evidence (0 posts in 5,834 raw captions).",
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

    extensions = {k: files.pop(k) for k in list(files) if k in EXTENSION_FILES}
    manifest = {
        "export_version": EXPORT_VERSION,
        "exported_at": EXPORTED_AT,
        "schema_contract": SCHEMA_CONTRACT,
        "vocab_mapping_applied": VOCAB_MAPPING_APPLIED,
        "files": files,
        "extensions": extensions,
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
