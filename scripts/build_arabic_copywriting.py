#!/usr/bin/env python3
"""
build_arabic_copywriting.py
Mine the Arabic text in caption_text for copywriting intelligence.

Agency questions answered:
  - Which Arabic phrases appear in high-engagement posts (and not in low)?
  - What Arabic sentence openers (first 5 words) drive engagement?
  - Arabic keyword clusters by occasion (Ramadan phrases ≠ National Day phrases)
  - Arabic copy formulas: question / sensory / community / authority openers
  - Brand signature phrases per account

Output: logs/arabic_copywriting.json
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
HIGH_ENG_THRESH = 0.75

# ── Arabic text utilities ──────────────────────────────────────────────────────
_ARABIC_BLOCK = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+")
_HASHTAG_RE   = re.compile(r"#[\w؀-ۿ]+")
_DIACRITIC_RE = re.compile(r"[ً-ٰٟ]")   # harakat


def _strip_diacritics(text: str) -> str:
    return _DIACRITIC_RE.sub("", text)


def _arabic_words(text: str):
    """Return list of Arabic words (no diacritics, no hashtags)."""
    cleaned = _HASHTAG_RE.sub(" ", text)
    cleaned = _strip_diacritics(cleaned)
    return [w.strip() for w in _ARABIC_BLOCK.findall(cleaned) if len(w.strip()) >= 2]


def _arabic_opener(text: str) -> str:
    """First 5 Arabic words of caption, joined — '' if less than 2 Arabic words."""
    words = _arabic_words(text)
    if len(words) < 2:
        return ""
    return " ".join(words[:5])


def _opener_formula(text: str) -> str:
    """Classify opener into broad Arabic copy formula."""
    head = text.strip()[:120]
    # Question
    if "?" in head or "؟" in head:
        return "question"
    ar_q = ["هل", "ما ", "ماذا", "من ", "أين", "كيف", "متى", "لماذا"]
    for q in ar_q:
        if head.startswith(q):
            return "question"
    # Community / invitation
    invite = ["حياكم", "أهلاً", "أهلا", "تعالوا", "تفضلوا", "عندنا", "جربوا", "اكتشف", "شاركونا"]
    for w in invite:
        if w in head:
            return "community_invite"
    # Sensory / emotive
    sensory = ["طعم", "رائحة", "لذيذ", "مميز", "أحلى", "ألذ", "الأجود", "جمال", "روعة", "ذكريات"]
    for w in sensory:
        if w in head:
            return "sensory_emotive"
    # Announcement / new
    announce = ["جديد", "يتوفر", "أطلقنا", "إطلاق", "الآن", "توفر", "حصري", "متاح"]
    for w in announce:
        if w in head:
            return "announcement"
    # Heritage / occasion
    heritage = ["رمضان", "العيد", "اليوم الوطني", "التأسيس", "الوطن", "المملكة", "تراث", "أصيل"]
    for w in heritage:
        if w in head:
            return "heritage_occasion"
    return "other"


def _occasion_keywords(text: str) -> list:
    """Extract Arabic keywords relevant to specific occasions."""
    occ_map = {
        "ramadan":      ["رمضان", "إفطار", "سحور", "ليلة القدر", "الفطر", "تراويح"],
        "national_day": ["اليوم الوطني", "المملكة", "السعودية", "وطن", "فخر"],
        "founding_day": ["يوم التأسيس", "التأسيس", "الدرعية", "محمد بن سعود"],
        "eid":          ["عيد", "تقبل الله", "عيد مبارك", "كل عام وأنتم"],
        "general":      ["طازج", "يومي", "اليوم", "الآن", "جديد"],
    }
    found = []
    for occ, kws in occ_map.items():
        for kw in kws:
            if kw in text:
                found.append(kw)
    return found


def _bigrams(word_list: list) -> list:
    """Return list of 2-word bigrams."""
    return [f"{word_list[i]} {word_list[i+1]}" for i in range(len(word_list) - 1)]


def main():
    # By obs: collect high/low eng Arabic phrases
    phrase_high = Counter()   # phrases that appear in HIGH-eng posts
    phrase_low  = Counter()   # phrases in LOW-eng posts
    phrase_any  = Counter()   # total appearances

    opener_high = Counter()
    opener_low  = Counter()

    formula_eng = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    occasion_phrases = defaultdict(Counter)   # occasion → phrase → count

    # Account-level signature phrases
    account_phrases = defaultdict(lambda: {"high": Counter(), "low": Counter()})

    total = 0
    ar_obs = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        vo  = data.get("voice_observations") or {}
        qa  = data.get("quality_assessment")  or {}
        cn  = data.get("cultural_notes")      or {}

        cap = vo.get("caption_text")
        if cap is None:
            continue   # not extracted yet

        cap_str = str(cap)
        ar_words = _arabic_words(cap_str)
        if len(ar_words) < 3:
            continue   # not enough Arabic to analyse

        ar_obs += 1
        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = eng >= HIGH_ENG_THRESH
        account = data.get("account_handle_normalized") or "unknown"
        occ     = str(cn.get("occasion_relevance") or "evergreen").lower() or "evergreen"

        # Phrases: unigrams + bigrams
        phrases = ar_words + _bigrams(ar_words)
        for ph in phrases:
            phrase_any[ph] += 1
            if is_high:
                phrase_high[ph] += 1
            else:
                phrase_low[ph] += 1
            account_phrases[account]["high" if is_high else "low"][ph] += 1

        # Opener (first 5 words)
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
        occ_kws = _occasion_keywords(cap_str)
        for kw in occ_kws:
            occasion_phrases[occ][kw] += 1

    # ── Discriminative phrase lists ────────────────────────────────────────────
    # "Signal words" = high freq in HIGH-eng but much less so in LOW-eng
    signal_words = []
    avoid_words  = []
    MIN_COUNT = 3

    for phrase, total_cnt in phrase_any.items():
        if total_cnt < MIN_COUNT:
            continue
        high_cnt = phrase_high.get(phrase, 0)
        low_cnt  = phrase_low.get(phrase, 0)
        # Ratio: fraction of appearances that are high-eng
        high_ratio = high_cnt / total_cnt
        if high_ratio >= 0.70 and high_cnt >= MIN_COUNT:
            signal_words.append({
                "phrase": phrase, "total": total_cnt,
                "in_high_eng": high_cnt, "in_low_eng": low_cnt,
                "high_ratio": round(high_ratio, 2),
            })
        if high_ratio <= 0.30 and low_cnt >= MIN_COUNT:
            avoid_words.append({
                "phrase": phrase, "total": total_cnt,
                "in_high_eng": high_cnt, "in_low_eng": low_cnt,
                "high_ratio": round(high_ratio, 2),
            })

    signal_words.sort(key=lambda x: (-x["high_ratio"], -x["in_high_eng"]))
    avoid_words.sort(key=lambda x: (x["high_ratio"], -x["in_low_eng"]))

    # ── Top openers ────────────────────────────────────────────────────────────
    # Openers that appear ≥2 times in high-eng but rarely in low-eng
    top_openers = []
    all_openers = set(list(opener_high.keys()) + list(opener_low.keys()))
    for op in all_openers:
        hc = opener_high.get(op, 0)
        lc = opener_low.get(op, 0)
        total_op = hc + lc
        if total_op < 2:
            continue
        ratio = hc / total_op
        if ratio >= 0.6 and hc >= 2:
            top_openers.append({
                "opener": op, "high_eng_appearances": hc,
                "low_eng_appearances": lc, "high_ratio": round(ratio, 2),
            })
    top_openers.sort(key=lambda x: (-x["high_ratio"], -x["high_eng_appearances"]))

    # ── Formula table ──────────────────────────────────────────────────────────
    formula_table = []
    for formula, d in formula_eng.items():
        n = d["count"]
        r = round(d["high"] / n, 3) if n else 0
        formula_table.append({
            "formula": formula, "count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"] / n, 3) if n else 0,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    formula_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))

    # ── Occasion keyword clusters ──────────────────────────────────────────────
    occ_clusters = {}
    for occ, kw_counter in occasion_phrases.items():
        occ_clusters[occ] = [
            {"keyword": kw, "count": cnt}
            for kw, cnt in kw_counter.most_common(15)
        ]

    # ── Findings ───────────────────────────────────────────────────────────────
    findings = []
    if signal_words:
        top3 = [w["phrase"] for w in signal_words[:3]]
        findings.append(f"High-engagement Arabic signal phrases: {' / '.join(top3)}")
    if avoid_words:
        bot3 = [w["phrase"] for w in avoid_words[:3]]
        findings.append(f"Low-engagement Arabic phrases to avoid: {' / '.join(bot3)}")
    if formula_table:
        best_f = formula_table[0]
        findings.append(
            f"Best opener formula: '{best_f['formula']}' = "
            f"{int(best_f['high_engagement_rate']*100)}% (n={best_f['count']})"
        )
    if top_openers:
        findings.append(
            f"Best performing Arabic opener: '{top_openers[0]['opener']}' "
            f"({top_openers[0]['high_eng_appearances']} high-eng appearances)"
        )

    agency_rules = []
    if formula_table:
        agency_rules.append(f"Lead with '{formula_table[0]['formula']}' opener — best formula")
    if signal_words:
        agency_rules.append(f"Use these Arabic phrases: {', '.join(w['phrase'] for w in signal_words[:5])}")
    if avoid_words:
        agency_rules.append(f"Avoid these Arabic phrases in captions: {', '.join(w['phrase'] for w in avoid_words[:3])}")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "arabic_caption_obs": ar_obs,
        "signal_phrases_high_eng": signal_words[:50],
        "avoid_phrases_low_eng": avoid_words[:30],
        "top_arabic_openers": top_openers[:30],
        "opener_formula_table": formula_table,
        "occasion_keyword_clusters": occ_clusters,
        "key_findings": findings,
        "agency_rules": agency_rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "arabic_copywriting.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Arabic copywriting: {ar_obs}/{total} obs with Arabic captions")
    print(f"\nOpener formula → engagement:")
    for r in formula_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['formula']:<26} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nTop Arabic signal phrases (high-eng):")
    for w in signal_words[:10]:
        print(f"  '{w['phrase']}'  high={w['in_high_eng']}  low={w['in_low_eng']}  ratio={w['high_ratio']}")
    print(f"\nTop Arabic openers (high-eng):")
    for op in top_openers[:8]:
        print(f"  '{op['opener']}'  ×{op['high_eng_appearances']} high-eng")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/arabic_copywriting.json")


if __name__ == "__main__":
    main()
