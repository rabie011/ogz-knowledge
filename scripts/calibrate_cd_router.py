#!/usr/bin/env python3
"""
calibrate_cd_router.py — Recalculate CD brain affinities from engagement data.

Maps top-performing patterns to their best-fit CD brains, then computes
data-backed sector_affinity and occasion_affinity scores for each brain.

Usage:
  python3 scripts/calibrate_cd_router.py              # print calibrated values
  python3 scripts/calibrate_cd_router.py --apply       # update CD brain files
"""
import json, yaml, argparse, glob, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
INTEL_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
CD_DIR = BASE / "20_cd_brains"
CHAINS_DIR = BASE / "02_what_to_build"

# Map patterns to CD brains based on methodology fit
PATTERN_TO_CD = {
    "heritage_storytelling_hook": ["cd_04", "cd_01"],
    "cultural_object_hero": ["cd_04", "cd_03"],
    "nostalgia_play": ["cd_04", "cd_05"],
    "youth_culture_collab": ["cd_05", "cd_02"],
    "community_pride_statement": ["cd_01", "cd_03"],
    "overhead_tabletop_spread": ["cd_03"],
    "product_hero": ["cd_01", "cd_03"],
    "close_up_macro_texture": ["cd_03", "cd_02"],
    "lifestyle_environment_integration": ["cd_01", "cd_02"],
    "customer_voice_ugc": ["cd_03", "cd_01"],
    "giveaway_contest": ["cd_05"],
    "question_cta": ["cd_01", "cd_05"],
    "occasion_specific_greeting": ["cd_04", "cd_01"],
    "parallel_original_bilingual": ["cd_04", "cd_02"],
    "urgency_without_pressure": ["cd_05", "cd_01"],
    "pattern_repeat_flatlay": ["cd_02", "cd_03"],
    "model_centered_frontal_portrait": ["cd_03"],
    "seasonal_collection_drop": ["cd_01", "cd_04"],
    "founding_day_dirayyah_heritage": ["cd_04"],
    "modest_wear": ["cd_03", "cd_04"],
    "fashion_accessory_integration": ["cd_02", "cd_03"],
}


def calibrate():
    intel = json.loads(INTEL_PATH.read_text())
    sectors = list(intel.get("sector_playbooks", {}).keys())
    occasions = [r["occasion"] for r in intel.get("occasion_rules", [])]

    cd_brains = ["cd_01", "cd_02", "cd_03", "cd_04", "cd_05"]
    sector_scores = {cd: {} for cd in cd_brains}
    occasion_scores = {cd: {} for cd in cd_brains}

    # Calculate sector affinity from pattern performance
    for sector, pb in intel.get("sector_playbooks", {}).items():
        cd_sector_signal = {cd: [] for cd in cd_brains}
        for p in pb.get("must_use", []):
            slug = p["pattern"]
            eng = p["engagement"]
            mapped_cds = PATTERN_TO_CD.get(slug, ["cd_01"])
            for cd in mapped_cds:
                cd_sector_signal[cd].append(eng)

        for cd in cd_brains:
            signals = cd_sector_signal[cd]
            if signals:
                avg = sum(signals) / len(signals) / 100
                sector_scores[cd][sector] = round(min(avg * 1.2, 1.0), 2)
            else:
                sector_scores[cd][sector] = 0.3

    # Calculate occasion affinity from occasion rules
    for occ_rule in intel.get("occasion_rules", []):
        occ = occ_rule["occasion"]
        eng = occ_rule["engagement"]
        # Heritage occasions favor cd_04, cd_01
        if occ in ("founding_day", "national_day", "ramadan"):
            occasion_scores["cd_04"][occ] = round(min(eng / 100 * 1.5, 1.0), 2)
            occasion_scores["cd_01"][occ] = round(min(eng / 100 * 1.3, 1.0), 2)
            occasion_scores["cd_03"][occ] = round(eng / 100 * 1.1, 2)
        elif occ in ("jeddah_season", "riyadh_season"):
            occasion_scores["cd_05"][occ] = round(min(eng / 100 * 1.3, 1.0), 2)
            occasion_scores["cd_02"][occ] = round(min(eng / 100 * 1.2, 1.0), 2)
        else:
            for cd in cd_brains:
                occasion_scores[cd][occ] = round(eng / 100, 2)

    return sector_scores, occasion_scores


def is_degenerate(sector_scores, occasion_scores):
    """True when the source carried no real signal.

    A live intelligence_layer fills every CD brain's sector_affinity with at
    least the 0.3 default for every sector, so all-empty sector_scores means
    the upstream keys (sector_playbooks / occasion_rules) are missing or empty
    — e.g. after a schema drift. Writing these empty blocks over real CD-brain
    affinities via --apply would silently destroy a calibrated organ.
    """
    any_sector = any(scores for scores in sector_scores.values())
    any_occasion = any(v > 0 for scores in occasion_scores.values() for v in scores.values())
    return not (any_sector or any_occasion)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    sector_scores, occasion_scores = calibrate()

    # Rule #8 — REFUSE, don't warn. A dry source must never reach --apply and
    # overwrite real affinities with nothing. Exit non-zero before any write.
    if is_degenerate(sector_scores, occasion_scores):
        msg = (
            "REFUSED: calibration source produced ZERO signal — "
            "intelligence_layer.json has no usable 'sector_playbooks' / "
            "'occasion_rules' (schema drift: data now lives under "
            "'sector_facts' / 'occasion_calendar', which this reader does not "
            "parse). Refusing to write empty affinities over the CD brains. "
            "Fix the reader (see backlog) before --apply."
        )
        if args.apply:
            print(f"\n⛔ {msg}", file=sys.stderr)
            sys.exit(2)
        print(f"\n⚠️  DRY SOURCE — {msg}\n(print-only run; --apply would refuse)")

    print("═" * 50)
    print("CD BRAIN CALIBRATION FROM ENGAGEMENT DATA")
    print("═" * 50)

    for cd in sorted(sector_scores):
        print(f"\n{cd}:")
        print(f"  sector_affinity:")
        for s, v in sorted(sector_scores[cd].items()):
            print(f"    {s}: {v}")
        print(f"  occasion_affinity:")
        for o, v in sorted(occasion_scores[cd].items()):
            if v > 0:
                print(f"    {o}: {v}")

    if args.apply:
        # Update each CD brain file's front-matter with calibrated values
        for cd_file in sorted(CD_DIR.glob("cd_0*.md")):
            cd_slug = cd_file.stem
            content = cd_file.read_text()

            if "sector_affinity:" in content and cd_slug in sector_scores:
                # Find and replace sector_affinity block
                import re
                sa_block = "sector_affinity:\n" + "\n".join(
                    f"  {s}: {v}" for s, v in sorted(sector_scores[cd_slug].items())
                )
                content = re.sub(
                    r"sector_affinity:.*?(?=\n[a-z]|\noccasion_affinity:)",
                    sa_block + "\n",
                    content,
                    flags=re.DOTALL
                )

            cd_file.write_text(content)
            print(f"\n✅ Updated {cd_file.name}")

        print("\n✅ All CD brain files calibrated from engagement data")

    # Save calibration report
    report = {"sector_affinity": sector_scores, "occasion_affinity": occasion_scores,
              "calibrated_at": __import__("datetime").datetime.now().isoformat(),
              "source": "intelligence_layer.json"}
    report_path = BASE / "logs" / "cd_router_calibration.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n✅ Calibration report: {report_path}")


if __name__ == "__main__":
    main()
