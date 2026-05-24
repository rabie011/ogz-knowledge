#!/usr/bin/env python3
"""
run_phase4_analysis.py
Run all Phase 4 analysis scripts in sequence after caption extraction completes.

Steps:
  1. validate_all.py          — must pass 913/913
  2. build_caption_intelligence.py
  3. build_arabic_copywriting.py
  4. build_hashtag_strategy.py
  5. build_video_audio_analysis.py
  6. Quick summary of what was unlocked

Usage:
  python3 scripts/run_phase4_analysis.py
"""
import json
import subprocess
import sys
from pathlib import Path

BASE    = Path(__file__).parent.parent
SCRIPTS = BASE / "scripts"
LOGS    = BASE / "logs"


def run(script_name: str, label: str) -> bool:
    print(f"\n{'─' * 60}")
    print(f"  ▶  {label}")
    print(f"{'─' * 60}")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name)],
        cwd=str(BASE),
    )
    ok = result.returncode == 0
    print(f"  {'✅ OK' if ok else '❌ FAILED'}")
    return ok


def caption_summary():
    """Print quick count of filled captions."""
    obs = list((BASE / "11_who_to_learn_from" / "observations").rglob("*.json"))
    filled = 0
    empty  = 0
    null   = 0
    for f in obs:
        try:
            d   = json.loads(f.read_text())
            cap = d.get("voice_observations", {}).get("caption_text")
            if cap is None:
                null += 1
            elif cap == "":
                empty += 1
            else:
                filled += 1
        except Exception:
            pass
    print(f"\n  Caption fill status:")
    print(f"    With text  : {filled}")
    print(f"    Empty ('')  : {empty}")
    print(f"    Not extracted (null): {null}")
    print(f"    Total obs  : {len(obs)}")


def main():
    print("=" * 60)
    print("  OGZ PHASE 4 ANALYSIS PIPELINE")
    print("=" * 60)

    caption_summary()

    # Step 1 — Validate
    ok = run("validate_all.py", "STEP 1: Schema validation")
    if not ok:
        print("\n⚠️  Validation failed — fix before running analysis")
        sys.exit(1)

    # Steps 2-5 — Analysis
    scripts = [
        ("build_caption_intelligence.py", "STEP 2: Caption intelligence"),
        ("build_arabic_copywriting.py",   "STEP 3: Arabic copywriting"),
        ("build_hashtag_strategy.py",     "STEP 4: Hashtag strategy"),
        ("build_video_audio_analysis.py", "STEP 5: Video & audio analysis"),
    ]

    failed = []
    for script, label in scripts:
        ok = run(script, label)
        if not ok:
            failed.append(label)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  PHASE 4 COMPLETE")
    print(f"{'=' * 60}")

    logs_produced = [
        "caption_intelligence.json",
        "arabic_copywriting.json",
        "hashtag_strategy.json",
        "video_audio_analysis.json",
    ]
    print(f"\n  Logs produced:")
    for log in logs_produced:
        p = LOGS / log
        if p.exists():
            size = round(p.stat().st_size / 1024, 1)
            print(f"    ✅  logs/{log}  ({size} KB)")
        else:
            print(f"    ❌  logs/{log}  MISSING")

    if failed:
        print(f"\n  Failed scripts: {', '.join(failed)}")
        sys.exit(1)

    print(f"\n  Next: python3 scripts/build_production_brief_engine.py --interactive")
    print(f"        (now with caption length, hashtag count, emoji, Arabic phrases)\n")


if __name__ == "__main__":
    main()
