#!/usr/bin/env python3
"""Write 12 obs each for @aldeebajofficial (retail) and @prettynature.official (beauty)."""
import json, pathlib, time, random, datetime, re

CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
REPO = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')

def make_ulid():
    ts = int(time.time() * 1000)
    ts_part = ''
    t = ts
    for _ in range(10):
        ts_part = CROCKFORD[t % 32] + ts_part
        t //= 32
    rand_part = ''.join(random.choice(CROCKFORD) for _ in range(16))
    time.sleep(0.003)
    return ts_part + rand_part

def obs(account_norm, account_ulid, sector, shortcode, content_type, capture_date,
        composition, lighting, colors, props, setting, chars, overlays,
        lang, dialect, register, tone, cta, hashtags, caption,
        hard_blocks, soft_flags, compliance,
        region, occasion, patterns, hosp_cues,
        prod_quality, brand_consistency, engagement_potential,
        source_handle=''):
    fn_ext = '_thumb.jpg' if content_type in ('video', 'reel') else '.jpg'
    return {
        'observation_ulid': make_ulid(),
        'schema_version': 1,
        'account_handle_normalized': account_norm,
        'account_ulid': account_ulid,
        'sector': sector,
        'content_ref': {
            'filename': shortcode + fn_ext,
            'platform': 'instagram',
            'content_type': content_type,
            'capture_date': capture_date,
            'source_url': f'https://www.instagram.com/p/{shortcode}/',
        },
        'visual_observations': {
            'composition_style': composition,
            'lighting': lighting,
            'color_palette_dominant': colors,
            'props_visible': props,
            'setting': setting,
            'characters_visible': {'count': chars},
            'text_overlays': overlays,
        },
        'voice_observations': {
            'language': lang,
            'dialect_detected': dialect,
            'register': register,
            'tone': tone,
            'notable_phrases': [],
            'call_to_action_present': cta,
        },
        'compliance_check': {
            'hard_blocks_triggered': hard_blocks,
            'soft_flags': soft_flags,
            'overall_compliance': compliance,
        },
        'cultural_notes': {
            'regional_orientation_detected': region,
            'occasion_relevance': occasion,
            'hospitality_cues': hosp_cues,
        },
        'pattern_matches': [{'pattern_slug': p, 'confidence': 'moderate', 'notes': None} for p in patterns],
        'quality_assessment': {
            'production_quality': prod_quality,
            'brand_consistency_with_account': brand_consistency,
            'engagement_potential': engagement_potential,
        },
        'provenance': {
            'source': f'benchmark:@{source_handle}; content:{shortcode}{fn_ext}',
            'date_added': datetime.datetime.utcnow().isoformat() + 'Z',
            'confirmer': 'claude_code_extraction',
            'confidence': 'inferred',
            'scope': f'sector:{sector}',
        },
    }

ALL_OBS = []

# ── @aldeebajofficial (retail) ────────────────────────────────────────────────
# Saudi heritage textiles/abayas brand. English-dominant captions. Small brand (est. 2-5K followers).
# Cairo Collection, modest fashion, product hero shots and video reels.
NORM_D = 'OGZ-RETAIL-Reference-001'
ULID_D = '01KRKHS8RBHMMSCHPYWXGGFKNT'

ALL_OBS += [
obs(NORM_D, ULID_D, 'retail', 'DYj72tQCMy7', 'video', '2026-05-17',
    'model walk product video', 'warm golden studio', ['black', 'white', 'gold'],
    ['flowing abaya with gold trim', 'clean white background'],
    'studio product video', 1,
    [{'language': 'english', 'content_summary': 'Elegant Abaya showcase reel'}],
    'arabic', 'general_saudi', 'casual', 'elegant', True, ['#aldeebajofficial', '#abaya'],
    'Elegant Abaya @aldeebajofficial ✨',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'model_centered_frontal_portrait'], [],
    'semi_professional', 'moderate', 'high', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYcQ8gCsB9s', 'video', '2026-05-15',
    'multi-occasion collection reveal', 'bright editorial', ['black', 'navy', 'ivory', 'beige'],
    ['multiple abaya styles', 'occasion tags'],
    'collection lookbook', 1,
    [{'language': 'english', 'content_summary': 'every occasion deserves a different abaya'}],
    'english', 'general_saudi', 'aspirational', 'confident', True, ['#aldeebajofficial', '#abaya', '#modest'],
    'If you believe every occasion deserves a completely different look',
    [], [], 'clean', 'general_saudi', 'none',
    ['seasonal_collection_drop', 'product_hero'], [],
    'semi_professional', 'moderate', 'high', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYZglTRqj86', 'video', '2026-05-14',
    'lifestyle model motion reel', 'warm natural light', ['black', 'dusty_rose', 'white'],
    ['flowy abaya', 'lifestyle setting outdoor'],
    'lifestyle product shoot', 1,
    [{'language': 'english', 'content_summary': 'Feminine energy modest soul lifestyle reel'}],
    'english', 'general_saudi', 'casual', 'warm', False, ['#aldeebajofficial', '#modestfashion'],
    'Feminine energy, modest soul🌙🫶🏻 Beautiful abaya from @aldeebajofficial',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'warm_golden_hour_hero'], [],
    'semi_professional', 'moderate', 'medium', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYhLjZcIpsz', 'video', '2026-05-18',
    'menswear collection reveal flat lay + model', 'clean bright studio', ['white', 'beige', 'cream'],
    ['traditional Saudi thobe', 'Cairo Collection tag', 'clean studio backdrop'],
    'new arrivals launch reel', 1,
    [{'language': 'english', 'content_summary': 'Cairo Collection – New Arrivals Thobes'}],
    'english', 'general_saudi', 'aspirational', 'proud', True, ['#aldeebajofficial', '#thobe', '#Cairo'],
    'Cairo Collection – New Arrivals Thobes ✨ Inspired by timeless heritage',
    [], [], 'clean', 'general_saudi', 'none',
    ['seasonal_collection_drop', 'product_hero'], [],
    'semi_professional', 'moderate', 'medium', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXpoI0IWa_', 'video', '2026-05-12',
    'product identity manifesto video', 'high contrast minimal', ['black', 'white'],
    ['minimal abaya', 'clean white space'],
    'brand identity video', 0,
    [{'language': 'english', 'content_summary': 'Minimal design. Premium feel. Powerful presence.'}],
    'english', 'general_saudi', 'premium', 'powerful', True, ['#aldeebajofficial'],
    'Minimal design. Premium feel. Powerful presence. Discover the new collection.',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'refusal_framing_positioning'], [],
    'professional', 'moderate', 'medium', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXpkOOoo3a', 'video', '2026-05-12',
    'product hero minimal motion', 'bright studio', ['black', 'white'],
    ['minimal abaya close-up', 'fabric texture detail'],
    'product detail studio', 0,
    [{'language': 'english', 'content_summary': 'Minimal premium presence — second variation'}],
    'english', 'general_saudi', 'premium', 'refined', False, ['#aldeebajofficial'],
    'Minimal design. Premium feel. Powerful presence.',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'close_up_macro_texture'], [],
    'professional', 'moderate', 'medium', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYfEQ_nMhnK', 'video', '2026-05-16',
    'model lifestyle walk contemplative', 'natural outdoor golden', ['beige', 'camel', 'white'],
    ['modest abaya flowing', 'outdoor lifestyle setting'],
    'brand ethos lifestyle reel', 1,
    [{'language': 'english', 'content_summary': 'Modesty never goes out of style'}],
    'english', 'general_saudi', 'casual', 'reflective', False, ['#aldeebajofficial', '#modesty'],
    'Modesty never goes out of style. 🕊️ Loving the flow and fabric of this piece.',
    [], [], 'clean', 'general_saudi', 'none',
    ['warm_golden_hour_hero', 'product_hero'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYkRDOqtQsR', 'video', '2026-05-19',
    'product hero dark dramatic', 'dramatic dark contrast', ['black', 'deep_charcoal'],
    ['all-black abaya', 'dramatic lighting'],
    'drama product shot', 1,
    [{'language': 'english', 'content_summary': 'Prettiest black abaya showcase'}],
    'english', 'general_saudi', 'premium', 'dramatic', True, ['#abaya', '#aldeebajofficial'],
    'Prettiest black abaya 💫✨ Abaya @aldeebajofficial',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXPQ7FILkD', 'video', '2026-05-12',
    'store operations graphic', 'branded flat', ['black', 'white', 'gold'],
    ['store opening times graphic', 'branded frame', 'outlet location text'],
    'operational announcement', 0,
    [{'language': 'bilingual', 'content_summary': 'outlets extended opening hours announcement'}],
    'bilingual', 'general_saudi', 'functional', 'informative', False, ['#aldeebajofficial'],
    'Good news for our customers! ✨ Our outlets will now remain open',
    [], [], 'clean', 'general_saudi', 'none',
    ['invitation_to_witness'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXOtrUIyjJ', 'image', '2026-05-12',
    'operational announcement flat graphic', 'clean branded', ['black', 'white'],
    ['opening hours text block', 'brand logo'],
    'store info graphic', 0,
    [{'language': 'bilingual', 'content_summary': 'outlet extended hours — graphic version'}],
    'bilingual', 'general_saudi', 'functional', 'informative', False, [],
    'Good news for our customers! ✨ Our outlets will now remain open',
    [], [], 'clean', 'general_saudi', 'none',
    ['invitation_to_witness'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXPIn7Iy8w', 'video', '2026-05-12',
    'animated hours graphic', 'bright branded', ['black', 'gold', 'white'],
    ['animated opening hours', 'outlet list'],
    'operational motion graphic', 0,
    [{'language': 'bilingual', 'content_summary': 'animated outlet hours announcement'}],
    'bilingual', 'general_saudi', 'functional', 'informative', False, [],
    'Good news for our customers! ✨ Our outlets will now remain open',
    [], [], 'clean', 'general_saudi', 'none',
    ['invitation_to_witness'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),

obs(NORM_D, ULID_D, 'retail', 'DYXOqxuoG6K', 'image', '2026-05-12',
    'store info static graphic', 'minimal branded', ['black', 'white'],
    ['store location list', 'times table', 'brand mark'],
    'static hours card', 0,
    [{'language': 'bilingual', 'content_summary': 'static opening hours card for all outlets'}],
    'bilingual', 'general_saudi', 'functional', 'neutral', False, [],
    'Good news for our customers! ✨ Our outlets will now remain open',
    [], [], 'clean', 'general_saudi', 'none',
    ['invitation_to_witness'], [],
    'semi_professional', 'moderate', 'low', 'aldeebajofficial'),
]

# ── @prettynature.official (beauty) ──────────────────────────────────────────
# Saudi natural skincare brand. Arabic captions, award-winning products. Small brand (est. 1-3K followers).
# Products: rose mask, nail oil, cherry lip balm, lemon scrub, musk butter, bakuchiol serum.
# Brand appears to be closing down or transitioning (farewell post).
NORM_P = 'OGZ-BEAUTY-Reference-002'
ULID_P = '01KRKHS8RFCFV3QA82P4D5VZMA'

ALL_OBS += [
obs(NORM_P, ULID_P, 'beauty', 'DAdDDu3t5NH', 'image', '2024-09-10',
    'product hero flat lay award badge', 'clean bright studio', ['pink', 'white', 'gold'],
    ['rose face mask jar', 'Beauty Show award badge', 'rose petal props'],
    'beauty product award showcase', 0,
    [{'language': 'arabic', 'content_summary': 'rose face mask — Beauty Show award winner announcement'}],
    'arabic', 'khaleeji', 'aspirational', 'proud', True, ['#prettynature', '#ماسك_الوجه'],
    'ماسك الوجه بالورد من pretty nature  فائز بجائزة Beauty Show',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'educational_explainer'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DAV5BiZNeZh', 'image', '2024-09-08',
    'product trio flat lay award', 'bright pastel studio', ['cherry_red', 'pink', 'white'],
    ['cherry lip balm', 'Beauty Show award trophy', 'fruit props cherry'],
    'beauty product award hero', 0,
    [{'language': 'arabic', 'content_summary': 'cherry lip balm — Beauty Show award winner'}],
    'arabic', 'khaleeji', 'aspirational', 'celebratory', True, ['#prettynature', '#مرطب_الشفاه'],
    'مرطب الشفاه بالكرز من pretty nature  فائز بجائزة Beauty Show',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'seasonal_collection_drop'], [],
    'semi_professional', 'moderate', 'high', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DAYDodGtZEd', 'image', '2024-09-09',
    'product duo flat lay', 'clean white studio', ['gold', 'white', 'nude'],
    ['nail oil bottle', 'face and hand cream jar', 'award plaque'],
    'beauty product multi-award', 0,
    [{'language': 'arabic', 'content_summary': 'nail oil and hand/face cream — award winners'}],
    'arabic', 'khaleeji', 'aspirational', 'proud', True, ['#prettynature'],
    'زيت الأظافر وكريم اليدين والوجه من pretty nature   الحاصلين على جوائز',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'educational_explainer'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDcDHOPt0dl', 'image', '2024-11-01',
    'product hero ingredient visual', 'clean botanical', ['green', 'beige', 'white'],
    ['bakuchiol serum bottle', 'leaf botanical props'],
    'ingredient hero product shot', 0,
    [{'language': 'arabic', 'content_summary': 'bakuchiol serum for natural skin renewal'}],
    'arabic', 'khaleeji', 'educational', 'nurturing', True, ['#prettynature', '#باكوتشيول'],
    'خلي بشرتك تعيش التجديد الطبيعي! سيروم باكوتشيول من بريتي نيتشر',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'educational_explainer', 'close_up_macro_texture'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDt7s-MN0a_', 'image', '2024-11-05',
    'product hero emotive flat lay', 'soft pastel pink', ['blush', 'white', 'rose'],
    ['rose mask', 'dried rose petals scattered', 'tired face illustration'],
    'problem-solution product shot', 0,
    [{'language': 'arabic', 'content_summary': 'rose mask rescues tired skin — problem-solution messaging'}],
    'arabic', 'khaleeji', 'casual', 'empathetic', True, ['#prettynature', '#ماسك'],
    'قد ما كانت بشرتك مرهقة، ماسك الورد من بريتي نيتشر ينقذها! 🌸',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'specific_emotional_state'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDjfQUYNLi6', 'image', '2024-11-08',
    'product luxe flat lay', 'warm cream studio', ['cream', 'musk', 'gold'],
    ['musk butter moisturizer', 'velvet fabric prop', 'oud incense stick'],
    'luxury moisturizer product shot', 0,
    [{'language': 'arabic', 'content_summary': 'musk butter moisturizer — worthy skin hydration'}],
    'arabic', 'khaleeji', 'aspirational', 'indulgent', True, ['#prettynature', '#مرطب'],
    'تدورين على ترطيب يليق ببشرتك؟  زبدة المسك من بريتي نيتشر تمنحك بشرة ناعمة',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'close_up_macro_texture'], [],
    'semi_professional', 'moderate', 'low', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDo3XzLtJAv', 'image', '2024-11-10',
    'product hero citrus styling', 'bright fresh studio', ['yellow', 'white', 'lemon'],
    ['lemon facial scrub', 'fresh lemon halves', 'citrus leaves'],
    'natural ingredient product shot', 0,
    [{'language': 'arabic', 'content_summary': 'lemon scrub for natural skin radiance'}],
    'arabic', 'khaleeji', 'educational', 'fresh', True, ['#prettynature', '#مقشر'],
    'ابهي بشرتك بإشراقة طبيعية! مقشر الليمون من بريتي نيتشر يزيل',
    [], [], 'clean', 'general_saudi', 'none',
    ['product_hero', 'educational_explainer'], [],
    'semi_professional', 'moderate', 'low', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDdTHUpoY_j', 'image', '2024-11-12',
    'national pride brand alignment graphic', 'green white gold', ['green', 'white', 'gold'],
    ['Saudi football jersey graphic', 'brand logo', 'World Cup 2034 hosting badge'],
    'national pride alignment post', 0,
    [{'language': 'arabic', 'content_summary': 'Saudi hosting FIFA 2034 — national pride alignment'}],
    'arabic', 'khaleeji', 'patriotic', 'proud', False, ['#prettynature', '#السعودية2034'],
    'فخورين ببلادنا وهي تستعد لاستضافة أكبر حدث كروي في العالم',
    [], [], 'clean', 'general_saudi', 'national_sports_pride',
    ['national_day_pride'], [],
    'semi_professional', 'moderate', 'low', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DEg6zqMtAcZ', 'carousel_slide', '2024-12-01',
    'announcement carousel personal milestone', 'warm celebratory', ['white', 'gold', 'blush'],
    ['milestone achievement graphic', 'brand logo', 'sparkle elements'],
    'brand milestone announcement', 0,
    [{'language': 'bilingual', 'content_summary': 'exciting news — founder career milestone announcement'}],
    'bilingual', 'khaleeji', 'personal', 'excited', True, ['#prettynature'],
    '✨ Exciting News! ✨ I\'m thrilled to announce that I\'ve been featured',
    [], [], 'clean', 'general_saudi', 'none',
    ['educational_explainer', 'invitation_to_witness'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DOdSiwtiDMf', 'video', '2025-03-15',
    'farewell video personal direct', 'warm intimate', ['warm_tone', 'neutral', 'white'],
    ['founder direct to camera', 'product lineup visible'],
    'brand farewell announcement', 1,
    [{'language': 'english', 'content_summary': 'brand farewell — after years of hard work its time to say goodbye'}],
    'bilingual', 'khaleeji', 'personal', 'bittersweet', False, ['#prettynature'],
    'After years of hard work and beautiful memories, it\'s time to say goodbye',
    [], [], 'clean', 'general_saudi', 'none',
    ['transformation_story'], [],
    'semi_professional', 'moderate', 'medium', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDdS-9CIO6Q', 'image', '2024-11-12',
    'national pride graphic variation', 'green gold', ['dark_green', 'gold'],
    ['FIFA ball', 'Saudi flag', 'brand overlay'],
    'national pride alignment', 0,
    [{'language': 'arabic', 'content_summary': 'Saudi FIFA 2034 hosting pride — second graphic'}],
    'arabic', 'khaleeji', 'patriotic', 'proud', False, [],
    'فخورين ببلادنا وهي تستعد لاستضافة أكبر حدث كروي في العالم',
    [], [], 'clean', 'general_saudi', 'national_sports_pride',
    ['national_day_pride'], [],
    'semi_professional', 'moderate', 'low', 'prettynature.official'),

obs(NORM_P, ULID_P, 'beauty', 'DDdS4WxIaUC', 'image', '2024-11-12',
    'national pride graphic third variation', 'green gold white', ['green', 'white', 'gold'],
    ['Saudi crest', 'world cup trophy', 'brand mark'],
    'national pride third angle', 0,
    [{'language': 'arabic', 'content_summary': 'Saudi FIFA 2034 — third graphic variation in series'}],
    'arabic', 'khaleeji', 'patriotic', 'celebratory', False, [],
    'فخورين ببلادنا وهي تستعد لاستضافة أكبر حدث كروي في العالم',
    [], [], 'clean', 'general_saudi', 'national_sports_pride',
    ['national_day_pride'], [],
    'semi_professional', 'moderate', 'low', 'prettynature.official'),
]

# Write observations to files
sectors = {
    'OGZ-RETAIL-Reference-001': 'retail',
    'OGZ-BEAUTY-Reference-002': 'beauty',
}

counts = {}
for record in ALL_OBS:
    norm = record['account_handle_normalized']
    sector = record['sector']
    obs_dir = REPO / '11_who_to_learn_from' / 'observations' / sector
    obs_dir.mkdir(parents=True, exist_ok=True)
    fname = obs_dir / f"{record['observation_ulid']}.json"
    fname.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    counts[norm] = counts.get(norm, 0) + 1

total = sum(counts.values())
print(f'Written: {total} new observations')
for norm, cnt in counts.items():
    handle = 'aldeebajofficial' if 'RETAIL' in norm else 'prettynature.official'
    print(f'  @{handle}: +{cnt}')
print('Done.')
