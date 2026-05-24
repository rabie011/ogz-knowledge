#!/usr/bin/env python3
"""
build_arabic_copywriting_by_sector.py
Sector-controlled version of build_arabic_copywriting.py.

THE CONFOUND:
  - F&B accounts: Arabic captions + ~70% high engagement baseline
  - Beauty accounts: Arabic captions + ~18% high engagement baseline
  - Original analysis: "Arabic phrase X = high signal" actually meant "F&B = high signal"
  - Any Arabic phrase that F&B uses = appeared high-eng for sector reasons

THIS SCRIPT:
  1. Splits obs by sector BEFORE phrase analysis
  2. Computes lift vs sector baseline (not corpus baseline)
  3. Only flags phrase as "signal" if it beats its OWN sector baseline
  4. Finds phrases that are high-signal in MULTIPLE sectors (true Arabic signals)
  5. Finds opener formulas that hold cross-sector

Output: logs/arabic_copywriting_by_sector.json
"""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75,
    "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}
HIGH_THRESH   = 0.75
MIN_COUNT     = 3          # min phrase appearances to consider

# ── Arabic text utilities ──────────────────────────────────────────────────────
_ARABIC_BLOCK = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+")
_HASHTAG_RE   = re.compile(r"#[\w؀-ۿ]+")
_DIACRITIC_RE = re.compile(r"[ً-ٰٟ]")


def _strip_diacritics(text: str) -> str:
    return _DIACRITIC_RE.sub("", text)


def _arabic_words(text: str) -> list:
    cleaned = _HASHTAG_RE.sub(" ", text)
    cleaned = _strip_diacritics(cleaned)
    return [w.strip() for w in _ARABIC_BLOCK.findall(cleaned) if len(w.strip()) >= 2]


def _arabic_opener(text: str) -> str:
    words = _arabic_words(text)
    if len(words) < 2:
        return ""
    return " ".join(words[:5])


def _opener_formula(text: str) -> str:
    head = text.strip()[:120]
    if "?" in head or "؟" in head:
        return "question"
    ar_q = ["هل", "ما ", "ماذا", "من ", "أين", "كيف", "متى", "لماذا"]
    for q in ar_q:
        if head.startswith(q):
            return "question"
    invite = ["حياكم", "أهلاً", "أهلا", "تعالوا", "تفضلوا", "عندنا", "جربوا", "اكتشف", "شاركونا"]
    for w in invite:
        if w in head:
            return "community_invite"
    sensory = ["طعم", "رائحة", "لذيذ", "مميز", "أحلى", "ألذ", "الأجود", "جمال", "روعة", "ذكريات"]
    for w in sensory:
        if w in head:
            return "sensory_emotive"
    announce = ["جديد", "يتوفر", "أطلقنا", "إطلاق", "الآن", "توفر", "حصري", "متاح"]
    for w in announce:
        if w in head:
            return "announcement"
    heritage = ["رمضان", "العيد", "اليوم الوطني", "التأسيس", "الوطن", "المملكة", "تراث", "أصيل"]
    for w in heritage:
        if w in head:
            return "heritage_occasion"
    return "other"


def _bigrams(word_list: list) -> list:
    return [f"{word_list[i]} {word_list[i+1]}" for i in range(len(word_list) - 1)]


def _occasion_keywords(text: str) -> list:
    occ_map = {
        "ramadan":      ["رمضان", "إفطار", "سحور", "ليلة القدر", "الفطر"],
        "national_day": ["اليوم الوطني", "المملكة", "السعودية", "وطن", "فخر"],
        "founding_day": ["يوم التأسيس", "التأسيس", "الدرعية"],
        "eid":          ["عيد", "تقبل الله", "عيد مبارك"],
    }
    found = []
    for occ, kws in occ_map.items():
        for kw in kws:
            if kw in text:
                found.append((occ, kw))
    return found


def _analyse_sector_arabic(obs_list: list, baseline: float) -> dict:
    """
    Phrase-level Arabic analysis for one sector.
    All lift is vs this sector's baseline.
    """
    phrase_high = Counter()
    phrase_low  = Counter()
    phrase_any  = Counter()
    opener_high = Counter()
    opener_low  = Counter()
    formula_eng = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    occ_phrases = defaultdict(Counter)

    ar_obs = 0

    for obs in obs_list:
        vo  = obs.get("voice_observations") or {}
        qa  = obs.get("quality_assessment")  or {}
        cn  = obs.get("cultural_notes")      or {}

        cap = vo.get("caption_text")
        if cap is None:
            continue

        cap_str  = str(cap)
        ar_words = _arabic_words(cap_str)
        if len(ar_words) < 3:
            continue

        ar_obs  += 1
        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = eng >= HIGH_THRESH

        # Phrases: unigrams + bigrams
        phrases = ar_words + _bigrams(ar_words)
        for ph in phrases:
            phrase_any[ph] += 1
            if is_high:
                phrase_high[ph] += 1
            else:
                phrase_low[ph] += 1

        # Opener
        opener = _arabic_opener(cap_str)
        if opener:
            if is_high:
                opener_high[opener] += 1
            else:
                opener_low[opener] += 1

        # Formula
        formula = _opener_formula(cap_str)
        formula_eng[formula]["count"] += 1
        formula_eng[formula]["high"]  += (1 if is_high else 0)
        formula_eng[formula]["sum"]   += eng

        # Occasion keywords
        for occ, kw in _occasion_keywords(cap_str):
            occ_phrases[occ][kw] += 1

    # ── Signal phrases (beat sector baseline) ────────────────────────────────
    signal_phrases = []
    avoid_phrases  = []

    for phrase, total_cnt in phrase_any.items():
        if total_cnt < MIN_COUNT:
            continue
        high_cnt   = phrase_high.get(phrase, 0)
        low_cnt    = phrase_low.get(phrase, 0)
        high_ratio = high_cnt / total_cnt
        lift       = round(high_ratio - baseline, 3)

        if high_ratio >= (baseline + 0.15) and high_cnt >= MIN_COUNT:
            signal_phrases.append({
                "phrase": phrase,
                "total": total_cnt,
                "in_high_eng": high_cnt,
                "in_low_eng": low_cnt,
                "high_ratio": round(high_ratio, 3),
                "lift_vs_sector_baseline": lift,
            })
        if high_ratio <= max(0.20, baseline - 0.20) and low_cnt >= MIN_COUNT:
            avoid_phrases.append({
                "phrase": phrase,
                "total": total_cnt,
                "in_high_eng": high_cnt,
                "in_low_eng": low_cnt,
                "high_ratio": round(high_ratio, 3),
                "lift_vs_sector_baseline": lift,
            })

    signal_phrases.sort(key=lambda x: (-x["lift_vs_sector_baseline"], -x["in_high_eng"]))
    avoid_phrases.sort(key=lambda x: (x["lift_vs_sector_baseline"], -x["in_low_eng"]))

    # ── Top openers ──────────────────────────────────────────────────────────
    top_openers = []
    all_ops = set(list(opener_high.keys()) + list(opener_low.keys()))
    for op in all_ops:
        hc = opener_high.get(op, 0)
        lc = opener_low.get(op, 0)
        total_op = hc + lc
        if total_op < 2:
            continue
        ratio = hc / total_op
        lift  = round(ratio - baseline, 3)
        if ratio >= (baseline + 0.10) and hc >= 2:
            top_openers.append({
                "opener": op,
                "high_eng": hc,
                "low_eng": lc,
                "high_ratio": round(ratio, 3),
                "lift_vs_sector_baseline": lift,
            })
    top_openers.sort(key=lambda x: (-x["lift_vs_sector_baseline"], -x["high_eng"]))

    # ── Formula table ─────────────────────────────────────────────────────────
    formula_table = []
    for formula, d in formula_eng.items():
        n = d["count"]
        r = round(d["high"] / n, 3) if n else 0
        formula_table.append({
            "formula": formula,
            "count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"] / n, 3) if n else 0,
            "lift_vs_sector_baseline": round(r - baseline, 3),
        })
    formula_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))

    # ── Occasion clusters ────────────────────────────────────────────────────
    occ_clusters = {
        occ: [{"keyword": kw, "count": cnt} for kw, cnt in ctr.most_common(10)]
        for occ, ctr in occ_phrases.items()
    }

    return {
        "arabic_caption_obs": ar_obs,
        "sector_baseline": round(baseline, 3),
        "signal_phrases": signal_phrases[:40],
        "avoid_phrases": avoid_phrases[:20],
        "top_openers": top_openers[:20],
        "opener_formula_table": formula_table,
        "occasion_keyword_clusters": occ_clusters,
    }


def _find_cross_sector_phrase_signals(per_sector: dict) -> list:
    """
    Phrases that are signal (beat sector baseline) in ≥2 sectors.
    These are genuine Arabic copywriting signals, not sector artifacts.
    """
    phrase_sector_data = defaultdict(list)

    for sector, analysis in per_sector.items():
        for row in analysis.get("signal_phrases", []):
            phrase_sector_data[row["phrase"]].append({
                "sector": sector,
                "lift": row["lift_vs_sector_baseline"],
                "count": row["total"],
                "high_ratio": row["high_ratio"],
            })

    signals = []
    for phrase, rows in phrase_sector_data.items():
        if len(rows) < 2:
            continue
        avg_lift = round(sum(r["lift"] for r in rows) / len(rows), 3)
        signals.append({
            "phrase": phrase,
            "confirmed_in_sectors": [r["sector"] for r in rows],
            "sector_count": len(rows),
            "avg_lift_across_sectors": avg_lift,
            "per_sector": rows,
        })
    signals.sort(key=lambda x: (-x["sector_count"], -x["avg_lift_across_sectors"]))
    return signals


def _find_cross_sector_formula_signals(per_sector: dict) -> list:
    """
    Opener formulas that beat sector baseline in ≥2 sectors.
    """
    formula_data = defaultdict(list)
    for sector, analysis in per_sector.items():
        for row in analysis.get("opener_formula_table", []):
            if row["lift_vs_sector_baseline"] > 0 and row["count"] >= 3:
                formula_data[row["formula"]].append({
                    "sector": sector,
                    "lift": row["lift_vs_sector_baseline"],
                    "rate": row["high_engagement_rate"],
                    "count": row["count"],
                })

    signals = []
    for formula, rows in formula_data.items():
        if len(rows) < 2:
            continue
        avg_lift = round(sum(r["lift"] for r in rows) / len(rows), 3)
        signals.append({
            "formula": formula,
            "confirmed_sectors": [r["sector"] for r in rows],
            "avg_lift_across_sectors": avg_lift,
            "per_sector": rows,
        })
    signals.sort(key=lambda x: (-len(x["confirmed_sectors"]), -x["avg_lift_across_sectors"]))
    return signals


def main():
    # ── 1. Load all obs, compute baselines ───────────────────────────────────
    sector_obs      = defaultdict(list)
    sector_baselines = defaultdict(lambda: {"total": 0, "high": 0, "sum": 0.0})

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        sector = data.get("sector") or "unknown"
        vo     = data.get("voice_observations") or {}
        qa     = data.get("quality_assessment")  or {}

        cap = vo.get("caption_text")
        if cap is None:
            continue

        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= HIGH_THRESH else 0

        # Only count obs with Arabic content
        cap_str  = str(cap)
        ar_words = _arabic_words(cap_str)
        if len(ar_words) >= 3:
            sector_baselines[sector]["total"] += 1
            sector_baselines[sector]["high"]  += is_high
            sector_baselines[sector]["sum"]   += eng
            sector_obs[sector].append(data)

    # ── 2. Compute sector baselines ──────────────────────────────────────────
    computed_baselines = {}
    for sector, d in sector_baselines.items():
        n = d["total"]
        computed_baselines[sector] = {
            "arabic_caption_obs": n,
            "baseline": round(d["high"] / n, 3) if n else None,
            "avg_engagement": round(d["sum"] / n, 3) if n else None,
        }

    print("Sector baselines (Arabic caption obs only):")
    for s, d in sorted(computed_baselines.items()):
        print(f"  {s:<12} baseline={int((d['baseline'] or 0)*100)}%  n={d['arabic_caption_obs']}")

    # ── 3. Run per-sector Arabic analysis ────────────────────────────────────
    per_sector_analysis = {}
    for sector, obs_list in sector_obs.items():
        if len(obs_list) < 5:
            print(f"  ⚠️  {sector}: only {len(obs_list)} Arabic-caption obs — skipping")
            continue
        baseline = computed_baselines[sector]["baseline"] or 0.5
        per_sector_analysis[sector] = _analyse_sector_arabic(obs_list, baseline)
        n_signals = len(per_sector_analysis[sector]["signal_phrases"])
        print(f"  ✓ {sector}: {per_sector_analysis[sector]['arabic_caption_obs']} Arabic obs, "
              f"baseline={int(baseline*100)}%, {n_signals} signal phrases")

    # ── 4. Cross-sector signals ───────────────────────────────────────────────
    cross_phrase_signals  = _find_cross_sector_phrase_signals(per_sector_analysis)
    cross_formula_signals = _find_cross_sector_formula_signals(per_sector_analysis)

    # ── 5. Confound report ────────────────────────────────────────────────────
    confound_warnings = [
        {
            "type": "sector_baseline_gap",
            "message": (
                "F&B sector has ~70% high-eng baseline vs beauty ~18%. "
                "Any Arabic phrase used predominantly by F&B accounts appears 'high-signal' "
                "in corpus-level analysis — NOT because of the phrase, but because of the sector. "
                "Only phrases that beat their OWN sector baseline are real signals."
            ),
        },
        {
            "type": "arabic_language_confound",
            "message": (
                "Original finding 'Arabic-only captions = 78% high engagement' reflects "
                "F&B dominance (399/474 obs), not Arabic language quality. "
                "Beauty sector Arabic captions need separate baseline (~18%) to evaluate."
            ),
        },
    ]

    # ── 6. Key findings ───────────────────────────────────────────────────────
    findings = []

    if cross_phrase_signals:
        top_ph = cross_phrase_signals[0]
        findings.append(
            f"TRUE cross-sector Arabic phrase: '{top_ph['phrase']}' — "
            f"beats baseline in {top_ph['sector_count']} sectors "
            f"(avg +{int(top_ph['avg_lift_across_sectors']*100)}pp)"
        )
    else:
        findings.append(
            "No single Arabic phrase beats sector baseline in ≥2 sectors. "
            "Existing 'signal phrases' are sector artifacts, not language signals."
        )

    if cross_formula_signals:
        top_f = cross_formula_signals[0]
        findings.append(
            f"TRUE cross-sector opener formula: '{top_f['formula']}' — "
            f"positive in {len(top_f['confirmed_sectors'])} sectors "
            f"(avg +{int(top_f['avg_lift_across_sectors']*100)}pp)"
        )

    # Per-sector top insights
    for sector, analysis in per_sector_analysis.items():
        baseline = computed_baselines[sector]["baseline"] or 0
        n_sig = len(analysis["signal_phrases"])
        top_formula = analysis["opener_formula_table"][0] if analysis["opener_formula_table"] else None
        if top_formula:
            findings.append(
                f"{sector.upper()} — Best opener formula: '{top_formula['formula']}' = "
                f"{int(top_formula['high_engagement_rate']*100)}% "
                f"(+{int(top_formula['lift_vs_sector_baseline']*100)}pp vs {int(baseline*100)}% baseline)"
            )

    # ── 7. Agency rules ───────────────────────────────────────────────────────
    agency_rules_universal = []
    agency_rules_by_sector = {}

    for sig in cross_phrase_signals[:10]:
        agency_rules_universal.append(
            f"Arabic phrase '{sig['phrase']}' — confirmed cross-sector signal "
            f"(sectors: {', '.join(sig['confirmed_sectors'])})"
        )

    for sig in cross_formula_signals[:5]:
        agency_rules_universal.append(
            f"Opener formula '{sig['formula']}' — beats baseline in all sectors tested"
        )

    for sector, analysis in per_sector_analysis.items():
        rules = []
        for ph in analysis["signal_phrases"][:5]:
            rules.append(
                f"Use '{ph['phrase']}' — "
                f"+{int(ph['lift_vs_sector_baseline']*100)}pp vs {sector} baseline"
            )
        for ph in analysis["avoid_phrases"][:3]:
            rules.append(
                f"Avoid '{ph['phrase']}' — "
                f"{int(ph['lift_vs_sector_baseline']*100)}pp vs {sector} baseline"
            )
        top_f = analysis["opener_formula_table"][0] if analysis["opener_formula_table"] else None
        if top_f and top_f["lift_vs_sector_baseline"] > 0:
            rules.append(
                f"Lead with '{top_f['formula']}' opener "
                f"({int(top_f['high_engagement_rate']*100)}% high-eng)"
            )
        agency_rules_by_sector[sector] = rules

    # ── 8. Output ─────────────────────────────────────────────────────────────
    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "methodology_note": (
            "Phrases are only flagged 'signal' if they exceed their OWN sector baseline by ≥15pp. "
            "Cross-sector signals require positive lift in ≥2 sectors. "
            "Confound warnings explain why the original analysis was misleading."
        ),
        "sector_baselines": computed_baselines,
        "per_sector_analysis": per_sector_analysis,
        "cross_sector_phrase_signals": cross_phrase_signals[:30],
        "cross_sector_formula_signals": cross_formula_signals,
        "confound_warnings": confound_warnings,
        "key_findings": findings,
        "agency_rules_universal": agency_rules_universal,
        "agency_rules_by_sector": agency_rules_by_sector,
    }

    LOGS.mkdir(exist_ok=True)
    out_path = LOGS / "arabic_copywriting_by_sector.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"\n{'='*60}")
    print("ARABIC COPYWRITING (SECTOR-CONTROLLED)")
    print(f"{'='*60}")
    for finding in findings:
        print(f"  ▸ {finding}")

    print(f"\nCross-sector phrase signals ({len(cross_phrase_signals)} found):")
    for sig in cross_phrase_signals[:10]:
        print(f"  '{sig['phrase']}'  sectors={','.join(sig['confirmed_sectors'])}  "
              f"avg_lift=+{int(sig['avg_lift_across_sectors']*100)}pp")

    print(f"\nCross-sector formula signals:")
    for sig in cross_formula_signals:
        print(f"  '{sig['formula']}'  sectors={','.join(sig['confirmed_sectors'])}  "
              f"avg_lift=+{int(sig['avg_lift_across_sectors']*100)}pp")

    print(f"\nUniversal agency rules:")
    for rule in agency_rules_universal:
        print(f"  ▸ {rule}")

    print(f"\nOutput: logs/arabic_copywriting_by_sector.json")


if __name__ == "__main__":
    main()
