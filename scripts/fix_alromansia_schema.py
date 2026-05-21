#!/usr/bin/env python3
"""Fix the 15 alromansia observations that used wrong field names."""
import json, pathlib, datetime

OBS_DIR = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge/11_who_to_learn_from/observations/f_and_b')

fixed = 0
for f in OBS_DIR.glob('*.json'):
    d = json.loads(f.read_text())
    if d.get('account_handle_normalized') != 'OGZ-F-AND-B-Reference-011':
        continue

    changed = False

    # Fix content_ref
    cr = d.get('content_ref', {})
    if 'shortcode' in cr:
        sc = cr.pop('shortcode')
        ct = cr.get('content_type', 'image')
        ext = '_thumb.jpg' if ct in ('video', 'reel') else '.jpg'
        cr['filename'] = sc + ext
        changed = True
    if 'post_date' in cr:
        cr['capture_date'] = cr.pop('post_date')
        changed = True
    if 'url' in cr:
        cr['source_url'] = cr.pop('url')
        changed = True

    # Fix visual_observations
    vo = d.get('visual_observations', {})
    if 'composition_type' in vo:
        vo['composition_style'] = vo.pop('composition_type').replace('_', ' ')
        changed = True
    if 'color_palette' in vo:
        vo['color_palette_dominant'] = vo.pop('color_palette')
        changed = True
    if 'props_and_items' in vo:
        vo['props_visible'] = vo.pop('props_and_items')
        changed = True
    if 'setting_context' in vo:
        vo['setting'] = vo.pop('setting_context').replace('_', ' ')
        changed = True
    # Fix text_overlays: must be array of {language, content_summary}
    to = vo.get('text_overlays')
    if isinstance(to, str):
        lang = 'arabic' if 'ar_' in to else 'bilingual' if 'bilingual' in to else 'arabic'
        summary = to.replace('ar_', '').replace('_', ' ')
        vo['text_overlays'] = [{'language': lang, 'content_summary': summary}]
        changed = True

    # Remove voice_observations (not allowed by schema additionalProperties:false)
    if 'voice_observations' in d:
        del d['voice_observations']
        changed = True

    # Fix compliance_check field names
    cc = d.get('compliance_check', {})
    if 'hard_blocks' in cc:
        cc['hard_blocks_triggered'] = cc.pop('hard_blocks')
        changed = True
    if 'overall_status' in cc:
        status = cc.pop('overall_status')
        cc['overall_compliance'] = 'clean' if status == 'pass' else 'hard_blocked'
        changed = True

    # Fix cultural_notes field names
    cn = d.get('cultural_notes', {})
    if 'region' in cn:
        cn['regional_orientation_detected'] = cn.pop('region')
        changed = True
    if 'hospitality_cues_present' in cn:
        cn['hospitality_cues'] = cn.pop('hospitality_cues_present')
        changed = True
    if 'analyst_notes' in cn:
        cn['free_notes'] = cn.pop('analyst_notes')
        changed = True
    if 'saudi_cultural_score' in cn:
        del cn['saudi_cultural_score']
        changed = True

    # Fix pattern_matches: must be array of {pattern_slug, confidence, notes}
    pm = d.get('pattern_matches', [])
    if pm and isinstance(pm[0], str):
        d['pattern_matches'] = [
            {'pattern_slug': slug, 'confidence': 'moderate', 'notes': None}
            for slug in pm
        ]
        changed = True

    # Fix quality_assessment field names
    qa = d.get('quality_assessment', {})
    if 'visual_quality_score' in qa:
        score = qa.pop('visual_quality_score')
        qa['production_quality'] = 'professional' if score >= 8 else 'semi_professional'
        changed = True
    if 'engagement_signal' in qa:
        likes = qa.pop('engagement_signal')
        qa['engagement_potential'] = 'high' if likes >= 200 else ('medium' if likes >= 50 else 'low')
        changed = True
    if 'content_originality' in qa:
        del qa['content_originality']
        changed = True
    if 'brand_consistency' in qa:
        qa['brand_consistency_with_account'] = qa.pop('brand_consistency')
        changed = True

    # Fix provenance: must match provenance_mixin schema
    prov = d.get('provenance', {})
    if 'extracted_by' in prov or 'source' not in prov:
        sc_val = d.get('content_ref', {}).get('filename', 'unknown')
        d['provenance'] = {
            'source': f"benchmark:@alromansiahksa; content:{sc_val}",
            'date_added': '2026-05-21T20:00:00Z',
            'confirmer': 'claude_code_extraction',
            'confidence': 'inferred',
            'scope': 'sector:f_and_b',
        }
        changed = True

    if changed:
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        fixed += 1

print(f'Fixed {fixed} alromansia observations')
