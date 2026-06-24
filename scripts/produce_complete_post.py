#!/usr/bin/env python3
"""Produce ONE complete post (photo + caption) for a (client, product) via the FULL system.

The reusable unit of the 20-perfect-posts orchestra (Rule #12 — the system produces):
  ART-DIRECTOR brief  →  product_truth + assembly-lock RENDER (gated, $15 cap)  →  CAPTION (the
  CD-brain pen, product name grounded). Emits JSON {image_url, caption} for RABIE (GPT) to judge.

Usage: python3 scripts/produce_complete_post.py --handle albaik --product "دبل بيك" [--occasion evergreen]
"""
import argparse, json, subprocess, sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--product", required=True)
    ap.add_argument("--occasion", default="evergreen")
    ap.add_argument("--idea", default="", help="optional scene seed; default = product-hero")
    a = ap.parse_args()
    import art_director as ad
    import render_client_slot as rcs

    idea = a.idea or f"منتج البطل: {a.product} — لقطة استوديو شهية للمنتج الحقيقي"

    # 1) PHOTO — Art-Director brief → master render (product_truth + assembly-lock; gated)
    brief = ad.art_direct(idea, a.handle, "image", occasion=a.occasion, llm=ad._real_gpt, product=a.product)
    args = ad.to_converter_args(brief)
    img = ""
    if args:
        cmd = [sys.executable, str(B / "scripts/render_openclaw.py"), "--handle", a.handle,
               "--chain", args["chain"], "--scene", args["scene"], "--product", a.product, "--go"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if "image_url:" in line:
                img = line.split("image_url:")[1].strip()
        if not img:
            sys.stderr.write((r.stdout[-500:] + r.stderr[-500:]) + "\n")

    # 2) CAPTION — the CD-brain pen (product name grounded); product-hero angle to match the photo
    c = rcs.load_client(a.handle)
    slot = {"occasion": a.occasion, "date": "2026-07-01", "type": "offer", "format": "image",
            "formula": "CF_01", "beat": a.occasion, "angle_theme": a.product}
    angle = {"scene_ar": f"{a.product}: {idea}", "brain": "firaasa", "post_type": "product", "core": "product"}
    cap = ""
    try:
        caps = rcs.render_captions(c, slot, angle)
        opts = caps if isinstance(caps, list) else caps.get("options", caps)
        if opts:
            cap = opts[0].get("caption") if isinstance(opts[0], dict) else opts[0]
    except Exception as e:
        sys.stderr.write(f"caption error: {type(e).__name__}: {e}\n")

    print(json.dumps({"handle": a.handle, "product": a.product, "occasion": a.occasion,
                      "image_url": img, "caption": cap, "render_ok": bool(img),
                      "complete": bool(img and cap)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
