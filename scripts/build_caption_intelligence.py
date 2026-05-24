#!/usr/bin/env python3
"""
build_caption_intelligence.py
Mine voice_observations.caption_text and derived fields across all obs.

Agency questions answered:
  - Short vs medium vs long captions — which engage more?
  - Hashtag count vs engagement (0 / 1-5 / 6-15 / 16+)
  - Emoji presence vs engagement
  - Question-open captions vs statement-open
  - Arabic-only vs English-only vs bilingual × engagement
  - Best caption length per sector
  - Best caption language per occasion

Output: logs/caption_intelligence.json
"""
import json
import re
import unicodedata
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
CORPUS_BASELINE = 0.54

# ── Language detection ─────────────────────────────────────────────────────────
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
    """True if caption opens with a question (Arabic or English)."""
    # Take first 80 chars
    head = text.strip()[:80]
    # Arabic question markers: ؟ or starts with question words
    ar_q_words = ["هل", "ما", "ماذا", "من", "أين", "كيف", "متى", "لماذا", "ما هو", "ما هي"]
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


def main():
    # Buckets
    by_length   = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0, "sectors": Counter()})
    by_hashtag  = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_emoji    = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_lang     = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0, "sectors": Counter()})
    by_open     = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    # Cross-cuts
    lang_sector = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))
    lang_occ    = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))
    len_sector  = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))

    total = 0
    cap_filled = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        vo  = data.get("voice_observations") or {}
        qa  = data.get("quality_assessment")  or {}
        cn  = data.get("cultural_notes")      or {}
        cr  = data.get("content_ref")         or {}

        cap = vo.get("caption_text")
        if cap is None:
            continue   # not yet extracted — skip

        cap_filled += 1
        cap_str     = str(cap)

        wc           = vo.get("caption_word_count") or 0
        hashtag_cnt  = vo.get("hashtag_count")      or 0
        emoji        = vo.get("has_emoji")

        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector")             or "unknown"
        occ     = str(cn.get("occasion_relevance") or "evergreen").lower() or "evergreen"

        # Length
        lb = _length_bucket(int(wc))
        by_length[lb]["count"]  += 1
        by_length[lb]["high"]   += is_high
        by_length[lb]["sum"]    += eng
        by_length[lb]["sectors"][sector] += 1
        len_sector[lb][sector]["count"] += 1
        len_sector[lb][sector]["high"]  += is_high

        # Hashtag count
        hb = _hashtag_bucket(int(hashtag_cnt))
        by_hashtag[hb]["count"] += 1
        by_hashtag[hb]["high"]  += is_high
        by_hashtag[hb]["sum"]   += eng

        # Emoji
        emoji_label = "has_emoji" if emoji else "no_emoji"
        by_emoji[emoji_label]["count"] += 1
        by_emoji[emoji_label]["high"]  += is_high
        by_emoji[emoji_label]["sum"]   += eng

        # Caption language
        cap_lang = _caption_language(cap_str) if cap_str else "empty"
        by_lang[cap_lang]["count"]  += 1
        by_lang[cap_lang]["high"]   += is_high
        by_lang[cap_lang]["sum"]    += eng
        by_lang[cap_lang]["sectors"][sector] += 1
        lang_sector[cap_lang][sector]["count"] += 1
        lang_sector[cap_lang][sector]["high"]  += is_high
        lang_occ[cap_lang][occ]["count"]       += 1
        lang_occ[cap_lang][occ]["high"]        += is_high

        # Question-open
        is_q = _is_question_open(cap_str) if cap_str else False
        q_label = "question_open" if is_q else "statement_open"
        by_open[q_label]["count"] += 1
        by_open[q_label]["high"]  += is_high
        by_open[q_label]["sum"]   += eng

    def _rate(d):
        return round(d["high"] / d["count"], 3) if d["count"] else 0

    def _table(bucket_dict, key_name):
        rows = []
        for k, d in bucket_dict.items():
            n = d["count"]
            r = _rate(d)
            row = {
                key_name: k,
                "count": n,
                "high_engagement_rate": r,
                "avg_engagement": round(d["sum"] / n, 3) if n else 0,
                "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
            }
            if "sectors" in d:
                row["top_sector"] = d["sectors"].most_common(1)[0][0] if d["sectors"] else None
            rows.append(row)
        rows.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))
        return rows

    length_table  = _table(by_length,  "caption_length_bucket")
    hashtag_table = _table(by_hashtag, "hashtag_count_bucket")
    emoji_table   = _table(by_emoji,   "emoji_presence")
    lang_table    = _table(by_lang,    "caption_language")
    open_table    = _table(by_open,    "caption_open_style")

    # Language × sector rows
    lang_sector_rows = []
    for lang, sects in lang_sector.items():
        for sect, d in sects.items():
            if d["count"] >= 3:
                r = round(d["high"] / d["count"], 3)
                lang_sector_rows.append({
                    "language": lang, "sector": sect,
                    "count": d["count"],
                    "high_eng_rate": r,
                    "lift": round(r - CORPUS_BASELINE, 3),
                })
    lang_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Language × occasion rows
    lang_occ_rows = []
    for lang, occs in lang_occ.items():
        for occ, d in occs.items():
            if d["count"] >= 3:
                r = round(d["high"] / d["count"], 3)
                lang_occ_rows.append({
                    "language": lang, "occasion": occ,
                    "count": d["count"],
                    "high_eng_rate": r,
                    "lift": round(r - CORPUS_BASELINE, 3),
                })
    lang_occ_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Key findings
    findings = []
    if length_table:
        best = length_table[0]
        worst = length_table[-1]
        findings.append(
            f"Best caption length: '{best['caption_length_bucket']}' = "
            f"{int(best['high_engagement_rate']*100)}% high-eng "
            f"({'+' if best['lift_vs_baseline']>=0 else ''}{int(best['lift_vs_baseline']*100)}pp vs baseline)"
        )
        findings.append(
            f"Worst caption length: '{worst['caption_length_bucket']}' = "
            f"{int(worst['high_engagement_rate']*100)}%"
        )
    if hashtag_table:
        best_h = hashtag_table[0]
        findings.append(
            f"Best hashtag count: '{best_h['hashtag_count_bucket']}' = "
            f"{int(best_h['high_engagement_rate']*100)}%"
        )
    if emoji_table:
        has_e = next((r for r in emoji_table if r["emoji_presence"] == "has_emoji"), None)
        no_e  = next((r for r in emoji_table if r["emoji_presence"] == "no_emoji"), None)
        if has_e and no_e:
            diff = has_e["high_engagement_rate"] - no_e["high_engagement_rate"]
            effect = "HELPS" if diff > 0.05 else "HURTS" if diff < -0.05 else "NEUTRAL"
            findings.append(
                f"Emoji {effect}: with={int(has_e['high_engagement_rate']*100)}% "
                f"vs without={int(no_e['high_engagement_rate']*100)}% "
                f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
            )
    if lang_table:
        best_l = lang_table[0]
        findings.append(
            f"Best caption language: '{best_l['caption_language']}' = "
            f"{int(best_l['high_engagement_rate']*100)}% (n={best_l['count']})"
        )
    if open_table:
        q = next((r for r in open_table if "question" in r["caption_open_style"]), None)
        s = next((r for r in open_table if "statement" in r["caption_open_style"]), None)
        if q and s:
            diff = q["high_engagement_rate"] - s["high_engagement_rate"]
            findings.append(
                f"Question-open captions: {int(q['high_engagement_rate']*100)}% "
                f"vs statement-open: {int(s['high_engagement_rate']*100)}% "
                f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
            )

    # Agency rules
    agency_rules = []
    if length_table:
        top_len = length_table[0]["caption_length_bucket"]
        agency_rules.append(f"Target caption length: '{top_len}' — highest engagement bucket")
    if hashtag_table:
        top_h = hashtag_table[0]["hashtag_count_bucket"]
        agency_rules.append(f"Optimal hashtag count: {top_h} — top performer")
    if emoji_table:
        has_e = next((r for r in emoji_table if r["emoji_presence"] == "has_emoji"), None)
        no_e  = next((r for r in emoji_table if r["emoji_presence"] == "no_emoji"), None)
        if has_e and no_e:
            if has_e["lift_vs_baseline"] > no_e["lift_vs_baseline"]:
                agency_rules.append("Use emoji in captions — they lift engagement")
            else:
                agency_rules.append("Avoid emoji — they hurt engagement in this corpus")
    if lang_table:
        agency_rules.append(
            f"Default caption language: '{lang_table[0]['caption_language']}' "
            f"({int(lang_table[0]['high_engagement_rate']*100)}% high-eng)"
        )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_caption": cap_filled,
        "obs_without_caption": total - cap_filled,
        "caption_length_table": length_table,
        "hashtag_count_table": hashtag_table,
        "emoji_presence_table": emoji_table,
        "caption_language_table": lang_table,
        "caption_open_style_table": open_table,
        "language_by_sector": lang_sector_rows,
        "language_by_occasion": lang_occ_rows,
        "key_findings": findings,
        "agency_rules": agency_rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "caption_intelligence.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Caption intelligence: {cap_filled}/{total} obs with captions")
    print(f"\nCaption length → engagement:")
    for r in length_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['caption_length_bucket']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nHashtag count → engagement:")
    for r in hashtag_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  hashtags={r['hashtag_count_bucket']:<10} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nEmoji → engagement:")
    for r in emoji_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['emoji_presence']:<20} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nCaption language → engagement:")
    for r in lang_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['caption_language']:<14} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nCaption open style → engagement:")
    for r in open_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['caption_open_style']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/caption_intelligence.json")


if __name__ == "__main__":
    main()
