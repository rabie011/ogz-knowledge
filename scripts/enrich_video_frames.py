#!/usr/bin/env python3
"""
enrich_video_frames.py
Extract the middle frame from each mp4 in 11_who_to_learn_from/_inbox/,
match to an obs by Instagram shortcode, analyse with GPT-4o-mini vision
via the OpenAI Batch API, and fill missing visual fields.

Fields filled (only if currently null/missing — never overwrites):
  visual_observations.composition_style
  visual_observations.human_presence      (none|partial|full)
  visual_observations.text_overlay_visible (bool)
  visual_observations.arabic_text_visible  (bool)
  visual_observations.product_visible      (bool)
  visual_observations.brand_logo_visible   (bool)
  visual_observations.scene_type           (indoor|outdoor|studio|graphic|mixed)

Usage:
  python3 scripts/enrich_video_frames.py --dry-run       # count matches, no API calls
  python3 scripts/enrich_video_frames.py                 # full pipeline (submit + poll + apply)
  python3 scripts/enrich_video_frames.py --limit 100     # process at most N videos
  python3 scripts/enrich_video_frames.py --status        # check active batch status
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO      = Path(__file__).parent.parent
INBOX     = REPO / "11_who_to_learn_from" / "_inbox"
OBS_ROOT  = REPO / "11_who_to_learn_from" / "observations"
LOGS      = REPO / "logs"
BATCH_DIR = LOGS / "video_frame_batches"
STATE_FILE = LOGS / "video_frames_state.json"

BATCH_DIR.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

FFMPEG   = "/opt/homebrew/bin/ffmpeg"
FFPROBE  = "/opt/homebrew/bin/ffprobe"

MAX_FILE_MB = 200
MODEL       = "gpt-4o-mini"

# ── Env / OpenAI ───────────────────────────────────────────────────────────────
def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_file = Path.home() / ".abraham_env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

_env = _load_env()
OPENAI_KEY = _env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_KEY:
    print("ERROR: OPENAI_API_KEY not found in ~/.abraham_env or environment", file=sys.stderr)
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai not installed — activate .venv or pip install openai", file=sys.stderr)
    sys.exit(1)

client = OpenAI(api_key=OPENAI_KEY)

# ── Vision prompt ──────────────────────────────────────────────────────────────
VISION_SYSTEM = (
    "Analyse this Saudi/Middle East Instagram video frame. Return ONLY JSON:\n"
    '{"composition_style":"product_hero"|"lifestyle_integrated"|"editorial"'
    '|"overhead_spread"|"face_forward"|"text_dominant"|"behind_the_scenes"|"mixed",'
    '"human_presence":true|false,'
    '"text_overlay_visible":true|false,'
    '"arabic_text_visible":true|false,'
    '"product_visible":true|false,'
    '"brand_logo_visible":true|false,'
    '"scene_type":"indoor"|"outdoor"|"studio"|"graphic"|"mixed"}'
)

# Fields we fill — in the order they appear in the schema
FILL_FIELDS = [
    "composition_style",
    "human_presence",
    "text_overlay_visible",
    "arabic_text_visible",
    "product_visible",
    "brand_logo_visible",
    "scene_type",
]


# ── State helpers ──────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── Shortcode helpers ──────────────────────────────────────────────────────────
_SC_RE = re.compile(r"[A-Za-z0-9_-]{7,12}")  # IG shortcodes are 11 chars but some vary


def shortcode_from_url(url: str) -> str | None:
    m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
    return m.group(1) if m else None


def shortcode_from_stem(stem: str) -> str | None:
    """
    Extract an Instagram shortcode from an mp4 stem.

    Handles multiple naming conventions seen in this repo:
      1. Pure shortcode:          "DYR5kPIIrY2"
      2. Shortcode with underscore: "DYTKbBTIP_I"  → the whole stem IS the shortcode
      3. Reel-prefixed:           "reel08_DWCKONTgX85"  → take part after prefix
      4. Carousel slide suffix:   "B0TItxdhwmQ_6"       → strip trailing _N if numeric
      5. Dash-prefixed stubs:     "-brOpFHoCZ"           → strip leading dash

    Key insight: Instagram shortcodes are ≤13 chars of [A-Za-z0-9_-].
    If the entire stem fits that profile it IS the shortcode — don't split it.
    """
    # Strip leading dashes (some instaloader artefacts)
    stem = stem.lstrip("-")

    if not stem:
        return None

    # IG shortcodes: base64url, typically 11 chars, max ~13.
    # If the whole stem is short enough and base64url, return it directly — even
    # if it contains underscores (which ARE valid shortcode characters).
    if len(stem) <= 13 and re.match(r"^[A-Za-z0-9_-]+$", stem):
        return stem

    if "_" in stem:
        parts = stem.rsplit("_", 1)
        last = parts[-1]
        if last.isdigit():
            # Carousel slide: base is parts[0]
            base = parts[0]
            # Base itself may be "DYR5kPIIrY2" or "reel08_DWCKONTgX85"
            # Recurse to extract from base
            return shortcode_from_stem(base)
        else:
            # reel08_DWCKONTgX85 style — last segment is the shortcode
            if re.match(r"^[A-Za-z0-9_-]+$", last):
                return last
    else:
        return stem if re.match(r"^[A-Za-z0-9_-]+$", stem) else None

    return None


# ── Build obs index ────────────────────────────────────────────────────────────
def build_obs_index() -> dict[str, Path]:
    """Return mapping: shortcode → obs json Path (video obs only)."""
    index: dict[str, Path] = {}
    for obs_path in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(obs_path.read_text())
        except Exception:
            continue
        cr = d.get("content_ref") or {}
        ct = str(cr.get("content_type") or "").lower()
        if ct not in ("video", "reel"):
            continue
        url = cr.get("source_url", "")
        sc = shortcode_from_url(url)
        if sc and sc not in index:
            index[sc] = obs_path
        # Also index by filename stem if no source_url
        filename = cr.get("filename", "")
        if filename:
            fstem = Path(filename).stem
            # Remove common suffixes like _thumb
            fstem = re.sub(r"_thumb$", "", fstem)
            fsc = shortcode_from_stem(fstem)
            if fsc and fsc not in index:
                index[fsc] = obs_path
    return index


# ── Check which obs need filling ───────────────────────────────────────────────
def needs_fill(obs_path: Path) -> bool:
    """Return True if any of our target fields is missing."""
    try:
        d = json.loads(obs_path.read_text())
    except Exception:
        return False
    vis = d.get("visual_observations") or {}
    for field in FILL_FIELDS:
        val = vis.get(field)
        if val is None:
            return True
    return False


# ── mp4 enumeration ────────────────────────────────────────────────────────────
def iter_mp4s():
    """Yield (mp4_path, shortcode) for all mp4s under INBOX."""
    for mp4 in sorted(INBOX.rglob("*.mp4")):
        sc = shortcode_from_stem(mp4.stem)
        if sc:
            yield mp4, sc


# ── ffprobe duration ───────────────────────────────────────────────────────────
def get_duration(mp4: Path) -> float | None:
    """Return video duration in seconds, or None on failure."""
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json",
             "-show_streams", str(mp4)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                dur = stream.get("duration")
                if dur:
                    return float(dur)
    except Exception:
        pass
    return None


# ── Frame extraction ───────────────────────────────────────────────────────────
def extract_middle_frame(mp4: Path) -> bytes | None:
    """
    Extract the middle frame from mp4 and return JPEG bytes.
    Uses ffprobe to get duration, then ffmpeg to seek to duration/2.
    Falls back to seeking to 1s if duration unavailable.
    Returns None on any failure.
    """
    dur = get_duration(mp4)
    seek = (dur / 2.0) if (dur and dur > 0) else 1.0

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [
                FFMPEG, "-y",
                "-ss", str(seek),
                "-i", str(mp4),
                "-vframes", "1",
                "-q:v", "2",
                str(tmp_path),
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0 or not tmp_path.exists() or tmp_path.stat().st_size == 0:
            return None
        return tmp_path.read_bytes()
    except Exception:
        return None
    finally:
        tmp_path.unlink(missing_ok=True)


def frame_to_data_url(frame_bytes: bytes) -> str:
    b64 = base64.b64encode(frame_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


# ── Batch request builder ──────────────────────────────────────────────────────
def build_batch_requests(
    work_items: list[tuple[Path, str, Path]],
    done_shortcodes: set[str],
    dry_run: bool,
) -> tuple[list[dict], int, int]:
    """
    Build OpenAI Batch API request dicts.

    work_items: list of (mp4_path, shortcode, obs_path)
    done_shortcodes: already-processed shortcodes (skip these)

    Returns: (requests, n_skipped_already_done, n_frame_errors)
    """
    requests_out: list[dict] = []
    cid_to_sc: dict[str, str] = {}   # custom_id → shortcode mapping
    n_skipped = 0
    n_errors  = 0

    for mp4, sc, obs_path in work_items:
        if sc in done_shortcodes:
            n_skipped += 1
            continue

        if dry_run:
            # In dry-run we don't extract frames — just count
            requests_out.append({"_dry_run_sc": sc})
            continue

        # Skip large files
        size_mb = mp4.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_MB:
            print(f"  SKIP (>{MAX_FILE_MB}MB): {mp4.name}")
            n_errors += 1
            continue

        frame_bytes = extract_middle_frame(mp4)
        if not frame_bytes:
            print(f"  SKIP (frame extract failed): {mp4.name}")
            n_errors += 1
            continue

        data_url = frame_to_data_url(frame_bytes)

        # Use filename stem as custom_id (unique even for carousel slides sharing a shortcode)
        unique_id = mp4.stem[:60].replace(" ", "_")
        cid = f"vf_{unique_id}"
        cid_to_sc[cid] = sc   # save mapping so apply() can look up shortcode
        requests_out.append({
            "custom_id": cid,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "max_tokens": 200,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": VISION_SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url, "detail": "low"},
                            },
                            {
                                "type": "text",
                                "text": "Analyse this Saudi/Middle East Instagram video frame.",
                            },
                        ],
                    },
                ],
            },
        })

    return requests_out, cid_to_sc, n_skipped, n_errors


# ── Batch submission ───────────────────────────────────────────────────────────
def submit_batch(requests_list: list[dict], label: str) -> str:
    """Write JSONL, upload, submit. Returns batch_id."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = BATCH_DIR / f"{label}_{ts}.jsonl"

    with open(jsonl_path, "w") as fh:
        for req in requests_list:
            fh.write(json.dumps(req, ensure_ascii=False) + "\n")

    size_kb = jsonl_path.stat().st_size // 1024
    print(f"  Uploading {len(requests_list)} requests ({size_kb} KB)...")

    with open(jsonl_path, "rb") as fh:
        file_obj = client.files.create(file=fh, purpose="batch")

    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print(f"  Batch submitted: {batch.id} (status: {batch.status})")
    return batch.id


# ── Batch polling ──────────────────────────────────────────────────────────────
def poll_batch(batch_id: str, timeout_s: int = 7200) -> list[dict]:
    """Poll until complete. Returns list of result dicts."""
    start   = time.time()
    label   = f"video_frames/{batch_id[:12]}"
    while True:
        elapsed = time.time() - start
        if elapsed > timeout_s:
            print(f"  WARNING: batch {batch_id} timed out after {timeout_s}s — "
                  f"re-run with --status to resume when ready")
            return []

        batch = client.batches.retrieve(batch_id)
        done  = batch.request_counts.completed if batch.request_counts else 0
        total = batch.request_counts.total     if batch.request_counts else "?"
        print(f"  [{label}] status={batch.status} completed={done}/{total} elapsed={int(elapsed)}s")

        if batch.status == "completed":
            raw = client.files.content(batch.output_file_id).text
            results = [
                json.loads(line)
                for line in raw.strip().splitlines()
                if line.strip()
            ]
            print(f"  Batch complete — {len(results)} results downloaded")
            return results

        if batch.status in ("failed", "expired", "cancelled"):
            print(f"  ERROR: batch {batch_id} ended with status={batch.status}")
            return []

        sleep_s = 30 if elapsed < 120 else 60
        time.sleep(sleep_s)


# ── Apply results to obs files ─────────────────────────────────────────────────
def parse_gpt_response(content: str) -> dict | None:
    """Parse JSON from GPT response text (handles markdown fences)."""
    content = content.strip()
    content = re.sub(r"```(?:json)?", "", content).strip().strip("`")
    try:
        return json.loads(content)
    except Exception:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return None


def apply_results(
    results: list[dict],
    obs_index: dict[str, Path],
    cid_to_sc: dict[str, str] | None = None,
) -> tuple[int, int]:
    """
    Write GPT results back to obs files.

    cid_to_sc maps custom_id → Instagram shortcode (needed because custom_ids
    now use mp4 stem, not raw shortcode, to avoid duplicate_custom_id errors).

    Returns: (n_written, n_errors)
    """
    _c2s = cid_to_sc or {}
    n_written = 0
    n_errors  = 0

    for result in results:
        if result.get("error"):
            n_errors += 1
            continue

        cid = result.get("custom_id", "")
        if not cid.startswith("vf_"):
            continue
        # Prefer explicit mapping; fall back to stripping "vf_" prefix for
        # backwards compatibility with old batches that used shortcode directly.
        sc = _c2s.get(cid, cid[3:])

        try:
            body    = result["response"]["body"]
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            n_errors += 1
            continue

        parsed = parse_gpt_response(content)
        if not parsed:
            n_errors += 1
            continue

        obs_path = obs_index.get(sc)
        if not obs_path:
            continue

        try:
            d   = json.loads(obs_path.read_text())
            vis = d.setdefault("visual_observations", {})
            changed = False

            for field in FILL_FIELDS:
                if vis.get(field) is None:
                    val = parsed.get(field)
                    if val is not None:
                        # human_presence: schema is boolean; normalise string responses
                        if field == "human_presence" and isinstance(val, str):
                            val = val.lower() not in ("none", "false", "no")
                        vis[field] = val
                        changed = True

            if changed:
                obs_path.write_text(json.dumps(d, ensure_ascii=False, indent=2))
                n_written += 1
        except Exception as e:
            print(f"  ERROR writing {obs_path.name}: {e}")
            n_errors += 1

    return n_written, n_errors


# ── Status command ─────────────────────────────────────────────────────────────
def print_status() -> None:
    state = load_state()
    active_id = state.get("active_batch_id")
    done_count = len(state.get("done_shortcodes", []))

    print("\n── Video Frame Enrichment Status ─────────────────────────")
    print(f"  Processed shortcodes : {done_count}")
    if active_id:
        print(f"  Active batch         : {active_id}")
        try:
            batch = client.batches.retrieve(active_id)
            done  = batch.request_counts.completed if batch.request_counts else "?"
            total = batch.request_counts.total     if batch.request_counts else "?"
            print(f"  Batch status         : {batch.status} ({done}/{total} completed)")
        except Exception as e:
            print(f"  (could not retrieve batch: {e})")
    else:
        print("  Active batch         : none")

    # Count remaining work
    obs_index = build_obs_index()
    remaining = 0
    for mp4, sc in iter_mp4s():
        if sc in obs_index and needs_fill(obs_index[sc]):
            remaining += 1
    print(f"  Videos still needing fill : {remaining}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich video obs with GPT-4o-mini frame analysis"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Count matches only, no API calls or file writes")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process at most N videos (0 = no limit)")
    parser.add_argument("--status", action="store_true",
                        help="Check active batch status and remaining work")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    # ── Load state ──────────────────────────────────────────────────────────
    state = load_state()
    done_shortcodes: set[str] = set(state.get("done_shortcodes", []))
    active_batch_id: str | None = state.get("active_batch_id")

    # ── Build index ─────────────────────────────────────────────────────────
    print("Building obs index...", end=" ", flush=True)
    obs_index = build_obs_index()
    print(f"{len(obs_index)} video obs indexed")

    # ── If there is an active (completed) batch, apply its results first ────
    if active_batch_id and not args.dry_run:
        print(f"\nResuming active batch: {active_batch_id}")
        try:
            batch = client.batches.retrieve(active_batch_id)
        except Exception as e:
            print(f"  WARNING: could not retrieve batch {active_batch_id}: {e}")
            batch = None

        if batch and batch.status == "completed":
            print("  Batch already complete — downloading and applying results...")
            raw = client.files.content(batch.output_file_id).text
            results = [
                json.loads(line)
                for line in raw.strip().splitlines()
                if line.strip()
            ]
            _c2s = state.get("cid_to_sc", {})
            n_written, n_errors = apply_results(results, obs_index, _c2s)
            print(f"  Applied: {n_written} obs updated, {n_errors} errors")
            # Mark all as done
            for r in results:
                cid = r.get("custom_id", "")
                if cid.startswith("vf_"):
                    done_shortcodes.add(_c2s.get(cid, cid[3:]))
            state["done_shortcodes"] = list(done_shortcodes)
            state.pop("active_batch_id", None)
            save_state(state)
            active_batch_id = None

        elif batch and batch.status in ("validating", "in_progress", "finalizing"):
            print(f"  Batch is still {batch.status} — polling until complete...")
            results = poll_batch(active_batch_id)
            if results:
                _c2s = state.get("cid_to_sc", {})
                n_written, n_errors = apply_results(results, obs_index, _c2s)
                print(f"  Applied: {n_written} obs updated, {n_errors} errors")
                for r in results:
                    cid = r.get("custom_id", "")
                    if cid.startswith("vf_"):
                        done_shortcodes.add(_c2s.get(cid, cid[3:]))
                state["done_shortcodes"] = list(done_shortcodes)
                state.pop("active_batch_id", None)
                save_state(state)
            # Return regardless; user can re-run for new work
            return

        elif batch and batch.status in ("failed", "expired", "cancelled"):
            print(f"  Previous batch {active_batch_id} has status={batch.status} — skipping resume")
            state.pop("active_batch_id", None)
            save_state(state)
            active_batch_id = None

    # ── Collect work items ──────────────────────────────────────────────────
    print("\nScanning mp4s for work...")
    work_items: list[tuple[Path, str, Path]] = []
    n_no_obs   = 0
    n_no_fill  = 0

    for mp4, sc in iter_mp4s():
        obs_path = obs_index.get(sc)
        if not obs_path:
            n_no_obs += 1
            continue
        if not needs_fill(obs_path):
            n_no_fill += 1
            continue
        if sc in done_shortcodes:
            continue
        work_items.append((mp4, sc, obs_path))

    if args.limit and args.limit > 0:
        work_items = work_items[: args.limit]

    cost_estimate = len(work_items) * 0.001
    print(f"  Total mp4s scanned   : {sum(1 for _ in iter_mp4s())}")
    print(f"  No matching obs      : {n_no_obs}")
    print(f"  Already fully filled : {n_no_fill}")
    print(f"  Already processed    : {len(done_shortcodes)}")
    print(f"  To process now       : {len(work_items)}")
    print(f"  Estimated cost       : ${cost_estimate:.3f}")

    if args.dry_run:
        print("\n[dry-run] No frames extracted, no API calls, no files written.")
        return

    if not work_items:
        print("\nNothing to do.")
        return

    # ── Extract frames and build batch requests ─────────────────────────────
    print(f"\nExtracting frames from {len(work_items)} mp4s...")
    requests_list, cid_to_sc, n_already_done, n_frame_errors = build_batch_requests(
        work_items, done_shortcodes, dry_run=False
    )

    if not requests_list:
        print("No valid frames extracted — nothing to submit.")
        return

    print(f"  Frame errors (skipped) : {n_frame_errors}")
    print(f"  Requests to submit     : {len(requests_list)}")

    # ── Submit batch ────────────────────────────────────────────────────────
    print("\nSubmitting batch to OpenAI...")
    batch_id = submit_batch(requests_list, "video_frames")
    state["active_batch_id"] = batch_id
    state["cid_to_sc"] = cid_to_sc   # persist mapping so apply() works after restart
    save_state(state)

    # ── Poll and apply ──────────────────────────────────────────────────────
    print("\nPolling batch (this may take a while for large runs)...")
    results = poll_batch(batch_id)

    if not results:
        print(
            "WARNING: no results returned. "
            "Re-run (without --dry-run) when the batch completes to apply results."
        )
        return

    # Apply
    print(f"\nApplying {len(results)} results to obs files...")
    n_written, n_errors = apply_results(results, obs_index, cid_to_sc)
    print(f"  Written : {n_written} obs updated")
    print(f"  Errors  : {n_errors}")

    # Mark done
    for r in results:
        cid = r.get("custom_id", "")
        if cid.startswith("vf_"):
            done_shortcodes.add(cid_to_sc.get(cid, cid[3:]))
    state["done_shortcodes"] = list(done_shortcodes)
    state.pop("active_batch_id", None)
    save_state(state)

    print(f"\nDone. State saved to {STATE_FILE}")
    print(f"Total processed to date: {len(done_shortcodes)}")


if __name__ == "__main__":
    main()
