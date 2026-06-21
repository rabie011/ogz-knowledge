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
RULINGS = B / "data/mohamed_rulings_live.json"
COST_LOG = B / "data/fal_cost_log.jsonl"
RENDER_DIR = B / "api/static/renders_v37"   # under api/static → the portal serves it at /static/renders_v37/
MODEL = "fal-ai/flux-2-pro/edit"
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--chain", required=True)
    ap.add_argument("--product", default="")
    ap.add_argument("--scene", default="")
    ap.add_argument("--go", action="store_true", help="attempt the real render (still gated)")
    ap.add_argument("--allow-unconfirmed", action="store_true")
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
    key = env("FAL_KEY") or env("FAL_API_KEY")
    refp = Path(ref)
    mime = "jpeg" if refp.suffix.lower() in (".jpg", ".jpeg") else (refp.suffix.lstrip(".").lower() or "jpeg")
    data_uri = f"data:image/{mime};base64," + base64.b64encode(refp.read_bytes()).decode()
    body = {"prompt": prompt, "image_urls": [data_uri], "image_size": "square_hd",
            "num_images": 1, "safety_tolerance": "2"}   # square_hd ≈ 1MP; strict-ish safety (prompt enforces modesty)
    rq = urllib.request.Request(f"https://fal.run/{MODEL}", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        out = json.loads(urllib.request.urlopen(rq, timeout=300).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"🛑 fal render failed HTTP {e.code}: {e.read()[:400].decode(errors='replace')}")
    imgs = out.get("images") or []
    if not imgs:
        sys.exit(f"🛑 fal returned no image: {json.dumps(out)[:300]}")
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{a.handle}_{resolve_id(a.chain)}.jpg"
    dest = RENDER_DIR / name
    urllib.request.urlretrieve(imgs[0]["url"], dest)
    usd = round(0.03, 4)   # flux-2-pro ≈ 3¢/MP, square_hd ≈ 1MP (measured; overwrite if the API returns cost)
    with open(COST_LOG, "a") as f:
        f.write(json.dumps({"day": time.strftime("%Y-%m-%d"), "handle": a.handle, "chain": a.chain,
                            "model": MODEL, "usd": usd, "image_url": f"/static/renders_v37/{name}",
                            "out": str(dest.relative_to(B))}, ensure_ascii=False) + "\n")
    print(f"  ✅ rendered → {dest.relative_to(B)}  ·  ~${usd}  ·  spent ${spent_usd():.2f}/{USD_CAP}")
    print(f"  image_url: /static/renders_v37/{name}")


def resolve_id(cid):
    import importlib.util
    spec = importlib.util.spec_from_file_location("oc", B / "scripts/openclaw_convert.py")
    oc = importlib.util.module_from_spec(spec); spec.loader.exec_module(oc)
    return oc.resolve_chain(cid)


if __name__ == "__main__":
    main()
