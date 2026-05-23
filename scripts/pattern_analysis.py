#!/usr/bin/env python3
"""
OGZ Knowledge — Pattern Analysis Report
Analyzes all observations to produce the Saudi F&B Content Playbook.
Output: logs/pattern_analysis_report.md
"""
import json, pathlib
from collections import Counter, defaultdict
from datetime import datetime

REPO    = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')
OBS_DIR = REPO / '11_who_to_learn_from' / 'observations'
OUT     = REPO / 'logs' / 'pattern_analysis_report.md'

# ── Load all observations ──────────────────────────────────────────────────────
all_obs = []
for sector_dir in OBS_DIR.iterdir():
    if not sector_dir.is_dir(): continue
    for f in sector_dir.glob('*.json'):
        try:
            d = json.loads(f.read_text())
            d['_sector_dir'] = sector_dir.name
            all_obs.append(d)
        except Exception as e:
            print(f"SKIP {f.name}: {e}")

print(f"Loaded {len(all_obs)} observations")

# ── Account handle map ─────────────────────────────────────────────────────────
# Map norm → real handle (from account files)
norm_to_handle = {}
norm_to_tier   = {}
for sector_dir in (REPO / '11_who_to_learn_from' / 'accounts').iterdir():
    if not sector_dir.is_dir(): continue
    for f in sector_dir.glob('*.json'):
        try:
            d = json.loads(f.read_text())
            norm  = d.get('account_handle_normalized', '')
            handle = d.get('account_handle_internal', norm)
            tier   = d.get('tier', 1)
            # infer tier 4 from sub_sector
            if 'International Fast Food' in d.get('sub_sector', ''):
                tier = 4
            norm_to_handle[norm] = f"@{handle}"
            norm_to_tier[norm]   = tier
        except: pass

def tier_of(obs):
    norm = obs.get('account_handle_normalized', '')
    return norm_to_tier.get(norm, 1)

def handle_of(obs):
    norm = obs.get('account_handle_normalized', '')
    return norm_to_handle.get(norm, norm)

# Split by tier
tier1_obs = [o for o in all_obs if tier_of(o) == 1]
tier4_obs = [o for o in all_obs if tier_of(o) == 4]

# ── Pattern frequency analysis ─────────────────────────────────────────────────
def count_patterns(obs_list):
    c = Counter()
    for obs in obs_list:
        for pm in obs.get('pattern_matches', []):
            slug = pm.get('pattern_slug', '')
            if slug:
                c[slug] += 1
    return c

def count_patterns_with_confidence(obs_list):
    by_conf = defaultdict(Counter)
    for obs in obs_list:
        for pm in obs.get('pattern_matches', []):
            slug = pm.get('pattern_slug', '')
            conf = pm.get('confidence', 'moderate')
            if slug:
                by_conf[slug][conf] += 1
    return by_conf

all_pattern_counts  = count_patterns(all_obs)
t1_pattern_counts   = count_patterns(tier1_obs)
t4_pattern_counts   = count_patterns(tier4_obs)
conf_breakdown      = count_patterns_with_confidence(tier1_obs)

# ── Engagement potential by pattern ──────────────────────────────────────────
ENG_SCORE = {'high': 2, 'medium': 1, 'low': 0}

def pattern_engagement(obs_list):
    """Return avg engagement score per pattern slug."""
    pat_eng = defaultdict(list)
    for obs in obs_list:
        eng = obs.get('quality_assessment', {}).get('engagement_potential', 'medium')
        score = ENG_SCORE.get(eng, 1)
        for pm in obs.get('pattern_matches', []):
            slug = pm.get('pattern_slug', '')
            if slug:
                pat_eng[slug].append(score)
    return {s: sum(v)/len(v) for s, v in pat_eng.items()}

t1_pat_eng = pattern_engagement(tier1_obs)

# ── Pattern by account ────────────────────────────────────────────────────────
acct_patterns = defaultdict(Counter)
for obs in tier1_obs:
    h = handle_of(obs)
    for pm in obs.get('pattern_matches', []):
        slug = pm.get('pattern_slug', '')
        if slug:
            acct_patterns[h][slug] += 1

# ── Compliance breakdown ───────────────────────────────────────────────────────
compliance_counts = Counter(
    o.get('compliance_check', {}).get('overall_compliance', 'unknown')
    for o in all_obs
)

# ── Production quality ─────────────────────────────────────────────────────────
quality_counts = Counter(
    o.get('quality_assessment', {}).get('production_quality', 'unknown')
    for o in all_obs
)

# ── Engagement potential distribution ─────────────────────────────────────────
engagement_counts = Counter(
    o.get('quality_assessment', {}).get('engagement_potential', 'unknown')
    for o in all_obs
)
t1_eng_counts = Counter(
    o.get('quality_assessment', {}).get('engagement_potential', 'unknown')
    for o in tier1_obs
)

# ── Occasion relevance ─────────────────────────────────────────────────────────
occasion_counts = Counter()
for obs in all_obs:
    occ = obs.get('cultural_notes', {}).get('occasion_relevance')
    if occ:
        occasion_counts[occ] += 1

# ── Heritage vs modern ─────────────────────────────────────────────────────────
hvm_counts = Counter(
    o.get('cultural_notes', {}).get('heritage_vs_modern', 'unknown')
    for o in all_obs
)

# ── Hospitality cues ──────────────────────────────────────────────────────────
hosp_all = Counter()
for obs in all_obs:
    for cue in obs.get('cultural_notes', {}).get('hospitality_cues', []):
        hosp_all[cue] += 1

# ── Soft flags ─────────────────────────────────────────────────────────────────
soft_flag_types = Counter()
for obs in all_obs:
    for sf in obs.get('compliance_check', {}).get('soft_flags', []):
        ft = sf.get('flag_type', '') if isinstance(sf, dict) else str(sf)
        if ft:
            soft_flag_types[ft] += 1

# ── Per-account obs count ─────────────────────────────────────────────────────
acct_obs_count = Counter()
for obs in all_obs:
    acct_obs_count[handle_of(obs)] += 1

# ── Sector breakdown ──────────────────────────────────────────────────────────
sector_counts = Counter(o.get('sector','') for o in all_obs)

# ── Top patterns for "high engagement" posts ──────────────────────────────────
high_eng_obs = [o for o in tier1_obs
                if o.get('quality_assessment',{}).get('engagement_potential') == 'high']
high_eng_patterns = count_patterns(high_eng_obs)

low_eng_obs = [o for o in tier1_obs
               if o.get('quality_assessment',{}).get('engagement_potential') == 'low']
low_eng_patterns = count_patterns(low_eng_obs)

# ── Build report ──────────────────────────────────────────────────────────────
lines = []
def h1(t): lines.append(f"\n# {t}\n")
def h2(t): lines.append(f"\n## {t}\n")
def h3(t): lines.append(f"\n### {t}\n")
def p(t=''):  lines.append(t)
def hr(): lines.append("\n---\n")

h1("OGZ Knowledge — Saudi F&B Content Playbook")
p(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Corpus: {len(all_obs)} observations across {len(acct_obs_count)} accounts*")

hr()

h2("1. Corpus Overview")
p(f"| Metric | Value |")
p(f"|--------|-------|")
p(f"| Total observations | {len(all_obs)} |")
p(f"| Tier 1 (benchmark) | {len(tier1_obs)} |")
p(f"| Tier 4 (anti-pattern) | {len(tier4_obs)} |")
p(f"| Accounts | {len(acct_obs_count)} |")
for sector, cnt in sorted(sector_counts.items()):
    p(f"| Sector: {sector} | {cnt} obs |")
p()

p("**Account breakdown:**")
p()
p("| Account | Obs | Tier |")
p("|---------|-----|------|")
for h, cnt in sorted(acct_obs_count.items(), key=lambda x: (-tier_of({'account_handle_normalized': [k for k,v in norm_to_handle.items() if v==x[0]][0] if any(v==x[0] for v in norm_to_handle.values()) else ''}), -x[1])):
    norm_match = [k for k,v in norm_to_handle.items() if v == h]
    t = norm_to_tier.get(norm_match[0], 1) if norm_match else 1
    tier_label = "T1" if t == 1 else "T4"
    p(f"| {h} | {cnt} | {tier_label} |")

hr()

h2("2. Top 20 Patterns — Tier 1 Benchmark Accounts")
p("*Sorted by frequency across 375 Tier 1 observations*")
p()
p("| Rank | Pattern | Count | % of obs | Avg Engagement | High Eng Posts |")
p("|------|---------|-------|----------|---------------|----------------|")
for i, (slug, cnt) in enumerate(t1_pattern_counts.most_common(20), 1):
    pct   = cnt / len(tier1_obs) * 100
    eng   = t1_pat_eng.get(slug, 1.0)
    eng_s = "🔴 high" if eng >= 1.5 else ("🟡 med" if eng >= 0.8 else "⚪ low")
    h_cnt = high_eng_patterns.get(slug, 0)
    p(f"| {i} | `{slug}` | {cnt} | {pct:.0f}% | {eng_s} ({eng:.2f}) | {h_cnt} |")

hr()

h2("3. Pattern × Engagement Matrix")
p("*Patterns with highest correlation to high-engagement posts (Tier 1 only)*")
p()

# Sort by avg engagement score, min 3 appearances
eng_ranked = [(s, e, t1_pattern_counts[s])
              for s, e in t1_pat_eng.items()
              if t1_pattern_counts[s] >= 3]
eng_ranked.sort(key=lambda x: -x[1])

p("| Pattern | Avg Eng Score | Count | Signal |")
p("|---------|--------------|-------|--------|")
for slug, eng, cnt in eng_ranked[:15]:
    h_c = high_eng_patterns.get(slug, 0)
    l_c = low_eng_patterns.get(slug, 0)
    signal = "✅ USE" if eng >= 1.4 else ("⚠️ MIXED" if eng >= 0.9 else "❌ AVOID")
    p(f"| `{slug}` | {eng:.2f} | {cnt} | {signal} ({h_c}H/{l_c}L) |")

hr()

h2("4. Tier 1 vs Tier 4 — Pattern Contrast")
p("*Patterns that separate authentic Saudi brands from global QSR chains*")
p()

# Patterns strong in T1, weak/absent in T4
t1_slugs = set(t1_pattern_counts.keys())
t4_slugs = set(t4_pattern_counts.keys())

only_t1 = t1_slugs - t4_slugs
shared   = t1_slugs & t4_slugs
only_t4  = t4_slugs - t1_slugs

p("**Tier 1 ONLY patterns (never seen in Tier 4):**")
p()
p("| Pattern | T1 count |")
p("|---------|----------|")
for slug in sorted(only_t1, key=lambda s: -t1_pattern_counts[s]):
    p(f"| `{slug}` | {t1_pattern_counts[slug]} |")

p()
p("**Shared patterns (both tiers — but check engagement difference):**")
p()
p("| Pattern | T1 count | T4 count | T1 eng |")
p("|---------|----------|----------|--------|")
for slug in sorted(shared, key=lambda s: -t1_pattern_counts[s]):
    eng = t1_pat_eng.get(slug, 1.0)
    p(f"| `{slug}` | {t1_pattern_counts[slug]} | {t4_pattern_counts[slug]} | {eng:.2f} |")

p()
p("**Tier 4 ONLY patterns (anti-pattern signals):**")
p()
for slug in sorted(only_t4, key=lambda s: -t4_pattern_counts[s]):
    p(f"- `{slug}` ({t4_pattern_counts[slug]}x)")

hr()

h2("5. Pattern by Account — Signature Patterns per Brand")
p()
for handle, pat_counter in sorted(acct_patterns.items(), key=lambda x: -sum(x[1].values())):
    total = sum(pat_counter.values())
    top3  = ", ".join(f"`{s}`" for s, _ in pat_counter.most_common(3))
    p(f"**{handle}** ({total} pattern hits) — top: {top3}")
p()

hr()

h2("6. Occasion Calendar — When Saudi Brands Post Culturally")
p()
p("| Occasion | Observations |")
p("|----------|-------------|")
for occ, cnt in occasion_counts.most_common():
    p(f"| {occ} | {cnt} |")
p()
p(f"*{sum(1 for o in all_obs if o.get('cultural_notes',{}).get('occasion_relevance'))} of {len(all_obs)} posts tied to a specific cultural occasion ({sum(1 for o in all_obs if o.get('cultural_notes',{}).get('occasion_relevance'))/len(all_obs)*100:.0f}%)*")

hr()

h2("7. Heritage vs Modern Positioning")
p()
p("| Positioning | Count | % |")
p("|-------------|-------|---|")
for hv, cnt in hvm_counts.most_common():
    p(f"| {hv} | {cnt} | {cnt/len(all_obs)*100:.0f}% |")

hr()

h2("8. Hospitality Cues — What Signals Saudi Warmth")
p("*Top cultural warmth signals in Tier 1 captions and visuals*")
p()
p("| Cue | Frequency |")
p("|-----|-----------|")
for cue, cnt in hosp_all.most_common(20):
    p(f"| {cue} | {cnt} |")

hr()

h2("9. Production Quality & Compliance")
p()
p("**Production quality across all accounts:**")
p()
p("| Quality | Count | % |")
p("|---------|-------|---|")
for q, cnt in quality_counts.most_common():
    p(f"| {q} | {cnt} | {cnt/len(all_obs)*100:.0f}% |")

p()
p("**Compliance distribution:**")
p()
p("| Status | Count | % |")
p("|--------|-------|---|")
for c, cnt in compliance_counts.most_common():
    p(f"| {c} | {cnt} | {cnt/len(all_obs)*100:.0f}% |")

p()
p("**Engagement potential (Tier 1 only):**")
p()
p("| Potential | Count | % |")
p("|-----------|-------|---|")
for e, cnt in t1_eng_counts.most_common():
    p(f"| {e} | {cnt} | {cnt/len(tier1_obs)*100:.0f}% |")

hr()

h2("10. High-Engagement Post Patterns — What Works")
p("*Patterns appearing in posts scored 'high' engagement potential (Tier 1 only)*")
p()
p(f"Total high-engagement posts: {len(high_eng_obs)} of {len(tier1_obs)} Tier 1 ({len(high_eng_obs)/len(tier1_obs)*100:.0f}%)")
p()
p("| Pattern | High-eng posts | % of high-eng |")
p("|---------|---------------|---------------|")
for slug, cnt in high_eng_patterns.most_common(15):
    pct = cnt / len(high_eng_obs) * 100
    p(f"| `{slug}` | {cnt} | {pct:.0f}% |")

hr()

h2("11. Soft Flags — What Trips Saudi Cultural Compliance")
p()
p(f"Soft-flagged observations: {compliance_counts.get('soft_flagged', 0)}")
p()
p("| Flag type | Count |")
p("|-----------|-------|")
for ft, cnt in soft_flag_types.most_common(20):
    p(f"| {ft} | {cnt} |")

hr()

h2("12. The Saudi F&B Content Playbook — Executive Summary")
p()

# Top 10 by engagement
top10 = [(s, t1_pat_eng.get(s, 1.0), t1_pattern_counts[s])
         for s in t1_pattern_counts
         if t1_pattern_counts[s] >= 5]
top10.sort(key=lambda x: -(x[1] * 0.6 + x[2]/len(tier1_obs) * 0.4))

p("### ✅ ALWAYS DO — Core Saudi F&B Patterns")
p()
p("These patterns appear frequently AND correlate with high engagement:")
p()
for slug, eng, cnt in top10[:8]:
    freq_pct = cnt/len(tier1_obs)*100
    p(f"- **`{slug}`** — appears in {cnt} obs ({freq_pct:.0f}%), avg eng {eng:.2f}")

p()
p("### ⚡ HIGH-IMPACT — Low-frequency but high-reward patterns")
p()
# Patterns with high engagement but lower frequency (gems)
gems = [(s, t1_pat_eng.get(s, 1.0), t1_pattern_counts[s])
        for s in t1_pattern_counts
        if t1_pattern_counts[s] >= 2 and t1_pat_eng.get(s, 1.0) >= 1.6
        and t1_pattern_counts[s] < 20]
gems.sort(key=lambda x: -x[1])
for slug, eng, cnt in gems[:6]:
    p(f"- **`{slug}`** — {cnt} obs, engagement {eng:.2f}")

p()
p("### ❌ AVOID — Tier 4 Anti-patterns")
p()
t4_only_sorted = sorted(only_t4, key=lambda s: -t4_pattern_counts[s])
for slug in t4_only_sorted[:5]:
    p(f"- `{slug}` — only seen in global chains, never in authentic Saudi brands")
p()

# Patterns in T4 that T1 uses differently
p("### ⚠️ SHARED BUT MISUSED — Patterns both tiers use, but differently")
p()
for slug in sorted(shared, key=lambda s: -(t1_pattern_counts[s] - t4_pattern_counts.get(s, 0))):
    t4_c = t4_pattern_counts.get(slug, 0)
    t1_c = t1_pattern_counts[slug]
    if t1_c > 5 and t4_c > 0:
        p(f"- **`{slug}`** — T1 uses it {t1_c}x with cultural warmth; T4 uses it {t4_c}x as pure commerce")

p()
p("### 🗓️ Occasion Calendar Rules")
p()
p("Saudi brands that win culturally always tie content to occasion. Top occasions in corpus:")
p()
for occ, cnt in occasion_counts.most_common(8):
    p(f"- **{occ}** — {cnt} posts")

p()
p("### 🎙️ Voice Rules — What Saudi Tone Sounds Like")
p()
p("- **Dialect**: Saudi colloquial (Najdi/Gulf blend) dominates in authentic accounts")
p("- **Register**: Warm-casual, never formal-corporate")
p("- **Hospitality cues**: قهوة، كرم، تفضل، عائلة — signal authentic Saudi soul")
p("- **CTA style**: Invitation not command — `تفضلوا`, `انتظرونا`, not `اشترِ الآن`")

p()
p("---")
p()
p(f"*OGZ Knowledge Base — Pattern Analysis v1.0 | {datetime.now().strftime('%Y-%m-%d')}*")

# Write output
OUT.parent.mkdir(parents=True, exist_ok=True)
report_text = "\n".join(lines)
OUT.write_text(report_text, encoding='utf-8')
print(f"\nReport written: {OUT}")
print(f"Size: {len(report_text):,} chars / {len(lines)} lines")
