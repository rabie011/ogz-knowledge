#!/usr/bin/env python3
"""
build_product_names.py — Extract correct/wrong product names for all 23 brands.

Only updates brands that don't already have a `correct` field.
Keeps albaik, pizzahutsaudi, barnscoffee untouched (already curated).

Usage:
    python3 scripts/build_product_names.py          # run + update intelligence_layer.json
    python3 scripts/build_product_names.py --verify # verify all 23 brands have correct field
    python3 scripts/build_product_names.py --dry-run # show what would be added, don't write

Mohamed can verify the result with:
    python3 -c "
    import json
    b = json.load(open('11_who_to_learn_from/intelligence_layer.json'))
    for brand, data in b['brand_product_names'].items():
        status = '✅' if data.get('correct') else '❌'
        print(status, brand, '→', data.get('correct', 'MISSING'))
    "
"""
from __future__ import annotations
import argparse, json, glob, re, sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRAIN_PATH = REPO / "11_who_to_learn_from" / "intelligence_layer.json"
OBS_DIR = REPO / "11_who_to_learn_from" / "observations"

# Brands already curated — don't touch these
CURATED = {"albaik", "pizzahutsaudi", "barnscoffee"}

# Known product names for brands where auto-extraction is unreliable
# (international brands with mostly English captions, or low obs count)
KNOWN_PRODUCT_NAMES: dict[str, dict] = {
    "zara":             {"correct": "أزياء", "also_correct": ["زارا"], "wrong": ["zara", "clothes"], "confidence": "curated"},
    "hm":               {"correct": "أزياء", "also_correct": ["إتش آند إم"], "wrong": ["hm", "clothes"], "confidence": "curated"},
    "randbfashion":     {"correct": "ملابس", "also_correct": ["أزياء"], "wrong": ["fashion", "clothing"], "confidence": "curated"},
    "aldeebajofficial": {"correct": "الديباج", "also_correct": ["عبايات"], "wrong": ["deebaj", "abaya"], "confidence": "curated"},
    "lifestyleshops":   {"correct": "لايف ستايل", "also_correct": [], "wrong": ["lifestyle"], "confidence": "curated"},
    "gissahperfumes":   {"correct": "عطر", "also_correct": ["قصة"], "wrong": ["perfume", "fragrance"], "confidence": "curated"},
    # Fix bad auto-extractions
    "maxfashionmena":   {"correct": "إطلالات", "also_correct": ["أزياء", "ماكس"], "wrong": ["maxfashion", "fashion"], "confidence": "curated"},
    "riyadhfood":       {"correct": "وجبة", "also_correct": ["طعام"], "wrong": ["riyadhfood", "food"], "confidence": "curated"},
    "asteribeautysa":   {"correct": "روج", "also_correct": ["مكياج", "ليب"], "wrong": ["lip", "shine", "asterie"], "confidence": "curated"},
}

# Arabic stopwords + generic words to exclude from product name extraction
ARABIC_STOPWORDS = {
    "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "ذلك", "تلك",
    "كل", "بعض", "قد", "لا", "ما", "كان", "كانت", "يكون", "تكون",
    "الآن", "الحين", "يالله", "الله", "سبحان", "الحمد", "نحن",
    "أنا", "أنت", "هو", "هي", "نعم", "طيب", "حلو", "خطير", "زين",
    "جديد", "جديدة", "حصري", "حصرياً", "متوفر", "متاح", "الآن",
    "اطلب", "اطلبه", "جرب", "جربه", "شوف", "وش", "ايش", "كذا",
    "فقط", "اليوم", "غداً", "أحسن", "أفضل", "عروض", "خصم", "سعر",
    "فرع", "فروع", "افتتاح", "موعد", "وقت",
}

# Common English words to map to Arabic wrong-list equivalents
ENGLISH_PRODUCT_PATTERNS = re.compile(r'\b[a-zA-Z]{3,}\b')


def load_obs_for_brand(handle: str) -> list[dict]:
    """Load all obs files for a given account handle, sorted by likes desc."""
    obs = []
    for sector_dir in OBS_DIR.iterdir():
        if not sector_dir.is_dir():
            continue
        for f in sector_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                if d.get("account_handle_normalized") == handle:
                    obs.append(d)
            except Exception:
                pass
    # Sort by likes_count descending (real metrics first)
    obs.sort(key=lambda x: (
        x.get("content_ref", {}).get("likes_count") or
        x.get("likes_count") or 0
    ), reverse=True)
    return obs


def extract_arabic_words(text: str) -> list[str]:
    """Extract Arabic words from caption text, excluding stopwords."""
    if not text:
        return []
    # Match Arabic word sequences
    arabic_words = re.findall(r'[؀-ۿ]+', text)
    # Filter: length ≥ 3, not stopword, not just numbers
    filtered = [
        w for w in arabic_words
        if len(w) >= 3 and w not in ARABIC_STOPWORDS and not w.isdigit()
    ]
    return filtered


def extract_english_words(text: str) -> list[str]:
    """Extract English words that appear in Arabic captions (likely brand/product terms)."""
    if not text:
        return []
    words = ENGLISH_PRODUCT_PATTERNS.findall(text)
    # Filter very common English words
    common_english = {"the", "and", "for", "with", "this", "that", "from", "our",
                      "new", "now", "get", "buy", "order", "visit", "check"}
    return [w.lower() for w in words if w.lower() not in common_english and len(w) >= 3]


def get_brand_product_names(handle: str, obs: list[dict]) -> dict:
    """
    Extract product names from a brand's observations.
    Uses top 30 captions by likes to find the most common product words.
    """
    if not obs:
        return {
            "correct": None,
            "wrong": [],
            "note": f"No observations found for @{handle}",
            "source": "auto_extracted",
            "confidence": "low"
        }

    # Get captions from top 30 obs
    top_obs = obs[:30]
    all_arabic_words = []
    all_english_words = []

    for o in top_obs:
        caption = o.get("voice_observations", {}).get("caption_text", "")
        if caption:
            all_arabic_words.extend(extract_arabic_words(caption))
            all_english_words.extend(extract_english_words(caption))

    if not all_arabic_words:
        # Try lower-engagement obs if top have no captions
        for o in obs[:50]:
            caption = o.get("voice_observations", {}).get("caption_text", "")
            if caption:
                all_arabic_words.extend(extract_arabic_words(caption))
                all_english_words.extend(extract_english_words(caption))

    # Count frequency
    arabic_counter = Counter(all_arabic_words)
    english_counter = Counter(all_english_words)

    # Remove the brand handle itself from results
    handle_clean = handle.replace("ksa", "").replace("sa", "").replace("saudi", "")
    arabic_counter.pop(handle_clean, None)
    arabic_counter.pop(handle, None)

    # Top 5 most common Arabic product words
    top_arabic = [w for w, _ in arabic_counter.most_common(10)
                  if len(w) >= 3 and w not in ARABIC_STOPWORDS][:5]

    # Top 3 most common English words (likely wrong product names to avoid)
    top_english = [w for w, _ in english_counter.most_common(5)][:3]

    # Primary correct = most common Arabic product word in top captions
    correct = top_arabic[0] if top_arabic else None
    also_correct = top_arabic[1:3] if len(top_arabic) > 1 else []
    wrong = top_english if top_english else []

    confidence = "medium" if len(top_obs) >= 10 and correct else "low"

    return {
        "correct": correct,
        "also_correct": also_correct,
        "wrong": wrong,
        "note": f"Auto-extracted from top {len(top_obs)} captions by likes. "
                f"Review and curate manually for best quality gate results.",
        "source": "auto_extracted_from_obs",
        "confidence": confidence
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Just verify, don't write")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written")
    args = parser.parse_args()

    brain = json.loads(BRAIN_PATH.read_text())
    product_names = brain.get("brand_product_names", {})
    real_metrics = brain.get("real_metrics", {})

    # Only process verified brands
    all_handles = list(real_metrics.keys())

    if args.verify:
        print("=== PRODUCT NAME VERIFICATION ===")
        missing = []
        for handle in all_handles:
            data = product_names.get(handle, {})
            status = "✅" if data.get("correct") else "❌"
            correct = data.get("correct", "MISSING")
            print(f"  {status} @{handle} → {correct}")
            if not data.get("correct"):
                missing.append(handle)
        print(f"\n{'✅ ALL COMPLETE' if not missing else f'❌ MISSING: {missing}'}")
        print(f"Total: {len(all_handles)} brands | Complete: {len(all_handles)-len(missing)} | Missing: {len(missing)}")
        return

    updated = []
    skipped = []

    for handle in all_handles:
        current = product_names.get(handle, {})

        # Use hardcoded known names if available
        if handle in KNOWN_PRODUCT_NAMES:
            known = KNOWN_PRODUCT_NAMES[handle]
            known["note"] = "Manually curated — auto-extraction was unreliable for this brand."
            known["source"] = "manual_curation"
            print(f"  [KNOWN] @{handle} → correct='{known['correct']}' (curated)")
            if not args.dry_run:
                product_names[handle] = known
                updated.append(handle)
            else:
                print(f"    [DRY RUN] Would write: {known}")
            continue

        # Skip already curated
        if handle in CURATED:
            skipped.append(handle)
            print(f"  [SKIP] @{handle} — already curated")
            continue

        # Skip if already has correct field
        if current.get("correct"):
            skipped.append(handle)
            print(f"  [SKIP] @{handle} — already has correct: {current['correct']}")
            continue

        print(f"  [PROCESSING] @{handle}...", end=" ", flush=True)
        obs = load_obs_for_brand(handle)
        result = get_brand_product_names(handle, obs)

        print(f"correct='{result['correct']}' wrong={result['wrong']} "
              f"confidence={result['confidence']} ({len(obs)} obs)")

        if args.dry_run:
            print(f"    [DRY RUN] Would write: {result}")
        else:
            product_names[handle] = result
            updated.append(handle)

    if not args.dry_run:
        # Write back to brain
        brain["brand_product_names"] = product_names
        BRAIN_PATH.write_text(json.dumps(brain, ensure_ascii=False, indent=2))
        print(f"\n✅ Updated {len(updated)} brands in intelligence_layer.json")
        print(f"   Skipped (already complete): {len(skipped)}")

        # Verify after write
        print("\n=== VERIFICATION ===")
        brain2 = json.loads(BRAIN_PATH.read_text())
        missing_after = [h for h in all_handles if not brain2["brand_product_names"].get(h, {}).get("correct")]
        if missing_after:
            print(f"❌ Still missing correct field: {missing_after}")
            sys.exit(1)
        else:
            print(f"✅ All {len(all_handles)} brands have correct field")

    print("\nMohamed can verify with:")
    print("  python3 scripts/build_product_names.py --verify")


if __name__ == "__main__":
    main()
