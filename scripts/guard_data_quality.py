#!/usr/bin/env python3
"""
guard_data_quality.py
Catches the 6 categories of issues that hit ogz-knowledge in its first month.
Run BEFORE any commit that touches observation/pattern/chain files.

Categories covered:
  1. Schema/enum mismatch — validates enums, slugs, types at field level
  2. Silent failure / 0-obs — detects accounts claiming done but having no data
  3. Timeout awareness — checks daemon state for stuck accounts
  4. State management — detects duplicate handles, orphaned state
  5. Coverage gaps — sector×content_type holes, chain coverage
  6. Data quality — missing required fields, outlier values

Exit 0 = clean, Exit 1 = issues found.
"""
import json, glob, os, sys, re
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent.parent
os.chdir(BASE)

quick = "--quick" in sys.argv
issues = []

def fail(category, msg):
    issues.append(f"[{category}] {msg}")
    print(f"  ❌ [{category}] {msg}")

def ok(msg):
    print(f"  ✅ {msg}")

print("=" * 60)
print("OGZ DATA QUALITY GUARD")
print("=" * 60)

# ── Load data
obs_files = glob.glob('11_who_to_learn_from/observations/*/*.json')
all_obs = []
for f in obs_files:
    with open(f) as fh:
        all_obs.append((f, json.load(fh)))
total = len(all_obs)
print(f"\nLoaded {total} observations\n")

# ═══════════════════════════════════════════════════════════
# 1. SCHEMA / ENUM MISMATCH
# ═══════════════════════════════════════════════════════════
print("── 1. Schema / Enum Validation")

VALID_CONTENT_TYPES = {"image", "video", "carousel_slide", "story", "reel"}
VALID_ENGAGEMENT = {"high", "medium", "low"}
VALID_COMPLIANCE = {"clean", "soft_flagged", "hard_blocked"}
VALID_QUALITY = {"professional", "semi_professional", "ugc", "low"}
VALID_LANGUAGE = {"arabic", "english", "bilingual", "none"}
VALID_CONFIDENCE = {"strong", "moderate", "weak"}
SLUG_RE = re.compile(r'^[a-z0-9_]+$')

bad_content_type = 0
bad_engagement = 0
bad_confidence = 0
bad_slug = 0
bad_human_presence = 0

for fp, d in all_obs:
    ct = d.get('content_ref', {}).get('content_type', '')
    if ct and ct not in VALID_CONTENT_TYPES:
        bad_content_type += 1

    ep = d.get('quality_assessment', {}).get('engagement_potential', '')
    if ep and ep not in VALID_ENGAGEMENT:
        bad_engagement += 1

    for pm in d.get('pattern_matches', []):
        conf = pm.get('confidence', '')
        if conf and conf not in VALID_CONFIDENCE:
            bad_confidence += 1
        slug = pm.get('pattern_slug', '')
        if slug and not SLUG_RE.match(slug):
            bad_slug += 1

    hp = d.get('visual_observations', {}).get('human_presence')
    if hp is not None and not isinstance(hp, bool):
        bad_human_presence += 1

if bad_content_type: fail("ENUM", f"{bad_content_type} obs with invalid content_type")
else: ok("All content_type values valid")

if bad_engagement: fail("ENUM", f"{bad_engagement} obs with invalid engagement_potential")
else: ok("All engagement_potential values valid")

if bad_confidence: fail("ENUM", f"{bad_confidence} pattern_matches with invalid confidence (must be strong/moderate/weak)")
else: ok("All pattern confidence values valid")

if bad_slug: fail("SLUG", f"{bad_slug} pattern slugs with invalid characters (must be lowercase a-z, 0-9, underscore)")
else: ok("All pattern slugs are clean")

if bad_human_presence: fail("TYPE", f"{bad_human_presence} obs with non-boolean human_presence")
else: ok("All human_presence values are boolean or null")

# ═══════════════════════════════════════════════════════════
# 2. SILENT FAILURE / 0-OBS DETECTION
# ═══════════════════════════════════════════════════════════
print("\n── 2. Silent Failure Detection")

ta_path = '11_who_to_learn_from/target_accounts.json'
if os.path.exists(ta_path):
    with open(ta_path) as f:
        ta = json.load(f)

    obs_handles = set()
    for _, d in all_obs:
        h = d.get('account_handle_normalized', '').lstrip('@').lower()
        if h:
            obs_handles.add(h)

    ghosts = []
    for a in ta['accounts']:
        if a['status'] in ('done', 'force_done'):
            if a['handle'].lower() not in obs_handles:
                ghosts.append(a['handle'])

    if ghosts:
        fail("GHOST", f"{len(ghosts)} accounts marked done/force_done with 0 observations: {', '.join(ghosts[:5])}")
    else:
        ok("No ghost accounts")

    # Check for duplicate handles
    handles = [a['handle'].lower() for a in ta['accounts']]
    dupes = [h for h, c in Counter(handles).items() if c > 1]
    if dupes:
        fail("DUPE", f"Duplicate handles in target_accounts: {dupes}")
    else:
        ok("No duplicate handles")

# ═══════════════════════════════════════════════════════════
# 3. DAEMON STATE HEALTH
# ═══════════════════════════════════════════════════════════
print("\n── 3. Daemon State Health")

state_path = 'logs/enricher_state.json'
if os.path.exists(state_path):
    with open(state_path) as f:
        state = json.load(f)
    fail_count = state.get('last_caption_fail_count', 0)
    vo_fail = state.get('last_voiceover_fail_count', 0)
    if fail_count > 200:
        fail("DAEMON", f"Caption fail count very high: {fail_count}")
    else:
        ok(f"Caption fail count: {fail_count}")
    if vo_fail > 10:
        fail("DAEMON", f"Voiceover fail count high: {vo_fail}")
    else:
        ok(f"Voiceover fail count: {vo_fail}")
else:
    ok("No enricher state (daemon may not be running)")

# ═══════════════════════════════════════════════════════════
# 4. STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════
print("\n── 4. State Integrity")

# Check accounts_index matches obs handles
idx_path = '11_who_to_learn_from/accounts_index.json'
if os.path.exists(idx_path):
    with open(idx_path) as f:
        idx = json.load(f)
    idx_handles = set(k.lower() for k in idx.keys())
    missing_from_idx = obs_handles - idx_handles
    if missing_from_idx:
        fail("INDEX", f"{len(missing_from_idx)} obs handles missing from accounts_index")
    else:
        ok(f"Accounts index complete ({len(idx)} entries)")

# Check for pattern files with spaces or uppercase in slug
bad_pattern_files = []
for f in glob.glob('11_who_to_learn_from/patterns/*/*.json'):
    with open(f) as fh:
        p = json.load(fh)
    slug = p.get('pattern_slug', '')
    if slug and not SLUG_RE.match(slug):
        bad_pattern_files.append(slug)
if bad_pattern_files:
    fail("PATTERN", f"{len(bad_pattern_files)} pattern files with bad slugs: {bad_pattern_files[:3]}")
else:
    ok("All pattern file slugs clean")

# ── 4b. Sector Alias Validation
alias_path = '12_data_shapes/sector_aliases.json'
if os.path.exists(alias_path):
    with open(alias_path) as f:
        sa_config = json.load(f)
    canonical = set(sa_config.get('canonical', []))
    non_canonical = set()
    for _, d in all_obs:
        s = d.get('sector', '')
        if s and s not in canonical:
            non_canonical.add(s)
    if non_canonical:
        fail("SECTOR", f"Non-canonical sector values in obs: {non_canonical} — must be one of {canonical}")
    else:
        ok(f"All obs use canonical sector names ({len(canonical)} sectors)")
else:
    ok("No sector_aliases.json (skipping canonical check)")

# ═══════════════════════════════════════════════════════════
# 5. COVERAGE GAPS
# ═══════════════════════════════════════════════════════════
print("\n── 5. Coverage")

# Sectors in obs vs sectors in chains
obs_sectors = set(d.get('sector', '') for _, d in all_obs if d.get('sector'))
chain_sectors = set()
for f in glob.glob('02_what_to_build/*/*.json'):
    if 'INDEX' in f:
        continue
    with open(f) as fh:
        c = json.load(fh)
    for s in c.get('eligibility_filters', {}).get('sectors_allowed', []):
        chain_sectors.add(s)

uncovered = obs_sectors - chain_sectors
if uncovered:
    fail("COVERAGE", f"Sectors with obs but NO chains: {uncovered}")
else:
    ok(f"All {len(obs_sectors)} obs sectors have chain coverage")

# Check pattern orphans
pattern_slugs_on_disk = set()
for f in glob.glob('11_who_to_learn_from/patterns/*/*.json'):
    with open(f) as fh:
        pattern_slugs_on_disk.add(json.load(fh).get('pattern_slug', ''))
obs_slugs = set()
for _, d in all_obs:
    for pm in d.get('pattern_matches', []):
        s = pm.get('pattern_slug', '')
        if s:
            obs_slugs.add(s)
orphans = obs_slugs - pattern_slugs_on_disk
if orphans:
    fail("ORPHAN", f"{len(orphans)} pattern slugs in obs without pattern files")
else:
    ok("No orphan pattern slugs")

# ═══════════════════════════════════════════════════════════
# 6. DATA QUALITY
# ═══════════════════════════════════════════════════════════
print("\n── 6. Data Quality")

# Check for obs with no sector
no_sector = sum(1 for _, d in all_obs if not d.get('sector'))
if no_sector:
    fail("QUALITY", f"{no_sector} obs missing sector")
else:
    ok("All obs have sector")

# Check for obs with empty pattern_matches
no_patterns = sum(1 for _, d in all_obs if not d.get('pattern_matches'))
if no_patterns > total * 0.02:
    fail("QUALITY", f"{no_patterns} obs with empty pattern_matches ({100*no_patterns//total}%)")
else:
    ok(f"Pattern coverage: {total - no_patterns}/{total}")

# Check for analytics outlier: any sector with <5 obs used for best_by calculations
sector_counts = Counter(d.get('sector', '') for _, d in all_obs)
thin_sectors = [(s, c) for s, c in sector_counts.items() if c < 5 and s]
if thin_sectors:
    fail("QUALITY", f"Thin sectors (<5 obs, risk of outlier analytics): {thin_sectors}")
else:
    ok("All sectors have sufficient obs for analytics")

# ── Summary
print(f"\n{'=' * 60}")
if issues:
    print(f"❌ {len(issues)} ISSUE(S) FOUND:")
    for i in issues:
        print(f"   {i}")
    sys.exit(1)
else:
    print("✅ ALL GUARDS PASS — data quality clean")
    sys.exit(0)
