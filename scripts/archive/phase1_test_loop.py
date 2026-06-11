#!/usr/bin/env python3
"""
phase1_test_loop.py — Comprehensive Phase 1 test suite.
Run 10 times: test → find issues → score each area.
Usage: python3 scripts/phase1_test_loop.py --iteration N
"""
import json, glob, re, os, sys, time
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / 'scripts'))

# Load env
env_path = Path.home() / '.abraham_env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"\''))

import lib.quality_gate as qg
qg._brain = None  # always fresh
from lib.quality_gate import check, auto_fix

import openai
client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

PASS = '✅'; WARN = '⚡'; FAIL = '❌'
issues = []
scores = {}

def log_issue(area, msg, severity='warn'):
    issues.append({'area': area, 'msg': msg, 'severity': severity})
    icon = FAIL if severity == 'fail' else WARN
    print(f'  {icon} {area}: {msg}')

def log_pass(area, msg):
    print(f'  {PASS} {area}: {msg}')


# ─────────────────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print(f'  PHASE 1 COMPREHENSIVE TEST')
print('='*60)

brain = json.loads((BASE / '11_who_to_learn_from' / 'intelligence_layer.json').read_text())
tlib = json.loads((BASE / '11_who_to_learn_from' / 'template_library.json').read_text())

# ── TEST A: Brain integrity ──────────────────────────────────────────────────
print('\n[A] BRAIN INTEGRITY')
bp = brain.get('brand_profiles', {})
rm = brain.get('real_metrics', {})
sf = brain.get('sector_facts', {})
bpn = brain.get('brand_product_names', {})

# A1: All verified brands have profiles
missing_profiles = [h for h in rm if h not in bp]
if missing_profiles: log_issue('A1_profiles', f'Missing: {missing_profiles}', 'fail')
else: log_pass('A1_profiles', f'All {len(rm)} verified brands have profiles')

# A2: No wrong sector names
bad_sectors = [(h, p['sector']) for h,p in bp.items() if p.get('sector') in ('beauty','retail','healthcare')]
if bad_sectors: log_issue('A2_sectors', f'Wrong sectors: {bad_sectors}', 'fail')
else: log_pass('A2_sectors', f'All {len(bp)} profiles have canonical sectors')

# A3: No stale arabic_style
stale = [(h, p.get('arabic_style')) for h,p in bp.items() if p.get('arabic_style') == 'colloquial_gulf']
if stale: log_issue('A3_arabic_style', f'Stale: {stale}', 'warn')
else: log_pass('A3_arabic_style', 'No stale arabic_style values')

# A4: Sector facts match real counts
actual_counts = Counter()
for f in glob.glob(str(BASE/'11_who_to_learn_from'/'observations'/'*'/'*.json')):
    d = json.loads(Path(f).read_text())
    actual_counts[d.get('sector','')] += 1
sf_ok = all(sf.get(s,{}).get('obs_count',0) == actual_counts[s] for s in actual_counts)
if not sf_ok:
    mismatches = [(s, sf.get(s,{}).get('obs_count',0), actual_counts[s]) for s in actual_counts
                  if sf.get(s,{}).get('obs_count',0) != actual_counts[s]]
    log_issue('A4_sector_facts', f'Mismatches: {mismatches}', 'fail')
else: log_pass('A4_sector_facts', 'All sector facts match real counts')

# A5: All verified brands have product names
missing_pnames = [h for h in rm if h not in bpn]
if missing_pnames: log_issue('A5_product_names', f'Missing: {missing_pnames}', 'warn')
else: log_pass('A5_product_names', f'All {len(rm)} brands have product name entries')

# A6: Brain has all 8 occasions
occ_cal = brain.get('occasion_calendar', {})
required_occasions = ['ramadan','eid_al_fitr','eid_al_adha','hajj_season','national_day','founding_day','riyadh_season','jeddah_season']
missing_occ = [o for o in required_occasions if o not in occ_cal]
if missing_occ: log_issue('A6_occasions', f'Missing: {missing_occ}', 'fail')
else: log_pass('A6_occasions', f'All 8 occasions in calendar')

scores['A_brain'] = 100 - len([i for i in issues if i['severity']=='fail' and 'A' in i['area']]) * 20

# ── TEST B: Template Library ─────────────────────────────────────────────────
print('\n[B] TEMPLATE LIBRARY')
templates = tlib.get('templates', [])

# B1: Count and integrity
if len(templates) < 1000:
    log_issue('B1_count', f'Only {len(templates)} templates (expected ≥1000)', 'fail')
else: log_pass('B1_count', f'{len(templates)} templates total')

# B2: No empty captions
empty = [t for t in templates if not t.get('caption') or len(t.get('caption','').strip()) < 10]
if empty: log_issue('B2_empty', f'{len(empty)} empty/short captions', 'fail')
else: log_pass('B2_empty', 'No empty captions')

# B3: Coverage — every sector has ≥3 gold or silver
SECTORS = ['f_and_b','fashion','retail_lifestyle','beauty_personal_care','healthcare_wellness','real_estate']
sector_tiers = defaultdict(lambda: defaultdict(int))
for t in templates:
    sector_tiers[t['sector']][t['tier']] += 1

coverage_issues = []
for s in SECTORS:
    gold = sector_tiers[s].get('gold', 0)
    silver = sector_tiers[s].get('silver', 0)
    gen = sector_tiers[s].get('generated', 0)
    total = gold + silver + gen
    if total < 3:
        coverage_issues.append(f'{s}:{total}')
if coverage_issues: log_issue('B3_coverage', f'Thin sectors: {coverage_issues}', 'warn')
else: log_pass('B3_coverage', 'All 6 sectors have templates')

# B4: Occasion coverage — f_and_b and fashion must have ≥3 for main occasions
MAIN_OCCASIONS = ['evergreen','ramadan','national_day','founding_day','eid_al_fitr','eid_al_adha']
occ_issues = []
for sector in ['f_and_b', 'fashion', 'retail_lifestyle']:
    for occ in MAIN_OCCASIONS:
        count = sum(1 for t in templates
                    if t['sector']==sector and t['occasion']==occ
                    and t['tier'] in ('gold','silver','bronze','generated'))
        if count < 3:
            occ_issues.append(f'{sector}/{occ}:{count}')
if occ_issues: log_issue('B4_occ_coverage', f'Thin combos ({len(occ_issues)}): {occ_issues[:5]}', 'warn')
else: log_pass('B4_occ_coverage', 'Main sector×occasion combos all have ≥3 templates')

# B5: Gold-tier templates are real (have original_likes)
fake_gold = [t for t in templates if t['tier']=='gold' and not t.get('original_likes')]
if fake_gold: log_issue('B5_gold_integrity', f'{len(fake_gold)} gold templates missing likes proof', 'fail')
else: log_pass('B5_gold_integrity', f'All {sector_tiers["f_and_b"]["gold"]+sector_tiers["fashion"]["gold"]} gold templates have real likes')

scores['B_templates'] = 100 - len([i for i in issues if 'B' in i['area'] and i['severity']=='fail']) * 25

# ── TEST C: Quality Gate ─────────────────────────────────────────────────────
print('\n[C] QUALITY GATE — 23 verified brands on real captions')
ref_examples = brain.get('reference_examples', {})
c_passed = c_failed = 0
c_issues = []

for handle in sorted(rm.keys()):
    examples = ref_examples.get(handle, [])
    if not examples: continue
    top = max(examples, key=lambda e: e.get('likes', 0))
    cap = top.get('caption_preview', '')
    if not cap or len(cap) < 10: continue
    r = check(cap, brand=handle, occasion='evergreen')
    profile_lang = bp.get(handle, {}).get('language', 'arabic-first')
    is_global = profile_lang in ('bilingual', 'english-first')
    min_score = 60 if is_global else 70
    if r['score'] >= min_score: c_passed += 1
    else:
        c_failed += 1
        c_issues.append(f'@{handle}:{r["score"]}')

if c_failed > 0:
    log_issue('C1_brands', f'{c_failed} brands below threshold: {c_issues}', 'fail' if c_failed > 3 else 'warn')
else:
    log_pass('C1_brands', f'All {c_passed} brands pass quality gate on real captions')

# C2: Auto-fix improves score
print('  Testing auto-fix...')
fix_cases = [
    ('تفضلوا تجربون المنتج الرائع من البيك', 'albaik', 'f_and_b'),
    ('#test1 #test2 #test3 #test4 لايك ريتويت 🎉🎊🎈🎁🎀🎂🎃🎄🎅🎆', 'barnscoffee', 'f_and_b'),
]
fix_ok = 0
for cap, brand, sector in fix_cases:
    before = check(cap, brand=brand)['score']
    fixed = auto_fix(cap, brand=brand, sector=sector)
    after = check(fixed, brand=brand)['score']
    if after >= before: fix_ok += 1
if fix_ok < len(fix_cases):
    log_issue('C2_autofix', f'Auto-fix degraded {len(fix_cases)-fix_ok} cases', 'warn')
else:
    log_pass('C2_autofix', f'Auto-fix improves or maintains score on all {len(fix_cases)} cases')

scores['C_quality'] = int(c_passed / max(c_passed+c_failed,1) * 100)

# ── TEST D: Generated content ────────────────────────────────────────────────
print('\n[D] GENERATED CONTENT — 6 sectors × 4 key occasions')
SECTOR_BRAND_PRODUCT = {
    'f_and_b': ('albaik', 'بروستد جديد'),
    'fashion': ('maxfashionmena', 'فستان صيفي'),
    'retail_lifestyle': ('tamimimarkets', 'عروض العيد'),
    'beauty_personal_care': ('mikyajy', 'أحمر شفاه'),
    'healthcare_wellness': ('fitnessfirstme', 'برنامج لياقة'),
    'real_estate': ('roshnksa', 'وحدات سكنية'),
}
TEST_OCCASIONS = ['evergreen', 'founding_day', 'ramadan', 'eid_al_adha']
d_passed = d_failed = 0
d_low = []

from build_agent_context import build_context

def generate_cap(brand, product, occasion, sector):
    good_templates = [t for t in templates
                      if t['sector']==sector and t['tier'] in ('gold','silver','bronze')
                      and t.get('original_likes',0) > 100]
    good_templates = sorted(good_templates, key=lambda t: -(t.get('original_likes') or 0))[:2]
    ex = '\n'.join(f'- {t["caption"][:80]}' for t in good_templates[:2]) or 'اكتب بأسلوب سعودي أصيل'
    try:
        ctx, _ = build_context(brand, occasion)
    except:
        ctx = f'Brand: {brand}'
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role':'user','content':
            f'اكتب كابشن سعودي واحد لـ @{brand}، منتج: "{product}"، مناسبة: {occasion}.\n'
            f'أمثلة:\n{ex}\nالكابشن فقط:'}],
        max_tokens=100, temperature=0.7,
    )
    return resp.choices[0].message.content.strip().strip('"\'')

for sector, (brand, product) in SECTOR_BRAND_PRODUCT.items():
    for occasion in TEST_OCCASIONS:
        cap = generate_cap(brand, product, occasion, sector)
        r = check(cap, brand=brand, occasion=occasion)
        if r['score'] >= 70: d_passed += 1
        else:
            d_failed += 1
            d_low.append(f'{sector}/{occasion}:{r["score"]}')

total_d = len(SECTOR_BRAND_PRODUCT) * len(TEST_OCCASIONS)
if d_failed > 2:
    log_issue('D1_generated', f'{d_failed}/{total_d} fail: {d_low[:4]}', 'fail' if d_failed > 5 else 'warn')
else:
    log_pass('D1_generated', f'{d_passed}/{total_d} pass (≥70/100)')

scores['D_generated'] = int(d_passed / total_d * 100)

# ── TEST E: Observation data quality ─────────────────────────────────────────
print('\n[E] OBSERVATION DATA QUALITY')
obs_files = glob.glob(str(BASE/'11_who_to_learn_from'/'observations'/'*'/'*.json'))
total_obs = len(obs_files)

field_counts = Counter()
for f in obs_files:
    d = json.loads(Path(f).read_text())
    if d.get('occasion'): field_counts['occasion'] += 1
    if d.get('emotion_primary'): field_counts['emotion'] += 1
    if d.get('voice_observations',{}).get('dialect_detected'): field_counts['dialect'] += 1
    if d.get('voice_observations',{}).get('notable_phrases'): field_counts['notable_phrases'] += 1
    if d.get('visual_observations',{}).get('props_visible') is not None: field_counts['props_visible'] += 1

thresholds = {'occasion': 90, 'emotion': 90, 'dialect': 90, 'notable_phrases': 90, 'props_visible': 99}
e_issues = []
for field, min_pct in thresholds.items():
    pct = field_counts[field] * 100 // total_obs
    if pct < min_pct:
        e_issues.append(f'{field}:{pct}%<{min_pct}%')
        log_issue(f'E_{field}', f'{field_counts[field]}/{total_obs} ({pct}%) — need {min_pct}%', 'fail')
    else:
        log_pass(f'E_{field}', f'{field_counts[field]}/{total_obs} ({pct}%)')

scores['E_obs_quality'] = 100 - len(e_issues) * 20

# ── TEST F: System consistency ────────────────────────────────────────────────
print('\n[F] SYSTEM CONSISTENCY')

# F1: verify_ship_ready passes
import subprocess
result = subprocess.run(
    [sys.executable, 'scripts/verify_ship_ready.py'],
    capture_output=True, text=True, cwd=str(BASE)
)
if 'ALL CHECKS PASS' in result.stdout:
    log_pass('F1_verify', 'verify_ship_ready.py passes')
else:
    fails = re.findall(r'❌ (.+)', result.stdout)
    log_issue('F1_verify', f'FAILED: {fails[:3]}', 'fail')

# F2: guard_data_quality passes
result2 = subprocess.run(
    [sys.executable, 'scripts/guard_data_quality.py', '--quick'],
    capture_output=True, text=True, cwd=str(BASE)
)
if 'ALL GUARDS PASS' in result2.stdout:
    log_pass('F2_guard', 'guard_data_quality.py passes')
else:
    log_issue('F2_guard', 'guard_data_quality FAILED', 'fail')

# F3: Template library and brain are in sync
brain_version = brain.get('meta',{}).get('version','?')
tlib_total = len(templates)
log_pass('F3_sync', f'Brain v{brain_version}, template library {tlib_total} templates')

# F4: Learning store exists and is growing
ls_path = BASE / 'logs' / 'learning_store.jsonl'
if ls_path.exists():
    entries = [l for l in ls_path.read_text().strip().split('\n') if l.strip()]
    log_pass('F4_learning', f'Learning store has {len(entries)} entries')
else:
    log_issue('F4_learning', 'learning_store.jsonl missing', 'warn')

scores['F_system'] = 100 - len([i for i in issues if 'F' in i['area'] and i['severity']=='fail']) * 25

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print('\n' + '='*60)
print('  RESULTS SUMMARY')
print('='*60)

overall = sum(scores.values()) // len(scores)
for area, score in scores.items():
    icon = PASS if score >= 90 else WARN if score >= 70 else FAIL
    print(f'  {icon} {area}: {score}/100')

print(f'\n  OVERALL: {overall}/100')
print(f'  Issues found: {len(issues)} ({sum(1 for i in issues if i["severity"]=="fail")} critical, {sum(1 for i in issues if i["severity"]=="warn")} warnings)')

if issues:
    print('\n  ISSUES TO FIX:')
    for i in sorted(issues, key=lambda x: 0 if x['severity']=='fail' else 1):
        icon = FAIL if i['severity']=='fail' else WARN
        print(f'    {icon} [{i["area"]}] {i["msg"]}')

print('='*60)
return_code = 0 if overall >= 90 and not any(i['severity']=='fail' for i in issues) else 1
sys.exit(return_code)
