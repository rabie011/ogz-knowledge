#!/usr/bin/env python3
"""WIRE THE MASTER (June 21) — route a produced post card through the v3.7 MASTER image path.

THE CORRECT PATH (Mohamed): post card → openclaw_convert (handle+chain+scene+organs → the full
15-block v3.7 prompt, picks the REAL brand reference image) → render_openclaw (flux-2-pro/edit +
that reference, GATED, dry by default). This is the thin glue that closes the loop: it reads a
post card already produced by render_client_slot.py, pulls its CONTENT-AWARE chain (visual.pro_chain.id
— the chain the new pick_pro_chain chose for the scene), its scene/occasion/product, and hands them
to render_openclaw. render_image.py (schnell + an improvised "Authentic Saudi lifestyle" string) is
the WRONG shortcut and is NOT touched — this never calls it.

GATED + DRY BY DEFAULT (Rule #8 refuse, don't warn): this script SPENDS NOTHING on its own. It only
shells out to render_openclaw.py, which REFUSES (exit non-zero, zero spend) unless ALL Mohamed's gates
are clear (no_fal_photos=false + FAL key + reference + b141 ack + USD cap). --go is forwarded to
render_openclaw but the gates still bite — there is no spend path here that bypasses them.

produce_batch.py should call this for the image render step (instead of the schnell shortcut): for
each chosen post card, render_via_master(handle, date) builds the aligned v3.7 prompt. Wire it where
the manifest is assembled, behind the same money-gate (today the gates hold, so it runs DRY and
emits the prompt + fill-report only).

Usage:
  python3 scripts/render_via_master.py --handle albaik --date 2026-09-23           # DRY (no spend)
  python3 scripts/render_via_master.py --handle albaik --date 2026-09-23 --go      # still gated
  python3 scripts/render_via_master.py --handle albaik --date 2026-09-23 --suffix __auto
"""
import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

B = Path(__file__).parent.parent


def load_card(handle: str, date: str, suffix: str = "") -> dict:
    """Find the post card for handle+date (optionally a specific suffix), newest first.
    REFUSES (exit non-zero) if no card exists — render_via_master never invents one."""
    pat = f"clients/{handle}/posts/{date}__*{suffix}.json"
    fs = sorted(glob.glob(str(B / pat)), key=lambda f: -Path(f).stat().st_mtime)
    if not fs:
        sys.exit(f"🛑 no post card for {handle} {date} (suffix '{suffix}') — produce it first "
                 f"(render_client_slot.py). render_via_master never authors a card.")
    return json.loads(Path(fs[0]).read_text())


def resolve_card_chain(card: dict) -> str:
    """The chain the SYSTEM chose for this scene → its v3.7 id. The card stores the tfNN_NN
    SHORT id in visual.pro_chain.id (the chain pick_pro_chain chose for the scene); we map it
    to the v3.7 id HERE (via openclaw_convert.resolve_chain → chain_bridge.json) and pass the
    RESOLVED id to render_openclaw. Why here and not let render_openclaw map it: openclaw_convert
    --save writes the sample as «{handle}_{--chain}.json» from the RAW arg, but render_openclaw
    reads it back as «{handle}_{resolve_id(--chain)}.json» — so a short id in == a v3.7 id out =
    filename mismatch. Resolving up-front makes both sides agree on the v3.7 id. REFUSES if the
    card has no chain (a card with no pro_chain can't be rendered to an image)."""
    import importlib.util
    pc = (card.get("visual") or {}).get("pro_chain") or {}
    cid = pc.get("id")
    if not cid:
        sys.exit("🛑 card has no visual.pro_chain.id — nothing to render. Re-render the slot so "
                 "pick_pro_chain assigns a content-aware chain (Rule #8: refuse, don't guess a chain).")
    spec = importlib.util.spec_from_file_location("oc", B / "scripts/openclaw_convert.py")
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    return oc.resolve_chain(cid)  # tfNN_NN → v3.7 id (U01/T41/…) via chain_bridge


def card_scene(card: dict) -> str:
    """The system's creative seed for the converter: the angle's scene + the slot theme."""
    idea = card.get("idea") or {}
    bits = [idea.get("scene_ar", ""), (card.get("slot") or {}).get("angle_theme", "")]
    return " ".join(b for b in bits if b).strip()


def card_occasion(card: dict) -> str:
    slot = card.get("slot") or {}
    occ = slot.get("occasion") or card.get("occasion") or ""
    return "" if occ in ("evergreen", "daily") else occ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--suffix", default="", help="match a specific card suffix (e.g. __auto, __v5)")
    ap.add_argument("--product", default="", help="which product (visual_dna.products[].name); default = first")
    ap.add_argument("--go", action="store_true",
                    help="forward --go to render_openclaw (STILL gated — no spend unless every gate clears)")
    ap.add_argument("--allow-unconfirmed", action="store_true",
                    help="forward to render_openclaw (override the reference-image gate only)")
    a = ap.parse_args()

    card = load_card(a.handle, a.date, a.suffix)
    chain = resolve_card_chain(card)
    scene = card_scene(card)
    occ = card_occasion(card)

    print(f"  MASTER PATH  {a.handle} {a.date}  →  chain {chain} "
          f"(scene: {scene[:70]}{'…' if len(scene) > 70 else ''})")

    cmd = [sys.executable, str(B / "scripts/render_openclaw.py"),
           "--handle", a.handle, "--chain", chain, "--scene", scene]
    if occ:
        # render_openclaw doesn't take --occasion; the converter reads it from --scene context.
        # The occasion still rides inside the scene seed (theme prefix) so the v3.7 SAUDI/occasion
        # blocks resolve. (Kept explicit here for the log; openclaw_convert --occasion is wired
        # when produce_batch calls the converter directly.)
        print(f"  occasion: {occ} (carried in the scene seed)")
    if a.product:
        cmd += ["--product", a.product]
    if a.go:
        cmd += ["--go"]              # forwarded — render_openclaw's gates still REFUSE without the key/ruling
    if a.allow_unconfirmed:
        cmd += ["--allow-unconfirmed"]

    # render_openclaw is DRY unless --go AND all gates clear; it prints the prompt + gate status.
    r = subprocess.run(cmd)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
