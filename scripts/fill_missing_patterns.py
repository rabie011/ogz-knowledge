#!/usr/bin/env python3
"""
fill_missing_patterns.py
Generate pattern JSON files for all orphaned pattern slugs —
slugs that appear in observations but have no corresponding pattern file.

Uses Claude Batch API (Haiku 4.5) for cost-efficient generation.
Writes to correct patterns/ subfolder based on pattern category.

Usage:
  python3 scripts/fill_missing_patterns.py           # generate all
  python3 scripts/fill_missing_patterns.py --batch 10 # generate 10 at a time
  python3 scripts/fill_missing_patterns.py --dry-run  # show what would be generated

Safe to re-run: skips slugs where pattern file already exists.
"""
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from ulid import ULID

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
PATTERNS    = BASE / "11_who_to_learn_from" / "patterns"
LOGS        = BASE / "logs"

# ── Pattern subfolder categories ──────────────────────────────────────────────
SUBFOLDERS = [
    "content_types",
    "voice_techniques",
    "occasion_plays",
    "visual_compositions",
    "color_palette_patterns",
    "setting_environment",
    "lighting_moods",
    "caption_structure",
    "character_representation",
    "hospitality_intensity",
]

# Heuristic pre-assignment based on slug keywords (reduces API calls)
SLUG_CATEGORY_HINTS = {
    "occasion": "occasion_plays",
    "eid": "occasion_plays",
    "ramadan": "occasion_plays",
    "national": "occasion_plays",
    "founding": "occasion_plays",
    "summer": "occasion_plays",
    "winter": "occasion_plays",
    "campaign": "content_types",
    "promo": "content_types",
    "launch": "content_types",
    "reveal": "content_types",
    "collab": "content_types",
    "ugc": "content_types",
    "gamif": "content_types",
    "behind": "content_types",
    "influencer": "content_types",
    "employee": "character_representation",
    "founder": "character_representation",
    "team": "character_representation",
    "face": "character_representation",
    "testimonial": "character_representation",
    "caption": "caption_structure",
    "copy": "voice_techniques",
    "voice": "voice_techniques",
    "tone": "voice_techniques",
    "nostalgia": "voice_techniques",
    "storytelling": "voice_techniques",
    "hospitality": "hospitality_intensity",
    "arabic_hospitality": "hospitality_intensity",
    "color": "color_palette_patterns",
    "palette": "color_palette_patterns",
    "setting": "setting_environment",
    "environment": "setting_environment",
    "location": "setting_environment",
    "lighting": "lighting_moods",
    "mood": "lighting_moods",
    "composition": "visual_compositions",
    "visual": "visual_compositions",
    "layout": "visual_compositions",
    "overhead": "visual_compositions",
    "closeup": "visual_compositions",
    "brand_values": "voice_techniques",
    "discount": "content_types",
    "price": "content_types",
    "limited": "content_types",
    "engagement_mechanic": "content_types",
    "app_exclusive": "content_types",
    "entertainment": "content_types",
}


def _guess_subfolder(slug: str) -> str:
    slug_lower = slug.lower()
    for keyword, folder in SLUG_CATEGORY_HINTS.items():
        if keyword in slug_lower:
            return folder
    return "content_types"  # default


# ── Load env ───────────────────────────────────────────────────────────────────
def _load_env():
    """Load env from ~/.abraham_env — override empty/missing keys."""
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # Override if not set or set to empty string
                if not os.environ.get(k):
                    os.environ[k] = v

_load_env()


# ── Find orphaned slugs ────────────────────────────────────────────────────────
def find_orphaned_slugs() -> list[dict]:
    """Return list of {slug, obs_count, sectors, eng_rates, examples}."""
    existing = {f.stem for f in PATTERNS.rglob("*.json")}
    slug_data: dict[str, dict] = {}

    for f in sorted(OBS_ROOT.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        sector = d.get("sector", "")
        eng = d.get("quality_assessment", {}).get("engagement_potential", "")
        caption = (d.get("voice_observations") or {}).get("caption_text") or ""
        account = d.get("account_handle_normalized", "")

        for pm in d.get("pattern_matches", []):
            slug = pm.get("pattern_slug") or pm.get("slug", "")
            if not slug or slug in existing:
                continue
            if slug not in slug_data:
                slug_data[slug] = {
                    "slug": slug,
                    "count": 0,
                    "sectors": Counter(),
                    "eng": Counter(),
                    "examples": [],
                    "accounts": set(),
                }
            sd = slug_data[slug]
            sd["count"] += 1
            sd["sectors"][sector] += 1
            sd["eng"][eng] += 1
            sd["accounts"].add(account)
            if len(sd["examples"]) < 3 and caption:
                sd["examples"].append(caption[:200])

    result = []
    for slug, sd in sorted(slug_data.items(), key=lambda x: -x[1]["count"]):
        total = sd["count"]
        high = sd["eng"].get("high", 0) + sd["eng"].get("very_high", 0)
        high_rate = round(high / total, 2) if total else 0
        result.append({
            "slug": slug,
            "obs_count": total,
            "sectors": dict(sd["sectors"].most_common()),
            "high_engagement_rate": high_rate,
            "account_count": len(sd["accounts"]),
            "examples": sd["examples"],
        })

    return result


# ── Build batch request ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Saudi content intelligence analyst building a pattern library.
Generate a complete pattern JSON for a Saudi Instagram content pattern.
Return ONLY valid JSON — no explanation, no markdown, just the JSON object."""

def _build_user_prompt(slug_info: dict) -> str:
    slug = slug_info["slug"]
    sectors = slug_info["sectors"]
    obs_count = slug_info["obs_count"]
    high_rate = slug_info["high_engagement_rate"]
    examples = slug_info["examples"]
    account_count = slug_info["account_count"]

    example_text = ""
    if examples:
        example_text = "\nCaption examples from observations:\n" + "\n".join(
            f'  - "{e[:150]}"' for e in examples
        )

    name_readable = slug.replace("_", " ").title()

    return f"""Generate a complete pattern JSON for the Saudi Instagram content pattern:
Slug: {slug}
Pattern name: {name_readable}
Appears in {obs_count} observations across {account_count} accounts
Sectors: {sectors}
High engagement rate: {high_rate:.0%}
{example_text}

Return JSON with ALL these fields (exact field names, exact enum values):
{{
  "pattern_ulid": "PLACEHOLDER",
  "pattern_name": "{name_readable}",
  "pattern_slug": "{slug}",
  "schema_version": 1,
  "description": "Clear 1-2 sentence description of what this pattern IS (30+ chars)",
  "observed_in_sectors": {json.dumps(list(sectors.keys()))},
  "observed_in_account_count": {account_count},
  "structural_recipe": "How to execute this pattern: what to show, what to say, how to structure it",
  "why_it_works": "Why this pattern drives engagement in Saudi market (cultural/psychological reason)",
  "transplantation_caveats": ["Any cultural constraints or risks when using this pattern"],
  "applicable_chains": [],
  "avg_engagement_multiplier_observed": "{high_rate:.0%} high-eng ({obs_count} obs)",
  "cultural_constraints": [],
  "provenance": {{
    "source": "cross_account_synthesis_2026 + benchmark_account observations",
    "date_added": "{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "confirmer": "claude_code_extraction",
    "confidence": "inferred",
    "scope": "{'+'.join('sector:' + s for s in sectors.keys()) if sectors else 'universal'}"
  }},
  "status": "evidence_based",
  "obs_usage_count": {obs_count}
}}"""


# ── Call Batch API ─────────────────────────────────────────────────────────────
def generate_batch(orphaned_batch: list[dict], client: anthropic.Anthropic) -> dict[str, dict]:
    """Submit batch, wait for completion, return {slug: pattern_dict}."""
    requests = []
    for info in orphaned_batch:
        requests.append({
            "custom_id": info["slug"],
            "params": {
                "model": "claude-haiku-4-5",
                "max_tokens": 1200,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": _build_user_prompt(info)}],
            },
        })

    print(f"  Submitting batch of {len(requests)} to Claude Haiku 4.5...", flush=True)
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"  Batch ID: {batch_id}", flush=True)

    # Poll until complete
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(
            f"  Status: {status} | "
            f"succeeded={counts.succeeded} errored={counts.errored} processing={counts.processing}",
            flush=True,
        )
        if status == "ended":
            break
        time.sleep(10)

    # Collect results
    results = {}
    for result in client.messages.batches.results(batch_id):
        slug = result.custom_id
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text.strip()
            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            try:
                pattern = json.loads(text)
                results[slug] = pattern
            except json.JSONDecodeError as e:
                print(f"  ⚠ JSON parse error for {slug}: {e}")
        else:
            print(f"  ✗ {slug}: {result.result.type}")

    return results


# ── Write pattern files ────────────────────────────────────────────────────────
def write_pattern(pattern: dict, subfolder: str) -> Path:
    slug = pattern["pattern_slug"]
    # Generate a real ULID
    pattern["pattern_ulid"] = str(ULID())

    folder = PATTERNS / subfolder
    folder.mkdir(exist_ok=True)
    out = folder / f"{slug}.json"
    out.write_text(json.dumps(pattern, ensure_ascii=False, indent=2))
    return out


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    dry_run  = "--dry-run" in sys.argv
    batch_n  = 10  # default batch size

    for i, arg in enumerate(sys.argv):
        if arg == "--batch" and i + 1 < len(sys.argv):
            batch_n = int(sys.argv[i + 1])

    if dry_run:
        print("DRY RUN — no files will be written\n")

    orphaned = find_orphaned_slugs()
    print(f"Orphaned pattern slugs found: {len(orphaned)}")
    if not orphaned:
        print("Nothing to do.")
        return

    # Show top 20
    print("\nTop orphaned slugs:")
    for info in orphaned[:20]:
        print(
            f"  {info['slug']:45s}  {info['obs_count']} obs  "
            f"{info['high_engagement_rate']:.0%} high-eng"
        )

    if dry_run:
        return

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    total_generated = 0
    total_errors    = 0
    LOGS.mkdir(exist_ok=True)

    # Process in batches
    for batch_start in range(0, len(orphaned), batch_n):
        batch = orphaned[batch_start : batch_start + batch_n]
        print(
            f"\nBatch {batch_start//batch_n + 1}: "
            f"slugs {batch_start+1}–{batch_start+len(batch)} / {len(orphaned)}"
        )

        results = generate_batch(batch, client)

        for info in batch:
            slug = info["slug"]
            if slug not in results:
                total_errors += 1
                continue

            pattern = results[slug]
            subfolder = _guess_subfolder(slug)
            out = write_pattern(pattern, subfolder)
            total_generated += 1
            print(
                f"  ✅  {slug:45s}  → patterns/{subfolder}/{slug}.json"
            )

        print(f"  Batch done: {len(results)}/{len(batch)} succeeded")

    print(f"\n{'='*60}")
    print(f"COMPLETE: Generated {total_generated} pattern files  |  Errors: {total_errors}")
    print(f"\nNext step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
