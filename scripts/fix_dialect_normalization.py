#!/usr/bin/env python3
"""
fix_dialect_normalization.py
Normalize voice_observations.dialect_detected to a controlled vocabulary across all obs JSON.
Edits files in-place. Run validate_all.py after.

Controlled vocab:
  najdi              — Riyadh / Central Saudi
  hejazi             — Jeddah / Mecca / Medina
  gulf               — Gulf coast / Eastern Province / khaleeji
  msa                — Modern Standard Arabic (فصحى)
  colloquial_arabic  — informal Saudi Arabic, unspecified region
  general_saudi      — Saudi but region unspecified / mixed
  english_arabic_mixed — bilingual EN+AR content
  urdu_arabic_mixed  — Pakistani/Urdu-influenced content
  spanish_colloquial — non-Arabic (Tier 4 comparison accounts)
  null               — unknown / not detected
"""
import json
import os

OBS_ROOT = os.path.expanduser("~/Desktop/ogz-knowledge/11_who_to_learn_from/observations")

# Mapping: raw value → normalized value (None = set to null)
NORMALIZATION_MAP = {
    # Already correct — passthrough
    "najdi":                "najdi",
    "hejazi":               "hejazi",
    "gulf":                 "gulf",
    "msa":                  "msa",
    "colloquial_arabic":    "colloquial_arabic",
    "general_saudi":        "general_saudi",
    "english_arabic_mixed": "english_arabic_mixed",
    "urdu_arabic_mixed":    "urdu_arabic_mixed",
    "spanish_colloquial":   "spanish_colloquial",

    # Najdi variants
    "saudi_najdi":                      "najdi",
    "Saudi (Riyadh-based account)":     "najdi",
    "Najdi/Gulf":                       "najdi",   # majority of corpus is Riyadh

    # Gulf / Khaleeji variants
    "khaleeji":             "gulf",
    "Gulf casual":          "gulf",
    "Gulf/Saudi colloquial":"gulf",
    "saudi_gulf_casual":    "gulf",
    "saudi_gulf":           "gulf",
    "MSA/Gulf":             "gulf",

    # MSA variants
    "standard":             "msa",
    "MSA":                  "msa",
    "msa_or_undetected":    "msa",
    "Modern Standard Arabic (MSA)":                             "msa",
    "Modern Standard Arabic with Saudi colloquial elements":    "msa",
    "Modern Standard Arabic (MSA) with brand identity focus":   "msa",
    "Saudi Modern Standard Arabic":                             "msa",
    "formal_modern_standard_arabic":                            "msa",
    "modern_standard_arabic":                                   "msa",
    "saudi_standard":       "msa",

    # Colloquial / general Saudi variants
    "saudi_colloquial":     "colloquial_arabic",
    "saudi_arabic":         "colloquial_arabic",

    # General Saudi (region ambiguous)
    "saudi_modern":         "general_saudi",
    "saudi_general":        "general_saudi",
    "modern_saudi":         "general_saudi",

    # Bilingual
    "modern standard arabic with bilingual english": "english_arabic_mixed",

    # Spanish (Tier 4 anti-pattern accounts)
    "puerto_rican_spanish":             "spanish_colloquial",
    "latin_american_neutral":           "spanish_colloquial",
    "Latin American (Puerto Rico implied by @crumblcookiespr handle)": "spanish_colloquial",

    # Null variants — set field to null
    "none":  None,
    "None":  None,
}

changed = 0
skipped = 0
added_null = 0
errors = []

for sector in sorted(os.listdir(OBS_ROOT)):
    sector_path = os.path.join(OBS_ROOT, sector)
    if not os.path.isdir(sector_path):
        continue
    for fname in sorted(os.listdir(sector_path)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(sector_path, fname)
        with open(fpath) as f:
            try:
                d = json.load(f)
            except Exception as e:
                errors.append(f"READ ERROR {fpath}: {e}")
                continue

        vo = d.get("voice_observations", {})
        if "dialect_detected" not in vo:
            # Field missing — add as null
            vo["dialect_detected"] = None
            d["voice_observations"] = vo
            with open(fpath, "w") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            added_null += 1
            continue

        raw = vo["dialect_detected"]

        # Already null — skip
        if raw is None:
            skipped += 1
            continue

        raw_str = str(raw)
        if raw_str not in NORMALIZATION_MAP:
            # Unknown value — leave as-is, log
            errors.append(f"UNKNOWN dialect '{raw_str}' in {fname}")
            skipped += 1
            continue

        normalized = NORMALIZATION_MAP[raw_str]
        if normalized == raw:
            skipped += 1
            continue

        # Apply normalization
        vo["dialect_detected"] = normalized
        d["voice_observations"] = vo
        with open(fpath, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        changed += 1

print(f"Done.")
print(f"  Changed:    {changed}")
print(f"  Added null: {added_null}")
print(f"  Skipped:    {skipped} (already correct or already null)")
if errors:
    print(f"\nWarnings/Errors ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
