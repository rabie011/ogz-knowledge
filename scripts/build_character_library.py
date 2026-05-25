#!/usr/bin/env python3
"""
build_character_library.py
--------------------------
Populates 16_character_library/ from the 636 obs corpus + _inbox media.

For each obs, classifies it into one or more library categories, copies the
matching media file into the category subfolder, and writes a catalog JSON.

Categories:
  faces/        → obs with people visible (character_count > 0)
  wardrobe/     → obs with wardrobe_notes (thobe, abaya, etc.)
  gestures/     → obs with gesture_notes
  props/        → obs with cultural/heritage props (dallah, sadu, mabkhara…)
  architecture/ → obs with heritage/Najdi/traditional settings
  rituals/      → obs tied to Saudi occasion with characters present

Run: python3 scripts/build_character_library.py
"""
import json, re, shutil
from pathlib import Path
from collections import defaultdict

REPO = Path('/Users/abarihm/Desktop/ogz-knowledge')
OBS_DIR  = REPO / '11_who_to_learn_from' / 'observations'
INBOX    = REPO / '11_who_to_learn_from' / '_inbox'
CHAR_LIB = REPO / '16_character_library'

# ── Keyword classifiers ───────────────────────────────────────────────────────
CULTURAL_PROP_KW = [
    'dallah', 'fenjan', 'mabkhara', 'majmar', 'sadu', 'bukhoor', 'oud',
    'incense', 'qahwa', 'khanjal', 'prayer rug', 'prayer beads', 'misba7',
    'thuya', 'lantern', 'fanoos', 'ghee', 'dirayah', 'thobes', 'shmagh',
    'ghutra', 'silver tray', 'serving tray', 'arabic coffee', 'dates tray'
]
HERITAGE_SETTING_KW = [
    'heritage', 'najdi', 'mud', 'rawasheen', 'traditional interior',
    'old quarter', 'historical', 'diriyah', 'fort', 'mud-brick', 'adobe',
    'traditional saudi', 'wooden mashrabiya', 'heritage architecture',
    'historical building', 'majlis', 'diwan', 'traditional home'
]
SAUDI_OCCASIONS = [
    'ramadan', 'eid_al_fitr', 'eid_al_adha', 'national_day', 'founding_day',
    'hajj', 'iftar', 'suhoor', 'vision_2030', 'winter_seasonal', 'graduation_season'
]

# ── Build inbox media index: shortcode → list[Path] ──────────────────────────
def build_media_index():
    idx = {}
    for f in INBOX.rglob('*'):
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.mp4', '.mov') and f.is_file():
            sc = re.sub(r'(_thumb|_\d+)$', '', f.stem)
            idx.setdefault(sc, []).append(f)
    return idx

# ── Extract shortcode from source_url ────────────────────────────────────────
def shortcode_from_url(url: str):
    m = re.search(r'/p/([^/]+)/', url or '')
    return m.group(1) if m else None

# ── Classify one observation → list of category names ────────────────────────
def classify(d: dict) -> list:
    vo    = d.get('visual_observations', {})
    chars = vo.get('characters_visible', {})
    props = vo.get('props_visible', [])
    setting = (vo.get('setting') or '').lower()
    wardrobe = (chars.get('wardrobe_notes') or '').lower() if isinstance(chars, dict) else ''
    gesture  = (chars.get('gesture_notes')  or '').lower() if isinstance(chars, dict) else ''
    count    = (chars.get('count') or 0)    if isinstance(chars, dict) else 0
    occasion = (d.get('occasion') or '').lower()
    props_str = ' '.join(str(p).lower() for p in (props or []) if isinstance(props, list))

    cats = []
    if count > 0:
        cats.append('faces')
    if wardrobe:
        cats.append('wardrobe')
    if gesture:
        cats.append('gestures')
    if any(kw in props_str for kw in CULTURAL_PROP_KW):
        cats.append('props')
    if any(kw in setting for kw in HERITAGE_SETTING_KW):
        cats.append('architecture')
    if occasion and any(occ in occasion for occ in SAUDI_OCCASIONS) and count > 0:
        cats.append('rituals')
    return cats

# ── Copy media file into library subfolder ────────────────────────────────────
def copy_media(src: Path, dest_dir: Path, shortcode: str, account: str, category: str, i: int) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext  = src.suffix.lower()
    name = f'{account}__{shortcode}__{category}_{i:03d}{ext}'
    dest = dest_dir / name
    if not dest.exists():
        shutil.copy2(src, dest)
    return name

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    media_idx = build_media_index()
    print(f'Media index: {len(media_idx)} unique shortcodes')

    # catalog[category] = list of catalog entries
    catalog = defaultdict(list)
    counters = defaultdict(int)
    copied_files = defaultdict(int)
    no_media = defaultdict(int)

    obs_files = list(OBS_DIR.rglob('*.json'))
    print(f'Processing {len(obs_files)} observations...\n')

    for obs_path in obs_files:
        d = json.loads(obs_path.read_text())
        vo        = d.get('visual_observations', {})
        chars     = vo.get('characters_visible', {})
        props     = vo.get('props_visible', [])
        account   = d.get('account_handle_normalized', 'unknown')
        # Extract clean handle from normalized (e.g. OGZ-F-AND-B-Reference-002 → ref002)
        handle = account.replace('OGZ-', '').replace('F-AND-B-', 'fb_').replace('BEAUTY-', 'beauty_').replace('RETAIL-', 'retail_').replace('Reference-', 'ref').lower()

        url = d.get('content_ref', {}).get('source_url', '')
        sc  = shortcode_from_url(url)

        cats = classify(d)
        if not cats:
            continue

        media_files = media_idx.get(sc, []) if sc else []
        # Prefer .jpg over .mp4 for still reference; take first if jpg not available
        img_files  = [f for f in media_files if f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
        vid_files  = [f for f in media_files if f.suffix.lower() in ('.mp4', '.mov')]
        best_media = (img_files or vid_files or [None])[0]

        for cat in cats:
            counters[cat] += 1
            dest_dir = CHAR_LIB / cat

            copied_name = None
            if best_media:
                counters[f'{cat}_with_media'] += 1
                i = counters[f'{cat}_with_media']
                copied_name = copy_media(best_media, dest_dir, sc or 'unknown', handle, cat, i)
                copied_files[cat] += 1

            # Build catalog entry regardless of whether we have media
            entry = {
                'obs_ulid': d.get('observation_ulid', ''),
                'account':  handle,
                'shortcode': sc,
                'source_url': url,
                'sector': d.get('sector', ''),
                'occasion': d.get('occasion', ''),
                'setting': vo.get('setting', ''),
                'character_count': chars.get('count', 0) if isinstance(chars, dict) else 0,
                'gender_presentation': chars.get('gender_presentation', '') if isinstance(chars, dict) else '',
                'wardrobe_notes': chars.get('wardrobe_notes', '') if isinstance(chars, dict) else '',
                'gesture_notes': chars.get('gesture_notes', '') if isinstance(chars, dict) else '',
                'props_visible': props if isinstance(props, list) else [],
                'engagement_potential': d.get('quality_assessment', {}).get('engagement_potential', ''),
                'media_file': copied_name,
                'has_media': bool(best_media),
            }
            catalog[cat].append(entry)

            if not best_media:
                no_media[cat] += 1

    # ── Write catalog JSON per category ─────────────────────────────────────
    for cat, entries in catalog.items():
        # Sort: with_media first, then by engagement_potential
        eng_order = {'high': 0, 'medium': 1, 'low': 2, '': 3}
        entries_sorted = sorted(entries, key=lambda e: (0 if e['has_media'] else 1, eng_order.get(e['engagement_potential'], 3)))

        out = {
            'category': cat,
            'total_entries': len(entries_sorted),
            'with_media': sum(1 for e in entries_sorted if e['has_media']),
            'without_media': sum(1 for e in entries_sorted if not e['has_media']),
            'note': f'Entries without media have source_url for manual reference retrieval',
            'entries': entries_sorted
        }
        catalog_path = CHAR_LIB / cat / 'catalog.json'
        catalog_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    # ── Print summary ─────────────────────────────────────────────────────────
    print('=' * 60)
    print('CHARACTER LIBRARY BUILD COMPLETE')
    print('=' * 60)
    all_cats = ['faces', 'wardrobe', 'gestures', 'props', 'architecture', 'rituals']
    for cat in all_cats:
        total    = counters.get(cat, 0)
        w_media  = copied_files.get(cat, 0)
        wo_media = no_media.get(cat, 0)
        print(f'  {cat:15s}: {total:3d} entries  ({w_media} with media file, {wo_media} URL-only)')

    total_media_copied = sum(copied_files.values())
    print(f'\n  Total media files copied: {total_media_copied}')
    print(f'  Catalog JSONs written: {len(catalog)} categories')
    print(f'\n  Location: {CHAR_LIB}')

if __name__ == '__main__':
    main()
