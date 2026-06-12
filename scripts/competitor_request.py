#!/usr/bin/env python3
"""THE سويلي زي ذا PATH (FLANK-04, June 11) — the owner forwards a competitor post.
Law: we answer the REQUEST without copying the rival. The competitor's post gives
us the ANGLE-CLASS (the idea); everything rendered comes from the CLIENT's own
truth pack and voice. Two code fences:
1. shingle-overlap kill — any 4-word run shared with the rival's caption = dead
2. the rival's product/brand words may never appear in our copy
Every request is an append-only event (competitor_reference) in the client ledger.

Usage: python3 scripts/competitor_request.py --handle albaik --competitor herfyfsc \
         --caption-file /tmp/herfy_caption.txt
"""
import argparse, datetime, json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from render_client_slot import load_client, render_captions, shot_card, gpt

TODAY = __import__("datetime").date.today().isoformat()


def shingles(text: str, n=4) -> set:
    words = re.findall(r"[\wء-ي]+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def translate_angle(c: dict, comp_handle: str, comp_caption: str) -> dict:
    """Extract the rival's IDEA-CLASS, re-ground it in the client's truth. One call,
    generation-side (not judging). The rival's wording never crosses this boundary."""
    products = [x["name"] for x in c["truth"]["product_candidates"]][:6] + c["truth"]["recurring_caption_terms"][:4]
    out = gpt([
        {"role": "system", "content":
         "A business owner forwarded a COMPETITOR's post and said 'make me one like this'. Your job: "
         "name the competitor post's ANGLE-CLASS abstractly (the human moment/mechanism it uses — e.g. "
         "'the relaxed evening sitting gets better with our treat'), then re-create that CLASS as a NEW "
         "concrete scene (WHO+WHEN+gesture) for OUR brand using ONLY our real products. NEVER reuse the "
         "competitor's wording, product names, or hashtags. "
         'Return JSON: {"angle_class": "...", "scene_ar": "...", "why_it_lands": "..."}'},
        {"role": "user", "content":
         f"COMPETITOR POST ({comp_handle}):\n{comp_caption[:400]}\n\n"
         f"OUR BRAND: {c['brand_ar']} (bio: {c['bio'][:120]})\nOUR REAL PRODUCTS: {products}"}], temp=0.8, max_tok=400)
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--competitor", required=True)
    ap.add_argument("--caption-file", required=True)
    a = ap.parse_args()
    comp_caption = open(a.caption_file).read()
    c = load_client(a.handle)

    # the event, before anything renders (memory law: the request itself is a fact)
    ev = {"ts": TODAY, "type": "competitor_reference", "competitor": a.competitor,
          "competitor_caption": comp_caption[:300], "stamp": "PROVISIONAL — pending Mohamed"}
    evf = BASE / "clients" / a.handle / "events" / "ledger.jsonl"
    with open(evf, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    angle = translate_angle(c, a.competitor, comp_caption)
    slot = {"date": TODAY, "type": "competitor_reference", "occasion": None,
            "angle_theme": angle["angle_class"], "beat": "request"}
    captions = render_captions(c, slot, angle)

    # fence 1: shingle overlap with the rival
    comp_sh = shingles(comp_caption)
    # fence 2: rival's distinctive tokens (brand + product words, Arabic + Latin) banned in our copy
    rival_tokens = {w for w in re.findall(r"[\wء-ي]{4,}", comp_caption.lower())} - \
                   {w for w in re.findall(r"[\wء-ي]{4,}", (c.get("corpus_text") or "").lower())}
    survivors = []
    for cap in captions:
        if shingles(cap) & comp_sh:
            print(f"  ✂️ shingle-overlap killed: {cap[:60]}…", file=sys.stderr)
            continue
        hit = next((t for t in re.findall(r"[\wء-ي]{4,}", cap.lower()) if t in rival_tokens), None)
        if hit:
            print(f"  ✂️ rival-token killed [{hit}]: {cap[:60]}…", file=sys.stderr)
            continue
        survivors.append(cap)

    card = {"handle": a.handle, "date": TODAY, "slot": slot,
            "request": {"competitor": a.competitor, "their_caption": comp_caption[:200]},
            "idea": angle, "captions": survivors,
            "visual": {"phone_shoot_card": shot_card(c, angle)},
            "provenance": {"source": "competitor_reference", "rendered": TODAY,
                            "stamp": "PROVISIONAL — pending Mohamed",
                            "law": "angle-class translated; zero wording/product overlap (2 code fences)"}}
    out = BASE / "clients" / a.handle / "posts" / f"{TODAY}__like_{a.competitor}.json"
    out.write_text(json.dumps(card, ensure_ascii=False, indent=2))
    print(f"✓ سويلي زي ذا → {out.relative_to(BASE)}")
    print(f"  THEIR angle-class: {angle['angle_class'][:90]}")
    print(f"  OUR scene: {angle['scene_ar'][:100]}")
    for i, cap in enumerate(survivors, 1):
        print(f"  ✍️ {i}. {cap[:110]}")


if __name__ == "__main__":
    main()
