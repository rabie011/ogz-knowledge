#!/usr/bin/env python3
"""RENDER REEL (June 18) — the hybrid still→reel engine (the 2.85x Reels-placement lever, cheapest
instrument). Takes an ALREADY-RENDERED still + an Arabic caption → a 9:16 Ken-Burns clip with the
caption burned in via Pillow + libraqm (RAW RTL — libraqm shapes/joins/orders; NEVER manual
reshape/bidi, which double-processes into garbled glyphs). ~$0 marginal (ffmpeg + Pillow local;
the image is already paid). Reuses the existing image; needs NO new fal render → NO gate.
Usage: python3 scripts/render_reel.py --image IMG.jpg --caption 'نص عربي' --out reel.mp4 [--secs 8]
"""
import argparse, re, subprocess, tempfile
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
try:
    from fontTools.ttLib import TTFont, TTCollection   # to check the chosen font's real glyph coverage
    _HAVE_FONTTOOLS = True
except Exception:
    _HAVE_FONTTOOLS = False
# Pillow on this Mac HAS libraqm → it does Arabic shaping + RTL itself. So pass RAW text with
# direction="rtl" (NEVER pre-reshape/bidi — that double-processes into garbled, reversed glyphs,
# the June-18 bug caught by eyeballing the frame).
# TWO ways a glyph becomes a tofu box, both guarded: (1) emoji/symbols — the WHITELIST keeps only
# Arabic/Latin/digits/punct; (2) a char the RENDER FONT lacks — Arabic-only GeezaPro boxes Latin
# "Dunkin"/Western digits (the skeptic's catch). So we lead with a DUAL-SCRIPT font (Arial Unicode)
# AND strip any kept char the chosen font can't actually draw (_covered). A box NEVER reaches the
# frame (Rule #8: refuse, don't warn — here, drop rather than burn a box).
def _clean(text, font_path=None):
    text = re.sub(r"#[^\s#]+", "", text)          # drop hashtag tokens — they belong in the IG caption,
    text = re.sub(r"https?://\S+|@[\w.]+", "", text)  # not burned on the frame (also URLs/@handles)
    covered = _covered(font_path) if font_path else None
    keep = []
    for ch in text:
        o = ord(ch)
        if not (0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFDFF
                or 0xFE70 <= o <= 0xFEFF                    # Arabic + presentation forms
                or 0x0020 <= o <= 0x007E                    # ASCII (Latin, digits, punct)
                or ch in " \n\t،؛؟…—–“”‘’"):                # whitespace + Arabic/common punct
            continue
        if covered is not None and not ch.isspace() and o not in covered:
            continue                                        # font can't draw it → drop, never box it
        keep.append(ch)
    return re.sub(r"\s+", " ", "".join(keep)).strip()

W, H = 1080, 1920
# DUAL-SCRIPT FONTS FIRST: these cover Arabic + Latin + Western digits in ONE face (verified via
# fontTools cmap + an eyeballed mixed render "قهوة Dunkin بـ 8 ريال"), so bilingual brand captions
# never box. The Arabic-ONLY faces (GeezaPro etc.) box Latin/digits → last-resort only, and the
# _covered strip then drops the Latin so a box still never ships.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Tahoma.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/GeezaPro.ttc", "/System/Library/Fonts/GeezaPro.ttc",
    "/Library/Fonts/GeezaPro.ttc", "/System/Library/Fonts/Supplemental/Baghdad.ttc",
    "/System/Library/Fonts/Supplemental/Al Bayan.ttc", "/System/Library/Fonts/Supplemental/DecoTypeNaskh.ttc",
]


def _font_path():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    # REFUSE, don't warn (Rule #8): load_default is a tiny bitmap font with no Arabic glyphs and
    # ignores direction='rtl' → silent tofu/garbled Arabic. A font regression must fail loudly.
    raise SystemExit("no Arabic-capable font found among FONT_CANDIDATES — refuse (load_default cannot shape RTL)")


def _font(size):
    return ImageFont.truetype(_font_path(), size)


@lru_cache(maxsize=8)
def _covered(path):
    """Codepoints the chosen font can actually draw (union over all faces of a .ttc). Used to STRIP
    any kept char the font lacks so a tofu box never reaches the frame. None = can't check → no strip."""
    if not (_HAVE_FONTTOOLS and path):
        return None
    cps = set()
    try:
        faces = TTCollection(path).fonts if str(path).endswith(".ttc") else [TTFont(path)]
        for f in faces:
            cps |= set(f.getBestCmap().keys())
    except Exception:
        return None
    return cps or None


def arabic_overlay(caption, png_path):
    """Transparent 1080x1920 PNG: a dark scrim + the caption. RAW text + direction='rtl' so libraqm
    shapes/joins/orders it (no manual reshape/bidi). _clean strips emoji + any glyph the font lacks."""
    fp = _font_path()
    caption = _clean(caption, fp)
    if not caption:
        # REFUSE, don't warn (Rule #8): a hashtag/emoji/url/font-uncovered/whitespace-only caption
        # cleans to '' and would silently emit a valid mp4 with a scrim but NO text. SystemExit (not
        # ValueError) for a clean one-line refuse matching the missing-image/font guards.
        raise SystemExit("empty caption after clean (hashtag/emoji/url/uncovered-only) — refuse blank-text reel")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(fp, 64)
    words, lines, cur = caption.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font, direction="rtl") <= W - 120:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    # CLAMP so the block always sits inside the frame bottom-third (a long caption used to push
    # start_y negative — top lines drawn off-frame). Cap line count, ellipsis the last kept line.
    MAX_LINES = 9                              # 9*78 + ~110 = ~812px block, fits within the bottom third
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        lines[-1] = (lines[-1] + " …")[:120]
    block = len(lines) * 78
    y = max(40, H - 70 - block)                # block TOP — bottom-anchored, never negative/off-top
    # SCRIM: a STRONG flat dark band behind the ACTUAL text + a short fade-in above its top edge. A
    # bottom-fade gradient (darkest at frame bottom, ~transparent at top) left the upper lines of a
    # tall block floating over the bright photo, illegible — the skeptic's catch. Back EVERY line.
    band_top, FADE = max(0, y - 40), 70
    for yy in range(band_top, H):
        a = int(195 * ((yy - band_top) / FADE)) if yy < band_top + FADE else 195
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    for ln in lines:
        tw = d.textlength(ln, font=font, direction="rtl")
        x = (W - tw) / 2
        d.text((x + 2, y + 2), ln, font=font, fill=(0, 0, 0, 200), direction="rtl")   # shadow
        d.text((x, y), ln, font=font, fill=(255, 255, 255, 255), direction="rtl")
        y += 78
    img.save(png_path)


def render(image, caption, out, secs=8):
    # REFUSE, don't warn (Rule #8): a missing still would otherwise surface as a raw ffmpeg stderr
    # dump. Fail clearly up front (also double-guards the producer, which only calls us on an
    # already-on-disk still — assembly is $0 ffmpeg+Pillow, NEVER a new fal render).
    if not Path(image).exists():
        raise SystemExit(f"image not found: {image} — refuse (would fail ffmpeg)")
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
    # preview frame at clip MIDPOINT for an eyes-check (always exists for any secs≥1; a fixed frame
    # 100 produced NO file for clips shorter than 4s, leaving a dangling _frame.jpg reference).
    mid = max(1, (secs * 25) // 2)
    subprocess.run(["ffmpeg", "-y", "-i", out, "-vf", f"select=eq(n\\,{mid})", "-vframes", "1",
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
