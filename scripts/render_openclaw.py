#!/usr/bin/env python3
"""P5 — the v3.7 RENDER PATH (gated). flux-2-pro/edit + reference image + the converter's
15-block prompt. This is the ALIGNED render path — unlike render_image.py (flux/schnell +
generic string), it emits the actual v3.7 prompt.

GATE-FIRST (Rule #8 refuse, don't warn). It REFUSES (exit non-zero, never spends) unless ALL
four of Mohamed's gates are clear:
  1. no_fal_photos must be FALSE in data/mohamed_rulings_live.json (his ruling to flip)
  2. a FAL key must exist in ~/.abraham_env (FAL_KEY / FAL_API_KEY)
  3. the brand+product must have a CONFIRMED reference image (identity lock) OR --allow-unconfirmed
  4. the per-batch USD cap (default $3, his first-batch law) must not be exceeded
B141 (no AI product depiction) is reconciled per-run: flux-2-pro/edit recomposes the REAL
product from its reference (identity-locked), it does not fabricate — but the gate still asks
for Mohamed's explicit ack via rulings_live.b141_reference_lock_ok.

Usage (dry by default — prints the request it WOULD send, spends nothing):
  python3 scripts/render_openclaw.py --handle alnasserjewelry --chain T08 --product "خاتم / خواتم ذهب" \\
      --scene "…"  [--go]   # --go attempts the real render (still blocked by the gates)
"""
import argparse, base64, json, os, subprocess, sys, time
import urllib.request, urllib.error
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))   # so the post-render hooks (image_modesty_gate) import cleanly
import model_registry as mr   # single source of truth for the render model + its fingerprint
RULINGS = B / "data/mohamed_rulings_live.json"
COST_LOG = B / "data/fal_cost_log.jsonl"
RENDER_DIR = B / "api/static/renders_v37"   # under api/static → the portal serves it at /static/renders_v37/
MODEL = mr.RENDER_MODEL        # was hardcoded "fal-ai/flux-2-pro/edit"; now the registry is the one place to swap it
USD_PER_IMAGE = 0.05          # flux-2-pro/edit est.; measured cost overwrites this in the log
USD_CAP = 15.00               # Mohamed June 23: "dont spend more that 15 dollars" — the 20-perfect-posts budget


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def spent_usd():
    if not COST_LOG.exists():
        return 0.0
    return sum(json.loads(l).get("usd", 0) for l in COST_LOG.read_text().splitlines() if l.strip())


def gates(go, allow_unconfirmed, ref):
    """Return (clear, reasons[]). Clear only if EVERY gate passes."""
    r = json.loads(RULINGS.read_text()) if RULINGS.exists() else {}
    reasons = []
    if r.get("no_fal_photos"):
        reasons.append("GATE1 no_fal_photos=true — Mohamed's ruling; flip it in rulings_live on his tap")
    if not (env("FAL_KEY") or env("FAL_API_KEY")):
        reasons.append("GATE2 no FAL key in ~/.abraham_env (FAL_KEY/FAL_API_KEY)")
    if not ref and not allow_unconfirmed:
        reasons.append("GATE3 no confirmed reference image — identity lock missing (--allow-unconfirmed to override)")
    if not r.get("b141_reference_lock_ok"):
        reasons.append("GATE4 B141 not reconciled — set rulings_live.b141_reference_lock_ok on Mohamed's ack")
    if spent_usd() >= USD_CAP:
        reasons.append(f"GATE5 batch cap ${USD_CAP} reached (spent ${spent_usd():.2f})")
    return (not reasons), reasons


def _composite_brand_logo(dest, handle):
    """Overlay the brand's REAL logo (clients/<h>/profile/logo.png) as a clean corner brand-bug.
    AI never renders brand text (it garbles it); the real mark is composited HERE (Mohamed June 21:
    'composite the real logo'). No-op if the brand has no logo asset yet."""
    lp = B / "clients" / handle / "profile" / "logo.png"
    if not lp.exists():
        print(f"  (no logo.png for {handle} — skipped composite; render is plain)")
        return
    from PIL import Image
    base = Image.open(dest).convert("RGBA")
    logo = Image.open(lp).convert("RGBA")
    bw, bh = base.size
    logo.thumbnail((int(bw * 0.16), int(bw * 0.16)))     # brand-bug ≈ 16% of width
    pad = int(bw * 0.04)
    base.alpha_composite(logo, (bw - logo.width - pad, bh - logo.height - pad))   # bottom-right
    base.convert("RGB").save(dest, quality=92)
    print(f"  🏷  composited real logo (brand-bug, bottom-right) ← {lp.relative_to(B)}")


def _composite_pepsi_can_label(dest, handle):
    """Overlay the real Pepsi wordmark on the plain-red rendered can (كومبو بيك combo shots).
    AI brand-text suppression forces all can surfaces plain; this composites the real label.
    Detection: scans the right 60% of the image for the largest red-dominant region (the can).
    No-op if clients/<handle>/profile/pepsi_label.png doesn't exist."""
    lp = B / "clients" / handle / "profile" / "pepsi_label.png"
    if not lp.exists():
        print(f"  (no pepsi_label.png for {handle} — Pepsi composite skipped; "
              f"add clients/{handle}/profile/pepsi_label.png to unlock brand_system 5/5)")
        return
    from PIL import Image, ImageChops

    base = Image.open(dest).convert("RGB")
    bw, bh = base.size

    # Detect the can in the right 60% (combo layout places it there)
    SCALE = 8
    right_x = bw * 2 // 5
    crop = base.crop((right_x, 0, bw, bh)).resize(
        ((bw - right_x) // SCALE, bh // SCALE), Image.BOX)
    r_ch, g_ch, b_ch = crop.split()
    # Red-dominant: R>140, G<90, B<90 — matches a plain-red can body
    red_mask = r_ch.point(lambda x: 255 if x > 140 else 0)
    not_green = g_ch.point(lambda x: 255 if x < 90 else 0)
    not_blue = b_ch.point(lambda x: 255 if x < 90 else 0)
    can_mask = ImageChops.multiply(ImageChops.multiply(red_mask, not_green), not_blue)

    bbox = can_mask.getbbox()
    if not bbox:
        print(f"  (no red can region found in right portion — Pepsi composite skipped)")
        return

    # Scale bbox back to full-res coords (add the crop offset)
    cx1 = bbox[0] * SCALE + right_x
    cy1 = bbox[1] * SCALE
    cx2 = bbox[2] * SCALE + right_x
    cy2 = bbox[3] * SCALE
    can_w, can_h = cx2 - cx1, cy2 - cy1

    # Sanity: a soda can is taller than wide; reject noise / background blobs
    if can_w < 20 or can_h < 30 or can_h > bh * 0.65 or can_w / max(1, can_h) > 2.0:
        print(f"  (red region {can_w}×{can_h} geometry doesn't match a can — Pepsi composite skipped)")
        return

    label = Image.open(lp).convert("RGBA")
    target_w = max(10, int(can_w * 0.88))
    target_h = int(label.height * target_w / label.width)
    label = label.resize((target_w, target_h), Image.LANCZOS)

    px = cx1 + (can_w - target_w) // 2
    py = cy1 + (can_h - target_h) // 2
    rgba = base.convert("RGBA")
    rgba.alpha_composite(label, (max(0, px), max(0, py)))
    rgba.convert("RGB").save(dest, quality=92)
    print(f"  🥤 Pepsi label composited on can ({can_w}×{can_h} at {cx1},{cy1}) ← {lp.relative_to(B)}")


# ─── THE RENDERER SEAM (the documented swap point) ───────────────────────────────────────────
# This is the ONE function the rest of the pipeline talks to. The moat is "the prompt doesn't
# change" — so when fal deprecates/re-prices flux-2-pro, or we move to a different backend, the
# swap is THIS function body, NOT a rewrite: keep the signature, return a hosted image URL.
#
#   TO SWAP THE RENDER BACKEND: change model_registry.RENDER_MODEL (+ bump RENDER_REGISTERED),
#   then re-point the urlopen below at the new backend's endpoint/auth. Nothing else moves.
#   (Deliberately NOT a plugin/factory — three clients, one pilot. One function, one docstring.)
#
# Contract: render_backend(prompt, image_urls, size) -> hosted image URL (str). Raises SystemExit
# on a backend error (Rule #8: refuse, don't return a broken URL). The caller fingerprints the
# result with mr.fingerprint_render(MODEL) so a later model change is detectable.
def render_backend(prompt: str, image_urls: list, size: str = "square_hd",
                   *, key: str, model: str = MODEL, timeout: int = 300) -> str:
    """Call the active render backend (currently fal flux-2-pro/edit) and return a hosted image URL.

    prompt     : the v3.7 prompt (already brand-text-suppressed by the caller)
    image_urls : reference image(s) as data-URIs or URLs (the identity lock)
    size       : fal image_size token (square_hd ≈ 1MP)
    key        : the backend API key (caller resolves it from ~/.abraham_env)
    model      : the backend model id (defaults to the registry's RENDER_MODEL)
    """
    body = {"prompt": prompt, "image_urls": image_urls, "image_size": size,
            "num_images": 1, "safety_tolerance": "2",
            "image_prompt_strength": 0.92}  # high reference-adherence: keeps reference bun/texture vs training bias
    rq = urllib.request.Request(f"https://fal.run/{model}", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        out = json.loads(urllib.request.urlopen(rq, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"🛑 render backend failed HTTP {e.code}: {e.read()[:400].decode(errors='replace')}")
    imgs = out.get("images") or []
    if not imgs:
        sys.exit(f"🛑 render backend returned no image: {json.dumps(out)[:300]}")
    return imgs[0]["url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--chain", required=True)
    ap.add_argument("--product", default="")
    ap.add_argument("--scene", default="")
    ap.add_argument("--ref", default="", help="force a specific reference image path, overriding "
                    "pick_reference — for product↔reference matching tests")
    ap.add_argument("--go", action="store_true", help="attempt the real render (still gated)")
    ap.add_argument("--allow-unconfirmed", action="store_true")
    ap.add_argument("--skip-image-gate", action="store_true",
                    help="$0 — skip the post-render gpt-4o pixel modesty gate (NOT clearance)")
    a = ap.parse_args()

    # 1) build the v3.7 prompt via the converter (no spend)
    cmd = [sys.executable, str(B / "scripts/openclaw_convert.py"), "--handle", a.handle,
           "--chain", a.chain, "--scene", a.scene, "--save"]
    if a.product:
        cmd += ["--product", a.product]
    conv = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(conv.stdout)
    if conv.returncode != 0:
        sys.exit(f"converter failed:\n{conv.stderr}")
    sample = json.loads((B / "data/openclaw_v37/samples" / f"{a.handle}_{resolve_id(a.chain)}.json").read_text())
    prompt, ref = sample["prompt"], sample.get("reference_image")
    if a.ref:
        ref = a.ref   # forced reference (product↔reference match test)
        print(f"  ⚙ reference FORCED → {ref}")

    # 2) GATES
    clear, reasons = gates(a.go, a.allow_unconfirmed, ref)
    print(f"\n  RENDER GATES for {a.handle}/{a.chain}: {'✅ ALL CLEAR' if clear else '🛑 BLOCKED'}")
    for r in reasons:
        print(f"    🛑 {r}")
    print(f"  model: {MODEL} · ref: {ref or '⚠ none'} · prompt {len(prompt)} chars · "
          f"spent ${spent_usd():.2f}/{USD_CAP}")

    if not a.go:
        print("  (dry run — no spend. add --go once gates clear.)")
        return
    if not clear:
        sys.exit("🛑 REFUSED: gates not clear — zero spend. (Rule #8 refuse, don't warn.)")

    # 3) real render — flux-2-pro/edit with the brand reference as a base64 data-URI (no separate
    # fal-storage upload needed; image_urls accepts data-URIs). Gated above (Rule #8: we only reach
    # here with --go AND every gate clear). Cost-logged; the batch cap already checked in gates().
    print("  → all gates clear; rendering via flux-2-pro/edit …")
    # BRAND-TEXT SUPPRESSION (June 21, Mohamed: composite the real logo): AI image models garble
    # brand wordmarks (post #1 rendered "اطيل/ALBAAK" not "البيك"). Force PLAIN packaging — zero text
    # of any kind — and composite the brand's REAL logo (clients/<h>/profile/logo.png) after.
    prompt = prompt + ("\n\n[BRAND TEXT — CRITICAL] Render ALL packaging, cups, bags, wrappers and "
        "products PLAIN: solid brand colours only, with ABSOLUTELY NO text, NO letters, NO words, NO "
        "wordmark, NO logo, NO numbers on ANY surface — smooth unbranded surfaces. (The real brand "
        "logo is composited in afterward.)")
    # PRODUCT-TRUTH ASSEMBLY + NEGATIVE PROMPT (June 23). The consult panel (GPT+Gemini) + RABIE:
    # the positive identity_dna fixed the SAUCE but flux still rendered a DECONSTRUCTED platter (loose
    # tenders + an empty/open bun) instead of the ASSEMBLED product. This last-mile, forceful block
    # locks the geometry per the product's real format and FORBIDS the generic-QSR tells RABIE named.
    _fmt = ""  # pre-init so the post-render Pepsi composite can check it after the try/except
    try:
        _d = json.loads((B / "clients" / a.handle / "profile" / "product_truth.json").read_text())
        _pt = _d.get("products", _d).get(a.product, {})  # handle both flat (albaik) and nested (jurisha)
        _fmt = (_pt.get("format") or "").lower()
        _neg = []
        if _fmt in ("burger", "sandwich"):
            _neg.append("This is ONE single fully-ASSEMBLED hero sandwich: the crispy broasted chicken "
                "fillet(s) are STACKED INSIDE the CLOSED pale bun — BUN IS PERFECTLY SMOOTH with "
                "ZERO seeds, ZERO sesame, ZERO toppings on the bun surface — exactly as in the "
                "reference photo. White garlic ثومية sauce visible at the edge. ABSOLUTELY FORBIDDEN: "
                "loose chicken tenders/strips/fingers scattered on a board; an EMPTY, OPEN or "
                "deconstructed bun; ANY seeds or sesame on the bun; a sesame burger bun; crinkle-cut "
                "fries; any generic Texas-Chicken/Hardee's/KFC/McDonald's/QSR platter.")
        elif _fmt in ("wrap", "roll"):
            _neg.append("This is ONE rolled flatbread WRAP (صاج/tortilla), broasted chicken + white garlic "
                "ثومية visible in the cut cross-section, held in hand or cut on a board — there is NO BUN. "
                "ABSOLUTELY FORBIDDEN: any burger/sesame bun, loose tenders, a deconstructed platter.")
        elif _fmt in ("strips", "tenders", "box", "combo"):
            if _fmt == "combo":
                _neg.append("A warm wooden board with: 5 BROASTED crispy golden chicken-breast strips, "
                    "a SOFT PALE bun served ALONGSIDE (NOT assembled as a sandwich — the bun sits next to "
                    "the strips, they are NOT combined into a sandwich), golden CURLY-CUT curly fries in a "
                    "wooden bowl (CURLY fries — spiral-shaped, NOT straight-cut, NOT crinkle-cut), "
                    "a small dip cup of CREAM-WHITE garlic sauce (ثومية) clearly visible, "
                    "and a red Pepsi can. The white garlic sauce (ثومية) must be visible. "
                    "ABSOLUTELY FORBIDDEN: an assembled burger/sandwich, straight-cut or crinkle-cut fries, "
                    "potato chips instead of fries, sesame seeds on the bun, missing sauce dip.")
            else:
                _neg.append("A pile of broasted crispy chicken strips on a warm wooden board with cream-WHITE "
                    "garlic ثومية sauce cups — NO bun. FORBIDDEN: a burger/sandwich, any bun, a generic platter.")
        elif _fmt == "bake":
            sig = _pt.get("signature", "")
            _neg.append(f"This is an OVEN-BAKED dish served in the brand's vessel — a bubbly golden-baked top "
                f"over creamy layered pasta, béchamel, and/or meat. {sig} The surface is GOLDEN and SET, "
                "NOT raw, NOT soupy, NOT fried, NOT a burger. ABSOLUTELY FORBIDDEN: any fried chicken, crispy "
                "crust, burger bun, or generic QSR food — this is a baked home-style dish.")
        elif _fmt in ("bowl", "dish", "porridge", "rice", "tray", "flatbread"):
            identity = _pt.get("identity_dna", "")
            sig = _pt.get("signature", "")
            tex = _pt.get("texture", "")
            comps = _pt.get("components", [])
            comp_line = "; ".join(comps) if comps else ""
            blob = (identity + " " + sig + " " + comp_line).lower()
            # forbid the generic-jureisha tells that bleed in from OTHER menu items, UNLESS this
            # product's own identity/components actually call for them (root-fix: سليق kept
            # rendering with red-pepper salsa it doesn't have — the jareesh look bleeding across).
            bleed = []
            if not any(w in blob for w in ("red pepper", "salsa", "roasted-pepper", "كشنة", "محمّر", "محمر")):
                bleed.append("red roasted-pepper salsa, diced red peppers, red كشنة")
            if not any(w in blob for w in ("chili", "chilli", "شطة", "شطه", "حار")):
                bleed.append("red chili paste, whole red chilies, شطة")
            if not any(w in blob for w in ("crisp", "fried", "broast", "مقلي", "مقرمش")):
                bleed.append("any fried/crispy/breaded crust or fried chicken")
            bleed_clause = (" THIS specific dish has NONE of the following (they belong to OTHER "
                            "menu items, do NOT add them): " + "; ".join(bleed) + "."
                            ) if bleed else ""
            # قرصان / tharid geometry: flux's prior renders a WHOLE intact flatbread on top; the
            # real dish is bread TORN into ragged pieces and SOAKED/submerged in broth UNDER the
            # stew. Force it when the identity is a soaked-bread dish.
            bread_clause = ""
            if any(w in blob for w in ("قرصان", "tharid", "ثريد", "soaked", "broth-soaked", "flatbread-in-broth")):
                bread_clause = (" CRITICAL GEOMETRY: the thin flatbread is TORN into ragged irregular "
                    "pieces and SUBMERGED, fully soaked and softened in the broth UNDERNEATH the stewed "
                    "meat and vegetables — soggy, glistening, broth-logged. ABSOLUTELY NOT a whole intact "
                    "round flatbread sitting dry on top; NOT a folded tortilla; the bread is wet, torn, layered, half-hidden in the stew.")
            _neg.append(
                f"This is a REAL cooked Saudi/Najdi dish. Render EXACTLY this dish and ONLY its own "
                f"listed components — add NOTHING from other menu items. EXACT PRODUCT IDENTITY: {identity} "
                f"SIGNATURE: {sig} TEXTURE: {tex} COMPONENTS (the ONLY things on/in this dish): {comp_line}."
                + bleed_clause + bread_clause +
                " Honest thick moist matte cooked-grain surface. ABSOLUTELY FORBIDDEN: a burger/sandwich/bun, "
                "plastic-uniform CGI food."
            )
        if _pt.get("signature_sauce"):
            comps = " ".join(_pt.get("components", []))
            has_cocktail = "cocktail" in comps.lower()
            if has_cocktail:
                _neg.append(f"Primary sauce is {_pt['signature_sauce']} (cream-WHITE garlic ثومية) with a "
                    "SMALL visible streak of orange cocktail sauce — both must appear.")
            else:
                _neg.append(f"The ONLY prominent sauce is {_pt['signature_sauce']} (cream-WHITE garlic ثومية) "
                    "— ABSOLUTELY NO orange, red or pink cocktail sauce visible anywhere; white garlic sauce ONLY "
                    "(it is Albaik's #1 recognition signature).")
        if _neg:
            prompt = prompt + "\n\n[PRODUCT TRUTH — CRITICAL, match the reference's assembled form exactly]\n" + " ".join(_neg)
            print(f"  🍔 product-truth assembly+negative block applied (format={_fmt or '?'})")
    except Exception as _e:
        print(f"  (no product_truth block: {type(_e).__name__})")
    # THE LEARNING READER (Rule #6 consumer of rabie_judge's verdict ledger): inject every past
    # correction RABIE flagged on THIS product so the system does NOT repeat a mistake the eye
    # already caught. This is what makes the loop LEARN — kills feed forward into the next prompt.
    try:
        import rabie_judge as rj
        _lessons = rj.lessons_for(a.handle, a.product)
        if _lessons:
            prompt = prompt + ("\n\n[LEARNED — past RABIE corrections on this product; DO NOT repeat these]\n"
                               + " ".join(f"- {l}" for l in _lessons[:8]))
            print(f"  🧠 injected {len(_lessons[:8])} learned correction(s) from RABIE's verdict ledger")
    except Exception as _e:
        print(f"  (no learned-corrections block: {type(_e).__name__})")
    key = env("FAL_KEY") or env("FAL_API_KEY")
    refp = Path(ref)
    mime = "jpeg" if refp.suffix.lower() in (".jpg", ".jpeg") else (refp.suffix.lstrip(".").lower() or "jpeg")
    data_uri = f"data:image/{mime};base64," + base64.b64encode(refp.read_bytes()).decode()
    # THE SEAM: one function call to the render backend (see render_backend's docstring for the swap
    # point). The model id flows from model_registry.RENDER_MODEL — the single place to bump it.
    img_url = render_backend(prompt, [data_uri], "square_hd", key=key, model=MODEL)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    # distinct file per PRODUCT (June 23): the 20-run renders many products on the same chain — a
    # bare handle_chain name made each overwrite the last. Slug the product into the name.
    _pslug = ((a.product or "x").strip().replace(" ", "_").replace("/", "-"))[:24] or "x"
    name = f"{a.handle}_{_pslug}_{resolve_id(a.chain)}.jpg"
    dest = RENDER_DIR / name
    urllib.request.urlretrieve(img_url, dest)
    _composite_brand_logo(dest, a.handle)   # overlay the REAL logo (AI rendered plain)
    if _fmt == "combo":
        _composite_pepsi_can_label(dest, a.handle)  # fix plain red can → real Pepsi label
    # ── PIXEL MODESTY GATE (2026-06-21, the audit's missing tooth) — the prompt gates can't see
    # the rendered pixels; this one can. AFTER the image is saved, BEFORE it can become a judge
    # card, a gpt-4o vision pass refuses a loosened-hijab / mixed-gender / exposed-skin / real-
    # person render against the client's CONFIRMED organs (Rule #6 reader; Rule #8 refuse). It
    # RAISES (SystemExit non-zero) on a violation — a bad pixel never reaches Mohamed's eye. The
    # spend just happened on the render; the ~$0.001 vision check is the cheap insurance on it.
    # --skip-image-gate keeps a $0 path (e.g. a deliberate no-vision test) but is NOT clearance.
    import image_modesty_gate as img_gate
    iv = img_gate.assert_image_clear(str(dest), a.handle, skip_vision=a.skip_image_gate)
    print(f"  🧕 image modesty gate: {iv.verdict.upper()} "
          f"(modest={iv.modest} mixed_gender={iv.mixed_gender} skin={iv.exposed_skin} "
          f"real_person={iv.identifiable_real_person_or_royal})")
    usd = round(0.03, 4)   # flux-2-pro ≈ 3¢/MP, square_hd ≈ 1MP (measured; overwrite if the API returns cost)
    # FINGERPRINT (I2): stamp the render with the model id+version+date so check_model_drift.py can
    # detect a silent model swap behind the live renders (consult's time-bomb made detectable).
    log_line = {"day": time.strftime("%Y-%m-%d"), "handle": a.handle, "chain": a.chain,
                "model": MODEL, "usd": usd, "image_url": f"/static/renders_v37/{name}",
                "out": str(dest.relative_to(B))}
    log_line.update(mr.fingerprint_render(MODEL))   # adds {"model_fingerprint": {...}}
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(log_line, ensure_ascii=False) + "\n")
    print(f"  ✅ rendered → {dest.relative_to(B)}  ·  ~${usd}  ·  spent ${spent_usd():.2f}/{USD_CAP}")
    print(f"  image_url: /static/renders_v37/{name}")


def resolve_id(cid):
    import importlib.util
    spec = importlib.util.spec_from_file_location("oc", B / "scripts/openclaw_convert.py")
    oc = importlib.util.module_from_spec(spec); spec.loader.exec_module(oc)
    return oc.resolve_chain(cid)


if __name__ == "__main__":
    main()
