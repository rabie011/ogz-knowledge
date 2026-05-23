#!/usr/bin/env python3
"""
build_phrase_engagement.py
Cross notable_phrases from voice_observations with engagement outcomes.
Which Arabic (and English) phrases appear in the highest-engagement posts?
Output: logs/phrase_engagement_analysis.json
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54


def normalize_phrase(p: str) -> str:
    """Light normalization: strip, lowercase for grouping."""
    return p.strip().lower()


def is_arabic(s: str) -> bool:
    return bool(re.search(r'[؀-ۿ]', s))


def main():
    # Per-phrase stats
    phrases = defaultdict(lambda: {
        "count": 0, "high": 0, "sum": 0.0,
        "sectors": Counter(),
        "tones": Counter(),
        "occasions": Counter(),
        "accounts": set(),
        "raw_forms": Counter(),  # original casings
    })

    total_obs = 0
    obs_with_phrases = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total_obs += 1
        vo   = data.get("voice_observations",{}) or {}
        raw_phrases = vo.get("notable_phrases") or []
        if not raw_phrases: continue

        obs_with_phrases += 1
        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0

        sector  = data.get("sector","unknown") or "unknown"
        account = data.get("account_handle_normalized","unknown")
        tone    = str((data.get("voice_observations",{}) or {}).get("tone") or "").lower()
        cn      = data.get("cultural_notes",{}) or {}
        occ     = str(cn.get("occasion_relevance") or "evergreen").lower().strip() or "evergreen"

        for ph in raw_phrases:
            if not isinstance(ph, str) or not ph.strip(): continue
            key = normalize_phrase(ph)
            if len(key) < 2: continue
            d = phrases[key]
            d["count"]  += 1
            d["high"]   += is_high
            d["sum"]    += eng
            d["sectors"][sector] += 1
            d["accounts"].add(account)
            d["raw_forms"][ph.strip()] += 1
            if tone: d["tones"][tone] += 1
            d["occasions"][occ] += 1

    # Build phrase table
    phrase_table = []
    for key, d in phrases.items():
        n = d["count"]
        if n < 2: continue  # skip single-use phrases
        rate = round(d["high"]/n, 3)
        avg  = round(d["sum"]/n, 3)
        # Most common raw form
        canonical = d["raw_forms"].most_common(1)[0][0] if d["raw_forms"] else key
        phrase_table.append({
            "phrase": canonical,
            "phrase_normalized": key,
            "is_arabic": is_arabic(canonical),
            "frequency": n,
            "account_count": len(d["accounts"]),
            "high_engagement_rate": rate,
            "avg_engagement_score": avg,
            "lift_vs_baseline": round(rate - CORPUS_BASELINE, 3),
            "dominant_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
            "dominant_tone": d["tones"].most_common(1)[0][0] if d["tones"] else None,
            "dominant_occasion": d["occasions"].most_common(1)[0][0] if d["occasions"] else None,
        })

    # Sort variants
    by_engagement = sorted(phrase_table, key=lambda x: (-x["high_engagement_rate"], -x["frequency"]))
    by_frequency  = sorted(phrase_table, key=lambda x: -x["frequency"])

    # Arabic vs English split
    arabic_phrases = [p for p in by_engagement if p["is_arabic"]]
    english_phrases= [p for p in by_engagement if not p["is_arabic"]]

    # Cross-account phrases (appear in 3+ accounts)
    cross_account = [p for p in by_engagement if p["account_count"] >= 3]

    # Key findings
    findings = []
    if arabic_phrases:
        a = arabic_phrases[0]
        findings.append(
            f"Top Arabic phrase by engagement: '{a['phrase']}' "
            f"({int(a['high_engagement_rate']*100)}% high eng, n={a['frequency']}, {a['account_count']} accounts)"
        )
    if english_phrases:
        e = english_phrases[0]
        findings.append(
            f"Top English phrase: '{e['phrase']}' "
            f"({int(e['high_engagement_rate']*100)}%, n={e['frequency']})"
        )
    if by_frequency:
        most_used = by_frequency[0]
        findings.append(
            f"Most-used phrase: '{most_used['phrase']}' (n={most_used['frequency']}, "
            f"{int(most_used['high_engagement_rate']*100)}% high eng)"
        )
    findings.append(
        f"{obs_with_phrases}/{total_obs} observations have notable phrases. "
        f"{len(phrase_table)} unique phrases appear 2+ times."
    )

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total_obs,
        "obs_with_phrases": obs_with_phrases,
        "unique_phrases_2plus_uses": len(phrase_table),
        "top_30_by_engagement": by_engagement[:30],
        "top_30_by_frequency": by_frequency[:30],
        "top_arabic_phrases": arabic_phrases[:20],
        "top_english_phrases": english_phrases[:20],
        "cross_account_phrases": cross_account[:20],
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "phrase_engagement_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Phrase engagement: {obs_with_phrases}/{total_obs} obs have phrases, {len(phrase_table)} unique (2+ uses)")
    print(f"\nTop 15 phrases by engagement rate:")
    print(f"  {'Phrase':<42} {'Lang':<4} {'HighEng':>8}  {'n':>4}  {'Lift':>7}")
    print("  " + "─"*72)
    for p in by_engagement[:15]:
        lang = "AR" if p["is_arabic"] else "EN"
        lift = f"+{int(p['lift_vs_baseline']*100)}%" if p['lift_vs_baseline'] >= 0 else f"{int(p['lift_vs_baseline']*100)}%"
        phrase_display = p["phrase"][:40]
        print(f"  {phrase_display:<42} {lang:<4} {int(p['high_engagement_rate']*100):>7}%  {p['frequency']:>4}  {lift:>7}")
    print(f"\nOutput: logs/phrase_engagement_analysis.json")


if __name__ == "__main__":
    main()
