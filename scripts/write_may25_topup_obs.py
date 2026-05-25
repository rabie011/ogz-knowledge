#!/usr/bin/env python3
"""
May 25 top-up pass — new posts for 3 accounts (browser-collected 2026-05-25):
  @alromansiahksa  24 → 30  (+6 posts, May 22-24)
  @herfyfsc        25 → 27  (+2 posts, May 22-23)
  @kuduksa         25 → 28  (+3 posts, May 22-24)
All posts confirmed image type (isVideo=false).
Context: pre-Eid Al-Adha (June 7, 2026) period.
"""
import json, pathlib, time, random, datetime

CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
REPO = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')
OBS_DIR_FB = REPO / '11_who_to_learn_from' / 'observations' / 'f_and_b'
OBS_DIR_FB.mkdir(parents=True, exist_ok=True)

def make_ulid():
    ts = int(time.time() * 1000)
    ts_part = ''
    t = ts
    for _ in range(10):
        ts_part = CROCKFORD[t % 32] + ts_part
        t //= 32
    rand_part = ''.join(random.choice(CROCKFORD) for _ in range(16))
    time.sleep(0.004)
    return ts_part + rand_part

def obs(account_norm, account_ulid, sector, shortcode, content_type, capture_date,
        composition, lighting, colors, props, setting, chars, overlays, notable,
        lang, dialect, register, tone, cta, hashtags, caption,
        hard_blocks, soft_flags, compliance,
        region, occasion, patterns, hosp_cues,
        prod_quality, brand_consistency, engagement_potential,
        source_suffix=''):
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
            'notable_visual_elements': notable,
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
            'source': f'benchmark:@{source_suffix}; content:{shortcode}{fn_ext}; browser_collected:2026-05-25',
            'date_added': datetime.datetime.utcnow().isoformat() + 'Z',
            'confirmer': 'claude_code_extraction',
            'confidence': 'inferred',
            'scope': f'sector:{sector}',
        },
    }

ALL_OBS = []

# ═══════════════════════════════════════════════════════════════════════════
# @alromansiahksa — OGZ-F-AND-B-Reference-011
# 24 existing obs (May 12-19). Adding 6 new posts (May 22-24).
# Pre-Eid Al-Adha: sacrifice booking, product promos, weekend dining.
# ═══════════════════════════════════════════════════════════════════════════
NORM_R = 'OGZ-F-AND-B-Reference-011'
ULID_R = '01KS5R0A1701GF09TMG4E65H5C'

ALL_OBS += [

# DYr3fpFiWEG — May 23, 118 likes — weekend gathering CTA — MEDIUM
obs(NORM_R, ULID_R, 'f_and_b', 'DYr3fpFiWEG', 'image', '2026-05-23',
    'food spread group dining table', 'warm amber restaurant', ['orange', 'cream', 'brown', 'golden'],
    ['assorted dishes family spread', 'brand colour overlay', 'brand hashtag'],
    'group dining table spread', 0,
    [{'language': 'arabic', 'content_summary': 'weekend gathering recipe with Al Romansiah brand'}],
    ['"وصفة الويكند الصح" — weekend recipe framing elevates dining to a ritual'],
    'arabic', 'najdi', 'casual', 'warm',
    False, ['#مطاعم_الرومانسية'],
    'وصفة الويكند الصح: لمّة الحبايب مع #مطاعم_الرومانسية تجمعكم 😍🧡',
    [], [], 'clean',
    'general_saudi', 'evergreen',
    ['family_group_dining', 'invitation_to_witness', 'lifestyle_occasion_framing'],
    ['lamma_gathering', 'weekend_ritual'],
    'professional', 'strong', 'medium', 'alromansiahksa'),

# DYpBHWAnDvw — May 22, 26 likes — Diriyah lamb / wellness angle — LOW
obs(NORM_R, ULID_R, 'f_and_b', 'DYpBHWAnDvw', 'image', '2026-05-22',
    'product hero close-up', 'warm studio', ['golden_brown', 'cream', 'orange'],
    ['Diriyah lamb dish', 'traditional clay presentation', 'sauce glistening'],
    'signature dish macro hero', 0,
    [{'language': 'arabic', 'content_summary': 'Diriyah lamb as natural collagen alternative'}],
    ['"لو تعبتِ من كبسولات الكولاجين" — wellness humour frame targeting female audience (feminine verb)'],
    'arabic', 'najdi', 'casual', 'playful',
    True, ['#مطاعم_الرومانسية'],
    'لو تعبتِ من كبسولات الكولاجين، جربي لحم الديرة، واستمتعي😋🧡 #مطاعم_الرومانسية',
    [], [], 'clean',
    'general_saudi', 'evergreen',
    ['product_hero', 'lifestyle_occasion_framing', 'humour_hook'],
    ['wellness_angle', 'feminine_addressed'],
    'professional', 'strong', 'low', 'alromansiahksa'),

# DYrjbZqlnis — May 23, 22 likes — Butter Chicken product hero — LOW
obs(NORM_R, ULID_R, 'f_and_b', 'DYrjbZqlnis', 'image', '2026-05-23',
    'signature dish close-up hero', 'warm dramatic', ['deep_orange', 'cream', 'brown'],
    ['butter chicken dish', 'spiced sauce close-up', 'brand logo'],
    'spiced product hero', 0,
    [{'language': 'arabic', 'content_summary': 'Butter Chicken flavour satisfaction claim'}],
    ['"تدوّر على الملغّم نكهات وتوابل" — bold spice search narrative'],
    'arabic', 'najdi', 'casual', 'confident',
    True, ['#مطاعم_الرومانسية'],
    'تدوّر على الملغّم نكهات وتوابل؟ بتر تشيكن الرومانسية يرضيك🫡🧡 #مطاعم_الرومانسية',
    [], [], 'clean',
    'general_saudi', 'evergreen',
    ['product_hero', 'flavour_bold_claim', 'satisfaction_promise'],
    [],
    'professional', 'strong', 'low', 'alromansiahksa'),

# DYt6JVYmQuL — May 24, 21 likes — Al Romansiah Box product — LOW
obs(NORM_R, ULID_R, 'f_and_b', 'DYt6JVYmQuL', 'image', '2026-05-24',
    'branded meal box flat lay', 'clean bright studio', ['orange', 'white', 'cream'],
    ['branded Al Romansiah meal box', 'varied items inside', 'brand colour background'],
    'branded box product reveal', 0,
    [{'language': 'arabic', 'content_summary': 'Al Romansiah Box satisfies when nothing else does'}],
    ['"بوكس الرومانسية يراضيك" — brand as solution to indecision; personification of the box'],
    'arabic', 'najdi', 'casual', 'reassuring',
    True, ['#مطاعم_الرومانسية'],
    'دام مافيه شيء على كيفك ويرضيك، بوكس الرومانسية يراضيك🧡 #مطاعم_الرومانسية',
    [], [], 'clean',
    'general_saudi', 'evergreen',
    ['product_hero', 'satisfaction_promise', 'brand_solution_framing'],
    [],
    'professional', 'strong', 'low', 'alromansiahksa'),

# DYuw3zojawc — May 24, 14 likes — Eid sacrifice booking CTA — LOW
obs(NORM_R, ULID_R, 'f_and_b', 'DYuw3zojawc', 'image', '2026-05-24',
    'Eid occasion graphic bold', 'warm festive', ['orange', 'cream', 'green', 'white'],
    ['sheep/livestock illustration', 'app CTA graphic', 'Eid text overlay bold'],
    'Eid sacrifice booking graphic', 0,
    [{'language': 'arabic', 'content_summary': 'Eid sacrifice booking via app — ready with one tap'}],
    ['"ازهلها بضغطة زر" — simplification of Eid ritual via digital ease'],
    'arabic', 'najdi', 'casual', 'upbeat',
    True, ['#مطاعم_الرومانسية'],
    'ازهلها بضغطة زر ذبيحة عيدكم جاهزة 🐑 😍🧡 #مطاعم_الرومانسية',
    [], [], 'clean',
    'general_saudi', 'eid_al_adha',
    ['eid_occasion_activation', 'app_digital_convenience', 'sacrifice_service'],
    ['eid_sacrifice_tradition', 'digital_ease_framing'],
    'professional', 'strong', 'low', 'alromansiahksa'),

# DYustEZNr5Y — May 24, 8 likes — App feature announcement — LOW
obs(NORM_R, ULID_R, 'f_and_b', 'DYustEZNr5Y', 'image', '2026-05-24',
    'app UI mockup screenshot', 'clean digital white', ['orange', 'white', 'light_grey'],
    ['smartphone app screen', 'new feature UI', 'Arabic interface labels'],
    'app feature launch announcement', 0,
    [{'language': 'arabic', 'content_summary': 'New sacrifice booking UI in app — permanent feature'}],
    ['"ميزة دائمة معكم في كل وقت" — permanence reassurance, not just Eid-limited'],
    'arabic', 'najdi', 'casual', 'informative',
    True, [],
    'سهّلناها عليك ✋🏼 حجز ذبيحتك صار بضغطة زر عبر الواجهة الجديدة بالتطبيق 📲 ميزة دائمة معكم في كل وقت ولأي عزيمة 🧡',
    [], [], 'clean',
    'general_saudi', 'eid_al_adha',
    ['app_feature_launch', 'digital_convenience', 'loyalty_app_engagement'],
    ['digital_ease_framing'],
    'professional', 'strong', 'low', 'alromansiahksa'),

]  # end alromansiahksa

# ═══════════════════════════════════════════════════════════════════════════
# @herfyfsc — OGZ-F-AND-B-Reference-006
# 25 existing obs (up to May 20). Adding 2 new posts (May 22-23).
# Context: ongoing PowerPuff Girls campaign + new product (Toasty Club).
# ═══════════════════════════════════════════════════════════════════════════
NORM_H = 'OGZ-F-AND-B-Reference-006'
ULID_H = '01KS8MQHR0SVWGFRK2NDA3YT6P'

ALL_OBS += [

# DYrOQO1IAzv — May 23, 98 likes — New product: Toasty Club — MEDIUM
obs(NORM_H, ULID_H, 'f_and_b', 'DYrOQO1IAzv', 'image', '2026-05-23',
    'new product reveal centred hero', 'bright clean studio', ['red', 'white', 'cream', 'golden_brown'],
    ['Toasty Club sandwich', 'branded packaging', 'brand logo'],
    'new product launch hero shot', 0,
    [{'language': 'arabic', 'content_summary': 'Toasty Club new product — not ordinary, elevates taste'}],
    ['"جديدنا مو عادي" — standard Herfy new-launch opener; #توستي_كلوب branded hashtag anchor'],
    'arabic', 'najdi', 'casual', 'excited',
    True, ['#توستي_كلوب', '#هرفي', '#Herfy'],
    'جديدنا مو عادي! توستي كلوب جاي يرفع مستوى اللذّة 🤩 #توستي_كلوب #هرفي #Herfy',
    [], [], 'clean',
    'general_saudi', 'evergreen',
    ['new_product_launch', 'product_hero', 'brand_campaign'],
    ['product_novelty_excitement'],
    'professional', 'strong', 'medium', 'herfyfsc'),

# DYopdUOoMJU — May 22, 76 likes — PowerPuff Girls campaign continuation — MEDIUM
obs(NORM_H, ULID_H, 'f_and_b', 'DYopdUOoMJU', 'image', '2026-05-22',
    'IP collab product styled flat lay', 'bright vivid pop art', ['pink', 'white', 'red', 'cream'],
    ['PPG branded meal', 'feminine styling ribbon bow', 'branded box'],
    'IP collab campaign image feminine styling', 0,
    [{'language': 'arabic', 'content_summary': 'Girl power meal large dose of cuteness — who can resist?'}],
    ['"جرعة لطافة كبيرة" — femininity/cuteness dosage metaphor; #وجبة_فتيات_القوة campaign hashtag'],
    'arabic', 'najdi', 'casual', 'playful',
    False, ['#وجبة_فتيات_القوة', '#هرفي', '#Herfy'],
    '#وجبة_فتيات_القوة جرعة لطافة كبيرة! مين يقدر يقاومها؟ 🎀 ✨ #هرفي #Herfy',
    [], [], 'clean',
    'general_saudi', 'brand_campaign',
    ['seasonal_collection_drop', 'IP_collab', 'feminine_audience_targeting'],
    ['feminine_gifting_culture'],
    'professional', 'strong', 'medium', 'herfyfsc'),

]  # end herfyfsc

# ═══════════════════════════════════════════════════════════════════════════
# @kuduksa — OGZ-F-AND-B-Reference-007
# 25 existing obs (up to May 21). Adding 3 new posts (May 22-24).
# Context: Eid Al-Adha period — Beef Box collab, Chicken Box offer, branch event.
# ═══════════════════════════════════════════════════════════════════════════
NORM_K = 'OGZ-F-AND-B-Reference-007'
ULID_K = '01KS8MQHR1WGRTDFZ2NDA3YT7Q'

ALL_OBS += [

# DYrHboajiZk — May 23, 185 likes — Beef Box × Shabab Al Bomb Eid collab — MEDIUM
obs(NORM_K, ULID_K, 'f_and_b', 'DYrHboajiZk', 'image', '2026-05-23',
    'collab product reveal hero', 'warm festive Eid lighting', ['blue', 'yellow', 'gold', 'brown', 'cream'],
    ['Beef Box branded packaging', 'Shabab Al Bomb collab logo', 'Eid decorative elements'],
    'Eid limited collab product shot', 0,
    [{'language': 'arabic', 'content_summary': 'Eid Beef Box collab Kudu x Shabab Al Bomb — rich flavour'}],
    ['"العيد صار احلى مع بوكس اللحم" — Eid elevation via product; dual-brand collab visibility; bilingual post'],
    'bilingual', 'najdi', 'casual', 'celebratory',
    True, [],
    'العيد صار احلى مع بوكس اللحم!! بوكس اللحم من كودو × شباب البومب — rich flavour Beef Box for Eid',
    [], [], 'clean',
    'general_saudi', 'eid_al_adha',
    ['brand_collab', 'eid_occasion_activation', 'product_hero', 'limited_time_offer'],
    ['eid_celebratory_dining', 'collab_social_proof'],
    'professional', 'strong', 'medium', 'kuduksa'),

# DYofAd-OMa- — May 22, 115 likes — Chicken Box + free strips Eid offer — MEDIUM
obs(NORM_K, ULID_K, 'f_and_b', 'DYofAd-OMa-', 'image', '2026-05-22',
    'product bundle offer flat lay', 'bright appetising studio', ['blue', 'yellow', 'cream', 'golden'],
    ['Kudu Chicken Box', 'strips bucket', 'Eid offer badge', 'bilingual text'],
    'Eid limited offer product bundle', 0,
    [{'language': 'arabic', 'content_summary': 'Chicken Box with free strips bucket — Eid limited offer'}],
    ['"العيد ألذ مع كودو" — Eid sweetness via food; free add-on as GWP mechanic; bilingual'],
    'bilingual', 'najdi', 'casual', 'celebratory',
    True, [],
    'العيد ألذ مع كودو. مع كل بوكس كودو دجاج، سطل ستربس علينا. عرض محدود — Eid offer Chicken Box + free strips bucket',
    [], [], 'clean',
    'general_saudi', 'eid_al_adha',
    ['eid_occasion_activation', 'gwp_offer', 'product_hero', 'limited_time_offer'],
    ['eid_celebratory_dining', 'value_gifting'],
    'professional', 'strong', 'medium', 'kuduksa'),

# DYug5VdtRK1 — May 24, 45 likes — Eid branch activation event graphic — LOW
obs(NORM_K, ULID_K, 'f_and_b', 'DYug5VdtRK1', 'image', '2026-05-24',
    'event announcement poster graphic', 'warm festive gold', ['blue', 'gold', 'white', 'green'],
    ['bus graphic Shabab Al Bomb collab', 'branch location callout', 'event schedule text'],
    'Eid in-store activation event poster', 0,
    [{'language': 'arabic', 'content_summary': 'Eid event at Khurais branch — Saudi coffee, ardah dance, gifts, face painting'}],
    ['"باص شباب البومب" — collab tour bus activation; in-person Eid celebration mechanic'],
    'arabic', 'najdi', 'casual', 'celebratory',
    True, [],
    'باص شباب البومب بانتظاركم في كودو خريص 🚍💛 — Eid activation event with Saudi coffee, ardah, gifts',
    [], [], 'clean',
    'general_saudi', 'eid_al_adha',
    ['eid_occasion_activation', 'experiential_marketing', 'community_gathering'],
    ['saudi_hospitality_ardah', 'eid_family_gathering', 'in_store_activation'],
    'professional', 'strong', 'low', 'kuduksa'),

]  # end kuduksa

# ── write files ─────────────────────────────────────────────────────────────
written = 0
for o in ALL_OBS:
    sector = o['sector']
    out_dir = REPO / '11_who_to_learn_from' / 'observations' / sector
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{o['observation_ulid']}.json"
    out_path.write_text(json.dumps(o, ensure_ascii=False, indent=4))
    written += 1

print(f"Written {written} observations")
print("Breakdown:")
from collections import Counter
c = Counter(o['account_handle_normalized'] for o in ALL_OBS)
for k, v in c.items():
    print(f"  {k}: {v} obs")
