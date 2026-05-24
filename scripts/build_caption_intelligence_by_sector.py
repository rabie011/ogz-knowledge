#!/usr/bin/env python3
"""
build_caption_intelligence_by_sector.py
Sector-controlled version of build_caption_intelligence.py.

THE CONFOUND:
  - F&B sector baseline: ~70% high engagement
  - Beauty sector baseline: ~18% high engagement
  - Retail sector baseline: ~20% high engagement
  - Original analysis mixed all sectors with a single 54% baseline
  - "Arabic language = 78% high eng" was actually "F&B = high eng" (sector effect)

THIS SCRIPT:
  1. Computes per-sector baselines from caption-filled obs
  2. Runs all dimension analyses WITHIN each sector
  3. Computes lift vs sector baseline (not corpus baseline)
  4. Flags confounds: findings that disappear or reverse when sector-controlled
  5. Identifies true cross-sector signals (hold in ≥2 sectors)

Output: logs/caption_intelligence_by_sector.json
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
HIGH_THRESH = 0.75

_ARABIC_RE  = re.compile(r"[؀-ۿݐ-ݿ]+")
_ENGLISH_RE = re.compile(r"[A-Za-z]+")


def _caption_language(text: str) -> str:
    has_ar = bool(_ARABIC_RE.search(text))
    has_en = bool(_ENGLISH_RE.search(text))
    if has_ar and has_en:
        return "bilingual"
    if has_ar:
        return "arabic"
    if has_en:
        return "english"
    return "other"


def _is_question_open(text: str) -> bool:
    head = text.strip()[:80]
    ar_q_words = ["هل", "ما", "ماذا", "من", "أين", "كيف", "متى", "لماذا"]
    if "?" in head or "؟" in head:
        return True
    for w in ar_q_words:
        if head.startswith(w + " ") or head.startswith(w + "\n"):
            return True
    return False


def _length_bucket(word_count: int) -> str:
    if word_count == 0:
        return "empty"
    if word_count <= 10:
        return "short_1_10"
    if word_count <= 30:
        return "medium_11_30"
    if word_count <= 75:
        return "long_31_75"
    return "very_long_75plus"


def _hashtag_bucket(count: int) -> str:
    if count == 0:
        return "0"
    if count <= 5:
        return "1_5"
    if count <= 15:
        return "6_15"
    return "16plus"


def _make_bucket():
    return {"count": 0, "high": 0, "sum": 0.0}


def _rate(d):
    return round(d["high"] / d["count"], 3) if d["count"] else None


def _lift(rate, baseline):
    if rate is None or baseline is None:
        return None
    return round(rate - baseline, 3)


def _bucket_table(bucket_dict, key_name, baseline):
    rows = []
    for k, d in sorted(bucket_dict.items()):
        n = d["count"]
        if n == 0:
            continue
        r = _rate(d)
        rows.append({
            key_name: k,
            "count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"] / n, 3),
            "lift_vs_sector_baseline": _lift(r, baseline),
        })
    rows.sort(key=lambda x: (-(x["high_engagement_rate"] or 0), -x["count"]))
    return rows


def _analyse_sector(obs_list: list, baseline: float) -> dict:
    """Run all caption dimension analyses for one sector."""
    by_length  = defaultdict(_make_bucket)
    by_hashtag = defaultdict(_make_bucket)
    by_emoji   = defaultdict(_make_bucket)
    by_lang    = defaultdict(_make_bucket)
    by_open    = defaultdict(_make_bucket)

    for obs in obs_list:
        vo  = obs.get("voice_observations") or {}
        qa  = obs.get("quality_assessment")  or {}
        cap = vo.get("caption_text")
        if cap is None:
            continue

        cap_str     = str(cap)
        wc          = int(vo.get("caption_word_count") or 0)
        hashtag_cnt = int(vo.get("hashtag_count") or 0)
        emoji       = vo.get("has_emoji")

        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= HIGH_THRESH else 0

        # Length
        lb = _length_bucket(wc)
        by_length[lb]["count"] += 1
        by_length[lb]["high"]  += is_high
        by_length[lb]["sum"]   += eng

        # Hashtag
        hb = _hashtag_bucket(hashtag_cnt)
        by_hashtag[hb]["count"] += 1
        by_hashtag[hb]["high"]  += is_high
        by_hashtag[hb]["sum"]   += eng

        # Emoji
        el = "has_emoji" if emoji else "no_emoji"
        by_emoji[el]["count"] += 1
        by_emoji[el]["high"]  += is_high
        by_emoji[el]["sum"]   += eng

        # Language
        cap_lang = _caption_language(cap_str) if cap_str else "empty"
        by_lang[cap_lang]["count"] += 1
        by_lang[cap_lang]["high"]  += is_high
        by_lang[cap_lang]["sum"]   += eng

        # Opener
        is_q  = _is_question_open(cap_str) if cap_str else False
        ql    = "question_open" if is_q else "statement_open"
        by_open[ql]["count"] += 1
        by_open[ql]["high"]  += is_high
        by_open[ql]["sum"]   += eng

    return {
        "caption_length":  _bucket_table(by_length,  "bucket", baseline),
        "hashtag_count":   _bucket_table(by_hashtag, "bucket", baseline),
        "emoji_presence":  _bucket_table(by_emoji,   "bucket", baseline),
        "caption_language": _bucket_table(by_lang,   "bucket", baseline),
        "opener_style":    _bucket_table(by_open,    "bucket", baseline),
    }


def _find_cross_sector_signals(sectors_data: dict, dim: str, key_field: str) -> list:
    """
    Find dimension values that show positive lift in EVERY sector with n>=5.
    These are true signals, not sector confounds.
    """
    # For each dimension value, collect lift across sectors
    value_lifts = defaultdict(list)
    for sector, analysis in sectors_data.items():
        for row in analysis.get(dim, []):
            n = row["count"]
            lift = row.get("lift_vs_sector_baseline")
            if n >= 5 and lift is not None:
                value_lifts[row[key_field]].append({
                    "sector": sector,
                    "lift": lift,
                    "count": n,
                    "rate": row["high_engagement_rate"],
                })

    signals = []
    for val, sector_rows in value_lifts.items():
        if len(sector_rows) < 2:
            continue   # only 1 sector has data — can't confirm cross-sector
        all_positive = all(r["lift"] > 0 for r in sector_rows)
        all_negative = all(r["lift"] < 0 for r in sector_rows)
        avg_lift = round(sum(r["lift"] for r in sector_rows) / len(sector_rows), 3)
        signals.append({
            key_field: val,
            "sectors_confirmed": len(sector_rows),
            "all_positive_lift": all_positive,
            "all_negative_lift": all_negative,
            "avg_lift_across_sectors": avg_lift,
            "per_sector": sector_rows,
            "verdict": (
                "TRUE_SIGNAL_POSITIVE" if all_positive else
                "TRUE_SIGNAL_NEGATIVE" if all_negative else
                "MIXED_INCONCLUSIVE"
            ),
        })
    signals.sort(key=lambda x: -abs(x["avg_lift_across_sectors"]))
    return signals


def main():
    # ── 1. Load all obs, partition by sector ──────────────────────────────────
    sector_obs    = defaultdict(list)
    sector_totals = defaultdict(lambda: {"total": 0, "with_caption": 0, "high": 0, "sum": 0.0})

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        sector = data.get("sector") or "unknown"
        vo     = data.get("voice_observations") or {}
        qa     = data.get("quality_assessment")  or {}

        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= HIGH_THRESH else 0

        sector_totals[sector]["total"] += 1
        if vo.get("caption_text") is not None:
            sector_totals[sector]["with_caption"] += 1
            sector_totals[sector]["high"] += is_high
            sector_totals[sector]["sum"]  += eng
            sector_obs[sector].append(data)

    # ── 2. Compute per-sector baselines ──────────────────────────────────────
    sector_baselines = {}
    sector_summaries = {}
    for sector, d in sector_totals.items():
        n = d["with_caption"]
        baseline = round(d["high"] / n, 3) if n else None
        sector_baselines[sector] = baseline
        sector_summaries[sector] = {
            "total_obs":    d["total"],
            "with_caption": n,
            "without_caption": d["total"] - n,
            "sector_baseline": baseline,
            "avg_engagement": round(d["sum"] / n, 3) if n else None,
        }

    print("Sector baselines (% high engagement among captioned obs):")
    for s, b in sorted(sector_baselines.items()):
        n = sector_summaries[s]["with_caption"]
        print(f"  {s:<12} baseline={int((b or 0)*100)}%  n={n}")

    # ── 3. Run per-sector analysis ────────────────────────────────────────────
    sectors_analysis = {}
    for sector, obs_list in sector_obs.items():
        if len(obs_list) < 5:
            print(f"  ⚠️  {sector}: only {len(obs_list)} captioned obs — skipping analysis")
            continue
        baseline = sector_baselines[sector] or 0.5
        sectors_analysis[sector] = _analyse_sector(obs_list, baseline)
        print(f"  ✓ {sector}: analysed {len(obs_list)} obs (baseline={int(baseline*100)}%)")

    # ── 4. Cross-sector signal detection ─────────────────────────────────────
    cross_signals = {
        "caption_language": _find_cross_sector_signals(
            sectors_analysis, "caption_language", "bucket"),
        "caption_length":   _find_cross_sector_signals(
            sectors_analysis, "caption_length", "bucket"),
        "hashtag_count":    _find_cross_sector_signals(
            sectors_analysis, "hashtag_count", "bucket"),
        "emoji_presence":   _find_cross_sector_signals(
            sectors_analysis, "emoji_presence", "bucket"),
        "opener_style":     _find_cross_sector_signals(
            sectors_analysis, "opener_style", "bucket"),
    }

    # ── 5. Confound detection — compare original findings vs corrected ────────
    confound_warnings = []

    # Language confound: was "Arabic = best language" actually sector effect?
    for lang_row in cross_signals["caption_language"]:
        if lang_row["bucket"] in ("arabic", "bilingual"):
            if not lang_row["all_positive_lift"]:
                confound_warnings.append({
                    "dimension": "caption_language",
                    "value": lang_row["bucket"],
                    "warning": (
                        f"'{lang_row['bucket']}' language shows mixed sector results "
                        f"(avg lift={lang_row['avg_lift_across_sectors']:+.0%}). "
                        "Original 'Arabic = best language' finding was likely a sector confound "
                        "(F&B accounts post in Arabic AND have high engagement)."
                    ),
                    "verdict": lang_row["verdict"],
                })

    # ── 6. Key findings (sector-controlled) ──────────────────────────────────
    findings = []

    # Sector baseline comparison
    baseline_sorted = sorted(
        [(s, b) for s, b in sector_baselines.items() if b is not None],
        key=lambda x: -x[1]
    )
    if len(baseline_sorted) >= 2:
        hi_s, hi_b = baseline_sorted[0]
        lo_s, lo_b = baseline_sorted[-1]
        findings.append(
            f"Sector baselines differ hugely: {hi_s}={int(hi_b*100)}% vs {lo_s}={int(lo_b*100)}%"
            " — must always control for sector before interpreting caption signals"
        )

    # True cross-sector language signal
    true_lang = [r for r in cross_signals["caption_language"] if r["verdict"] == "TRUE_SIGNAL_POSITIVE"]
    negative_lang = [r for r in cross_signals["caption_language"] if r["verdict"] == "TRUE_SIGNAL_NEGATIVE"]
    if true_lang:
        findings.append(
            f"Cross-sector language signal: '{true_lang[0]['bucket']}' "
            f"lifts engagement in ALL sectors (avg +{int(true_lang[0]['avg_lift_across_sectors']*100)}pp)"
        )
    if negative_lang:
        findings.append(
            f"Cross-sector language to avoid: '{negative_lang[0]['bucket']}' "
            f"hurts in all sectors (avg {int(negative_lang[0]['avg_lift_across_sectors']*100)}pp)"
        )

    # True length signal
    true_len = [r for r in cross_signals["caption_length"] if r["verdict"] == "TRUE_SIGNAL_POSITIVE"]
    if true_len:
        findings.append(
            f"Caption length cross-sector winner: '{true_len[0]['bucket']}' "
            f"(avg +{int(true_len[0]['avg_lift_across_sectors']*100)}pp)"
        )

    # True hashtag signal
    true_hash = [r for r in cross_signals["hashtag_count"] if r["verdict"] == "TRUE_SIGNAL_POSITIVE"]
    if true_hash:
        findings.append(
            f"Hashtag count cross-sector winner: '{true_hash[0]['bucket']}' "
            f"(avg +{int(true_hash[0]['avg_lift_across_sectors']*100)}pp)"
        )

    # Confound warnings
    for w in confound_warnings:
        findings.append(f"⚠️  CONFOUND: {w['warning']}")

    # ── 7. Agency rules (sector-specific + universal) ─────────────────────────
    agency_rules_universal = []
    agency_rules_by_sector = {}

    # Universal rules: cross-sector TRUE_SIGNAL
    for dim in ("caption_language", "caption_length", "hashtag_count", "emoji_presence"):
        for row in cross_signals[dim]:
            if row["verdict"] == "TRUE_SIGNAL_POSITIVE" and row["avg_lift_across_sectors"] > 0.05:
                agency_rules_universal.append(
                    f"[{dim}] Use '{row['bucket']}' — true cross-sector lift "
                    f"(+{int(row['avg_lift_across_sectors']*100)}pp average)"
                )

    # Per-sector rules: top-performing bucket within sector
    for sector, analysis in sectors_analysis.items():
        rules = []
        for dim, rows in analysis.items():
            if not rows:
                continue
            top = rows[0]
            if (top.get("lift_vs_sector_baseline") or 0) > 0.05 and top["count"] >= 3:
                rules.append(
                    f"[{dim}] '{top['bucket']}' = {int((top['high_engagement_rate'] or 0)*100)}% "
                    f"(+{int((top['lift_vs_sector_baseline'] or 0)*100)}pp vs {sector} baseline)"
                )
        agency_rules_by_sector[sector] = rules

    # ── 8. Output ─────────────────────────────────────────────────────────────
    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "methodology_note": (
            "All lift values are vs per-sector baseline (not corpus baseline). "
            "F&B baseline ~70%, beauty ~18%, retail ~20%. "
            "Cross-sector signals require lift in ≥2 sectors."
        ),
        "sector_summaries": sector_summaries,
        "sector_baselines": sector_baselines,
        "per_sector_analysis": sectors_analysis,
        "cross_sector_signals": cross_signals,
        "confound_warnings": confound_warnings,
        "key_findings": findings,
        "agency_rules_universal": agency_rules_universal,
        "agency_rules_by_sector": agency_rules_by_sector,
    }

    LOGS.mkdir(exist_ok=True)
    out_path = LOGS / "caption_intelligence_by_sector.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"\n{'='*60}")
    print("CAPTION INTELLIGENCE (SECTOR-CONTROLLED)")
    print(f"{'='*60}")
    for finding in findings:
        print(f"  ▸ {finding}")
    print(f"\nCross-sector language signals:")
    for row in cross_signals["caption_language"]:
        print(f"  {row['bucket']:<14} verdict={row['verdict']:<30} avg_lift={row['avg_lift_across_sectors']:+.0%}")
    print(f"\nUniversal agency rules:")
    for rule in agency_rules_universal:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/caption_intelligence_by_sector.json")


if __name__ == "__main__":
    main()
