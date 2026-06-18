#!/usr/bin/env python3
"""REEL BATCH (June 18) — reel-ify a set of image+caption posts via render_reel (the hybrid still→reel
engine). Reuses ALREADY-rendered/scraped stills → NO new fal render → NO gate for the assembly. For
the PILOTS this runs the moment their images exist (after the $3 no_fal_photos+key tap); for a GOLD
reference like Dunkin it reel-ifies real stills now as a proof. Guards: skips any post with no local
image (and says so — never silently). Money: $0 marginal (ffmpeg+Pillow local).
Usage: python3 scripts/reel_batch.py --handle dunkindonutsksa --n 3 --out /tmp/reels
"""
import argparse, glob, json
from pathlib import Path
import render_reel as rr

B = Path(__file__).parent.parent


def _posts_with_images(handle):
    """top-engagement posts that HAVE a local still + a caption → [(likes, shortcode, img, caption)]."""
    fe = next((Path(p) for p in glob.glob(str(B / f"11_who_to_learn_from/_inbox/*{handle}*/*_full_extraction.json"))), None)
    mediadir = fe.parent / "media" if fe else None
    out = []
    if fe:
        for p in json.loads(fe.read_text()).get("posts", []):
            sc, cap = p.get("shortcode"), (p.get("caption") or "").strip()
            img = mediadir / f"{sc}.jpg" if mediadir else None
            if sc and cap and img and img.exists():
                out.append((p.get("likes", 0), sc, str(img), cap))
    return sorted(out, reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default="dunkindonutsksa")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--out", default="/tmp/reels")
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    posts = _posts_with_images(a.handle)
    if not posts:
        print(f"  ⚠ {a.handle}: 0 posts with a local image — reel assembly is READY but needs rendered "
              f"images (pilots await the $3 no_fal_photos+FAL-key tap). No reel produced (not silently).")
        return
    made = 0
    for likes, sc, img, cap in posts[:a.n]:
        outp = f"{a.out}/{a.handle}_{sc}.mp4"
        try:
            rr.render(img, cap, outp, secs=8)
            made += 1
            print(f"  ✅ {sc} ({likes} likes) → {Path(outp).name}")
        except SystemExit as e:
            print(f"  ⚠ {sc}: {str(e)[:80]}")
    print(f"  reels: {made}/{min(a.n,len(posts))} · out → {a.out}  ($0 marginal, no gate)")


if __name__ == "__main__":
    main()
