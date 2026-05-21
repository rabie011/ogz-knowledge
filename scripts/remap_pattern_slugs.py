#!/usr/bin/env python3
"""
Remap free-form pattern slugs in all observations to match the 40-pattern library.
Only remaps clear duplicates — genuinely new patterns are left as-is.
"""
import json, pathlib
from collections import Counter

REPO = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')
OBS_DIR = REPO / '11_who_to_learn_from' / 'observations'

# Definite remaps: same concept, different name
# Right side must be a valid library slug
REMAP = {
    # product_hero variants
    'product_hero_close_up':            'product_hero',
    'product_hero_video':               'product_hero',
    'product_hero_macro':               'product_hero',

    # UGC / customer voice
    'user_generated_amplification':     'customer_voice_ugc',
    'ugc_testimonial':                  'customer_voice_ugc',
    'influencer_review':                'customer_voice_ugc',

    # Macro / texture close-ups
    'steam_and_texture_macro':          'close_up_macro_texture',
    'sensory_close_up':                 'close_up_macro_texture',

    # Architectural / interior framing
    'architectural_framing':            'interior_architectural_framing',

    # Behind the craft
    'behind_the_scenes_production':     'behind_the_craft',
    'behind_the_scenes':                'behind_the_craft',
    'behind_scenes_reel_teaser':        'behind_the_craft',

    # Seasonal / launch / collection drops
    'product_launch_reveal':            'seasonal_collection_drop',
    'menu_expansion_announcement':      'seasonal_collection_drop',
    'collab_campaign_reveal':           'seasonal_collection_drop',
    'seasonal_campaign_graphic':        'seasonal_collection_drop',
    'campaign_teaser':                  'seasonal_collection_drop',

    # Bilingual / parallel copy
    'bilingual_brand_voice':            'parallel_original_bilingual',

    # Educational
    'tutorial_how_to':                  'educational_explainer',
    'educational_ingredient_spotlight': 'educational_explainer',
    'transparency_trust_content':       'educational_explainer',

    # National day / Saudi pride
    'national_day_93_94':               'national_day_pride',
    'expo_2030_pride':                  'national_day_pride',
    'vision_2030_alignment':            'national_day_modernity_heritage',

    # Eid
    'eid_occasion_content':             'eid_family_gathering',
    'whole_lamb_visual':                'eid_al_adha_sacrifice_generosity',
    'saudi_feast_photography':          'eid_al_adha_sacrifice_generosity',

    # Invitation / CTA voice
    'call_to_action_soft_invite':       'invitation_to_witness',

    # Arabic warmth / Najdi voice
    'arabic_hospitality_cue':           'warm_najdi_invitational',
    'poetic_arabic_copy':               'classical_arabic_warmth',
    'food_emotion_connection':          'classical_arabic_warmth',
    'specific_emotional_state':         'classical_arabic_warmth',

    # Visual compositions
    'duo_product_comparison':           'split_screen_before_after',
    'feast_spread_overhead':            'overhead_tabletop_spread',
    'saudi_feast_photography':          'overhead_tabletop_spread',

    # Specific dish naming
    'specific_dish_naming':             'specific_dish_naming',   # already correct slug

    # Founding day
    'founding_day':                     'founding_day_heritage',

    # Ramadan
    'ramadan_iftar':                    'ramadan_iftar_warmth',
    'ramadan_content':                  'ramadan_iftar_warmth',

    # Gamified / interactive mechanics
    'gamified_content':                 'invitation_to_witness',
    'personality_food_pairing':         'specific_dish_naming',
    'weekly_series_anchor':             'invitation_to_witness',

    # Nostalgia
    'nostalgia_play':                   'classical_arabic_warmth',
}

# Load defined library slugs for validation
patterns_dir = REPO / '11_who_to_learn_from' / 'patterns'
defined = set(f.stem for f in patterns_dir.rglob('*.json'))

# Verify all remap targets are valid library slugs
for src, tgt in REMAP.items():
    if tgt not in defined:
        print(f'WARNING: remap target "{tgt}" not in library — skipping')

REMAP = {k: v for k, v in REMAP.items() if v in defined}

# Apply remaps
files_updated = 0
slugs_remapped = Counter()

for obs_file in OBS_DIR.rglob('*.json'):
    data = json.loads(obs_file.read_text())
    pm = data.get('pattern_matches', [])
    if not pm:
        continue

    new_pm = []
    changed = False
    seen_slugs = set()  # deduplicate after remap

    for entry in pm:
        if isinstance(entry, dict):
            slug = entry.get('pattern_slug', '')
            new_slug = REMAP.get(slug, slug)
            if new_slug != slug:
                slugs_remapped[f'{slug} → {new_slug}'] += 1
                changed = True
            if new_slug not in seen_slugs:
                new_entry = dict(entry)
                new_entry['pattern_slug'] = new_slug
                new_pm.append(new_entry)
                seen_slugs.add(new_slug)
        elif isinstance(entry, str):
            # Legacy string-style entries — convert to dict format
            new_slug = REMAP.get(entry, entry)
            if new_slug != entry:
                slugs_remapped[f'{entry} → {new_slug}'] += 1
                changed = True
            if new_slug not in seen_slugs:
                new_pm.append({'pattern_slug': new_slug, 'confidence': 'moderate', 'notes': None})
                seen_slugs.add(new_slug)

    if changed:
        data['pattern_matches'] = new_pm
        obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        files_updated += 1

print(f'Files updated: {files_updated}')
print(f'Slug remaps applied: {sum(slugs_remapped.values())}')
print()
print('Remaps performed:')
for remap, cnt in sorted(slugs_remapped.items(), key=lambda x: -x[1]):
    print(f'  {cnt:>4}x  {remap}')
