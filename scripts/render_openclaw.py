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
USD_CAP = 3.00                # Mohamed's first-batch law


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
            "num_images": 1, "safety_tolerance": "2"}   # strict-ish safety (prompt enforces modesty)
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
    key = env("FAL_KEY") or env("FAL_API_KEY")
    refp = Path(ref)
    mime = "jpeg" if refp.suffix.lower() in (".jpg", ".jpeg") else (refp.suffix.lstrip(".").lower() or "jpeg")
    data_uri = f"data:image/{mime};base64," + base64.b64encode(refp.read_bytes()).decode()
    # THE SEAM: one function call to the render backend (see render_backend's docstring for the swap
    # point). The model id flows from model_registry.RENDER_MODEL — the single place to bump it.
    img_url = render_backend(prompt, [data_uri], "square_hd", key=key, model=MODEL)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{a.handle}_{resolve_id(a.chain)}.jpg"
    dest = RENDER_DIR / name
    urllib.request.urlretrieve(img_url, dest)
    _composite_brand_logo(dest, a.handle)   # overlay the REAL logo (AI rendered plain)
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
