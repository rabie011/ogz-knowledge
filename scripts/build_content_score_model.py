#!/usr/bin/env python3
"""
build_content_score_model.py
Build a pre-computed engagement prediction model from corpus signal data.

Model: weighted linear combination of feature signal rates.
Input: logs/engagement_signal_table.json (204 signals, 11 dimensions)
Output: logs/content_score_model.json
"""
import json
from pathlib import Path

LOGS = Path(__file__).parent.parent / "logs"

# Signal type importance weights (sum = 1.0)
# Derived from corpus: patterns are strongest predictor, voice signals weakest
SIGNAL_TYPE_WEIGHTS = {
    "pattern":            0.30,
    "media_type":         0.18,
    "setting":            0.14,
    "lighting":           0.10,
    "composition":        0.10,
    "occasion":           0.09,
    "register":           0.05,
    "tone":               0.05,
    "dialect":            0.03,
    "heritage_vs_modern": 0.04,
    "hospitality_cues":   0.02,
}

CORPUS_BASELINE   = 0.54   # fleet-wide high engagement rate
MIN_OBS_THRESHOLD = 3      # signals below this use corpus baseline


def confidence(n: int) -> float:
    """Sigmoid-style confidence: 0.5 at n=3, 1.0 at n≥15."""
    return min(n / 15.0, 1.0) if n >= MIN_OBS_THRESHOLD else 0.0


def score_brief(signal_lookup: dict, brief: dict) -> dict:
    """
    Score a content brief against the signal lookup.

    brief keys (all optional):
      patterns: list[str]   — pattern slugs
      media_type: str
      setting: str
      lighting: str
      composition: str
      occasion: str
      register: str
      tone: str
      dialect: str
      heritage_vs_modern: str

    Returns: dict with predicted_high_engagement_rate, grade, factors, missing
    """
    weighted_sum = 0.0
    total_weight = 0.0
    factors      = []
    missing      = []

    def get_sig(stype, value):
        sig = signal_lookup.get(stype, {}).get(str(value))
        if sig and sig.get("obs_count", 0) >= MIN_OBS_THRESHOLD and sig["confidence"] > 0:
            return sig
        return None

    # Patterns — average across all slugs provided
    patterns = brief.get("patterns", [])
    if patterns:
        pat_rates = []
        pat_confs = []
        for slug in patterns:
            sig = get_sig("pattern", slug)
            if sig:
                pat_rates.append(sig["high_eng_rate"])
                pat_confs.append(sig["confidence"])
                factors.append({
                    "signal_type": "pattern",
                    "value": slug,
                    "rate": sig["high_eng_rate"],
                    "verdict": sig["verdict"],
                    "obs_count": sig["obs_count"],
                })
            else:
                missing.append(f"pattern:{slug}")
        if pat_rates:
            avg_rate = sum(r * c for r, c in zip(pat_rates, pat_confs)) / sum(pat_confs)
            avg_conf = sum(pat_confs) / len(pat_confs)
            w = SIGNAL_TYPE_WEIGHTS["pattern"] * avg_conf
            weighted_sum += avg_rate * w
            total_weight += w

    # Single-value signals
    for field, stype in [
        ("media_type",         "media_type"),
        ("setting",            "setting"),
        ("lighting",           "lighting"),
        ("composition",        "composition"),
        ("occasion",           "occasion"),
        ("register",           "register"),
        ("tone",               "tone"),
        ("dialect",            "dialect"),
        ("heritage_vs_modern", "heritage_vs_modern"),
    ]:
        val = brief.get(field)
        if not val:
            continue
        sig = get_sig(stype, val)
        if sig:
            w = SIGNAL_TYPE_WEIGHTS.get(stype, 0.03) * sig["confidence"]
            weighted_sum += sig["high_eng_rate"] * w
            total_weight += w
            factors.append({
                "signal_type": stype,
                "value": val,
                "rate": sig["high_eng_rate"],
                "verdict": sig["verdict"],
                "obs_count": sig["obs_count"],
            })
        else:
            missing.append(f"{stype}:{val}")

    # Fill remaining weight with corpus baseline
    if total_weight < 1.0:
        weighted_sum += CORPUS_BASELINE * (1.0 - total_weight)
        total_weight  = 1.0

    score = round(weighted_sum / total_weight, 3) if total_weight > 0 else CORPUS_BASELINE
    grade = "A" if score >= 0.75 else "B" if score >= 0.60 else "C" if score >= 0.45 else "D"
    factors.sort(key=lambda x: -x["rate"])

    return {
        "predicted_high_engagement_rate": score,
        "grade": grade,
        "lift_vs_baseline": round(score - CORPUS_BASELINE, 3),
        "top_contributing_factors": factors[:5],
        "missing_signals": missing,
        "confidence_note": (
            f"Score based on {len(factors)} known signals. "
            f"{len(missing)} features had insufficient data — fell back to baseline ({CORPUS_BASELINE})."
        ),
    }


def main():
    eng_signals  = json.loads((LOGS / "engagement_signal_table.json").read_text())
    all_signals  = eng_signals.get("all_signals", [])

    # Build lookup: {signal_type → {signal_value → {rate, obs_count, confidence, verdict}}}
    signal_lookup: dict = {}
    for s in all_signals:
        st   = s.get("signal_type")
        sv   = s.get("signal_value")
        n    = s.get("obs_count", 0)
        rate = s.get("high_engagement_rate", CORPUS_BASELINE)
        if not st or not sv:
            continue
        if st not in signal_lookup:
            signal_lookup[st] = {}
        signal_lookup[st][sv] = {
            "high_eng_rate": rate,
            "obs_count":     n,
            "confidence":    round(confidence(n), 3),
            "verdict":       s.get("verdict", "neutral"),
        }

    # Self-tests — 5 representative briefs
    test_briefs = [
        {
            "label": "Heritage F&B carousel (expect HIGH)",
            "brief": {
                "patterns":    ["heritage_storytelling_hook", "overhead_tabletop_spread"],
                "media_type":  "carousel_slide",
                "setting":     "heritage_setting",
                "lighting":    "dramatic_moody",
                "composition": "overhead_spread",
                "occasion":    "evergreen",
                "register":    "casual",
                "tone":        "warm",
            }
        },
        {
            "label": "Educational video flat graphic (expect LOW)",
            "brief": {
                "patterns":    ["educational_explainer"],
                "media_type":  "video",
                "setting":     "editorial_lifestyle",
                "lighting":    "branded_bright",
                "composition": "graphic_text",
                "occasion":    "evergreen",
                "register":    "educational",
                "tone":        "informative",
            }
        },
        {
            "label": "Eid carousel with occasion pattern (expect HIGH)",
            "brief": {
                "patterns":   ["eid_occasion_greeting"],
                "media_type": "carousel_slide",
                "occasion":   "eid_al_fitr",
                "tone":       "celebratory",
                "register":   "celebratory",
            }
        },
        {
            "label": "Standard product hero image (expect MID)",
            "brief": {
                "patterns":    ["product_hero"],
                "media_type":  "image",
                "setting":     "tabletop_food",
                "lighting":    "cold_studio",
                "composition": "product_hero_closeup",
                "occasion":    "evergreen",
            }
        },
        {
            "label": "National Day reel patriotic (expect HIGH)",
            "brief": {
                "patterns":  ["national_day_modernity_heritage", "community_pride_statement"],
                "media_type": "reel",
                "occasion":   "national_day",
                "tone":       "patriotic",
                "register":   "patriotic",
            }
        },
    ]

    self_test_results = []
    for t in test_briefs:
        result = score_brief(signal_lookup, t["brief"])
        result["label"] = t["label"]
        self_test_results.append(result)

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "model_description": (
            "Weighted linear combination of feature signal rates from 474-observation Saudi Instagram corpus. "
            "Weights: pattern 30%, media_type 18%, setting 14%, lighting 10%, composition 10%, "
            "occasion 9%, register 5%, tone 5%, dialect 3%, heritage_vs_modern 4%, hospitality_cues 2%. "
            "Confidence-adjusted per signal: full weight at n≥15, half weight at n=3, "
            "below threshold falls back to corpus baseline (0.54)."
        ),
        "corpus_baseline":      CORPUS_BASELINE,
        "signal_type_weights":  SIGNAL_TYPE_WEIGHTS,
        "min_obs_threshold":    MIN_OBS_THRESHOLD,
        "total_signals_loaded": len(all_signals),
        "signal_dimensions":    list(signal_lookup.keys()),
        "signal_lookup":        signal_lookup,
        "self_test_results":    self_test_results,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "content_score_model.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Content score model built")
    print(f"  {len(all_signals)} signals across dimensions: {', '.join(signal_lookup.keys())}")
    print(f"\nSelf-test results:")
    print(f"  {'Grade':<6} {'Score':>6}  {'Lift':>7}  Label")
    print(f"  {'─'*65}")
    for r in self_test_results:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  [{r['grade']}]   {int(r['predicted_high_engagement_rate']*100):>4}%  {lift:>7}  {r['label']}")
    print(f"\nOutput: logs/content_score_model.json")


if __name__ == "__main__":
    main()
