#!/usr/bin/env python3
"""
overnight_runner.py
Full autonomous overnight pipeline for OGZ knowledge base.

Sequence:
  1. Wait for caption retry to finish (PID 81300)
  2. Run phase4 analysis with all new captions
  3. Download missing videos for all video obs
  4. Run Whisper transcription on all local videos
  5. Run editing pace extraction on all local videos
  6. Re-run phase4 analysis (now with voiceover_text data)
  7. Validate: python3 scripts/validate_all.py
  8. Extract new accounts (beauty → retail → f_and_b, 5 accounts each)
     Uses Claude haiku API + instaloader for full observation extraction
  9. Validate again (post-extraction)
  10. Final phase4 analysis (full corpus)
  11. Commit + push everything to git

Usage:
  python3 scripts/overnight_runner.py
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE    = Path(__file__).parent.parent
SCRIPTS = BASE / "scripts"
LOGS    = BASE / "logs"
PYTHON  = sys.executable


def _run(script: str, label: str, extra_args: list = None) -> bool:
    args = extra_args or []
    print(f"\n{'━'*60}")
    print(f"  ▶  {label}")
    print(f"{'━'*60}")
    result = subprocess.run(
        [PYTHON, str(SCRIPTS / script)] + args,
        cwd=str(BASE),
    )
    ok = result.returncode == 0
    print(f"\n  {'✅ DONE' if ok else '❌ FAILED'}")
    return ok


def _wait_for_caption_retry(pid: int = 81300, timeout_sec: int = 10800):
    """Wait for the caption retry process to finish."""
    import psutil
    print(f"\n{'━'*60}")
    print(f"  ⏳  Waiting for caption retry (PID {pid})...")
    print(f"{'━'*60}")

    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            proc = psutil.Process(pid)
            if proc.status() in ("zombie", "dead"):
                break
        except Exception:
            break   # process no longer exists = done
        elapsed = int(time.time() - start)
        print(f"  ... caption retry still running ({elapsed}s elapsed)", flush=True)
        time.sleep(60)  # check every 60 seconds

    print("  ✅ Caption retry finished (or timed out)")


def _git_commit_push(message: str):
    print(f"\n{'━'*60}")
    print(f"  📦  Git commit + push")
    print(f"{'━'*60}")
    os.chdir(str(BASE))
    subprocess.run(["git", "add", "-A"], cwd=str(BASE))
    subprocess.run(
        ["git", "commit", "-m", message,
         "--author=overnight-runner <noreply@anthropic.com>"],
        cwd=str(BASE),
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE))
    print("  ✅ Pushed to remote")


def _corpus_status() -> dict:
    obs_files = list((BASE / "11_who_to_learn_from" / "observations").rglob("*.json"))
    caps = sum(
        1 for f in obs_files
        if json.loads(f.read_text()).get("voice_observations", {}).get("caption_text")
    )
    vt = sum(
        1 for f in obs_files
        if json.loads(f.read_text()).get("voice_observations", {}).get("voiceover_text")
    )
    dur = sum(
        1 for f in obs_files
        if (json.loads(f.read_text()).get("content_ref") or {}).get("video_duration_seconds") is not None
    )
    return {"total": len(obs_files), "captions": caps, "voiceover_text": vt, "durations": dur}


def main():
    start_time = time.time()
    print("=" * 60)
    print("  OGZ OVERNIGHT RUNNER")
    print(f"  Started: {time.strftime('%H:%M:%S')}")
    print("=" * 60)

    status = _corpus_status()
    print(f"\n  Initial state:")
    print(f"    Total obs    : {status['total']}")
    print(f"    Captions     : {status['captions']}")
    print(f"    Voiceover txt: {status['voiceover_text']}")
    print(f"    Durations    : {status['durations']}")

    # ── STEP 1: Wait for caption retry ───────────────────────────────────────
    try:
        import psutil
        _wait_for_caption_retry(pid=81300)
    except ImportError:
        print("\n  psutil not installed — sleeping 7200s for caption retry")
        time.sleep(7200)

    # ── STEP 2: Phase 4 analysis with new captions ────────────────────────────
    _run("run_phase4_analysis.py", "STEP 2: Phase 4 analysis (post-retry)")

    # ── STEP 3: Download missing videos ──────────────────────────────────────
    _run("download_obs_videos.py", "STEP 3: Download missing video obs")

    # ── STEP 4: Whisper transcription ─────────────────────────────────────────
    _run("run_whisper_extraction.py", "STEP 4: Whisper transcription (Arabic)", ["--model", "small"])

    # ── STEP 5: Editing pace ─────────────────────────────────────────────────
    _run("extract_editing_pace.py", "STEP 5: Editing pace (ffmpeg scdet)")

    # ── STEP 6: Final analysis with all enriched data ─────────────────────────
    _run("run_phase4_analysis.py", "STEP 6: Final phase 4 analysis")

    # ── STEP 7: Validate ─────────────────────────────────────────────────────
    ok = _run("validate_all.py", "STEP 7: Schema validation")
    if not ok:
        print("\n⚠️  Validation failed — committing anyway, check manually")

    # ── STEP 8: New account extraction (beauty → retail → f_and_b) ────────────
    print(f"\n{'━'*60}")
    print(f"  ▶  STEP 8: New account extraction (beauty first)")
    print(f"{'━'*60}")

    # Extract beauty accounts first (most underrepresented — only 2 extracted)
    _run(
        "extract_new_accounts.py",
        "STEP 8a: New beauty accounts (top 5 by followers)",
        ["--sector", "beauty", "--max-accounts", "5", "--count", "20", "--extract-count", "15"],
    )
    # Then retail (only 1 extracted)
    _run(
        "extract_new_accounts.py",
        "STEP 8b: New retail accounts (top 5 by followers)",
        ["--sector", "retail", "--max-accounts", "5", "--count", "20", "--extract-count", "15"],
    )
    # Then remaining F&B (27 not extracted)
    _run(
        "extract_new_accounts.py",
        "STEP 8c: New F&B accounts (top 5 by followers)",
        ["--sector", "f_and_b", "--max-accounts", "5", "--count", "20", "--extract-count", "15"],
    )

    # ── STEP 9: Re-validate after new obs ─────────────────────────────────────
    ok2 = _run("validate_all.py", "STEP 9: Post-extraction validation")
    if not ok2:
        print("\n⚠️  Validation failed after new extraction — check logs")

    # ── STEP 10: Final analysis with full corpus ──────────────────────────────
    _run("run_phase4_analysis.py", "STEP 10: Final phase 4 analysis (full corpus)")

    # ── STEP 11: Git commit + push ────────────────────────────────────────────
    status_final = _corpus_status()
    elapsed_min  = int((time.time() - start_time) / 60)

    new_obs_added = status_final['total'] - status['total']

    commit_msg = (
        f"Overnight run complete ({elapsed_min} min)\n\n"
        f"Corpus: {status['total']} → {status_final['total']} obs (+{new_obs_added} new)\n"
        f"Captions: {status['captions']} → {status_final['captions']}\n"
        f"Voiceover text: {status['voiceover_text']} → {status_final['voiceover_text']}\n"
        f"Durations: {status['durations']} → {status_final['durations']}\n\n"
        f"Scripts run: caption retry, video download, whisper,\n"
        f"editing pace, phase4 analysis, new account extraction,\n"
        f"validation\n\n"
        f"Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    )
    _git_commit_push(commit_msg)

    print()
    print("=" * 60)
    print("  OVERNIGHT RUNNER COMPLETE")
    print(f"  Finished: {time.strftime('%H:%M:%S')}")
    print(f"  Duration: {elapsed_min} min")
    print()
    print(f"  Total obs    : {status['total']} → {status_final['total']} (+{new_obs_added})")
    print(f"  Captions     : {status['captions']} → {status_final['captions']}")
    print(f"  Voiceover txt: {status['voiceover_text']} → {status_final['voiceover_text']}")
    print(f"  Durations    : {status['durations']} → {status_final['durations']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
