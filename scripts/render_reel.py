#!/usr/bin/env python3
"""RENDER REEL (June 18) — the hybrid still→reel engine (the 2.85x Reels-placement lever, cheapest
instrument). Takes an ALREADY-RENDERED still + an Arabic caption → a 9:16 Ken-Burns clip with the
Arabic burned in via Pillow (reshaped+bidi — no AI video model renders Arabic reliably, so we
overlay it deterministically). ~$0 marginal (ffmpeg + Pillow local; the image is already paid).
Reuses the existing image; needs NO new fal render → NO gate for the assembly itself.
Usage: python3 scripts/render_reel.py --image IMG.jpg --caption 'نص عربي' --out reel.mp4 [--secs 8]
"""
import argparse, re, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
# Pillow on this Mac HAS libraqm → it does Arabic shaping + RTL itself. So pass RAW text with
# direction="rtl" (NEVER pre-reshape/bidi — that double-processes into garbled, reversed glyphs,
# the June-18 bug caught by eyeballing the frame).
# GeezaPro has no emoji/symbol glyphs → tofu boxes. WHITELIST instead of blacklist (a blacklist
# misses emoji; June 18 frame showed leftover tofu): keep only Arabic, Latin, digits, whitespace,
# and basic punctuation — drop everything else (emoji, symbols, variation selectors, ZWJ).
def _clean(text):
    text = re.sub(r"#[^\s#]+", "", text)          # drop hashtag tokens — they belong in the IG caption,
    text = re.sub(r"https?://\S+|@[\w.]+", "", text)  # not burned on the frame (also URLs/@handles)
    keep = []
    for ch in text:
        o = ord(ch)
        if (0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFDFF
                or 0xFE70 <= o <= 0xFEFF                    # Arabic + presentation forms
                or 0x0020 <= o <= 0x007E                    # ASCII (Latin, digits, punct)
                or ch in " \n\t،؛؟…—–“”‘’"):                # whitespace + Arabic/common punct
            keep.append(ch)
    return re.sub(r"\s+", " ", "".join(keep)).strip()

W, H = 1080, 1920
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/GeezaPro.ttc", "/System/Library/Fonts/GeezaPro.ttc",
    "/Library/Fonts/GeezaPro.ttc", "/System/Library/Fonts/Supplemental/Baghdad.ttc",
    "/System/Library/Fonts/Supplemental/Al Bayan.ttc", "/System/Library/Fonts/Supplemental/DecoTypeNaskh.ttc",
]


def _font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def arabic_overlay(caption, png_path):
    """Transparent 1080x1920 PNG: a bottom scrim + the Arabic caption. RAW text + direction='rtl'
    so libraqm shapes/joins/orders it (no manual reshape/bidi). Emoji stripped (no glyph → tofu)."""
    caption = _clean(caption)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(360):                       # bottom scrim for legibility over any photo
        a = int(180 * (i / 360))
        d.line([(0, H - 360 + i), (W, H - 360 + i)], fill=(0, 0, 0, a))
    font = _font(64)
    words, lines, cur = caption.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font, direction="rtl") <= W - 120:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    y = H - 110 - len(lines) * 78
    for ln in lines:
        tw = d.textlength(ln, font=font, direction="rtl")
        x = (W - tw) / 2
        d.text((x + 2, y + 2), ln, font=font, fill=(0, 0, 0, 200), direction="rtl")   # shadow
        d.text((x, y), ln, font=font, fill=(255, 255, 255, 255), direction="rtl")
        y += 78
    img.save(png_path)


def render(image, caption, out, secs=8):
    tmp = tempfile.mkdtemp()
    ov = str(Path(tmp) / "ov.png")
    arabic_overlay(caption, ov)
    frames = secs * 25
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"zoompan=z='min(zoom+0.0009,1.25)':d={frames}:s={W}x{H}:fps=25[bg];"
          f"[bg][1:v]overlay=0:0,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", image, "-i", ov,
           "-filter_complex", vf, "-map", "[v]", "-t", str(secs), "-c:v", "libx264", "-r", "25", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("ffmpeg failed:\n" + r.stderr[-600:])
    # also drop a preview frame (mid-clip) for an eyes-check on the Arabic
    subprocess.run(["ffmpeg", "-y", "-i", out, "-vf", "select=eq(n\\,100)", "-vframes", "1",
                    out.replace(".mp4", "_frame.jpg")], capture_output=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--caption", required=True)
    ap.add_argument("--out", default="/tmp/reel_demo.mp4")
    ap.add_argument("--secs", type=int, default=8)
    a = ap.parse_args()
    out = render(a.image, a.caption, a.out, a.secs)
    print(f"✅ reel → {out}  (+ preview frame {out.replace('.mp4','_frame.jpg')})")
