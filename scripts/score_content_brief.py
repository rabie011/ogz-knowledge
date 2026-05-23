#!/usr/bin/env python3
"""
score_content_brief.py
Score any content brief against the corpus prediction model.

Usage:
  python3 scripts/score_content_brief.py
      → runs self-test results from the model file

  python3 scripts/score_content_brief.py --brief '{"patterns":["heritage_storytelling_hook"],"media_type":"carousel_slide"}'
      → scores a JSON brief from the command line

  python3 scripts/score_content_brief.py --interactive
      → step-by-step prompt for each field

Requires: logs/content_score_model.json (run build_content_score_model.py first)
"""
import json
import sys
import argparse
from pathlib import Path

LOGS             = Path(__file__).parent.parent / "logs"
CORPUS_BASELINE  = 0.54
MIN_OBS_THRESHOLD = 3


def load_model() -> dict:
    path = LOGS / "content_score_model.json"
    if not path.exists():
        print("ERROR: content_score_model.json not found.")
        print("       Run: python3 scripts/build_content_score_model.py")
        sys.exit(1)
    return json.loads(path.read_text())


def score_brief(signal_lookup: dict, brief: dict) -> dict:
    weights = {
        "pattern": 0.30, "media_type": 0.18, "setting": 0.14,
        "lighting": 0.10, "composition": 0.10, "occasion": 0.09,
        "register": 0.05, "tone": 0.05, "dialect": 0.03,
        "heritage_vs_modern": 0.04, "hospitality_cues": 0.02,
    }

    def get_sig(stype, value):
        sig = signal_lookup.get(stype, {}).get(str(value))
        if sig and sig.get("obs_count", 0) >= MIN_OBS_THRESHOLD and sig.get("confidence", 0) > 0:
            return sig
        return None

    weighted_sum = 0.0
    total_weight = 0.0
    factors      = []
    missing      = []

    patterns = brief.get("patterns", [])
    if patterns:
        pat_rates, pat_confs = [], []
        for slug in patterns:
            sig = get_sig("pattern", slug)
            if sig:
                pat_rates.append(sig["high_eng_rate"])
                pat_confs.append(sig["confidence"])
                factors.append({"signal_type": "pattern", "value": slug,
                                 "rate": sig["high_eng_rate"], "verdict": sig["verdict"],
                                 "obs_count": sig["obs_count"]})
            else:
                missing.append(f"pattern:{slug}")
        if pat_rates:
            avg_rate = sum(r*c for r,c in zip(pat_rates,pat_confs)) / sum(pat_confs)
            avg_conf = sum(pat_confs) / len(pat_confs)
            w = weights["pattern"] * avg_conf
            weighted_sum += avg_rate * w
            total_weight += w

    for field, stype in [
        ("media_type","media_type"), ("setting","setting"), ("lighting","lighting"),
        ("composition","composition"), ("occasion","occasion"), ("register","register"),
        ("tone","tone"), ("dialect","dialect"), ("heritage_vs_modern","heritage_vs_modern"),
    ]:
        val = brief.get(field)
        if not val: continue
        sig = get_sig(stype, val)
        if sig:
            w = weights.get(stype, 0.03) * sig["confidence"]
            weighted_sum += sig["high_eng_rate"] * w
            total_weight += w
            factors.append({"signal_type": stype, "value": val,
                             "rate": sig["high_eng_rate"], "verdict": sig["verdict"],
                             "obs_count": sig["obs_count"]})
        else:
            missing.append(f"{stype}:{val}")

    if total_weight < 1.0:
        weighted_sum += CORPUS_BASELINE * (1.0 - total_weight)
        total_weight = 1.0

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
            f"Based on {len(factors)} known signals. "
            f"{len(missing)} features had insufficient corpus data."
        ),
    }


def print_result(result: dict, label: str = "Brief"):
    score = result["predicted_high_engagement_rate"]
    grade = result["grade"]
    lift  = result["lift_vs_baseline"]
    lift_str = f"+{int(lift*100)}%" if lift >= 0 else f"{int(lift*100)}%"

    grade_color = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(grade, "⚪")
    print(f"\n{'═'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"  {grade_color} Grade {grade}  —  {int(score*100)}% predicted high engagement  ({lift_str} vs {int(CORPUS_BASELINE*100)}% baseline)")
    print(f"\n  Top signals:")
    for f in result["top_contributing_factors"]:
        bar = "█" * int(f["rate"] * 10) + "░" * (10 - int(f["rate"] * 10))
        verdict_tag = {"strong_positive":"✅","positive":"✅","neutral":"➖","avoid":"⚠️","insufficient_data":"❓"}.get(f["verdict"],"")
        print(f"    {f['signal_type']:<16} {f['value']:<28} {int(f['rate']*100):>3}%  {bar}  {verdict_tag}  n={f['obs_count']}")
    if result["missing_signals"]:
        print(f"\n  ⚪ Unknown (fell back to baseline): {', '.join(result['missing_signals'][:6])}")
    print(f"\n  {result['confidence_note']}")
    print(f"{'═'*60}")


def interactive_mode(signal_lookup: dict):
    print("\n" + "═"*60)
    print("  Content Brief Scorer — interactive mode")
    print("  Press ENTER to skip any field. Type 'quit' to exit.")
    print("═"*60)
    while True:
        brief = {}
        print()
        raw = input("  patterns (comma-sep slugs): ").strip()
        if raw.lower() == "quit": break
        if raw:
            brief["patterns"] = [p.strip() for p in raw.split(",") if p.strip()]

        for field, hint in [
            ("media_type",  "image / carousel_slide / reel / video"),
            ("setting",     "heritage_setting / restaurant_indoor / tabletop_food / outdoor_nature / ..."),
            ("lighting",    "dramatic_moody / natural_daylight / cold_studio / branded_bright / ..."),
            ("composition", "overhead_spread / architectural_frame / product_hero_closeup / ..."),
            ("occasion",    "evergreen / eid_al_fitr / national_day / ramadan / ..."),
            ("register",    "casual / formal / aspirational / playful / celebratory / ..."),
            ("tone",        "warm / playful / proud / nostalgic / patriotic / informative / ..."),
        ]:
            val = input(f"  {field} ({hint}): ").strip()
            if val.lower() == "quit": return
            if val: brief[field] = val

        result = score_brief(signal_lookup, brief)
        print_result(result)


def main():
    parser = argparse.ArgumentParser(description="Score a content brief for predicted engagement")
    parser.add_argument("--brief",       type=str, help="JSON brief string")
    parser.add_argument("--interactive", action="store_true", help="Interactive prompt mode")
    args = parser.parse_args()

    model         = load_model()
    signal_lookup = model["signal_lookup"]

    if args.interactive:
        interactive_mode(signal_lookup)

    elif args.brief:
        try:
            brief = json.loads(args.brief)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON — {e}")
            sys.exit(1)
        result = score_brief(signal_lookup, brief)
        print_result(result, "Content Brief")

    else:
        # Default: show self-tests
        print("\nContent Score Model — self-test results")
        print(f"  Corpus baseline: {int(CORPUS_BASELINE*100)}% high engagement\n")
        for t in model.get("self_test_results", []):
            lift = f"+{int(t['lift_vs_baseline']*100)}%" if t['lift_vs_baseline'] >= 0 else f"{int(t['lift_vs_baseline']*100)}%"
            grade_icon = {"A":"🟢","B":"🟡","C":"🟠","D":"🔴"}.get(t['grade'],"⚪")
            print(f"  {grade_icon} [{t['grade']}] {int(t['predicted_high_engagement_rate']*100):>3}% ({lift})  {t['label']}")
        print(f"\n  Usage:")
        print(f"    python3 scripts/score_content_brief.py --interactive")
        print(f"    python3 scripts/score_content_brief.py --brief '{{\"patterns\":[\"heritage_storytelling_hook\"],\"media_type\":\"carousel_slide\"}}'")


if __name__ == "__main__":
    main()
