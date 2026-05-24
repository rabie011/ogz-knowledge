#!/usr/bin/env python3
"""
extract_captions_instaloader.py
Batch-extract caption_text (and derived fields) for all obs that have a
source_url pointing to an Instagram post.

Uses instaloader to fetch post metadata JSON from each shortcode.
Fields written per obs (only if currently null — never overwrites):

  voice_observations.caption_text         ← full verbatim caption (or "" if none)
  voice_observations.caption_word_count   ← int
  voice_observations.hashtag_count        ← int  (# chars in caption)
  voice_observations.has_emoji            ← bool
  content_ref.video_duration_seconds      ← int  (video/reel obs only)

Safe to re-run: skips obs where caption_text is not null.

Usage:
  python3 scripts/extract_captions_instaloader.py           # full run
  python3 scripts/extract_captions_instaloader.py --dry-run # plan only, no writes
"""
import json
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
LOGS        = BASE / "logs"
INSTALOADER = "/opt/homebrew/bin/instaloader"
SLEEP_SEC   = 4   # seconds between instaloader calls (be gentle)

# ── Emoji detection ────────────────────────────────────────────────────────────
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport & map symbols
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002600-\U000027BF"   # misc symbols
    "\U0001F900-\U0001F9FF"   # supplemental symbols & pictographs
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    re.UNICODE,
)


def _has_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text))


# ── URL helpers ────────────────────────────────────────────────────────────────
def _shortcode(url: str):
    """Extract Instagram shortcode from a post URL, or None."""
    m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
    return m.group(1) if m else None


# ── Instaloader wrapper ────────────────────────────────────────────────────────
def _fetch(shortcode: str, work_dir: Path):
    """
    Run instaloader for one shortcode.
    Returns the parsed metadata dict, or None on any failure.
    """
    cmd = [
        INSTALOADER,
        "--no-videos",
        "--no-pictures",
        "--no-profile-pic",
        "--no-compress-json",
        "--",
        f"-{shortcode}",
    ]
    try:
        subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=90,
        )
    except Exception:
        return None

    # Instaloader writes to work_dir/-{shortcode}/*.json
    post_dir = work_dir / f"-{shortcode}"
    if not post_dir.exists():
        return None

    json_files = sorted(post_dir.glob("*.json"))
    if not json_files:
        return None

    try:
        return json.loads(json_files[-1].read_text())
    except Exception:
        return None


# ── Caption field derivation ───────────────────────────────────────────────────
def _derive(caption_text: str) -> dict:
    return {
        "caption_word_count": len(caption_text.split()),
        "hashtag_count":      caption_text.count("#"),
        "has_emoji":          _has_emoji(caption_text),
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be written\n")

    stats  = defaultdict(int)
    errors = []

    # ── 1. Collect obs that need extraction ────────────────────────────────────
    to_process = []
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            stats["parse_error"] += 1
            continue

        stats["total"] += 1
        cr  = data.get("content_ref")         or {}
        vo  = data.get("voice_observations")  or {}
        url = cr.get("source_url")            or ""

        # Already extracted → skip
        if vo.get("caption_text") is not None:
            stats["already_done"] += 1
            continue

        # No usable URL → skip
        if "instagram.com/p/" not in url:
            stats["no_url"] += 1
            continue

        sc = _shortcode(url)
        if not sc:
            stats["bad_url"] += 1
            continue

        to_process.append((obs_file, data, sc))

    n       = len(to_process)
    eta_min = round(n * (SLEEP_SEC + 5) / 60, 1)

    print(f"Obs total        : {stats['total']}")
    print(f"Already done     : {stats['already_done']}")
    print(f"No source URL    : {stats['no_url']}")
    print(f"Queue            : {n}  (≈{eta_min} min at {SLEEP_SEC}s/req)")

    if dry_run or n == 0:
        if n == 0:
            print("Nothing to do.")
        return

    print()

    # ── 2. Extract ─────────────────────────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)

        for i, (obs_file, data, sc) in enumerate(to_process, 1):
            pct = round(i / n * 100)
            print(f"[{i:>3}/{n}  {pct:>3}%]  {sc:<26}", end="  ", flush=True)

            raw = _fetch(sc, work_dir)

            if raw is None:
                print("FAILED (no JSON)")
                stats["failed"] += 1
                errors.append({"shortcode": sc, "file": obs_file.name, "error": "no_json"})
                time.sleep(SLEEP_SEC)
                continue

            # ── Caption ────────────────────────────────────────────────────────
            try:
                node   = raw.get("node") or {}
                edges  = (node.get("edge_media_to_caption") or {}).get("edges") or []
                cap    = edges[0]["node"]["text"] if edges else ""
            except (KeyError, IndexError, TypeError):
                cap = ""

            vo = data["voice_observations"]
            cr = data["content_ref"]

            derived = _derive(cap)
            vo["caption_text"]        = cap
            vo["caption_word_count"]  = derived["caption_word_count"]
            vo["hashtag_count"]       = derived["hashtag_count"]
            vo["has_emoji"]           = derived["has_emoji"]

            if cap:
                stats["cap_filled"] += 1
            else:
                stats["cap_empty"] += 1

            note = f"{derived['caption_word_count']:>3}w  {derived['hashtag_count']}#"

            # ── Video duration ─────────────────────────────────────────────────
            try:
                node = raw.get("node") or {}
                if node.get("is_video") and cr.get("video_duration_seconds") is None:
                    dur = node.get("video_duration")
                    if dur is not None:
                        cr["video_duration_seconds"] = int(round(float(dur)))
                        stats["dur_filled"] += 1
                        note += f"  {cr['video_duration_seconds']}s"
            except (ValueError, TypeError):
                pass

            print(f"OK  {note}")
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            stats["written"] += 1

            if i < n:
                time.sleep(SLEEP_SEC)

    # ── 3. Summary ─────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("EXTRACTION COMPLETE")
    print(f"  Written              : {stats['written']}")
    print(f"  Captions (with text) : {stats['cap_filled']}")
    print(f"  Captions (empty)     : {stats['cap_empty']}")
    print(f"  Video duration added : {stats['dur_filled']}")
    print(f"  Failed               : {stats['failed']}")

    if errors:
        LOGS.mkdir(exist_ok=True)
        err_path = LOGS / "caption_extraction_errors.json"
        err_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2))
        print(f"  Error log            : logs/caption_extraction_errors.json")
        for e in errors[:5]:
            print(f"    {e['shortcode']}  →  {e['error']}")
        if len(errors) > 5:
            print(f"    ... +{len(errors) - 5} more (see log)")

    print()
    print("Next step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
