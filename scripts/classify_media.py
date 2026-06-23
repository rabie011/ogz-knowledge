#!/usr/bin/env python3
"""CLASSIFY BRAND MEDIA for safe reference selection (June 21, Mohamed: 'fix reference selection').

The v3.7 render uses a brand media image as the flux-2-pro/edit REFERENCE (identity lock). The old
pick_reference returned the first file alphabetically — which for albaik was a ROYAL PORTRAIT, and
the edit model anchors identity on the reference → it rendered a MAN for a woman scene (and royals
are a cultural red line). This vision-tags each media image (gpt-4o, OpenAI funded) so the reference
pick uses a clean PRODUCT/PACKAGING shot, NEVER a person/royal portrait.

Cached + idempotent (skips already-tagged). → clients/<h>/profile/media_class.json
Usage: python3 scripts/classify_media.py --handle albaik [--n 60]
"""
import argparse, base64, json, os, re, urllib.request
from pathlib import Path

B = Path(__file__).parent.parent


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


PROMPT = (
    "Classify this brand's social-media image for use as an AI image-generation REFERENCE. "
    "Return STRICT JSON only: "
    '{"kind":"product_food|packaging|storefront|person_portrait|graphic|other",'
    '"has_person":true|false,"is_royal_or_public_figure":true|false,'
    '"usable_as_product_reference":true|false,'
    '"product_en":"<2-4 word ENGLISH name of the SPECIFIC product/dish shown, e.g. '
    "'double chicken fillet burger' / 'crispy chicken strips' / 'chicken nuggets box' / "
    "'chicken wrap' / 'storefront' — empty if none>\","
    '"product_keywords":"<comma-separated match keywords, INCLUDING any Arabic product name '
    "visible in the image, e.g. 'دبل بيك,burger,double,fillet' or 'بيكيز,strips,tenders'>\"}. "
    "usable_as_product_reference is TRUE only if the image cleanly shows the brand's FOOD / PRODUCT / "
    "PACKAGING with NO prominent person. Any portrait or photo featuring a person — ESPECIALLY a "
    "royal or public figure — is FALSE (it would hijack the generated subject). "
    "Be SPECIFIC about the food in product_en/product_keywords (burger vs strips vs nuggets vs wrap "
    "vs box) so it can be matched to a named menu item."
)


def classify(path, key):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    body = {"model": "gpt-4o", "max_tokens": 120, "temperature": 0,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}}]}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=60).read())
    txt = out["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)) if m else {"kind": "other", "usable_as_product_reference": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--n", type=int, default=60, help="max images to classify this run")
    a = ap.parse_args()
    key = env("OPENAI_API_KEY")
    if not key:
        raise SystemExit("no OPENAI_API_KEY in ~/.abraham_env")
    md = B / "clients" / a.handle / "media"
    out_f = B / "clients" / a.handle / "profile" / "media_class.json"
    cache = json.loads(out_f.read_text()) if out_f.exists() else {}
    imgs = sorted(md.glob("*.jpg"))[:a.n]
    done = 0
    for p in imgs:
        rel = str(p.relative_to(B))
        c = cache.get(rel, {})
        # re-tag a clean product ref that predates the product_en field (so pick_reference can match
        # the brief's product to the right photo); skip everything already complete or non-usable.
        if "kind" in c and ("product_en" in c or not c.get("usable_as_product_reference")):
            continue
        try:
            cache[rel] = classify(p, key)
            done += 1
        except Exception as e:
            cache[rel] = {"error": str(e)[:80]}
        if done and done % 5 == 0:
            out_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
            print(f"  …{done} new classified")
    out_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    usable = [k for k, v in cache.items() if v.get("usable_as_product_reference")
              and not v.get("has_person") and not v.get("is_royal_or_public_figure")]
    persons = [k for k, v in cache.items() if v.get("has_person") or v.get("is_royal_or_public_figure")]
    print(f"✅ {len(cache)} tagged · {len(usable)} clean product references · {len(persons)} person/royal (excluded) "
          f"→ {out_f.relative_to(B)}")
    for u in usable[:6]:
        print("  ✓ ref:", u)


if __name__ == "__main__":
    main()
