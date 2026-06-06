"""
quality_gate.py — Importable quality gate for Arabic caption checking.

Usage:
    from lib.quality_gate import check, auto_fix, log_mistake

    result = check(caption, brand="albaik", occasion="founding_day")
    # Returns: {score, checks[], fixes[], passed, confidence}

    fixed = auto_fix(caption, brand="albaik", sector="f_and_b")
    log_mistake(brand="pizzahutsaudi", score=65, mistake="No Saudi markers")
"""
import json, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
BRAIN_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
LEARNING_STORE = BASE / "logs" / "learning_store.jsonl"

# ── Lazy-load brain (cache it) ─────────────────────────────────────────────
_brain = None

def _get_brain():
    global _brain
    if _brain is None:
        _brain = json.loads(BRAIN_PATH.read_text())
    return _brain

# ── Saudi markers ──────────────────────────────────────────────────────────
SAUDI_USE = ['وش', 'ايش', 'اللي', 'حيّاكم', 'الحين', 'كذا', 'يالله', 'طيب', 'حلو', 'اطلبه', 'جربه', 'شرايكم', 'الآن', 'أهلاً', 'تعالوا']
SAUDI_AVOID = ['شنو', 'جذي', 'زين', 'تسحرني', 'تفضلوا', 'هيا بنا']

# English transliteration words that should be Arabic in Saudi brand captions
# From human review: "فرايز" should be "بطاطس", English brand names should be Arabic
ENGLISH_IN_ARABIC = ['فرايز', 'برغر', 'هامبرغر', 'بيتزا هت', 'ماكدونالدز ']

# Overused generic phrases (human review: lacks creativity)
OVERUSED_PHRASES = ['لا تفوتون الفرصة', 'لا تفوّتون الفرصة', 'عرض لفترة محدودة فقط']
MSA_REPLACE = {'تفضلوا': 'تعالوا', 'تسحرني': 'يعجبني', 'رائع': 'حلو', 'مذهل': 'خطير', 'هيا بنا': 'يالله'}
SECTOR_EMOJI_LIMITS = {'fashion': 1, 'f_and_b': 2, 'retail_lifestyle': 3, 'beauty_personal_care': 4}


def _count_emojis(text):
    return sum(1 for c in text if ord(c) > 0x1F000)

def _count_hashtags(text):
    return len(re.findall(r'#\S+', text))

def _arabic_ratio(text):
    arabic = len(re.findall(r'[؀-ۿ]', text))
    latin = len(re.findall(r'[a-zA-Z]', text))
    total = arabic + latin
    if total == 0: return 1.0
    return arabic / total


def check(text: str, brand: str = None, occasion: str = 'evergreen') -> dict:
    """
    Run 10 quality checks on a caption.
    Returns: {score, checks[], fixes[], passed, confidence}
    """
    brain = _get_brain()
    brand_profiles = brain.get('brand_profiles', {})
    brand_product_names = brain.get('brand_product_names', {})
    occasion_required = brain.get('occasion_required_words', {})
    guardrails = brain.get('cultural_guardrails', {})

    profile = brand_profiles.get(brand, {})
    sector = profile.get('sector', '')
    product_data = brand_product_names.get(brand, {})

    checks = []
    fixes = []
    hard_blocked = False

    # ── Check 7 first: Cultural violations (hard block) ──────────────────
    forbidden = (guardrails.get('forbidden_props', []) +
                 guardrails.get('forbidden_behaviors', []))
    cultural_hit = [f for f in forbidden if f.lower() in text.lower()]
    if cultural_hit:
        hard_blocked = True
        checks.append({'check': 'cultural_violation', 'passed': False, 'weight': 20,
                        'detail': f'Forbidden: {cultural_hit}'})
    else:
        checks.append({'check': 'cultural_violation', 'passed': True, 'weight': 20, 'detail': 'Clean'})

    # ── Check 6: Arabic > English ratio ──────────────────────────────────
    # All brands must produce Arabic output — even global brands like Zara/H&M.
    # The engine generates Arabic for the Saudi market regardless of what the brand posts.
    ratio = _arabic_ratio(text)
    posting_lang = profile.get('posting_language', 'arabic')

    if ratio < 0.3:
        # Hard block — less than 30% Arabic is not acceptable for any Saudi brand
        hard_blocked = True
        checks.append({'check': 'arabic_ratio', 'passed': False, 'weight': 15,
                        'detail': f'Only {ratio:.0%} Arabic — must be at least 30% Arabic'})
    elif ratio < 0.6:
        # Soft fail — should be majority Arabic
        checks.append({'check': 'arabic_ratio', 'passed': False, 'weight': 15,
                        'detail': f'Low Arabic ratio: {ratio:.0%} — should be majority Arabic'})
        fixes.append('arabic_ratio')
    else:
        checks.append({'check': 'arabic_ratio', 'passed': True, 'weight': 15,
                        'detail': f'{ratio:.0%} Arabic'})

    # ── Check 1: Product name correct ────────────────────────────────────
    wrong_names = product_data.get('wrong', [])
    if isinstance(product_data.get('top_words_in_captions'), list):
        wrong_names = []  # auto-extracted, can't enforce "wrong" names yet

    wrong_found = [w for w in wrong_names if isinstance(w, str) and w.lower() in text.lower()]
    if wrong_found:
        hard_blocked = True
        checks.append({'check': 'product_name', 'passed': False, 'weight': 20,
                        'detail': f'Wrong product: {wrong_found}'})
        fixes.append('product_name')
    else:
        checks.append({'check': 'product_name', 'passed': True, 'weight': 20, 'detail': 'OK'})

    # ── Check 2: Brand hashtag present ───────────────────────────────────
    # Pass if: any signature phrase present in text, OR ANY hashtag present at all.
    # The signal we enforce: posts should have at least one hashtag.
    # The preferred hashtags are advisory (soft warning if not in sig_phrases).
    sig_phrases = profile.get('signature_phrases', [])
    hashtags_in_text = re.findall(r'#\S+', text)
    exact_match = any(p in text for p in sig_phrases) if sig_phrases else False
    any_hashtag = bool(hashtags_in_text)

    if exact_match:
        matched = [p for p in sig_phrases if p in text]
        checks.append({'check': 'brand_hashtag', 'passed': True, 'weight': 15,
                        'detail': f'Brand hashtag found: {matched[:2]}'})
    elif any_hashtag:
        # Has a hashtag but not the preferred one — pass with note
        checks.append({'check': 'brand_hashtag', 'passed': True, 'weight': 15,
                        'detail': f'Has hashtag (preferred: {sig_phrases[:1] if sig_phrases else "none defined"})'})
    else:
        # No hashtag at all — soft fail
        checks.append({'check': 'brand_hashtag', 'passed': False, 'weight': 15,
                        'detail': f'No hashtag found (add brand hashtag)'})
        fixes.append('brand_hashtag')

    # ── Check 3: Saudi markers — advisory only (weight=5, never blocks)
    # Data shows: only 9% of gold captions use explicit markers.
    # Many top posts get 10K+ likes with no markers at all.
    # This check catches obvious non-Saudi content, not gold-standard absence.
    saudi_found = [w for w in SAUDI_USE if w in text]
    has_arabic_content = ratio >= 0.6  # Most content is Arabic = Saudi context
    if not saudi_found and not has_arabic_content:
        checks.append({'check': 'saudi_markers', 'passed': False, 'weight': 5,
                        'detail': 'No Saudi markers — content may not be Saudi-specific'})
        fixes.append('saudi_markers')
    elif saudi_found:
        checks.append({'check': 'saudi_markers', 'passed': True, 'weight': 5,
                        'detail': f'Found: {saudi_found[:3]}'})
    else:
        # Arabic content without markers — passes (gold captions prove this works)
        checks.append({'check': 'saudi_markers', 'passed': True, 'weight': 5,
                        'detail': f'Arabic content present ({ratio:.0%}) — markers optional for gold-tier brands'})

    # ── Check 4: No non-Saudi words ───────────────────────────────────────
    bad_words = [w for w in SAUDI_AVOID if w in text]
    if bad_words:
        checks.append({'check': 'non_saudi_words', 'passed': False, 'weight': 10,
                        'detail': f'Non-Saudi words: {bad_words}'})
        fixes.append('msa_replace')
    else:
        checks.append({'check': 'non_saudi_words', 'passed': True, 'weight': 10, 'detail': 'Clean'})

    # ── Check 4b: No overused generic phrases (human review finding) ─────────
    overused_found = [p for p in OVERUSED_PHRASES if p in text]
    if overused_found:
        checks.append({'check': 'overused_phrase', 'passed': False, 'weight': 5,
                        'detail': f'Generic phrase detected: {overused_found[0]}'})
        fixes.append('overused_phrase')
    else:
        checks.append({'check': 'overused_phrase', 'passed': True, 'weight': 5, 'detail': 'Creative'})

    # ── Check 5: Occasion keyword present ─────────────────────────────────
    required = occasion_required.get(occasion, [])
    occ_found = any(word in text for word in required) if required else True
    if not occ_found:
        checks.append({'check': 'occasion_keyword', 'passed': False, 'weight': 10,
                        'detail': f'Missing occasion words: {required}'})
        fixes.append('occasion_keyword')
    else:
        checks.append({'check': 'occasion_keyword', 'passed': True, 'weight': 10,
                        'detail': f'OK (occasion: {occasion})'})

    # ── Check 8: Emoji limit ───────────────────────────────────────────────
    emoji_count = _count_emojis(text)
    limit = SECTOR_EMOJI_LIMITS.get(sector, 3)
    if emoji_count > limit:
        checks.append({'check': 'emoji_limit', 'passed': False, 'weight': 5,
                        'detail': f'{emoji_count} emojis (limit: {limit})'})
        fixes.append('emoji_limit')
    else:
        checks.append({'check': 'emoji_limit', 'passed': True, 'weight': 5,
                        'detail': f'{emoji_count} emojis (OK)'})

    # ── Check 9: Hashtag count ≤ 3 + no duplicates ─────────────────────────
    import re as _re_ht
    all_tags = _re_ht.findall(r'#[^\s#]+', text)
    unique_tags = list(dict.fromkeys(all_tags))
    has_dupes = len(all_tags) != len(unique_tags)
    if len(unique_tags) > 3:
        checks.append({'check': 'hashtag_count', 'passed': False, 'weight': 5,
                        'detail': f'{len(unique_tags)} unique hashtags (max 3)'})
        fixes.append('hashtag_limit')
    elif has_dupes:
        checks.append({'check': 'hashtag_count', 'passed': False, 'weight': 5,
                        'detail': f'Duplicate hashtags detected: {all_tags}'})
        fixes.append('hashtag_dedup')
    else:
        checks.append({'check': 'hashtag_count', 'passed': True, 'weight': 5,
                        'detail': f'{len(unique_tags)} hashtags (OK)'})

    # ── Check 10: No MSA formality ─────────────────────────────────────────
    msa_found = [w for w in MSA_REPLACE if w in text]
    if msa_found:
        checks.append({'check': 'msa_formality', 'passed': False, 'weight': 5,
                        'detail': f'MSA words: {msa_found}'})
        fixes.append('msa_replace')
    else:
        checks.append({'check': 'msa_formality', 'passed': True, 'weight': 5, 'detail': 'Clean'})

    # ── Score ───────────────────────────────────────────────────────────────
    if hard_blocked:
        score = 0
        passed = False
    else:
        total_weight = sum(c['weight'] for c in checks)
        earned = sum(c['weight'] for c in checks if c['passed'])
        score = int((earned / total_weight) * 100) if total_weight > 0 else 0
        passed = score >= 70

    if score >= 80:
        confidence = 'high'
    elif score >= 60:
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'score': score,
        'passed': passed,
        'confidence': confidence,
        'hard_blocked': hard_blocked,
        'checks': checks,
        'fixes_needed': list(set(fixes)),
    }


def auto_fix(text: str, brand: str = None, sector: str = None) -> str:
    """Apply automatic fixes to a caption."""
    brain = _get_brain()
    brand_product_names = brain.get('brand_product_names', {})
    brand_profiles = brain.get('brand_profiles', {})

    if not sector and brand:
        sector = brand_profiles.get(brand, {}).get('sector', '')

    fixed = text

    # Fix 1: MSA → Saudi replacements
    for msa, saudi in MSA_REPLACE.items():
        fixed = fixed.replace(msa, saudi)

    # Fix 2: Dedup hashtags + strip excess (keep first 3 unique)
    hashtags = re.findall(r'#[^\s#]+', fixed)
    seen_tags = []
    for tag in hashtags:
        if tag in seen_tags:
            fixed = fixed.replace(tag, '', 1).strip()
        else:
            seen_tags.append(tag)
    if len(seen_tags) > 3:
        for extra_tag in seen_tags[3:]:
            fixed = fixed.replace(extra_tag, '').strip()

    # Fix 3: Strip excess emojis by sector
    emoji_limit = SECTOR_EMOJI_LIMITS.get(sector, 3)
    emoji_chars = [c for c in fixed if ord(c) > 0x1F000]
    if len(emoji_chars) > emoji_limit:
        for extra_emoji in emoji_chars[emoji_limit:]:
            fixed = fixed.replace(extra_emoji, '', 1)

    # Fix 4: Product name (if wrong → correct)
    product_data = brand_product_names.get(brand, {})
    correct = product_data.get('correct', '')
    wrong_list = product_data.get('wrong', [])
    if correct and isinstance(wrong_list, list):
        for wrong in wrong_list:
            if isinstance(wrong, str) and wrong.lower() in fixed.lower():
                fixed = re.sub(wrong, correct, fixed, flags=re.IGNORECASE)

    return fixed.strip()


def log_mistake(brand: str, score: int, mistake: str):
    """Log a quality failure to learning store."""
    entry = {
        'handle': brand,
        'score': score,
        'mistake': mistake,
        'timestamp': datetime.now().isoformat(),
    }
    LEARNING_STORE.parent.mkdir(exist_ok=True)
    with open(LEARNING_STORE, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def get_recent_mistakes(brand: str = None, limit: int = 10) -> list:
    """Read recent content quality mistakes from learning store.

    Filters out runtime errors (timeouts, HTTP errors) — only returns
    real content quality failures where score > 0 and mistake is a
    human-readable content lesson, not an exception trace.
    """
    if not LEARNING_STORE.exists():
        return []
    lines = LEARNING_STORE.read_text().strip().split('\n')
    entries = [json.loads(l) for l in lines if l.strip()]

    # Filter to real content failures only
    def is_content_failure(e: dict) -> bool:
        score = e.get('score', 0)
        mistake = e.get('mistake', '')
        # Skip runtime errors — not content lessons
        if score == 0:
            return False
        if any(kw in mistake for kw in ('TimeoutError', 'HTTP Error', 'exception:', 'api_error:')):
            return False
        return True

    content_failures = [e for e in entries if is_content_failure(e)]

    # Brand-relevant mistakes first, then others
    if brand:
        relevant = [e for e in content_failures if e.get('handle') == brand]
        other    = [e for e in content_failures if e.get('handle') != brand]
        content_failures = relevant + other

    return content_failures[-limit:]


# ── CLI test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    test_caption = sys.argv[1] if len(sys.argv) > 1 else "الآن #بيكيز_حراق الجديد من #البيك 🔥"
    brand = sys.argv[2] if len(sys.argv) > 2 else "albaik"
    occasion = sys.argv[3] if len(sys.argv) > 3 else "evergreen"

    result = check(test_caption, brand=brand, occasion=occasion)
    print(f"\nCaption: {test_caption}")
    print(f"Brand: {brand} | Occasion: {occasion}")
    print(f"\nScore: {result['score']}/100 | Passed: {result['passed']} | Confidence: {result['confidence']}")
    if result['hard_blocked']:
        print("⛔ HARD BLOCKED")
    print("\nChecks:")
    for c in result['checks']:
        icon = "✅" if c['passed'] else "❌"
        print(f"  {icon} {c['check']:20} (w={c['weight']:2}) — {c['detail']}")
    if result['fixes_needed']:
        print(f"\nFixes needed: {result['fixes_needed']}")
        fixed = auto_fix(test_caption, brand=brand)
        print(f"After auto-fix: {fixed}")
