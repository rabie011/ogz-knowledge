#!/usr/bin/env python3
"""
download_video_thumbnails.py
Download the display-image thumbnail for video obs that are missing scene_type
and have no local file in _inbox/.

Uses instaloader with Chrome cookies. Saves:
  11_who_to_learn_from/_inbox/@{handle}/media/{shortcode}_thumb.jpg

Usage:
  python3 scripts/download_video_thumbnails.py --dry-run   # show counts only
  python3 scripts/download_video_thumbnails.py             # download all
  python3 scripts/download_video_thumbnails.py --limit 100 # first N posts
  python3 scripts/download_video_thumbnails.py --account kuduksa  # one account
"""
from __future__ import annotations
import argparse, json, re, sys, time, traceback
from pathlib import Path
import requests

try:
    import instaloader
except ImportError:
    sys.exit("pip install instaloader")

REPO     = Path(__file__).parent.parent
OBS_ROOT = REPO / "11_who_to_learn_from" / "observations"
INBOX    = REPO / "11_who_to_learn_from" / "_inbox"
STATE_F  = REPO / "logs" / "thumb_download_state.json"

FILL_FIELDS = ["text_overlay_visible", "arabic_text_visible",
               "product_visible", "brand_logo_visible", "scene_type"]


# ── helpers ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_F.exists():
        return json.loads(STATE_F.read_text())
    return {"done": [], "failed": []}

def save_state(s: dict) -> None:
    STATE_F.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def sc_from_url(url: str) -> str | None:
    m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
    return m.group(1) if m else None

def local_stems() -> set[str]:
    stems = set()
    for f in INBOX.rglob("*"):
        if f.suffix in (".mp4", ".jpg", ".jpeg", ".png"):
            stems.add(re.sub(r"_thumb$", "", f.stem))
    return stems

def needs_scene(d: dict) -> bool:
    vis = d.get("visual_observations") or {}
    return vis.get("scene_type") is None

def collect_work(account_filter: str | None = None) -> list[dict]:
    """Return list of {shortcode, handle, url, obs_path}."""
    existing = local_stems()
    work = []
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            ct = str(d.get("content_ref", {}).get("content_type", "")).lower()
            if ct not in ("video", "reel"):
                continue
            if not needs_scene(d):
                continue
            url = d.get("content_ref", {}).get("source_url", "")
            sc  = sc_from_url(url)
            if not sc:
                continue
            if sc in existing:
                continue
            handle = d.get("account_handle_normalized", "unknown")
            if account_filter and handle != account_filter:
                continue
            work.append({"shortcode": sc, "handle": handle,
                         "url": url, "obs_path": str(f)})
        except Exception:
            pass
    # deduplicate by shortcode
    seen: set[str] = set()
    deduped = []
    for item in work:
        if item["shortcode"] not in seen:
            seen.add(item["shortcode"])
            deduped.append(item)
    return deduped


# ── core download ──────────────────────────────────────────────────────────────

def download_thumbnail(
    L: "instaloader.Instaloader",
    shortcode: str,
    handle: str,
    state: dict,
    session: requests.Session,
) -> bool:
    """
    Download the display image for a post by shortcode.
    Returns True on success, False on failure.
    """
    out_dir = INBOX / f"@{handle}" / "media"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{shortcode}_thumb.jpg"
    if out_path.exists():
        return True

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        display_url = post.url          # highest-res display image
        r = session.get(display_url, timeout=20)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except instaloader.exceptions.LoginRequiredException:
        print(f"    ⚠ Login required for {shortcode} — skipping")
        state["failed"].append(shortcode)
        return False
    except instaloader.exceptions.QueryReturnedNotFoundException:
        print(f"    ⚠ Post not found: {shortcode}")
        state["failed"].append(shortcode)
        return False
    except Exception as e:
        print(f"    ⚠ Error {shortcode}: {e}")
        state["failed"].append(shortcode)
        return False


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true")
    ap.add_argument("--limit",    type=int, default=0)
    ap.add_argument("--account",  type=str, default="")
    args = ap.parse_args()

    state = load_state()
    already_failed = set(state.get("failed", []))
    already_done   = set(state.get("done", []))

    work = collect_work(args.account or None)
    # skip already done/failed
    work = [w for w in work
            if w["shortcode"] not in already_done
            and w["shortcode"] not in already_failed]

    if args.limit:
        work = work[: args.limit]

    print(f"Posts to download: {len(work)}")
    by_acct = {}
    for w in work:
        by_acct.setdefault(w["handle"], 0)
        by_acct[w["handle"]] += 1
    for h, n in sorted(by_acct.items(), key=lambda x: -x[1]):
        print(f"  @{h}: {n}")

    if args.dry_run or not work:
        if args.dry_run:
            print("[dry-run] No downloads.")
        return

    # ── Init instaloader ────────────────────────────────────────────────────
    print("\nInitialising instaloader with Chrome cookies...")
    L = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )
    try:
        L.load_session_from_cookies_txt(
            "/Users/abarihm/Library/Application Support/Google/Chrome/Default/Cookies"
        )
        print("  Loaded Chrome cookies ✅")
    except Exception as e:
        try:
            instaloader.load_session_from_cookies(L, "chrome")
            print("  Loaded Chrome cookies (browser_cookie3) ✅")
        except Exception as e2:
            print(f"  ⚠ Cookie load failed: {e2} — attempting anonymous")

    session = requests.Session()
    # Copy cookies from instaloader context to requests session
    try:
        for k, v in L.context._session.cookies.items():
            session.cookies.set(k, v)
    except Exception:
        pass
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36"
    })

    # ── Download loop ───────────────────────────────────────────────────────
    ok = fail = 0
    for i, item in enumerate(work, 1):
        sc, handle = item["shortcode"], item["handle"]
        print(f"  [{i}/{len(work)}] @{handle}/{sc}", end=" ", flush=True)
        success = download_thumbnail(L, sc, handle, state, session)
        if success:
            ok += 1
            state["done"].append(sc)
            print("✅")
        else:
            fail += 1
            print("❌")
        # save state every 20
        if i % 20 == 0:
            save_state(state)
        # polite pacing: 1 req/sec
        time.sleep(1.0)

    save_state(state)
    print(f"\nDone: {ok} downloaded, {fail} failed")
    print(f"Next: python3 scripts/enrich_video_frames_ext.py")


if __name__ == "__main__":
    main()
