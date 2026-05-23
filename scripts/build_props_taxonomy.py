#!/usr/bin/env python3
"""
build_props_taxonomy.py
Reads all visual_observations.props_visible across 474 obs, classifies each
unique prop mention into one of 15 canonical categories, outputs count/top
terms/avg engagement per category.
Output: logs/props_taxonomy.json
"""
import json
import re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)

ENG_MAP = {
    "high": 1.0,
    "very_high": 1.0,
    "above_average": 0.75,
    "medium": 0.5,
    "low": 0.0,
    "below_average": 0.25,
}

# Ordered list of (category, keyword_fragments).
# First match wins. Longer/more specific patterns first to avoid false positives.
TAXONOMY_RULES = [
    ("vessel_traditional", [
        "dallah", "ibrik", "gahwa pot", "coffee pot", "clay pot", "clay jug",
        "copper pot", "copper dallah", "copper kettle", "copper jug",
        "brass pot", "brass dallah", "tin pot", "tin kettle",
        "teapot", "tea pot", "traditional pot", "traditional cup",
        "finjan", "demitasse", "arabic coffee cup", "arabic cup",
        "small cup", "traditional mug",
    ]),
    ("vessel_modern", [
        "glass", "cup", "mug", "bowl", "plate", "dish",
        "jar", "bottle", "pitcher", "jug", "flask",
        "ceramic", "porcelain", "stoneware", "ramekin", "terracotta",
        "container", "carton", "tin can", "serving dish",
        "platter", "saucer", "spoon", "fork", "knife", "cutlery",
        "utensil", "straw", "lid", "condiment holder",
        "beverage glass", "drinking glass", "serving bowl",
    ]),
    ("textile", [
        "fabric", "cloth", "textile", "embroidery", "embroidered",
        "thoub", "thobe", "abaya", "scarf", "shawl", "shmagh",
        "keffiyeh", "ghutrah", "kandura", "bisht",
        "linen", "cotton", "silk", "velvet", "weave", "woven",
        "pattern cloth", "patterned fabric", "table cloth", "tablecloth",
        "napkin", "runner", "clothing", "outfit", "uniform",
        "doctor coat", "chef coat", "apron", "coat", "shirt",
        "dress", "casual wear",
    ]),
    ("wood_natural", [
        "wooden tray", "wooden board", "wooden plate", "wooden spoon",
        "wooden bowl", "wooden block", "wooden surface", "wooden table",
        "wooden chair", "wooden bench", "wooden shelf",
        "cutting board", "chopping board", "serving board", "cheese board",
        "wood plank", "wood log", "bamboo", "rattan",
    ]),
    ("herbs_spices", [
        "herb", "mint", "saffron", "cardamom", "cinnamon", "spice",
        "pepper", "basil", "rosemary", "thyme", "turmeric", "baharat",
        "clove", "anise", "fennel", "cumin", "coriander", "bay leaf",
        "dried herb", "fresh herb", "parsley", "dill", "oregano",
        "sumac", "zaatar", "za'atar", "nigella", "black seed",
        "coffee bean", "scattered bean",
    ]),
    ("fresh_produce", [
        "fruit", "vegetable", "dates", "date", "tomato", "lemon",
        "lime", "orange", "pomegranate", "fig", "grape", "apple",
        "strawberry", "mango", "melon", "watermelon", "berry",
        "lettuce", "cucumber", "onion", "garlic", "avocado",
        "fresh produce", "seasonal fruit", "fresh juice", "juice",
        "potato", "fries", "french fries",
    ]),
    ("bread_grain", [
        "bread", "rice", "grain", "wheat", "pita", "khubz",
        "flatbread", "cracker", "baguette", "sourdough", "naan",
        "flour", "dough", "loaf", "roll", "bun", "sandwich",
        "burger", "pizza", "wrap", "toast",
    ]),
    ("meat_protein", [
        "meat", "chicken", "fish", "lamb", "beef", "shrimp",
        "prawn", "salmon", "steak", "kabsa", "machboos", "grilled",
        "kebab", "shawarma", "kofta", "protein", "egg", "poultry",
        "fried chicken", "grilled meat", "chicken sandwich",
    ]),
    ("sauce_condiment", [
        "sauce", "dip", "honey", "jam", "hummus", "tahini",
        "dressing", "mayo", "ketchup", "vinegar", "pickle", "chutney",
        "ghee", "butter", "cream cheese", "labneh", "yogurt", "laban",
        "syrup", "drizzle", "spread",
    ]),
    ("dessert_sweet", [
        "sweet", "dessert", "pastry", "baklawa", "baklava", "cake",
        "cookie", "pudding", "cream", "chocolate", "caramel", "kunafa",
        "luqaimat", "halwa", "maamoul", "knafeh", "qatayef", "basbousa",
        "macaron", "tart", "eclair", "truffle", "sugar", "confection",
        "ice cream", "powdered sugar", "gold confetti",
    ]),
    ("furniture_prop", [
        "chair", "table", "cushion", "sofa", "stool", "mat",
        "carpet", "rug", "shelf", "counter", "bench", "tray stand",
        "prop stand", "display stand", "display table", "tiered display",
        "display", "flat lay", "pool", "window", "wall", "door", "floor",
        "kitchen", "setting",
    ]),
    ("candle_light", [
        "candle", "lantern", "flame", "incense", "bakhoor", "bukhoor",
        "oud", "candelabra", "fairy light", "string light", "glow",
        "sparkle", "match", "lighter", "ramadan lantern",
        "crescent moon", "moon", "ramadan crescent", "steam",
    ]),
    ("brand_signage", [
        "logo", "packaging", "package", "box", "label", "sign",
        "banner", "badge", "tag", "wrapper", "paper bag", "cup sleeve",
        "brand", "sticker", "stamp", "seal", "certificate",
        "menu", "card", "brochure", "signage", "branded",
        "branding", "flag", "illustrated", "illustration",
        "product lineup", "product line", "product",
    ]),
    ("person_accessory", [
        "hand", "watch", "jewelry", "ring", "bracelet", "necklace",
        "glove", "nail", "finger", "wrist", "arm", "earring", "accessory",
        "sunglasses", "glasses", "lip", "lips", "makeup", "brush",
        "foundation", "swatch", "face", "skin", "beauty tool",
    ]),
    ("outdoor_nature", [
        "plant", "sand", "stone", "rock", "flower", "leaf", "grass",
        "branch", "earth", "soil", "petal", "cactus", "tree", "bush",
        "nature", "outdoor", "sky", "water", "river", "mountain",
        "potted plant", "palm tree", "stadium", "architectural",
    ]),
]


def classify_prop(raw: str) -> str:
    """Return the first matching taxonomy category, or 'other'."""
    # normalize underscores (common in auto-tagged props) and collapse whitespace
    norm = raw.lower().replace("_", " ").strip()
    norm = re.sub(r"\s+", " ", norm)
    for category, keywords in TAXONOMY_RULES:
        for kw in keywords:
            # leading word-boundary match (covers plurals: "plate" matches "plates")
            if re.search(r'\b' + re.escape(kw), norm):
                return category
    return "other"


def load_obs(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main():
    all_files = list(OBS_ROOT.glob("**/*.json"))
    print(f"Found {len(all_files)} observation files")

    # category → list of (raw_prop, eng_score) tuples
    cat_entries: dict[str, list[tuple[str, float | None]]] = defaultdict(list)
    # unique normalized props → category (for dedup reporting)
    unique_props: dict[str, str] = {}

    total_prop_mentions = 0

    for fpath in sorted(all_files):
        obs = load_obs(fpath)
        if not obs:
            continue

        props = obs.get("visual_observations", {}).get("props_visible", [])
        if not isinstance(props, list):
            continue

        eng_raw = (
            obs.get("quality_assessment", {})
               .get("engagement_potential", "")
               .lower()
               .strip()
        )
        eng_score = ENG_MAP.get(eng_raw)

        for raw_prop in props:
            if not isinstance(raw_prop, str) or not raw_prop.strip():
                continue
            total_prop_mentions += 1
            norm = raw_prop.strip().lower()
            cat = classify_prop(norm)
            if norm not in unique_props:
                unique_props[norm] = cat
            cat_entries[cat].append((norm, eng_score))

    print(f"Total prop mentions: {total_prop_mentions}")
    print(f"Unique normalized props: {len(unique_props)}")

    # Build output per category
    all_cats = [cat for cat, _ in TAXONOMY_RULES] + ["other"]
    output = {"meta": {
        "total_prop_mentions": total_prop_mentions,
        "unique_props": len(unique_props),
        "categories": len(all_cats),
    }, "taxonomy": {}}

    for cat in all_cats:
        entries = cat_entries.get(cat, [])
        count = len(entries)

        # Top raw terms by frequency
        term_freq: dict[str, int] = defaultdict(int)
        for raw, _ in entries:
            term_freq[raw] += 1
        top_terms = sorted(term_freq.items(), key=lambda x: -x[1])[:20]

        # Avg engagement (exclude None)
        eng_scores = [s for _, s in entries if s is not None]
        avg_eng = round(sum(eng_scores) / len(eng_scores), 3) if eng_scores else None

        output["taxonomy"][cat] = {
            "count": count,
            "unique_terms": len(term_freq),
            "avg_engagement": avg_eng,
            "top_terms": [{"term": t, "freq": f} for t, f in top_terms],
        }
        print(f"  {cat:25s}  {count:4d} mentions  avg_eng={avg_eng}")

    out_path = LOGS / "props_taxonomy.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
