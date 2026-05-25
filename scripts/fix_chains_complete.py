#!/usr/bin/env python3
"""
fix_chains_complete.py
----------------------
Does three things in one pass:

1. Translates all 88 chain name_ar fields to proper Arabic using Claude API
2. Fills chain_codes_in_family arrays in INDEX.json
3. Flags the 7 chains with model_id "Not supported" / "—" in a report

Run: python3 scripts/fix_chains_complete.py
"""
import json, os, time
from pathlib import Path
import anthropic

REPO = Path('/Users/abarihm/Desktop/ogz-knowledge')
CHAINS_DIR = REPO / '02_what_to_build'
INDEX_PATH = CHAINS_DIR / 'INDEX.json'

# ── Load env ──────────────────────────────────────────────────────────────────
def load_env():
    env_path = Path.home() / '.abraham_env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

# ── Collect all chains ────────────────────────────────────────────────────────
chains_data = []
for f in sorted(CHAINS_DIR.rglob('*.json')):
    if f.name == 'INDEX.json':
        continue
    d = json.loads(f.read_text())
    chains_data.append({
        'path': f,
        'chain_id': d['chain_id_short'],
        'family': d['family'],
        'name_en': d['name_en'],
        'name_ar': d['name_ar'],
        'data': d
    })

chains_data.sort(key=lambda x: x['chain_id'])
print(f'Loaded {len(chains_data)} chains')

# ── Build translation prompt for ALL 88 at once ───────────────────────────────
chain_list = '\n'.join(
    f'{c["chain_id"]} | {c["name_en"]}'
    for c in chains_data
)

SYSTEM = """You are a senior Arabic creative director at a Saudi digital marketing agency.
You are translating content chain names from English to Arabic for a Saudi B2B creative intelligence platform.

Rules:
- Use natural Saudi creative industry Arabic — the kind used in agency briefs, not academic MSA
- Photography/visual terms: use established Arabic equivalents (تصوير، خلفية، إضاءة، منتج، etc.)
- For Saudi-specific chains (TF23): preserve the cultural specificity, use authentic Saudi framing
- Keep names SHORT — max 6 words in Arabic, matching the brevity of the English originals
- Do NOT transliterate English words — always use Arabic equivalents
- Numbers, punctuation and dashes can stay as-is
- Return ONLY the translation list in the exact format: chain_id | arabic_name
- No explanation, no extra text, just the list"""

USER = f"""Translate these 88 content chain names to Arabic creative industry terminology.
Each line: chain_id | english_name → return: chain_id | arabic_translation

{chain_list}"""

# ── Call Claude API ───────────────────────────────────────────────────────────
print('Calling Claude API for all 88 translations...')
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

message = client.messages.create(
    model='claude-opus-4-5',
    max_tokens=4096,
    system=SYSTEM,
    messages=[{'role': 'user', 'content': USER}]
)

raw_response = message.content[0].text
print(f'Received {len(raw_response)} chars from API')
print()

# ── Parse response ────────────────────────────────────────────────────────────
translations = {}
for line in raw_response.strip().splitlines():
    line = line.strip()
    if not line or '|' not in line:
        continue
    parts = line.split('|', 1)
    if len(parts) == 2:
        chain_id = parts[0].strip()
        arabic = parts[1].strip()
        translations[chain_id] = arabic

print(f'Parsed {len(translations)} translations')

# Verify we got all 88
missing = [c['chain_id'] for c in chains_data if c['chain_id'] not in translations]
if missing:
    print(f'WARNING: Missing translations for: {missing}')
else:
    print('All 88 chains translated ✅')

# ── Task 1: Write name_ar to all chain files ──────────────────────────────────
print('\n── Task 1: Writing Arabic names to chain files ──')
updated = 0
for c in chains_data:
    arabic = translations.get(c['chain_id'])
    if not arabic:
        print(f'  SKIP {c["chain_id"]} — no translation')
        continue
    d = c['data']
    d['name_ar'] = arabic
    c['path'].write_text(json.dumps(d, indent=2, ensure_ascii=False))
    print(f'  ✅ {c["chain_id"]:12s} | {c["name_en"]:45s} → {arabic}')
    updated += 1

print(f'\nUpdated {updated}/88 chain files')

# ── Task 2: Fill chain_codes_in_family in INDEX.json ─────────────────────────
print('\n── Task 2: Filling chain_codes_in_family in INDEX.json ──')
index = json.loads(INDEX_PATH.read_text())

# Build family → raw_codes mapping
family_codes = {}
for c in chains_data:
    fam = c['family']
    # Extract raw_code from chain_id (tf01_01 → T01, tf23_10 → T10 etc.)
    # Actually raw_code is in the chain data
    raw_code = c['data'].get('notes', {})
    # Get it from the chain data directly
    d = c['data']
    # raw_code field might be in notes or we derive from chain_id_short
    # Check the actual field
    rc = None
    for key in ['raw_code']:
        if key in d:
            rc = d[key]
            break
    if not rc:
        # derive: tf01_01 → the raw code in the filename
        # Look at the notes field for source code
        notes = d.get('notes', {})
        rc = notes.get('source_code') or notes.get('raw_code')
    if not rc:
        rc = c['chain_id'].upper()

    family_codes.setdefault(fam, []).append(rc)

# Update INDEX families
families_updated = 0
for fam_entry in index['families']:
    fid = fam_entry['family_id']
    codes = family_codes.get(fid, [])
    fam_entry['chain_codes_in_family'] = codes
    families_updated += 1
    print(f'  {fid}: {len(codes)} codes → {codes}')

# Also update name_ar in INDEX chains array
for chain_entry in index.get('chains', []):
    cid = chain_entry.get('chain_id_short')
    if cid and cid in translations:
        chain_entry['name_ar'] = translations[cid]

index['updated_at'] = '2026-05-25T00:00:00Z'
INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False))
print(f'\nUpdated {families_updated} family entries in INDEX.json ✅')

# ── Task 3: Flag model_id issues ──────────────────────────────────────────────
print('\n── Task 3: Model availability report ──')
flagged = []
for c in chains_data:
    d = c['data']
    for m in d.get('models_used', []):
        model_id = m.get('model_id', '')
        if model_id in ('Not supported', '—', '', None):
            flagged.append({
                'chain_id': c['chain_id'],
                'name_en': c['name_en'],
                'family': c['family'],
                'role': m.get('role', ''),
                'model_id': model_id
            })

print(f'Found {len(flagged)} chains with unsupported/TBD model_id:')
for f in flagged:
    print(f'  {f["chain_id"]:12s} | {f["family"]} | {f["role"]:30s} | model_id="{f["model_id"]}"')

# Write flag report
report_path = REPO / 'logs' / 'chain_model_flags.json'
report_path.write_text(json.dumps({
    'generated_at': '2026-05-25T00:00:00Z',
    'note': 'Chains where model_id is Not supported or TBD. These chains need model assignment when image-to-video / native video generation is available.',
    'flagged_count': len(flagged),
    'flagged': flagged
}, indent=2, ensure_ascii=False))
print(f'\nModel flag report written to logs/chain_model_flags.json')

# ── Final summary ─────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('ALL TASKS COMPLETE')
print('='*60)
print(f'  Task 1 — name_ar translated:      {updated}/88 chains')
print(f'  Task 2 — chain_codes_in_family:   {families_updated}/23 families filled')
print(f'  Task 3 — model flags logged:      {len(flagged)} chains flagged')
print(f'\nRun validate_all.py to confirm schema still passes.')
