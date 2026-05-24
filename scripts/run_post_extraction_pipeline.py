#!/usr/bin/env python3
"""
run_post_extraction_pipeline.py
Run immediately after extract_captions_instaloader.py completes.

Steps:
  1. Validate all obs (must pass 100%)
  2. Run all caption/Arabic/hashtag analytics
  3. Rebuild intelligence playbook
  4. Print new caption fill rate
  5. Commit everything to git

Usage:
  python3 scripts/run_post_extraction_pipeline.py
  python3 scripts/run_post_extraction_pipeline.py --no-commit
"""
import subprocess, sys, time, argparse, json, re
from pathlib import Path

SCRIPTS = Path(__file__).parent
BASE    = SCRIPTS.parent
LOGS    = BASE / "logs"
PYTHON  = sys.executable


def run(name, script, check=True):
    path = SCRIPTS / script
    if not path.exists():
        print(f"  SKIP  {name} (not found)")
        return "SKIP"
    print(f"  ...   {name}", end="", flush=True)
    t0 = time.time()
    r = subprocess.run([PYTHON, str(path)], capture_output=True, text=True, cwd=str(BASE))
    elapsed = round(time.time() - t0, 1)
    if r.returncode == 0:
        print(f"\r  ✓     {name:<45} ({elapsed}s)")
        return "OK"
    else:
        err = (r.stderr or r.stdout or "")[-150:].strip()
        print(f"\r  ✗     {name:<45} ({elapsed}s)")
        print(f"        ↳ {err[:100]}")
        return "FAIL"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-commit", action="store_true")
    args = parser.parse_args()

    W = 65
    print(f"\n{'═'*W}")
    print(f"  OGZ Post-Extraction Pipeline")
    print(f"{'═'*W}\n")

    # ── Step 1: Validate ────────────────────────────────────────────────
    print(f"  STEP 1: Validate observations")
    r = subprocess.run([PYTHON, str(SCRIPTS/"validate_all.py")],
                       capture_output=True, text=True, cwd=str(BASE))
    val_line = (r.stdout or "").strip().split("\n")[-1]
    print(f"  {val_line}")
    if "All records valid" not in r.stdout:
        print(f"\n  ✗ Validation failed — fix errors before continuing\n")
        sys.exit(1)
    print()

    # ── Step 2: Caption fill summary ────────────────────────────────────
    print(f"  STEP 2: Caption fill summary")
    OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
    obs_files = list(OBS_ROOT.rglob("*.json"))
    filled  = sum(1 for f in obs_files
                  if json.loads(f.read_text()).get("voice_observations",{}).get("caption_text") is not None)
    print(f"  caption_text filled: {filled}/{len(obs_files)} ({filled/len(obs_files):.0%})")
    print()

    # ── Step 3: Arabic intelligence scripts ─────────────────────────────
    print(f"  STEP 3: Build caption + Arabic intelligence")
    CAPTION_SCRIPTS = [
        ("Caption intelligence",        "build_caption_intelligence.py"),
        ("Caption intelligence/sector", "build_caption_intelligence_by_sector.py"),
        ("Arabic copywriting",          "build_arabic_copywriting.py"),
        ("Arabic copywriting/sector",   "build_arabic_copywriting_by_sector.py"),
        ("Hashtag strategy",            "build_hashtag_strategy.py"),
        ("Caption length & hashtag",    "build_caption_length_hashtag_analysis.py"),
        ("Notable phrases",             "build_notable_phrases_intelligence.py"),
    ]
    results = []
    for name, script in CAPTION_SCRIPTS:
        results.append(run(name, script))
    print()

    # ── Step 4: Refresh synthesis scripts ───────────────────────────────
    print(f"  STEP 4: Refresh synthesis")
    SYNTH_SCRIPTS = [
        ("Master signal table",         "build_master_signal_table.py"),
        ("Engagement signals",          "build_engagement_signals.py"),
        ("Intelligence playbook",       "build_intelligence_playbook_v2.py"),
        # NOTE: build_production_brief_engine.py is interactive (requires --sector/--occasion args)
        # Run manually: python3 scripts/build_production_brief_engine.py --sector f_and_b --occasion ramadan
    ]
    for name, script in SYNTH_SCRIPTS:
        results.append(run(name, script))
    print()

    # ── Step 5: Summary ─────────────────────────────────────────────────
    ok   = results.count("OK")
    fail = results.count("FAIL")
    skip = results.count("SKIP")
    print(f"  {'─'*55}")
    print(f"  {ok} OK  ·  {fail} FAIL  ·  {skip} SKIP")
    print()

    # ── Step 6: Commit ──────────────────────────────────────────────────
    if not args.no_commit and fail == 0:
        print(f"  STEP 5: Commit")
        # Count new captions
        cap_msg = f"captions: {filled}/{len(obs_files)} obs filled"
        msg = f"data: caption extraction complete — {cap_msg}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
        r_add = subprocess.run(
            ["git", "add", "-A", "--", "11_who_to_learn_from/observations/", "logs/"],
            cwd=str(BASE), capture_output=True
        )
        r_commit = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(BASE), capture_output=True, text=True
        )
        if r_commit.returncode == 0:
            print(f"  ✓ Committed: {cap_msg}")
            r_push = subprocess.run(["git", "push", "origin", "main"],
                                    cwd=str(BASE), capture_output=True, text=True)
            if r_push.returncode == 0:
                print(f"  ✓ Pushed to GitHub")
            else:
                print(f"  ⚠ Push failed: {r_push.stderr[:80]}")
        else:
            out = r_commit.stdout.strip()
            print(f"  ℹ {out[:100]}")
    elif args.no_commit:
        print(f"  (--no-commit: skipping git)")

    print(f"\n{'═'*W}\n")


if __name__ == "__main__":
    main()
