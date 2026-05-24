#!/usr/bin/env python3
"""
run_all_analytics.py
Refresh all analytics in dependency order.
Run after adding new observations to regenerate all logs.

Usage:
  python3 scripts/run_all_analytics.py              # run all
  python3 scripts/run_all_analytics.py --dry-run    # show what would run
  python3 scripts/run_all_analytics.py --fast       # skip slow pattern scripts

Output: prints progress + summary
"""
import subprocess, sys, time, argparse
from pathlib import Path

SCRIPTS = Path(__file__).parent

# Run order: independent first → derived/synthesis last
PIPELINE = [
    # Tier 1: raw signal analytics (read obs directly)
    ("Sector fingerprint",         "build_sector_fingerprint.py",          False),
    ("Content type analysis",      "build_content_type_analysis.py",       False),
    ("Setting analysis",           "build_setting_analysis.py",            False),
    ("Lighting analysis",          "build_lighting_analysis.py",           False),
    ("Composition analysis",       "build_composition_analysis.py",        False),
    ("Visual complexity analysis", "build_visual_complexity_analysis.py",  False),
    ("Tone & register analysis",   "build_tone_register_analysis.py",      False),
    ("Cultural signal analysis",   "build_cultural_signal_analysis.py",    False),
    ("Hospitality intelligence",   "build_hospitality_intelligence.py",    False),
    ("Day of week analysis",       "build_day_of_week_analysis.py",        False),
    ("Wardrobe & gender",          "build_wardrobe_gender_analysis.py",    False),
    ("Caption length & hashtag",   "build_caption_length_hashtag_analysis.py", False),
    ("Notable phrases",            "build_notable_phrases_intelligence.py",False),
    ("Text overlay intelligence",  "build_text_overlay_intelligence.py",   False),
    ("Quality signals",            "build_quality_signals.py",             False),
    ("Engagement signals",         "build_engagement_signals.py",          False),
    ("Media engagement analysis",  "build_media_engagement_analysis.py",   False),
    ("Temporal analysis",          "build_temporal_analysis.py",           False),
    ("Props taxonomy",             "build_props_taxonomy.py",              False),

    # Tier 2: multi-dim combinations
    ("Composition × setting",      "build_composition_setting_synergy.py", False),
    ("Complexity × composition",   "build_complexity_composition_matrix.py",False),
    ("Format × occasion matrix",   "build_format_occasion_matrix.py",      False),
    ("Occasion × sector × format", "build_occasion_sector_format_matrix.py",False),
    ("Master signal table",        "build_master_signal_table.py",         False),

    # Tier 3: account-level (fast)
    ("Account performance",        "build_account_performance_analysis.py",False),
    ("Elite vs weak DNA",          "build_elite_vs_weak_dna.py",           False),
    ("Account coach reports",      "build_account_coach_reports.py",       False),
    ("Competitive gap",            "build_competitive_gap.py",             False),
    ("Cross-sector opportunity",   "build_cross_sector_opportunity.py",    False),

    # Tier 4: pattern analytics (slow — optional)
    ("Pattern engagement",         "build_pattern_engagement.py",          True),   # slow=True
    ("Pattern sector matrix",      "build_pattern_sector_matrix.py",       True),
    ("Occasion sector matrix",     "build_occasion_sector_matrix.py",      True),
    ("Winning formula",            "build_winning_formula.py",             True),

    # Tier 5: synthesis (read logs)
    ("Intelligence playbook",      "build_intelligence_playbook_v2.py",    False),
]

PYTHON = sys.executable


def run_script(name, script, dry_run=False):
    path = SCRIPTS / script
    if not path.exists():
        return "SKIP", 0, f"{script} not found"
    if dry_run:
        return "DRY", 0, ""
    t0 = time.time()
    result = subprocess.run(
        [PYTHON, str(path)],
        capture_output=True, text=True,
        cwd=str(SCRIPTS.parent)
    )
    elapsed = round(time.time() - t0, 1)
    if result.returncode == 0:
        return "OK", elapsed, ""
    else:
        err = (result.stderr or result.stdout or "")[-200:].strip()
        return "FAIL", elapsed, err


def main():
    parser = argparse.ArgumentParser(description="OGZ Analytics Pipeline Runner")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fast",    action="store_true", help="Skip slow pattern scripts")
    parser.add_argument("--tier",    type=int, default=0, help="Run only tier N (1-5)")
    args = parser.parse_args()

    print(f"\n{'═'*65}")
    print(f"  OGZ Analytics Pipeline")
    if args.dry_run: print(f"  MODE: DRY RUN")
    if args.fast:    print(f"  MODE: FAST (skipping slow pattern scripts)")
    print(f"{'═'*65}\n")

    results = []
    for name, script, is_slow in PIPELINE:
        if args.fast and is_slow:
            results.append((name, "SKIP", 0, "fast mode"))
            print(f"  SKIP  {name}")
            continue

        print(f"  ...   {name}", end="", flush=True)
        status, elapsed, err = run_script(name, script, args.dry_run)
        status_sym = "  ✓  " if status == "OK" else "  ✗  " if status == "FAIL" else "  -  "
        time_str   = f" ({elapsed}s)" if elapsed else ""
        print(f"\r{status_sym}{name:<40}{time_str}")
        if err: print(f"        ↳ {err[:80]}")
        results.append((name, status, elapsed, err))

    # Summary
    ok   = sum(1 for _,s,_,_ in results if s == "OK")
    fail = sum(1 for _,s,_,_ in results if s == "FAIL")
    skip = sum(1 for _,s,_,_ in results if s in ("SKIP","DRY"))
    total_t = sum(t for _,_,t,_ in results)

    print(f"\n{'─'*65}")
    print(f"  Done: {ok} OK  ·  {fail} FAIL  ·  {skip} skipped  ·  {total_t:.0f}s total")
    if fail:
        print(f"\n  Failed scripts:")
        for name, status, _, err in results:
            if status == "FAIL":
                print(f"    ✗ {name}: {err[:100]}")
    print()

    # Run validation at the end
    if ok > 0 and not args.dry_run:
        print(f"  Running validation...")
        val = subprocess.run([PYTHON, str(SCRIPTS/"validate_all.py")],
                             capture_output=True, text=True, cwd=str(SCRIPTS.parent))
        val_line = (val.stdout or "").strip().split("\n")[-1]
        print(f"  {val_line}\n")


if __name__ == "__main__":
    main()
