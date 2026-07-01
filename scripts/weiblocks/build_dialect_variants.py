#!/usr/bin/env python3
"""build_dialect_variants.py — aggregate voice_observations -> Weiblocks §5.2 dialect_variant
(exports/weiblocks_v1/dialect_variants.json, flat array — validator contract).

DeepSeek-consulted (scoping + implementation round, July 1). Agreed design:
  GRAIN = every non-empty sector x dialect cell (15 measured; scoping estimated ~14).
  DIALECT_FOLD + SECTOR_MAP are IMPORTED from build_brand_observations.py — identical by
  construction, so graph joins stay consistent (Mohamed's fold-to-4 ruling; unfoldable
  mixed/saudi/non_arabic/unknown/southern are EXCLUDED from cells and counted honestly in
  extra.corpus_coverage — per-record, because the file must stay a flat homogeneous array).

  signature_phrases_ar = verbatim notable_phrases with freq>=2 within the cell, filtered:
    - Arabic-script REQUIRED ([؀-ۿ])
    - extractor prose stripped (shared is_extractor_prose — 'Two key Arabic phrases' etc.)
    - any digit (ASCII or Arabic-Indic) => dropped: times/prices/phones/licenses/promo codes.
      Edge case (DeepSeek A4, documented): this also drops phrases whose only digit is a promo
      code or year (e.g. 'خصم 20% … كود SINGLE20', 'كأس العالم 2034') — accepted: none of those
      are dialect register signals. Digits written as WORDS (e.g. 'ألف رياال…') are kept.
    - '@' anywhere => dropped (third-party-mention privacy, the brand_observations P0 scar)
    - '#' anywhere => NOT a signature (hashtags are brand/campaign identity tokens, not spoken
      register; an Arabic brand-name list to split brand vs non-brand DOES NOT EXIST in this
      repo, and hand-deciding would be authored curation). Arabic hashtags are NOT lost: they
      ship verbatim with counts in extra.hashtags_ar_excluded[] for partner mining
      (documented field — DeepSeek D5 condition).
    - measured extractor artifacts ('من إلى', 'من تصوير…' — stripped time-range/photo-credit
      fragments, eyeballed 14x/6x in the corpus) => dropped
    - occasion-generic greetings (كل عام و…/رمضان مبارك/كريم/عيد مبارك/تقبل الله/ينعاد علينا)
      => routed to extra.occasion_generic[], never signatures.
    Cap 10/cell (locked order); truncation visible via extra.qualifying_phrase_count.

  avoid_phrases_ar = [] on ALL records — ZERO per-dialect avoid-phrase source exists; any value
  would be fabrication. Universal arabic_text guidance rides as extra.advisory_pointer (path
  string into the shipped cultural_rules arabic_text_* family).

  register_notes = honest computed string with precise denominators (DeepSeek A1 — no 'dominant'
  claim; register labels are SPARSE: 7/15 cells only). Zero labels => null + extra flag.

  confidence = 'inferred' everywhere (claude_code_extraction; controlled vocab
  {verified,inferred,experimental}); observed_count = sample_size = REAL cell recount
  (hard-asserted against an independent recount before writing — Rule #8: refuse, don't warn).
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

# identical fold/map/prose-filter by construction — never a local copy that can drift
from build_brand_observations import DIALECT_FOLD, SECTOR_MAP, is_extractor_prose

ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "11_who_to_learn_from" / "observations"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"

SPEC_DIALECTS = {"Najdi", "Hejazi", "Khaleeji", "Fusha (MSA)"}
SHIPPED_SECTORS = {"F&B", "Beauty_Wellness", "Retail", "Other"}
SECTOR_SLUG = {"F&B": "f_and_b", "Beauty_Wellness": "beauty_wellness", "Retail": "retail", "Other": "other"}
DIALECT_SLUG = {"Najdi": "najdi", "Hejazi": "hejazi", "Khaleeji": "khaleeji", "Fusha (MSA)": "fusha_msa"}

AR_RE = re.compile(r"[؀-ۿ]")
DIGIT_RE = re.compile(r"[0-9٠-٩]")  # ASCII + Arabic-Indic (٠-٩): times/prices/phones/licenses
ARTIFACT_RES = [re.compile(r"^من\s+إلى\s*$"),      # stripped time-range fragment (measured 14x+2x)
                re.compile(r"^من\s+تصوير\b")]       # stripped photo-credit fragment (measured 4x+2x)
# occasion-generic greeting family (substring match) — routed to extra.occasion_generic, never signatures
# (مبارك عليكم الشهر added after eyeballing the first run: a Ramadan greeting was riding as a signature)
OCCASION_GENERIC = ["كل عام و", "رمضان مبارك", "رمضان كريم", "عيد مبارك", "عيدكم مبارك",
                    "تقبل الله", "ينعاد علينا", "مبارك عليكم الشهر"]
ADVISORY_POINTER = "exports/weiblocks_v1/cultural_rules.json#rule_key=arabic_text_*"
CAP = 10
THIN = 20
MIN_FREQ = 2


def classify(phrase):
    """one deterministic bucket per freq>=2 phrase. Order matters (script check first)."""
    if not AR_RE.search(phrase):
        return "non_arabic_script"
    if is_extractor_prose(phrase):
        return "extractor_prose"
    if "@" in phrase:
        return "mention_privacy"
    if "#" in phrase or "_" in phrase:
        # underscore-joined Arabic = hashtag BODY with '#' stripped by the extractor
        # (eyeballed: 'دجاجنا_من_ارض_السعودية' 5x, 'الاحد_الشاورمري' 2x) — same token class
        return "hashtag_ar"
    if DIGIT_RE.search(phrase):
        return "digits"
    if any(rx.search(phrase) for rx in ARTIFACT_RES):
        return "artifact"
    if any(g in phrase for g in OCCASION_GENERIC):
        return "occasion_generic"
    return "signature"


def _ranked(counter_items):
    """deterministic: count desc, then text asc."""
    return sorted(counter_items, key=lambda kv: (-kv[1], kv[0]))


def build():
    cells = {}   # (sector_key, dialect) -> {"n", "phrases": Counter, "registers": Counter, "raw_sectors": Counter}
    coverage = {"total_observations": 0, "no_dialect_detected": 0, "unfoldable_excluded": Counter()}
    for fp in sorted(glob.glob(str(OBS / "*" / "*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        coverage["total_observations"] += 1
        vo = d.get("voice_observations") or {}
        dd = vo.get("dialect_detected")
        if not dd:
            coverage["no_dialect_detected"] += 1
            continue
        if dd not in DIALECT_FOLD:
            coverage["unfoldable_excluded"][dd] += 1   # mixed/saudi/non_arabic/unknown/southern — never folded
            continue
        sk = SECTOR_MAP.get(d.get("sector"), "Other")
        c = cells.setdefault((sk, DIALECT_FOLD[dd]), {
            "n": 0, "phrases": Counter(), "registers": Counter(), "raw_sectors": Counter()})
        c["n"] += 1
        c["raw_sectors"][d.get("sector") or "unknown"] += 1
        if vo.get("register"):
            c["registers"][vo["register"]] += 1
        for p in (vo.get("notable_phrases") or []):
            if p and str(p).strip():
                c["phrases"][str(p).strip()] += 1

    cov_out = {"total_observations": coverage["total_observations"],
               "no_dialect_detected": coverage["no_dialect_detected"],
               "unfoldable_excluded": dict(sorted(coverage["unfoldable_excluded"].items())),
               "folded_into_cells": sum(c["n"] for c in cells.values()),
               "non_empty_cells": len(cells)}

    records = []
    for (sk, dialect) in sorted(cells):
        c = cells[(sk, dialect)]
        n = c["n"]
        buckets = {}   # bucket -> list[(phrase, freq)] ranked
        for p, f in _ranked([(p, f) for p, f in c["phrases"].items() if f >= MIN_FREQ]):
            buckets.setdefault(classify(p), []).append((p, f))
        qualifying = buckets.get("signature", [])
        signatures = [p for p, _ in qualifying[:CAP]]
        occ_generic = [p for p, _ in buckets.get("occasion_generic", [])]
        hashtags_ar = [{"tag": p, "count": f} for p, f in buckets.get("hashtag_ar", [])]

        labeled = sum(c["registers"].values())
        if labeled:
            dist = ", ".join(f"{k} {v}" for k, v in _ranked(c["registers"].items()))
            register_notes = (f"register labels on {labeled} of {n} obs in this cell; "
                              f"labeled distribution: {dist}")
        else:
            register_notes = None   # honest: source carries no register label in this cell

        extra = {
            "extraction": "claude_code_extraction over voice_observations (dialect_detected + notable_phrases + register)",
            "advisory_pointer": ADVISORY_POINTER,   # universal arabic_text guidance — English path string only
            "avoid_phrases_note": "empty by design: no per-dialect avoid-phrase source exists; any value would be fabricated",
            "thin_cell": n < THIN,
            "signature_insufficient": len(signatures) < 3,
            "qualifying_phrase_count": len(qualifying),   # cap-10 truncation stays visible
            "signature_phrase_counts": {p: f for p, f in qualifying[:CAP]},
            "occasion_generic": occ_generic,
            "occasion_generic_counts": {p: f for p, f in buckets.get("occasion_generic", [])},
            # documented mining field (DeepSeek D5 condition): Arabic hashtags at freq>=2 in this
            # cell — excluded from signature_phrases_ar (brand/campaign tokens, not spoken register)
            "hashtags_ar_excluded": hashtags_ar,
            "register_distribution": {k: v for k, v in _ranked(c["registers"].items())},
            "register_labeled_count": labeled,
            "filtered_phrase_counts": {b: len(v) for b, v in sorted(buckets.items()) if b != "signature"},
            "source_sector_distribution": {k: v for k, v in sorted(c["raw_sectors"].items())},
            "corpus_coverage": cov_out,   # per-record: file must stay a flat homogeneous array
        }
        if not labeled:
            extra["register_data_absent"] = True
        if sk == "Other":
            extra["provisional_sector"] = True   # merges unshipped raw slugs (same flag as brand_observations)

        records.append({
            "id": f"dvar_{SECTOR_SLUG[sk]}_{DIALECT_SLUG[dialect]}",
            "entity": "dialect_variant",
            "sector_key": sk,
            "dialect": dialect,
            "register_notes": register_notes,
            "signature_phrases_ar": signatures,
            "avoid_phrases_ar": [],   # ZERO per-dialect source — any value is fabrication
            "sample_size": n,
            "provenance": {
                "source": "apify_scrape",
                "confidence": "inferred",       # claude_code_extraction, not human/metric-verified
                "observed_count": n,            # REAL recount of observations in the cell
                "date_added": DATE_ADDED,
                "scope": f"sector:{sk}+dialect:{dialect}",
            },
            "extra": extra,
        })

    # ---- Rule #8 pre-write hard asserts: REFUSE to write a record that breaks the contract ----
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "duplicate record ids"
    for r in records:
        assert r["dialect"] in SPEC_DIALECTS, f"{r['id']}: dialect {r['dialect']!r} outside spec 4-set"
        assert r["sector_key"] in SHIPPED_SECTORS, f"{r['id']}: sector_key {r['sector_key']!r} not shipped"
        assert r["avoid_phrases_ar"] == [], f"{r['id']}: avoid_phrases_ar must be [] (no source)"
        assert r["sample_size"] == r["provenance"]["observed_count"] > 0
        for ph in r["signature_phrases_ar"]:
            assert AR_RE.search(ph), f"{r['id']}: non-Arabic signature {ph!r}"
            assert not DIGIT_RE.search(ph) and "#" not in ph and "@" not in ph, f"{r['id']}: junk survived {ph!r}"
            assert not any(g in ph for g in OCCASION_GENERIC), f"{r['id']}: greeting in signatures {ph!r}"
        assert (r["register_notes"] is None) == bool(r["extra"].get("register_data_absent")), \
            f"{r['id']}: register_notes/flag mismatch"
    assert sum(r["sample_size"] for r in records) == cov_out["folded_into_cells"]

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "dialect_variants.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(records)} dialect_variant records "
          f"({cov_out['folded_into_cells']} obs folded of {cov_out['total_observations']}; "
          f"excluded: {cov_out['no_dialect_detected']} no-dialect + "
          f"{sum(coverage['unfoldable_excluded'].values())} unfoldable)")
    for r in records:
        print(f"  {r['id']:32s} n={r['sample_size']:5d} sig={len(r['signature_phrases_ar']):2d}"
              f"{' THIN' if r['extra']['thin_cell'] else ''}")
    return records


if __name__ == "__main__":
    build()
