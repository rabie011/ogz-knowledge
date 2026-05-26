#!/usr/bin/env python3
"""
detect_chain_gaps.py
Detect underserved content_type × sector combinations:
- Count observation frequency per (content_type, sector)
- Count chains covering each combo
- Flag combos with high obs count but <3 chains

Output: JSON list of gap dicts, sorted by obs_count descending.

Usage:
  python3 scripts/detect_chain_gaps.py              # print gaps
  python3 scripts/detect_chain_gaps.py --save       # save to logs/chain_gaps.json
  python3 scripts/detect_chain_gaps.py --threshold 5  # min obs to flag
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
CHAINS_BASE = BASE / "02_what_to_build"
LOGS        = BASE / "logs"

MIN_OBS_THRESHOLD = 5    # min obs count to flag as gap
MIN_CHAIN_COVERAGE = 3   # chains below this = gap


def load_observations() -> list[dict]:
    obs = []
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("content_ref"):
                obs.append(d)
        except Exception:
            pass
    return obs


def load_chains() -> list[dict]:
    chains = []
    for tf_dir in sorted(CHAINS_BASE.glob("TF*")):
        if not tf_dir.is_dir():
            continue
        for f in sorted(tf_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text())
                if d.get("chain_id_short"):
                    chains.append(d)
            except Exception:
                pass
    return chains


def get_chain_coverage(chains: list[dict]) -> dict:
    """
    Returns dict: {(sector, content_type): chain_count}
    Counts how many chains cover each sector × output_type combo.
    """
    coverage = defaultdict(int)
    for c in chains:
        ef = c.get("eligibility_filters") or {}
        sa = ef.get("sectors_allowed") or ["*"]
        ot = c.get("output_type", "image")

        # output_type → content_type mapping
        # Note: chain output_type="video" covers obs content_type="video" AND "reel"
        # (reels are vertical videos — same chain family applies)
        # TF24 chains use output_type="carousel" (short form) — map to obs "carousel_slide"
        ct_map = {
            "image":          ["image"],
            "carousel_slide": ["carousel_slide"],
            "carousel":       ["carousel_slide"],  # TF24 chains use "carousel" short form
            "video":          ["video", "reel"],   # chains covering video cover reels too
        }
        cts = ct_map.get(ot, [ot])

        sectors = sa if "*" not in sa else [
            "f_and_b", "food_and_beverage",
            "beauty", "beauty_personal_care",
            "retail", "retail_lifestyle",
            "fashion",
            "real_estate",
        ]
        for sector in sectors:
            for ct in cts:
                coverage[(sector, ct)] += 1

    return dict(coverage)


def detect_gaps(threshold: int = MIN_OBS_THRESHOLD) -> list[dict]:
    obs_list = load_observations()
    chains   = load_chains()
    coverage = get_chain_coverage(chains)

    # Count obs per (sector, content_type)
    obs_counts = Counter()
    high_eng_counts = Counter()
    for obs in obs_list:
        sector = obs.get("sector", "")
        ct_ref = obs.get("content_ref") or {}
        ct = ct_ref.get("content_type", "image")
        qual = (obs.get("quality_assessment") or {}).get("engagement_potential", "")
        key = (sector, ct)
        obs_counts[key] += 1
        if qual in ("high", "very_high"):
            high_eng_counts[key] += 1

    # Build gap report
    gaps = []
    for (sector, ct), obs_count in sorted(obs_counts.items(), key=lambda x: -x[1]):
        if obs_count < threshold:
            continue
        chain_count = coverage.get((sector, ct), 0)
        if chain_count >= MIN_CHAIN_COVERAGE:
            continue
        high = high_eng_counts.get((sector, ct), 0)
        high_rate = round(high / obs_count, 2) if obs_count else 0
        gaps.append({
            "gap_id": f"{ct}__{sector}",
            "sector": sector,
            "content_type": ct,
            "obs_count": obs_count,
            "high_engagement_rate": high_rate,
            "chain_count": chain_count,
            "chains_needed": MIN_CHAIN_COVERAGE - chain_count,
            "priority": "high" if high_rate >= 0.6 and obs_count >= 20 else
                        "medium" if obs_count >= 10 else "low",
        })

    # Sort by priority then obs_count
    priority_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: (priority_order[g["priority"]], -g["obs_count"]))
    return gaps


def main():
    threshold = MIN_OBS_THRESHOLD
    save = "--save" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = int(sys.argv[i + 1])

    gaps = detect_gaps(threshold)

    if not gaps:
        print("No chain gaps detected — all content types well-covered.")
        if save:
            (LOGS / "chain_gaps.json").write_text(json.dumps([], indent=2))
        return

    print(f"Chain gaps detected: {len(gaps)}\n")
    print(f"{'GAP ID':35s}  {'OBS':>4}  {'HI%':>4}  {'CHAINS':>6}  PRIORITY")
    print("─" * 68)
    for g in gaps:
        print(
            f"  {g['gap_id']:33s}  {g['obs_count']:4d}  "
            f"{g['high_engagement_rate']:4.0%}  "
            f"{g['chain_count']:6d}  {g['priority']}"
        )

    if save:
        out = LOGS / "chain_gaps.json"
        out.write_text(json.dumps(gaps, ensure_ascii=False, indent=2))
        print(f"\nSaved: {out}")
    else:
        # Print JSON to stdout for daemon consumption
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(gaps, ensure_ascii=False))


if __name__ == "__main__":
    main()
