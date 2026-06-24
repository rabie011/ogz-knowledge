#!/usr/bin/env python3
"""RABIE VISUAL JUDGE — RABIE (GPT-4o vision) judges a complete post or photo-only render.

24h-orchestra rule: RABIE is the GPT critic, not Claude. This is the mechanical RABIE.
He judges HARSH: 3=default good-work, 4=earned-with-proof, 5=rare.
Criteria: product-truth · composition/style · Saudi/Najdi cultural fit · caption-photo alignment.

Usage:
  # Photo-only judge
  python3 scripts/rabie_judge.py --image api/static/renders_v37/albaik_دبل_بيك_R05.jpg \\
      --handle albaik --product "دبل بيك"

  # Complete post (photo + caption)
  python3 scripts/rabie_judge.py --image api/static/renders_v37/albaik_دبل_بيك_R05.jpg \\
      --handle albaik --product "دبل بيك" --caption "نص الكابشن هنا"
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

VISION_MODEL = "gpt-4o"


def _env(k):
    f = os.path.expanduser("~/.abraham_env")
    if not os.path.exists(f):
        return None
    for l in open(f):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def _product_truth(handle, product):
    p = B / "clients" / handle / "profile" / "product_truth.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    products = d.get("products", d)  # some have {"products": {...}}, some are flat
    return products.get(product, {})


def _brand_meta(handle):
    p = B / "clients" / handle / "profile" / "product_truth.json"
    if not p.exists():
        return ""
    d = json.loads(p.read_text())
    m = d.get("_meta", {})
    return m.get("brand", "") or m.get("hard_truth", "")


def _build_prompt(handle, product, pt, caption):
    brand_ctx = _brand_meta(handle)
    identity = pt.get("identity_dna", "")
    signature = pt.get("signature", "")
    texture = pt.get("texture", "")
    fmt = pt.get("format", "")
    components = pt.get("components", [])

    comp_text = "\n".join(f"  - {c}" for c in components) if components else "(not specified)"

    caption_section = ""
    if caption:
        caption_section = f"""
CAPTION (judge alignment with photo):
\"\"\"{caption}\"\"\"
"""

    return f"""You are RABIE — a HARSH Saudi creative director judging this post for OGZ Studios.
You have FULL veto power. 3 = default for good work, 4 = must earn it with proof, 5 = rare.
If anything is wrong, say it clearly and what to fix in the machine (not hand-editing).

BRAND: {handle} — {brand_ctx}
PRODUCT: {product}

PRODUCT TRUTH (what the real product looks like):
  Identity: {identity}
  Signature: {signature}
  Texture/form: {texture}
  Format: {fmt}
  Components:
{comp_text}

JUDGING AXES (score each 1-5, then give overall):
1. PRODUCT TRUTH — does the image show the REAL product? Right shape, color, components, format?
   A generic or wrong-looking product = 1-2. Exact match = 4-5.
2. COMPOSITION / VISUAL QUALITY — lighting, framing, style. OGZ standard = dark moody studio or
   authentic Najdi environment. Clean, professional, appetite-forward.
3. SAUDI/CULTURAL FIT — does it look like it belongs in Saudi Arabia? No Western-only aesthetics.
4. BRAND SYSTEM — correct packaging (if visible), no competing brands, no invented logos.
{f"5. CAPTION-PHOTO ALIGNMENT — does the caption match what we see? Product name correct?" if caption else ""}

Respond in JSON only — no prose before or after:
{{
  "product_truth_score": <1-5>,
  "composition_score": <1-5>,
  "cultural_fit_score": <1-5>,
  "brand_system_score": <1-5>,
  {"\"caption_alignment_score\": <1-5>," if caption else ""}
  "overall": <1-5>,
  "verdict": "bank" | "fix" | "kill",
  "what_is_wrong": ["<specific issue>", ...],
  "machine_fix": ["<what to change in the prompt/system, not hand-edit>", ...],
  "rabie_note": "<one sharp sentence>"
}}

verdict rules: overall ≥ 4 = "bank", overall = 3 = "fix", overall ≤ 2 = "kill"
{caption_section}
Describe what you SEE in the image FIRST (one sentence) then score."""


def judge(image_path, handle, product, caption=""):
    img = Path(image_path)
    if not img.exists():
        raise SystemExit(f"🛑 image not found: {image_path}")

    key = _env("OPENAI_API_KEY")
    if not key:
        raise SystemExit("🛑 no OPENAI_API_KEY in ~/.abraham_env")

    pt = _product_truth(handle, product)
    prompt = _build_prompt(handle, product, pt, caption)

    suffix = img.suffix.lower().lstrip(".") or "jpeg"
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    data_uri = "data:image/" + mime + ";base64," + base64.b64encode(img.read_bytes()).decode()

    import urllib.request
    body = {
        "model": VISION_MODEL,
        "temperature": 0,
        "max_tokens": 600,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_uri, "detail": "high"}},
            ]
        }]
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except Exception as e:
        raise SystemExit(f"🛑 GPT vision call failed: {e}")

    raw = (resp["choices"][0]["message"]["content"] or "").strip()
    if raw.startswith("```"):
        import re
        raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` ")

    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit(f"🛑 RABIE reply not JSON: {raw[:300]}")

    # normalise
    d.setdefault("what_is_wrong", [])
    d.setdefault("machine_fix", [])
    d.setdefault("rabie_note", "")
    overall = int(d.get("overall", 1))
    if "verdict" not in d:
        d["verdict"] = "bank" if overall >= 4 else ("fix" if overall == 3 else "kill")
    return d


VERDICT_LOG = B / "data/rabie_verdicts.jsonl"


def log_verdict(handle, product, image, verdict):
    """PERSIST every RABIE verdict (the learning ledger — Rule #6 writer). Append-only.
    The reader is lessons_for() below + render_openclaw's pre-prompt LEARNED block."""
    import time
    rec = {
        "ts": int(time.time()),
        "handle": handle, "product": product, "image": image,
        "verdict": verdict.get("verdict"), "overall": verdict.get("overall"),
        "scores": {k: verdict.get(k) for k in (
            "product_truth_score", "composition_score", "cultural_fit_score",
            "brand_system_score", "caption_alignment_score")},
        "what_is_wrong": verdict.get("what_is_wrong", []),
        "machine_fix": verdict.get("machine_fix", []),
        "rabie_note": verdict.get("rabie_note", ""),
    }
    VERDICT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(VERDICT_LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def lessons_for(handle, product):
    """READER (Rule #6) — the accumulated past corrections for this (handle, product): every
    'what_is_wrong' RABIE has ever flagged on a non-bank verdict. render_openclaw injects these
    so the system does NOT repeat a mistake the eye already caught. Returns a deduped list."""
    if not VERDICT_LOG.exists():
        return []
    seen, lessons = set(), []
    for ln in VERDICT_LOG.read_text().splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("handle") != handle or r.get("product") != product:
            continue
        # learn from what was WRONG (kills + fixes), not from banks
        if r.get("verdict") in ("fix", "kill"):
            for w in (r.get("what_is_wrong") or []):
                key = w.strip()[:60]
                if key and key not in seen:
                    seen.add(key)
                    lessons.append(w.strip())
    return lessons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--handle", required=True)
    ap.add_argument("--product", required=True)
    ap.add_argument("--caption", default="")
    ap.add_argument("--no-log", action="store_true", help="do not persist this verdict (default: persist)")
    a = ap.parse_args()

    verdict = judge(a.image, a.handle, a.product, a.caption)

    overall = verdict.get("overall", 0)
    v = verdict.get("verdict", "?")
    note = verdict.get("rabie_note", "")

    emoji = {"bank": "✅", "fix": "🔧", "kill": "💀"}.get(v, "?")
    print(f"\n{'='*60}")
    print(f"RABIE says: {emoji} {v.upper()}  (overall {overall}/5)")
    print(f"  product_truth: {verdict.get('product_truth_score')}/5")
    print(f"  composition:   {verdict.get('composition_score')}/5")
    print(f"  cultural_fit:  {verdict.get('cultural_fit_score')}/5")
    print(f"  brand_system:  {verdict.get('brand_system_score')}/5")
    if "caption_alignment_score" in verdict:
        print(f"  caption_align: {verdict.get('caption_alignment_score')}/5")
    print(f"\n  Note: {note}")
    if verdict["what_is_wrong"]:
        print("\n  WRONG:")
        for w in verdict["what_is_wrong"]:
            print(f"    - {w}")
    if verdict["machine_fix"]:
        print("\n  FIX THE MACHINE:")
        for f in verdict["machine_fix"]:
            print(f"    → {f}")
    print(f"{'='*60}\n")
    if not a.no_log:
        log_verdict(a.handle, a.product, a.image, verdict)
        print(f"  📝 verdict logged → {VERDICT_LOG.relative_to(B)} (the system now remembers this)")
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
