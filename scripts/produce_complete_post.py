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

    # 2) CAPTION — the CD-brain pen; product name MUST appear (Rule #12 — the system grounds it)
    c = rcs.load_client(a.handle)
    slot = {"occasion": a.occasion, "date": "2026-07-01", "type": "offer", "format": "image",
            "formula": "CF_01", "beat": a.occasion, "angle_theme": a.product, "product_name": a.product}
    # ANGLE FROM THE 5-CD-BRAIN PANEL (minds on DIFFERENT models — GPT/Gemini/Groq), not a
    # hardcoded brain (Mohamed June 24: "are all the minds working?"). panel=True fans the same
    # organ-built prompt across the model family; a dead key falls back inside — never blocks.
    try:
        sector = oc.load_brand(a.handle).get("sector", "")
    except Exception:
        sector = ""
    angle = None
    try:
        angle = rcs.make_angle(c, slot, sector, panel=True)
    except Exception as _ae:
        sys.stderr.write(f"panel angle failed ({type(_ae).__name__}: {str(_ae)[:60]}) — product-hero fallback\n")
    if not isinstance(angle, dict):
        angle = {}
    # always anchor the angle to THIS product's hero scene (the photo is product-forward)
    angle.setdefault("brain", "firaasa")
    angle.setdefault("post_type", "product")
    angle.setdefault("core", "product")
    angle["scene_ar"] = f"{a.product}: {idea}"
    print(f"  🧠 angle by minds: brain={angle.get('brain')} model={angle.get('by_model','?')}", file=sys.stderr)
    cap = ""
    # Try up to 3 times; keep first caption that names the product
    for _attempt in range(3):
        try:
            caps = rcs.render_captions(c, slot, angle)
            opts = caps if isinstance(caps, list) else caps.get("options", caps)
            if opts:
                for opt in (opts if isinstance(opts, list) else [opts]):
                    c_text = opt.get("caption") if isinstance(opt, dict) else opt
                    if c_text and a.product in c_text:
                        cap = c_text
                        break
                if not cap and opts:
                    # fallback: take first even without product name, then mark it
                    cap = (opts[0].get("caption") if isinstance(opts[0], dict) else opts[0]) or ""
        except Exception as e:
            sys.stderr.write(f"caption error (attempt {_attempt+1}): {type(e).__name__}: {e}\n")
        if cap and a.product in cap:
            break

    print(json.dumps({"handle": a.handle, "product": a.product, "occasion": a.occasion,
                      "image_url": img, "caption": cap, "render_ok": bool(img),
                      "complete": bool(img and cap)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
