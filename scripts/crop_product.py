#!/usr/bin/env python3
"""PRODUCT-CROP for the LIFESTYLE-RENDER path (C245, patch-1).

WHY (Mohamed, test-all-industries): jewelry/fashion/beauty brands post model/lifestyle shots, not
clean product photos (alnasserjewelry: 0 usable clean refs in 149). The v3.7 render uses a brand
image as the flux edit REFERENCE (identity lock) — but a person_incidental ref LEAKS the person
(skin/body/face) into the output even with a faceless prompt (diffusion is associative → UNSAFE,
DeepSeek's safety catch). SAFE design: locate the PRODUCT inside the lifestyle photo (vision bbox) →
CROP it out → use the clean crop as the reference → the render NEVER sees the person.

This module is patch-1: the crop PRIMITIVE. Two clean halves so the geometry is testable with zero
spend:
  • crop_to_bbox(img_path, bbox, out_path)  — PURE PIL geometry, no network (this is what tests hit)
  • product_bbox(img_path, key)             — gpt-4o vision returns the normalized bbox (OpenAI funded)
  • crop_product(img_path, key, out_path)    — the two composed (locate → crop)

Bbox convention: normalized floats {x0,y0,x1,y1} in [0,1], origin top-left, x1>x0, y1>y0.

CONSUMER (Rule #6): the crop written to clients/<h>/profile/crops/ is READ by pick_reference
(openclaw_convert.py). C245 patch-3 wired the reader: register_crop() (below) persists each crop
into the brand's media_class.json as a clean, person-free product reference, and pick_reference's
existing clean-ref scorer matches it by product — so a jewelry/fashion brand with no clean product
photo gets a SAFE crop reference instead of a GAP-REFUSE. The wire is live (test_crop_product.py
TestPatch3CropRegistration proves register→pick_reference end-to-end).
"""
import argparse, base64, json, os, re, urllib.request
from pathlib import Path
from PIL import Image

B = Path(__file__).parent.parent


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


BBOX_PROMPT = (
    "You are locating the SINGLE main product a jewelry/fashion/beauty brand is selling in this "
    "lifestyle photo, so it can be cropped away from any person. Return STRICT JSON only: "
    '{"found":true|false,'
    '"product_en":"<2-4 word english name, e.g. \'gold pendant necklace\' / \'diamond ring\'>",'
    '"bbox":{"x0":<float>,"y0":<float>,"x1":<float>,"y1":<float>}}. '
    "bbox is the tight box around the PRODUCT ONLY (the jewelry/garment/item — NOT the person), "
    "as fractions of image width/height in [0,1], origin top-left, with x1>x0 and y1>y0. "
    "If no clear product is visible, set found=false and bbox to zeros."
)


def clamp01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else float(v)


def _sanitize_bbox(bbox):
    """Coerce a raw model bbox into a valid normalized box, or raise if unusable."""
    x0, y0 = clamp01(bbox["x0"]), clamp01(bbox["y0"])
    x1, y1 = clamp01(bbox["x1"]), clamp01(bbox["y1"])
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"degenerate bbox after clamp: {(x0, y0, x1, y1)}")
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def crop_to_bbox(img_path, bbox, out_path):
    """PURE geometry: crop img_path to a normalized bbox and save to out_path. No network.

    Returns (out_path, (left, upper, right, lower)) in absolute pixels.
    """
    bbox = _sanitize_bbox(bbox)
    im = Image.open(img_path)
    w, h = im.size
    left, upper = int(round(bbox["x0"] * w)), int(round(bbox["y0"] * h))
    right, lower = int(round(bbox["x1"] * w)), int(round(bbox["y1"] * h))
    # guarantee at least a 1px box even if rounding collapses it
    right = max(right, left + 1)
    lower = max(lower, upper + 1)
    crop = im.crop((left, upper, right, lower))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if crop.mode not in ("RGB", "L"):
        crop = crop.convert("RGB")
    crop.save(out_path, "JPEG", quality=92)
    return str(out_path), (left, upper, right, lower)


def product_bbox(img_path, key):
    """gpt-4o vision → {found, product_en, bbox}. Raises on API/parse failure."""
    b64 = base64.b64encode(Path(img_path).read_bytes()).decode()
    body = {"model": "gpt-4o", "max_tokens": 150, "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": BBOX_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}}]}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=60).read())
    txt = out["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError(f"no JSON in vision reply: {txt[:120]}")
    return json.loads(m.group(0))


def crop_product(img_path, key, out_path):
    """Locate (vision) → crop (PIL). Returns dict with product_en + crop path, or {'found': False}."""
    loc = product_bbox(img_path, key)
    if not loc.get("found"):
        return {"found": False, "src": str(img_path)}
    saved, px = crop_to_bbox(img_path, loc["bbox"], out_path)
    return {"found": True, "product_en": loc.get("product_en", ""),
            "src": str(img_path), "crop": saved, "px": px}


def register_crop(handle, crop_path, product_en, src=""):
    """CONSUMER WIRE (Rule #6, C245 patch-3): persist the crop into the brand's media_class.json
    as a clean, person-free product reference, so pick_reference (openclaw_convert.py) matches it
    BY PRODUCT and uses it as the flux-edit reference — instead of GAP-REFUSING a jewelry/fashion
    brand that has no clean product photo (the whole reason the lifestyle-render path exists).

    Design (RABIE + DeepSeek, consult-before-build): reuse the EXISTING media_class.json schema +
    pick_reference's existing scorer — NOT a second _index.json (over-engineering). A crop is safe
    (the person was cropped out, DeepSeek's safety design) so it carries has_person=False,
    is_royal_or_public_figure=False, usable_as_product_reference=True → it flows straight into
    pick_reference's `clean` list and is scored by product_en/product_keywords like any real ref.

    Returns the repo-relative key written (so B/key == the crop file, which pick_reference checks)."""
    mc = B / "clients" / handle / "profile" / "media_class.json"
    data = json.loads(mc.read_text()) if mc.exists() else {}
    cp = Path(crop_path)
    key = str(cp.relative_to(B)) if cp.is_absolute() else str(cp)
    data[key] = {
        "kind": "product_crop",
        "has_person": False,
        "is_royal_or_public_figure": False,
        "usable_as_product_reference": True,
        "product_en": product_en or "",
        "product_keywords": product_en or "",
        "source": "crop",
        "src": src,
    }
    mc.parent.mkdir(parents=True, exist_ok=True)
    mc.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--image", required=True, help="path (abs or repo-relative) to a lifestyle image")
    a = ap.parse_args()
    key = env("OPENAI_API_KEY")
    if not key:
        raise SystemExit("no OPENAI_API_KEY in ~/.abraham_env")
    src = Path(a.image)
    if not src.is_absolute():
        src = B / a.image
    out = B / "clients" / a.handle / "profile" / "crops" / (src.stem + "_crop.jpg")
    res = crop_product(src, key, out)
    if not res.get("found"):
        print(f"— no product located in {src.name} (safe: nothing written)")
        return
    # CONSUMER WIRE (C245 patch-3): register the crop into media_class.json so pick_reference
    # matches it by product and uses it as the flux-edit ref (no longer a severed wire).
    reg = register_crop(a.handle, res["crop"], res["product_en"], src=str(src))
    print(f"✅ cropped {res['product_en']!r} → {Path(res['crop']).relative_to(B)}  px={res['px']}")
    print(f"   ↳ registered as clean product ref in media_class.json ({reg}) — pick_reference will match '{res['product_en']}'")


if __name__ == "__main__":
    main()
