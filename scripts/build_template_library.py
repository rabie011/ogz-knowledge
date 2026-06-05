#!/usr/bin/env python3
"""
build_template_library.py — Build scored template library from real observations.

Extracts Arabic captions with real likes from all 3,816 obs.
Assigns tier: gold(1000+), silver(100-999), bronze(1-99).
Merges 40 generated templates from brain.
Saves to: 11_who_to_learn_from/template_library.json

Run: python3 scripts/build_template_library.py
"""
import json, glob, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
BRAIN_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
OUTPUT_PATH = BASE / "11_who_to_learn_from" / "template_library.json"

def tier_from_likes(likes):
    if likes >= 1000: return "gold"
    if likes >= 100:  return "silver"
    if likes > 0:     return "bronze"
    return None

def is_arabic(text):
    return bool(re.search(r'[؀-ۿ]', text or ''))

def clean_caption(cap, brand_name=None, product_names=None):
    """Replace brand-specific words with placeholders."""
    text = cap.strip()
    # Don't modify too aggressively — keep as structural template
    return text

def main():
    print("Loading brain...")
    brain = json.loads(BRAIN_PATH.read_text())
    brand_profiles = brain.get('brand_profiles', {})
    real_metrics = brain.get('real_metrics', {})

    templates = []
    sector_occasion_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    print("Scanning observations...")
    obs_files = glob.glob(str(BASE / "11_who_to_learn_from" / "observations" / "*" / "*.json"))
    print(f"  Total obs: {len(obs_files)}")

    processed = 0
    for fpath in obs_files:
        d = json.loads(Path(fpath).read_text())
        sector = d.get('sector', '')
        likes = d.get('content_ref', {}).get('likes_count', 0)
        cap = d.get('voice_observations', {}).get('caption_text', '') or ''
        handle = d.get('account_handle_normalized', '').lstrip('@')
        occasion = d.get('occasion', '') or d.get('cultural_notes', {}).get('occasion_relevance', '') or 'evergreen'
        content_type = d.get('content_ref', {}).get('content_type', 'image')
        tone = d.get('voice_observations', {}).get('tone', '')
        source_url = d.get('content_ref', {}).get('source_url', '')

        # Only include: has Arabic caption + real likes
        if not is_arabic(cap) or likes <= 0:
            continue

        tier = tier_from_likes(likes)
        if not tier:
            continue

        # Skip very short captions (< 15 chars) — not useful as templates
        if len(cap.strip()) < 15:
            continue

        templates.append({
            'caption': cap.strip(),
            'tier': tier,
            'sector': sector,
            'occasion': occasion if occasion not in ('null', 'none', '', None) else 'evergreen',
            'content_type': content_type,
            'tone': tone,
            'brand_source': handle,
            'original_likes': likes,
            'original_url': source_url,
            'source': 'real_instagram',
        })

        sector_occasion_counts[sector][occasion][tier] += 1
        processed += 1

    print(f"  Extracted {processed} real templates (Arabic + likes)")

    # Add generated templates from brain
    saudi_templates = brain.get('saudi_templates', {})
    generated_count = 0
    for sector, data in saudi_templates.items():
        templates_text = data.get('templates', '')
        if not isinstance(templates_text, str):
            continue
        # Parse numbered list
        lines = [l.strip() for l in templates_text.split('\n') if l.strip()]
        for line in lines:
            # Match: "1. **Title** \n"caption"" or just the quoted caption
            # Extract Arabic text
            arabic_matches = re.findall(r'"([^"]*[؀-ۿ][^"]*)"', line)
            if not arabic_matches:
                arabic_matches = re.findall(r'([؀-ۿ][^"\n]{10,})', line)
            for cap_text in arabic_matches:
                if len(cap_text.strip()) < 10:
                    continue
                templates.append({
                    'caption': cap_text.strip(),
                    'tier': 'generated',
                    'sector': sector,
                    'occasion': 'evergreen',
                    'content_type': 'image',
                    'tone': 'informative',
                    'brand_source': None,
                    'original_likes': None,
                    'original_url': None,
                    'source': 'generated_saudi',
                })
                sector_occasion_counts[sector]['evergreen']['generated'] += 1
                generated_count += 1

    print(f"  Added {generated_count} generated templates")

    # Sort: gold first, then silver, bronze, generated
    tier_order = {'gold': 0, 'silver': 1, 'bronze': 2, 'generated': 3}
    templates.sort(key=lambda t: (tier_order.get(t['tier'], 99), -(t['original_likes'] or 0)))

    # Save
    output = {
        'meta': {
            'total': len(templates),
            'real': processed,
            'generated': generated_count,
            'built_from': f'{len(obs_files)} observations',
        },
        'templates': templates,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(templates)} templates to template_library.json")

    # Print coverage matrix
    print("\n=== COVERAGE MATRIX (sector × tier) ===")
    sectors = ['f_and_b', 'fashion', 'retail_lifestyle', 'beauty_personal_care', 'healthcare_wellness', 'real_estate']
    print(f"{'Sector':<25} {'Gold':>6} {'Silver':>8} {'Bronze':>8} {'Generated':>10}")
    print('-' * 60)
    for s in sectors:
        occ_data = sector_occasion_counts[s]
        g = sum(v.get('gold', 0) for v in occ_data.values())
        sv = sum(v.get('silver', 0) for v in occ_data.values())
        br = sum(v.get('bronze', 0) for v in occ_data.values())
        ge = sum(v.get('generated', 0) for v in occ_data.values())
        status = "✅" if g >= 10 else "⚡" if g >= 3 else "⚠️" if g >= 1 else "❌"
        print(f"{s:<25} {g:>6} {sv:>8} {br:>8} {ge:>10} {status}")

    print("\n=== TOP OCCASIONS COVERED ===")
    all_occasions = defaultdict(lambda: defaultdict(int))
    for t in templates:
        all_occasions[t['occasion']][t['tier']] += 1
    for occ, tiers in sorted(all_occasions.items(), key=lambda x: -(x[1].get('gold',0)+x[1].get('silver',0))):
        g = tiers.get('gold', 0)
        sv = tiers.get('silver', 0)
        if g + sv > 0:
            print(f"  {occ:<25} gold={g:>4}  silver={sv:>4}")

if __name__ == '__main__':
    main()
