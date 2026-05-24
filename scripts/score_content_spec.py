#!/usr/bin/env python3
"""
score_content_spec.py
Score any content specification against the OGZ corpus.
Input: dimension=value pairs (sector, occasion, format, setting, tone, etc.)
Output: predicted engagement score + breakdown of which signals help/hurt

Usage:
  python3 scripts/score_content_spec.py \
    sector=food_and_beverage occasion=ramadan content_type=image \
    setting=restaurant_indoor tone=celebratory visual_complexity=complex
  python3 scripts/score_content_spec.py --interactive
"""
import json, sys, argparse
from pathlib import Path

LOGS = Path(__file__).parent.parent / "logs"

# Dimension weights — how much each dimension contributes to prediction
# Based on master_signal_table variance across values
DIM_WEIGHTS = {
    "occasion":          0.20,
    "sector":            0.18,
    "content_type":      0.12,
    "visual_complexity": 0.10,
    "aspect_ratio":      0.09,
    "tone":              0.08,
    "register":          0.07,
    "heritage_framing":  0.06,
    "setting":           0.05,
    "lighting":          0.03,
    "day_of_week":       0.02,
}
WEIGHT_TOTAL = sum(DIM_WEIGHTS.values())

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def build_signal_lookup():
    """Build dim → val → avg_engagement lookup from master_signal_table."""
    mst = _load("master_signal_table.json")
    lookup = {}
    for dim, signals in (mst.get("by_dimension") or {}).items():
        lookup[dim] = {}
        for sig in (signals if isinstance(signals, list) else []):
            val = sig.get("value","")
            avg = sig.get("avg_engagement")
            if val and avg is not None:
                lookup[dim][str(val).lower().strip()] = {
                    "avg_engagement": avg,
                    "lift": sig.get("lift_vs_avg", 0),
                    "count": sig.get("count", 0),
                    "confidence": sig.get("confidence","?"),
                }
    # Add sector-level data from sector_fingerprint
    sfp = _load("sector_fingerprint.json")
    lookup["sector"] = {}
    for sec, data in (sfp.get("sectors") or {}).items():
        avg = data.get("avg_engagement")
        if avg is not None:
            lookup["sector"][sec] = {
                "avg_engagement": avg,
                "lift": data.get("lift_vs_corpus", 0),
                "count": data.get("obs_count", 0),
                "confidence": "high" if (data.get("obs_count") or 0) >= 30 else "medium",
            }
    return lookup


def score(spec_dict, baseline=0.654):
    """
    Score a content spec. Returns:
        predicted_engagement, grade, breakdown
    """
    lookup = build_signal_lookup()

    scored_dims = []
    total_weight = 0

    for dim, val in spec_dict.items():
        if dim not in DIM_WEIGHTS: continue
        val_clean = str(val).lower().strip()
        dim_data  = lookup.get(dim, {})
        sig       = dim_data.get(val_clean)

        if not sig:
            # Try partial match
            for k,v in dim_data.items():
                if val_clean in k or k in val_clean:
                    sig = v; break

        w = DIM_WEIGHTS[dim]
        total_weight += w

        if sig:
            scored_dims.append({
                "dimension":  dim,
                "value":      val,
                "weight":     w,
                "avg_eng":    round(sig["avg_engagement"], 3),
                "lift":       round(sig["lift"], 3),
                "count":      sig["count"],
                "confidence": sig["confidence"],
            })
        else:
            scored_dims.append({
                "dimension":  dim,
                "value":      val,
                "weight":     w,
                "avg_eng":    baseline,
                "lift":       0,
                "count":      0,
                "confidence": "unknown",
            })

    if not scored_dims:
        return baseline, "B", []

    # Weighted average of known engagement values
    weighted_sum = sum(d["avg_eng"] * d["weight"] for d in scored_dims)
    eff_weight   = sum(d["weight"] for d in scored_dims)
    # Blend with baseline for unscored dimensions
    unscored_weight = WEIGHT_TOTAL - eff_weight
    predicted = (weighted_sum + baseline * unscored_weight) / WEIGHT_TOTAL

    # Clamp to [0.20, 0.98]
    predicted = max(0.20, min(0.98, round(predicted, 3)))

    grade = "A+" if predicted >= 0.88 else "A" if predicted >= 0.80 else \
            "B+" if predicted >= 0.72 else "B" if predicted >= 0.64 else \
            "C+" if predicted >= 0.55 else "C" if predicted >= 0.45 else "D"

    # Sort: biggest boosters first, then killers
    scored_dims.sort(key=lambda x: -x["lift"])

    return predicted, grade, scored_dims


def print_score(spec_dict, predicted, grade, breakdown, baseline=0.654):
    W = 66
    print(f"\n{'═'*W}")
    print(f"  OGZ ENGAGEMENT SCORE")
    spec_str = "  " + " | ".join(f"{k}={v}" for k,v in spec_dict.items())
    print(spec_str[:W])
    print(f"{'═'*W}")
    pct = int(predicted * 100)
    lift = predicted - baseline
    lift_str = f"+{lift:.0%}" if lift >= 0 else f"{lift:.0%}"
    print(f"\n  PREDICTED:  {pct}%  Grade {grade}  (baseline {int(baseline*100)}%, lift {lift_str})\n")
    print(f"  {'Dimension':<22}  {'Value':<22}  {'Eng':>5}  {'Lift':>6}  n")
    print(f"  {'─'*62}")
    for d in breakdown:
        l_str = f"+{d['lift']:.0%}" if d['lift'] >= 0 else f"{d['lift']:.0%}"
        print(f"  {d['dimension']:<22}  {str(d['value']):<22}  {d['avg_eng']:.0%}  {l_str:>6}  {d['count']}")
    print(f"\n{'═'*W}\n")


def main():
    parser = argparse.ArgumentParser(description="OGZ Content Engagement Scorer")
    parser.add_argument("spec", nargs="*", help="dimension=value pairs")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or not args.spec:
        print("\nOGZ Content Scorer — Interactive")
        print("─"*40)
        print("Enter specs as dimension=value pairs (empty line to score):")
        print("Dimensions: sector, occasion, content_type, aspect_ratio, setting,")
        print("            lighting, visual_complexity, tone, register, heritage_framing, day_of_week")
        print()
        spec_dict = {}
        while True:
            line = input(f"  spec> ").strip()
            if not line: break
            if "=" in line:
                k,v = line.split("=",1)
                spec_dict[k.strip()] = v.strip()
        if not spec_dict:
            print("No specs entered.")
            return
    else:
        spec_dict = {}
        for s in args.spec:
            if "=" in s:
                k,v = s.split("=",1)
                spec_dict[k.strip()] = v.strip()

    # Normalize sector
    SECTOR_KEY_MAP = {
        "food_and_beverage":"f_and_b","beauty_personal_care":"beauty","retail_lifestyle":"retail",
        "fb":"f_and_b","f&b":"f_and_b","food":"f_and_b","beauty":"beauty","retail":"retail",
    }
    if "sector" in spec_dict:
        spec_dict["sector"] = SECTOR_KEY_MAP.get(spec_dict["sector"].lower(), spec_dict["sector"])

    # Rename heritage_vs_modern if user passed heritage_framing
    if "heritage_framing" in spec_dict:
        spec_dict["heritage_vs_modern"] = spec_dict.pop("heritage_framing")
        DIM_WEIGHTS["heritage_vs_modern"] = DIM_WEIGHTS.pop("heritage_framing", 0.06)

    predicted, grade, breakdown = score(spec_dict)
    print_score(spec_dict, predicted, grade, breakdown)

if __name__ == "__main__":
    main()
