#!/usr/bin/env python3
"""OpenClaw v3.7 CONVERTER — turn what the system says into a spec-matching prompt.

Mohamed's question (2026-06-13): «how we gonna take what the system says and convert
it to a prompt? it MUST match this file.» This is the answer: a deterministic converter
that takes a creative seed (the system's idea/scene + chosen chain) and a brand's organs,
and emits the FULL OpenClaw v3.7 prompt — the 15-block image prompt (or 5-block native
video), every {placeholder} filled, conditional blocks resolved, char-capped.

THREE fill sources, every one tagged honestly (Rule #9 + SELF-AUDIT — no value is
claimed confirmed unless an organ on disk holds it):
  • organ        — read from the brand's organ files on disk (a real, confirmed fact)
  • derived      — agent-side logic the v3.7 canon itself prescribes (companion table,
                   color-field principle, material-by-substrate, scale-by-product). A
                   CANDIDATE — visible, reviewable, becomes a client CONFIRM question.
  • client_needed— brand-specific truth no logic can invent (exact hex, label text,
                   the deep identity). Rendered as «CLIENT: …» so the gap is loud.

The converter NEVER spends. It writes the prompt + a fill-report; rendering is a
separate, gated step (render_openclaw.py) behind Mohamed's go + the FAL key.

Usage:
  python3 scripts/openclaw_convert.py --handle albaik --chain G03 \\
      --scene "بوكس البيك على صينية مجلس، لحظة عزيمة بعد العشا" \\
      [--occasion ramadan] [--intent grow] [--text "وجبة العيلة"]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

B = Path(__file__).parent.parent
V37 = B / "data/openclaw_v37"
PLACE = re.compile(r"\{([a-z][a-z0-9_.]+)\}")
BLOCK = re.compile(r"^\[([^\]]+)\]")
TS = "2026-06-13"

# ── sector → agent-side derivation (the v3.7 canon's own logic, Section B) ──────────
# companion table (Section B "Companion-element derivation logic", verbatim intent)
COMPANION = {
    "coffee": "serving cup, dallah/pot, beans, dates, cardamom, rising steam",
    "tea":    "serving cup, pot, dates, cardamom, steam",
    "cold_beverage": "ice, condensation beads, citrus, frosted glass, mint",
    "fragrance": "the box, scent-matched botanicals, a vanity surface",
    "oud": "the box, oud chips, brass mabkhara, a vanity surface",
    "sweets": "cocoa dusting, the unwrapped piece, nuts",
    "skincare": "water droplets, the hero ingredient, a folded towel",
    "packaged_food": "the prepared dish, a raw hero ingredient, a serving utensil",
    "fried_chicken": "the prepared piece on a plate, dipping sauce ramekin, fresh-cut lemon",
    "traditional_najdi": "the dish in its real serving vessel, a serving spoon, dates or laban on the side",
    "jewelry": "black velvet pad, silk drape, a single gift box — one hero only",
    "apparel": "a folded companion garment, a styling surface — one hero only",
    "default": "one restrained, category-true companion object",
}
# material-truth by substrate (Section B {product.material_texture})
MATERIAL = {
    "fried_chicken": "crisp golden-brown crust with honest oil sheen and visible craggy texture; tender steam-moist interior where broken; true fried-food surface, never plastic-uniform",
    "traditional_najdi": "true cooked-grain substrate — cracked wheat or rice, honest moist matte surface with a soft mounded form, real steam where hot; served in ceramic or a foil tray with its own true finish; NEVER a fried crust, never plastic-uniform",
    "packaged_food": "real food surface — honest moisture, natural colour variation, true texture; packaging film stays pliable with genuine creases, never rigid",
    "coffee": "ceramic/paper cup with true matte or glaze; liquid with real crema and surface tension; honest steam",
    "jewelry": "polished 18–22k gold with true warm specular; faceted gemstone refraction and internal fire; honest metal micro-scratches, never CGI-perfect",
    "fragrance": "real glass refraction and weight, true cap metal, honest liquid level and meniscus",
    "apparel": "true fabric weave and drape, honest thread and seam, natural fold shadows",
    "default": "honest material truth for the real substrate — genuine micro-reflectance, true texture, no plastic uniformity",
}
# scale anchor by product (Section B {product.dimensions})
DIMENSIONS = {
    "fried_chicken": "a meal box ≈20–25cm wide; a chicken piece ≈8–10cm, so a piece is ~⅓ the box width — honest serving scale",
    "traditional_najdi": "a single-serve bowl/cup ≈9–11cm, or a family foil tray ≈22–26cm; scale-anchored to a serving spoon beside it — honest portion scale",
    "jewelry": "a ring ≈2cm, a necklace pendant ≈3–4cm; shown at true intimate jewelry scale against a hand or pad, never enlarged for drama",
    "fragrance": "a bottle ≈9–12cm tall; a hand spans ~⅔ its height — true shelf scale",
    "coffee": "a cup ≈9–11cm tall; the product reads in honest relation to it",
    "default": "real-world product size with a clear scale-anchor object in frame — never distorted larger for emphasis",
}
# brand-derived color field (principle, not a borrowed accent) — sector seed; client confirms exact
COLOR_FIELD = {
    "f_and_b": "warm appetite-forward field drawn from the brand's own palette (reds/golds/cream) — saturated, never a borrowed reference accent",
    "fried_chicken": "warm brand red and golden-brown against cream — the brand's own appetite palette, saturated for pop",
    "traditional_najdi": "warm earthen Najdi tones from the brand's own palette (signature red, cream, warm browns) — saturated, never borrowed",
    "jewelry": "deep jewel field (oxblood, midnight, forest) or warm gold — the brand's own luxury palette against which gold reads",
    "fragrance": "soft warm neutral or the brand's signature accent — gold/amber for oud, pastel for fresh",
    "beauty": "soft brand-owned pastel or clean editorial neutral",
    "retail": "the brand's signature field colour, saturated for editorial pop",
    "default": "a saturated field built only from the brand's own palette — exclude any colour the brand does not own",
}
PALETTE_PRIMARY = {
    "fried_chicken": "brand red", "f_and_b": "warm brand red/orange",
    "traditional_najdi": "the brand's signature warm/earthen tone",
    "jewelry": "warm gold", "fragrance": "brand signature accent",
    "beauty": "soft brand pastel", "retail": "brand signature colour",
    "default": "the brand's primary colour",
}
CAPTURE = {  # default capture character by chain family kind
    "studio": "clean_studio", "dark": "clean_studio with theatrical lift",
    "natural": "natural_daylight_documentary", "lifestyle": "warm_lifestyle_film",
    "default": "clean_studio",
}


def _sectorize(brand):
    """Map the brand to a derivation key (more specific than year_map sector)."""
    sec = (brand.get("sector") or "").lower()
    name = (brand.get("name") or "") + " " + " ".join(brand.get("products", []))
    # traditional Najdi/Gulf dishes FIRST — else a single "إضافة دجاج" option mislabels a
    # porridge brand as fried chicken (the verify caught this: جريش got a fried crust). Rule #9.
    TRAD = ["جريش", "جريشة", "قرصان", "مرقوق", "مطازيز", "كبسة", "مندي", "سليق",
            "مظبي", "حنيذ", "مفطح", "كابلي", "تمن", "مراصيع", "مصابيب", "هريس", "مطبق"]
    if any(w in name for w in TRAD):
        return "traditional_najdi", "f_and_b"
    if any(w in name for w in ["دجاج", "بروست", "broast", "chicken", "البيك", "كرسبي", "فيليه"]):
        return "fried_chicken", "f_and_b"
    if any(w in name for w in ["ذهب", "مجوهرات", "خاتم", "عقد", "jewel", "gold", "الماس"]):
        return "jewelry", "jewelry"
    if any(w in name for w in ["قهوة", "coffee", "كوفي", "اسبريسو"]):
        return "coffee", "f_and_b"
    if any(w in name for w in ["عطر", "عود", "perfume", "fragrance", "oud"]):
        return "oud" if "عود" in name or "oud" in name else "fragrance", "fragrance"
    if "f_and_b" in sec or "food" in sec:
        return "packaged_food", "f_and_b"
    return "default", (sec or "default")


def load_brand(handle):
    p = B / "clients" / handle / "profile"
    def j(f, d=None):
        fp = p / f
        return json.loads(fp.read_text()) if fp.exists() else (d or {})
    fp = j("fingerprint.json")
    tp = j("truth_pack.json")
    ym = j("../year_map.json")
    products = [c.get("name") for c in tp.get("product_candidates", []) if c.get("name")]
    names = {"albaik": "البيك", "eatjurisha": "جريش الرياض", "alnasserjewelry": "مجوهرات الناصر"}
    return {
        "handle": handle,
        "name": names.get(handle, handle),
        "sector": ym.get("sector") or fp.get("sector", ""),
        "products": products,
        "dialect": fp.get("l2_voice", {}).get("dialect", ""),
        "tone": fp.get("l2_voice", {}).get("tone", ""),
        "l3_visual": fp.get("l3_visual", {}) or {},
        "red_lines": j("red_lines.json").get("lines", []),
        "visual_dna": j("visual_dna.json"),   # v3.7 organ — may not exist yet
    }


def Field(value, src):
    return {"value": value, "src": src}


_STATUS_SRC = {"GREEN": "organ", "YELLOW": "derived", "RED": "client_needed"}


def _sf(field_obj, fallback_val, fallback_src="derived"):
    """Read a v3.7 statusField {value,status} from visual_dna.json → Field(value, src).
    GREEN→organ · YELLOW→derived · RED→client_needed. Falls back to the canon's derivation
    when the organ has no usable value (so the converter still produces a full prompt)."""
    if isinstance(field_obj, dict):
        val, st = field_obj.get("value"), field_obj.get("status")
        # B186d: Mohamed's confirmed free-text answer (h_v37_visual) is authoritative client
        # truth — append it to the candidate value (or use it alone where we had none) and mark
        # the source 'organ'. Dormant until his tap lands client_confirmed.
        cc = field_obj.get("client_confirmed") or {}
        ca = (cc.get("answer") or "").strip() if isinstance(cc, dict) else ""
        if val not in (None, "", []):
            return Field(f"{val} — client-confirmed: {ca}" if ca else val,
                         "organ" if ca else _STATUS_SRC.get(st, "derived"))
        if ca:
            return Field(ca, "organ")
        if st == "RED":
            return Field(fallback_val, "client_needed")
    return Field(fallback_val, fallback_src)


def derive_visual_dna(brand, chain, product_name=None):
    """Fill the v3.7 placeholders — visual_dna.json (the v3.7 organ) FIRST, the canon's
    derivation logic as the fallback. Status in the organ maps to the fill-source tag."""
    pk, sector = _sectorize(brand)
    vd = brand.get("visual_dna") or {}
    vb = vd.get("brand") or {}
    vpal = vb.get("palette") or {}
    prods = vd.get("products") or []
    prod = (next((p for p in prods if p.get("name") == product_name), None) if product_name else None)
    prod = prod or (prods[0] if prods else {})

    fam = (chain.get("family") or "").lower()
    kind = ("dark" if any(w in fam for w in ["spotlight", "dark"]) else
            "natural" if any(w in fam for w in ["natural", "environment", "lifestyle"]) else
            "lifestyle" if "lifestyle" in fam else "studio")

    products = brand.get("products") or []
    hero = prod.get("name") or (products[0] if products else brand["name"])

    return {
        "brand.name": Field(brand["name"], "organ"),
        "brand.sector": Field(sector, "organ" if brand.get("sector") else "derived"),
        "brand.palette.primary": _sf(vpal.get("primary"), PALETTE_PRIMARY.get(pk, PALETTE_PRIMARY["default"])),
        "brand.palette.background_tone": _sf(vpal.get("background_tone"), "clean brand-owned neutral (not clinical white unless the brand owns it)"),
        "brand.color_field_palette": _sf(vb.get("color_field_palette"), COLOR_FIELD.get(pk) or COLOR_FIELD.get(sector, COLOR_FIELD["default"])),
        "brand.aesthetic.capture_character": _sf(vb.get("capture_character"), CAPTURE.get(kind, CAPTURE["default"])),
        "brand.anti_attributes": _sf(vb.get("anti_attributes"), _anti(brand)),
        "brand.modesty_register": _sf(vb.get("modesty_register"), "STRICT (Saudi default — modest, no skin, no mixed-gender intimacy)"),
        "brand.tone_register": _sf(vb.get("tone_register"), brand.get("tone") or "—"),
        "brand.quality_tier": _sf(vb.get("quality_tier"), chain.get("quality_tier") or "universal"),
        "brand.price_position": _sf(vb.get("price_position"), "mid-market"),
        "product.name": Field(hero, "organ" if (prod or products) else "client_needed"),
        "product.identity_dna": _sf(prod.get("identity_dna"), f"«CLIENT: the locked identity of {hero} — the reference image carries it; confirm wordmark, signature colour, form»"),
        "product.silhouette_description": _sf(prod.get("silhouette_description"), f"the recognizable form of {hero}"),
        "product.material_finish": _sf(prod.get("material_finish"), MATERIAL.get(pk, MATERIAL["default"]).split(";")[0]),
        "product.material_texture": _sf(prod.get("material_texture"), MATERIAL.get(pk, MATERIAL["default"])),
        "product.dimensions": _sf(prod.get("dimensions"), DIMENSIONS.get(pk, DIMENSIONS["default"])),
        "product.companion_elements": _sf(prod.get("companion_elements"), COMPANION.get(pk, COMPANION["default"])),
        "product.label_text_arabic": _sf(prod.get("label_text_arabic"), f"«CLIENT: exact Arabic wordmark of {brand['name']}»"),
        "product.label_text_latin": _sf(prod.get("label_text_latin"), "«CLIENT: exact Latin wordmark, if any»"),
    }


def _anti(brand):
    rl = brand.get("red_lines") or []
    base = "no cartoon/illustration/stylized rendering, no oversaturation, no plastic CGI uniformity, no borrowed reference colours, no readable text on neighbouring objects"
    def _txt(x):
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            return x.get("line") or x.get("text") or x.get("rule") or x.get("value") or ""
        return str(x)
    lines = [t for t in (_txt(x) for x in rl[:3]) if t]
    if lines:
        base += " · brand red lines: " + "؛ ".join(lines)
    # sector-specific hard exclusion (GPT cross-check catch): a soft cooked dish must
    # explicitly forbid fried/crispy tropes, not merely omit them
    pk = _sectorize(brand)[0]
    if pk == "traditional_najdi":
        base += " · this is a soft cooked dish — NO fried or crispy crust, no breading, no deep-fried texture"
    return base


def saudi_fields(brand, occasion):
    return {
        "saudi.scene_context": Field("authentic contemporary Saudi setting — true materials, never generic-Arabian", "derived"),
        "saudi.apparel_context": Field("modest Saudi dress where people appear (thobe/abaya), right-hand interaction (CS-08)", "derived"),
        "saudi.material_context": Field("real Saudi-context materials — brass dallah, sadu textile, palm, true regional surfaces", "derived"),
        "saudi.color_palette_adjust": Field("warmer gold/sand/amber tones", "derived"),
        "saudi.occasion_overlay": Field(occasion or "", "organ" if occasion else "n/a"),
    }


def brief_fields(occasion, intent, platform, text):
    f = {
        "brief.occasion": Field(occasion or "", "organ" if occasion else "n/a"),
        "brief.intent": Field(intent or "grow", "organ"),
        "brief.platform": Field(platform or "instagram", "organ"),
    }
    if text:
        f["brief.text_request.copy"] = Field(text, "organ")
        f["brief.text_request.style"] = Field("brand-clean Arabic, high legibility", "derived")
        f["brief.text_request.zone"] = Field("lower third, integrated as intentional design", "derived")
    return f


def fill(chain, ph, scene, has_text, saudi_relevant=True):
    """Fill the chain template; resolve conditional blocks; weave the system's scene."""
    tmpl = chain["video_prompt_template"] if chain["native_video"] else chain["image_prompt_template"]
    lines = tmpl.split("\n")
    out, dropped, cur_keep = [], [], True
    for ln in lines:
        bm = BLOCK.match(ln)
        if bm:
            head = bm.group(1).upper()
            if "TEXT OVERLAY" in head and not has_text:
                cur_keep = False; dropped.append("TEXT OVERLAY (no text_request)"); continue
            if "SAUDI ADAPTATION" in head and not saudi_relevant:
                cur_keep = False; dropped.append("SAUDI ADAPTATION (brand not Saudi-relevant)"); continue
            cur_keep = True
            out.append(ln)
            # weave the system's creative seed INTO the SCENE block (the canon's seed slot)
            if "SCENE" in head and scene:
                out.append(f"Creative seed (from the system): {scene}")
            continue
        if cur_keep:
            out.append(ln)
    text = "\n".join(out)
    # substitute placeholders
    miss = []
    def sub(m):
        key = m.group(1)
        if key in ph:
            return str(ph[key]["value"])
        miss.append(key)
        return m.group(0)
    text = PLACE.sub(sub, text)
    # cleanup: empty conditional lead-ins left by an absent occasion (verify caught "For : …"),
    # and any doubled spaces from a dropped placeholder
    text = re.sub(r"\bFor\s*:\s*", "", text)
    text = re.sub(r"\bduring\s*:\s*", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text, dropped, sorted(set(miss))


def lint(text, chain, miss):
    cap = 8000 if not chain["native_video"] else 2500
    blocks = [BLOCK.match(l).group(1) for l in text.split("\n") if BLOCK.match(l)]
    issues = []
    if len(text) > cap:
        issues.append(f"OVER CHAR CAP: {len(text)}/{cap}")
    if miss:
        issues.append(f"UNRESOLVED placeholders (not in fill map): {miss}")
    leftover = PLACE.findall(text)
    if leftover:
        issues.append(f"UNFILLED {{}} remain: {sorted(set(leftover))}")
    # hard-rule presence (canon §1.8): must keep brand-constraints + output + variance
    need = ["BRAND LOCK", "OUTPUT", "CREATIVE VARIANCE"] if not chain["native_video"] else ["OUTPUT"]
    for n in need:
        if not any(n in b.upper() for b in blocks):
            issues.append(f"MISSING required block: [{n}]")
    return {"chars": len(text), "cap": cap, "n_blocks": len(blocks), "blocks": blocks, "issues": issues}


def resolve_chain(cid):
    """Accept a v3.7 id (U01/T08/…) → return it. Accept a legacy v3.2 id (tf01_01) or a
    family (tf01) → map via chain_bridge.json to the family's default v3.7 chain. P2 bridge."""
    cid = (cid or "").strip()
    if (V37 / "chains" / f"{cid}.json").exists():
        return cid
    bf = V37 / "chain_bridge.json"
    if bf.exists():
        fam = cid.lower().split("_")[0]            # tf01_01 → tf01
        chains = json.loads(bf.read_text()).get("by_family", {}).get(fam, [])
        if chains:
            return chains[0]
    raise SystemExit(f"unknown chain '{cid}' — not a v3.7 id and no bridge match")


def pick_reference(handle, product="", scene=""):
    """Pick the flux-edit REFERENCE — a clean PRODUCT shot whose PRODUCT MATCHES the post's product.
    NEVER a person/royal portrait (the edit model anchors identity on it — a royal ref rendered a man
    for a woman scene; a red line). June 23 root-fix: the old code returned clean[0] (first alphabetic)
    REGARDLESS of the post's product, so a Crispy-Beek brief rendered on a chicken-strips reference →
    wrong product entirely. Now matched via the vision product tags (classify_media.py product_en /
    product_keywords). If NOTHING matches the brief's product, that's a real GAP (the brand has no
    clean reference for that item) — FLAG it (Rule #8), don't paper over it with the wrong product."""
    md = B / "clients" / handle / "media"
    cf = B / "clients" / handle / "profile" / "media_class.json"
    q = f"{product} {scene}".lower()
    if cf.exists():
        try:
            cls = json.loads(cf.read_text())
            clean = [(k, v) for k, v in cls.items()
                     if isinstance(v, dict) and v.get("usable_as_product_reference")
                     and not v.get("has_person") and not v.get("is_royal_or_public_figure")
                     and (B / k).exists()]
            if clean:
                def score(v):
                    kws = [t.strip().lower() for t in
                           (v.get("product_keywords", "") + "," + v.get("product_en", "")).split(",")]
                    return sum(1 for kw in kws if len(kw) >= 3 and kw in q)
                best, best_v = sorted(clean, key=lambda kv: -score(kv[1]))[0]
                if product and score(best_v) > 0:
                    print(f"  🎯 reference matched product '{product}' → {Path(best).name} "
                          f"({best_v.get('product_en','')})", flush=True)
                    return best
                food = [k for k, v in clean if v.get("kind") == "product_food"]
                pick = sorted(food)[0] if food else sorted(k for k, _ in clean)[0]
                print(f"  ⚠ GAP: no clean reference matches product '{product}' — the brand has no "
                      f"photo of it. Using {Path(pick).name} as a stand-in (NOT faithful). "
                      f"Fix = add a real '{product}' product photo.", flush=True)
                return pick
        except Exception:
            pass
    imgs = sorted(md.glob("*.jpg")) + sorted(md.glob("*.png")) if md.exists() else []
    if imgs:
        print("  ⚠ no media_class.json clean-product reference — run classify_media.py "
              f"(falling back to {imgs[0].name}; may be a person/royal — unsafe)", flush=True)
        return str(imgs[0].relative_to(B))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--chain", required=True)
    ap.add_argument("--product", default="", help="which product (matches visual_dna.products[].name); default = first")
    ap.add_argument("--scene", default="", help="the system's creative seed (idea/scene)")
    ap.add_argument("--occasion", default="")
    ap.add_argument("--intent", default="grow")
    ap.add_argument("--platform", default="instagram")
    ap.add_argument("--text", default="", help="brief.text_request.copy if a text overlay is wanted")
    ap.add_argument("--save", action="store_true", help="write to data/openclaw_v37/samples/")
    a = ap.parse_args()

    chain = json.loads((V37 / "chains" / f"{resolve_chain(a.chain)}.json").read_text())
    brand = load_brand(a.handle)
    ph = {}
    ph.update(derive_visual_dna(brand, chain, a.product or None))
    ph.update(saudi_fields(brand, a.occasion))
    ph.update(brief_fields(a.occasion, a.intent, a.platform, a.text))

    text, dropped, miss = fill(chain, ph, a.scene, bool(a.text))
    rep = lint(text, chain, miss)
    ref = pick_reference(a.handle, a.product, a.scene)

    # fill-report: how each used placeholder was sourced
    used = sorted(set(chain["_stats"]["placeholders"]))
    by_src = {"organ": [], "derived": [], "client_needed": [], "n/a": []}
    for k in used:
        by_src[ph.get(k, {}).get("src", "n/a")].append(k)

    print(f"\n{'='*78}\n  CHAIN {chain['chain_id']} · {chain['title']}  →  {brand['name']} ({a.handle})")
    print(f"  model: {chain['image_model'].split('(')[0].strip()}  |  ref image: {ref or '⚠ none found'}")
    print(f"{'='*78}\n")
    print(text)
    print(f"\n{'─'*78}")
    print(f"  LINT: {rep['chars']}/{rep['cap']} chars · {rep['n_blocks']} blocks · "
          f"{'✅ clean' if not rep['issues'] else '❌ ' + ' ; '.join(rep['issues'])}")
    if dropped:
        print(f"  conditional blocks dropped: {dropped}")
    print(f"  FILL SOURCES:")
    print(f"    ✅ organ (confirmed on disk):  {by_src['organ'] or '—'}")
    print(f"    🟡 derived (candidate, canon logic): {by_src['derived'] or '—'}")
    print(f"    🔴 client_needed (RED — confirm Q): {by_src['client_needed'] or '—'}")

    if a.save:
        out = V37 / "samples"
        out.mkdir(exist_ok=True)
        fn = out / f"{a.handle}_{a.chain}.json"
        fn.write_text(json.dumps({
            "handle": a.handle, "chain": a.chain, "scene": a.scene,
            "occasion": a.occasion, "intent": a.intent,
            "model": chain["image_model"], "reference_image": ref,
            "prompt": text, "lint": rep,
            "fill_sources": by_src, "generated": TS,
        }, ensure_ascii=False, indent=2))
        print(f"  saved → {fn.relative_to(B)}")


if __name__ == "__main__":
    main()
