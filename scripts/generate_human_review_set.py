#!/usr/bin/env python3
"""
generate_human_review_set.py
OGZ Knowledge Base — human validation set generator.

Generates 50 Arabic content outputs for Mohamed to manually review and rate.
This is the human validation step the automated quality gate cannot perform.

Usage:
    python3 scripts/generate_human_review_set.py

Output: logs/system/HUMAN_REVIEW_SET.md
"""
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE     = Path(__file__).parent.parent
LOG_DIR  = BASE / "logs" / "system"
OUT_FILE = LOG_DIR / "HUMAN_REVIEW_SET.md"

API_URL  = "http://localhost:4100/api/create"
TIMEOUT  = 20  # seconds per request

# ---------------------------------------------------------------------------
# 50 combos — coverage requirements:
#   Sectors : f_and_b ≥10, fashion ≥8, retail ≥8, beauty ≥8,
#             real_estate ≥8, healthcare ≥8
#   Occasions: all 10 must appear at least once
#   Brands  : mix of strong (albaik, zara) AND weak (randbfashion, roshnksa,
#             gissahperfumes)
#
# Format: (brand, product_arabic, occasion, sector, note)
# ---------------------------------------------------------------------------
COMBOS = [
    # ── F&B (10) ────────────────────────────────────────────────────────────
    ("albaik",           "بروستد",               "founding_day",  "f_and_b",      "strong"),
    ("albaik",           "برجر",                 "national_day",  "f_and_b",      "strong"),
    ("albaik",           "حلقات بصل",            "evergreen",     "f_and_b",      "strong"),
    ("barnscoffee",      "قهوة مثلجة",           "ramadan",       "f_and_b",      "strong"),
    ("barnscoffee",      "كيك الشوكولاتة",       "eid",           "f_and_b",      "strong"),
    ("mcdonaldsksa",     "ماك فراييز",            "summer",        "f_and_b",      "strong"),
    ("mcdonaldsksa",     "بيج ماك",              "back_to_school", "f_and_b",      "strong"),
    ("altazaj_fakieh",   "دجاج مشوي",            "weekend",       "f_and_b",      "strong"),
    ("pizzahutsaudi",    "بيتزا سبريم",          "new_year",      "f_and_b",      "strong"),
    ("kyancafe",         "قهوة ترك",             "winter",        "f_and_b",      "strong"),

    # ── Fashion (8) ─────────────────────────────────────────────────────────
    ("zara",             "جاكيت جلد",            "winter",        "fashion",      "strong"),
    ("zara",             "فستان صيفي",           "summer",        "fashion",      "strong"),
    ("hm",               "تيشيرت أساسي",         "evergreen",     "fashion",      "strong"),
    ("hm",               "بنطلون جينز",          "back_to_school","fashion",      "strong"),
    ("maxfashionmena",   "عباءة كلاسيكية",       "ramadan",       "fashion",      "strong"),
    ("maxfashionmena",   "ثوب رسمي",             "eid",           "fashion",      "strong"),
    ("kiabiksa",         "حذاء رياضي",           "national_day",  "fashion",      "strong"),
    ("randbfashion",     "فستان سهرة",           "new_year",      "fashion",      "weak"),

    # ── Retail (8) ──────────────────────────────────────────────────────────
    ("pandasaudi",       "عرض أسبوعي",           "ramadan",       "retail",       "strong"),
    ("pandasaudi",       "منتجات طازجة",         "founding_day",  "retail",       "strong"),
    ("tamimimarkets",    "تخفيضات العيد",        "eid",           "retail",       "strong"),
    ("tamimimarkets",    "سلة رمضان",            "ramadan",       "retail",       "strong"),
    ("mumzworld",        "مستلزمات أطفال",       "back_to_school","retail",       "strong"),
    ("mumzworld",        "عربة أطفال",           "evergreen",     "retail",       "strong"),
    ("elixirbunn",       "قهوة خام",             "weekend",       "retail",       "strong"),
    ("riyadhfood",       "وجبة عائلية",          "national_day",  "retail",       "strong"),

    # ── Beauty (8) ──────────────────────────────────────────────────────────
    ("mikyajy",          "كريم مرطب",            "summer",        "beauty",       "strong"),
    ("mikyajy",          "عطر نسائي",            "eid",           "beauty",       "strong"),
    ("mikyajy",          "أحمر شفاه",            "ramadan",       "beauty",       "strong"),
    ("asteribeautysa",   "سيروم للبشرة",         "evergreen",     "beauty",       "strong"),
    ("asteribeautysa",   "كريم ليلي",            "winter",        "beauty",       "strong"),
    ("asteribeautysa",   "ماسك وجه",             "weekend",       "beauty",       "strong"),
    ("gissahperfumes",   "عطر عود",              "founding_day",  "beauty",       "weak"),
    ("gissahperfumes",   "بخور فاخر",            "winter",        "beauty",       "weak"),

    # ── Real Estate (8) ─────────────────────────────────────────────────────
    ("roshnksa",         "فيلا عائلية",          "founding_day",  "real_estate",  "weak"),
    ("roshnksa",         "شقة في القدية",        "national_day",  "real_estate",  "weak"),
    ("roshnksa",         "حي سدير",              "evergreen",     "real_estate",  "weak"),
    ("roshnksa",         "حي المسقاط",           "summer",        "real_estate",  "weak"),
    ("roshnksa",         "وحدة سكنية",           "new_year",      "real_estate",  "weak"),
    ("roshnksa",         "مجمع تجاري",           "eid",           "real_estate",  "weak"),
    ("roshnksa",         "أرض سكنية",            "back_to_school","real_estate",  "weak"),
    ("roshnksa",         "مشروع نيوم",           "ramadan",       "real_estate",  "weak"),

    # ── Healthcare (8) ──────────────────────────────────────────────────────
    ("myfitness.sa",     "اشتراك شهري",          "new_year",      "healthcare",   "weak"),
    ("myfitness.sa",     "جلسة يوغا",            "evergreen",     "healthcare",   "weak"),
    ("myfitness.sa",     "برنامج تخسيس",         "summer",        "healthcare",   "weak"),
    ("myfitness.sa",     "تمرين كارديو",         "back_to_school","healthcare",   "weak"),
    ("myfitness.sa",     "تغذية صحية",           "ramadan",       "healthcare",   "weak"),
    ("myfitness.sa",     "اشتراك سنوي",          "national_day",  "healthcare",   "weak"),
    ("myfitness.sa",     "حصة رياضية",           "founding_day",  "healthcare",   "weak"),
    ("myfitness.sa",     "تحدي ٣٠ يوم",         "winter",        "healthcare",   "weak"),
]

# Sanity check: exactly 50 combos
assert len(COMBOS) == 50, f"Expected 50 combos, got {len(COMBOS)}"

# Verify sector counts meet minimums
from collections import Counter
sector_counts    = Counter(c[3] for c in COMBOS)
occasion_counts  = Counter(c[2] for c in COMBOS)
all_10_occasions = {"evergreen", "ramadan", "eid", "founding_day", "national_day",
                    "summer", "winter", "new_year", "back_to_school", "weekend"}

assert sector_counts["f_and_b"]     >= 10, f"f_and_b only {sector_counts['f_and_b']}"
assert sector_counts["fashion"]     >=  8, f"fashion only {sector_counts['fashion']}"
assert sector_counts["retail"]      >=  8, f"retail only {sector_counts['retail']}"
assert sector_counts["beauty"]      >=  8, f"beauty only {sector_counts['beauty']}"
assert sector_counts["real_estate"] >=  8, f"real_estate only {sector_counts['real_estate']}"
assert sector_counts["healthcare"]  >=  8, f"healthcare only {sector_counts['healthcare']}"

missing_occasions = all_10_occasions - set(occasion_counts.keys())
assert not missing_occasions, f"Missing occasions: {missing_occasions}"


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def call_api(brand: str, product: str, occasion: str) -> dict | None:
    payload = json.dumps({"brand": brand, "product": product, "occasion": occasion}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"  [HTTP {e.code}] {brand}/{occasion} — {body[:120]}", flush=True)
        return None
    except urllib.error.URLError as e:
        print(f"  [URLError] {brand}/{occasion} — {e.reason}", flush=True)
        return None
    except Exception as e:
        print(f"  [Error] {brand}/{occasion} — {e}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Markdown block builder
# ---------------------------------------------------------------------------
def build_block(idx: int, brand: str, product: str, occasion: str,
                sector: str, strength: str, data: dict) -> str:
    quality   = data.get("quality", {})
    score     = quality.get("score", "—")
    tier      = quality.get("template_tier", "—")
    confidence = quality.get("confidence", "—")

    content   = data.get("content", {})
    caption   = content.get("caption", "—")
    hashtags  = content.get("hashtags", [])
    hashtag_str = " ".join(hashtags) if hashtags else "—"

    proof     = data.get("proof", {})
    template_url = proof.get("template_url") or "—"
    brand_metrics = proof.get("brand_metrics") or "—"

    strength_label = f"[{strength.upper()} BRAND]"

    lines = [
        f"## Review {idx:03d} — {brand} | {occasion} | {sector} {strength_label}",
        f"Score: {score} | Tier: {tier} | Confidence: {confidence}",
        f"Brand metrics: {brand_metrics}",
        f"Template: {template_url}",
        "",
        f"**Product:** {product}",
        "",
        "**Arabic output:**",
        caption,
        "",
        f"**Hashtags:** {hashtag_str}",
        "",
        "**Rate this (Mohamed fills in):**",
        "[ ] Excellent — sounds like a real Saudi brand",
        "[ ] Good — minor issues",
        "[ ] Weak — doesn't sound Saudi",
        "[ ] Fail — wrong language/brand/occasion",
        "Notes: ___",
        "---",
    ]
    return "\n".join(lines)


def build_error_block(idx: int, brand: str, product: str, occasion: str,
                      sector: str, strength: str) -> str:
    lines = [
        f"## Review {idx:03d} — {brand} | {occasion} | {sector} [ERROR]",
        "Score: — | Tier: — | Confidence: —",
        "",
        f"**Product:** {product}",
        "",
        "**Arabic output:** API call failed — skipped.",
        "",
        "---",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    errors    = 0
    blocks    = []

    print(f"OGZ Human Review Set Generator", flush=True)
    print(f"Target: {len(COMBOS)} combos → {OUT_FILE}", flush=True)
    print(f"API: {API_URL}", flush=True)
    print("─" * 60, flush=True)

    for i, (brand, product, occasion, sector, strength) in enumerate(COMBOS, start=1):
        label = f"{i:02d}/{len(COMBOS)} {brand} | {occasion} | {sector}"
        print(f"  Generating {label} ...", end=" ", flush=True)

        data = call_api(brand, product, occasion)

        if data is None:
            errors += 1
            blocks.append(build_error_block(i, brand, product, occasion, sector, strength))
            print("ERROR — skipped", flush=True)
            continue

        score = data.get("quality", {}).get("score", "?")
        tier  = data.get("quality", {}).get("template_tier", "?")
        print(f"score={score} tier={tier}", flush=True)

        blocks.append(build_block(i, brand, product, occasion, sector, strength, data))
        generated += 1

    # ── Compose full document ────────────────────────────────────────────────
    header = "\n".join([
        "# OGZ Human Review Set",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total: {generated} generated, {errors} errors",
        "",
        "**Instructions for Mohamed:**",
        "- Read each Arabic caption aloud (or in your head).",
        "- Mark one of the four ratings. Add notes if useful.",
        "- Focus on: does it sound like a REAL Saudi brand?",
        "  Does the occasion feel natural? Is the Arabic authentic?",
        "- You do NOT need to rate skipped (ERROR) entries.",
        "",
        "**Sector breakdown:**",
    ])

    for sector, count in sorted(sector_counts.items()):
        header += f"\n- {sector}: {count}"

    header += "\n\n---\n"

    document = header + "\n\n".join(blocks) + "\n"

    OUT_FILE.write_text(document, encoding="utf-8")

    # ── Terminal summary ─────────────────────────────────────────────────────
    print("─" * 60, flush=True)
    print(f"Generated : {generated}/{len(COMBOS)}", flush=True)
    print(f"Errors    : {errors}", flush=True)
    print(f"Output    : {OUT_FILE}", flush=True)

    if errors > 0:
        print(f"\nWARNING: {errors} combo(s) failed. Review ERROR blocks in output file.", flush=True)
    else:
        print("\nAll combos generated successfully.", flush=True)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
