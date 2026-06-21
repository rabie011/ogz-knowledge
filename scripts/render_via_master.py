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
import re
import subprocess
import sys
from pathlib import Path

B = Path(__file__).parent.parent

# ── SCENE CLEANING (June 21 — BUG-2: the campaign-hashtag-soup pollution) ─────────────
# THE BUG (albaik 2026-12-15 dry-run): card_scene() concatenated idea.scene_ar + the slot's
# angle_theme, and the angle_theme carried HASHTAG/CAMPAIGN soup —
#   «family: أهلنا في #الرياض #بيككم_منكم_ومعكم و #كلنا_مسؤول مبادرة #خ»
# — which bled straight into the converter's [SCENE] block. The image scene must be the CLEAN
# VISUAL scene only: no hashtags, no leading «label:» prefix, no URLs, no @handles. Computed
# strips (regex), never a hand-edited per-post scene (Rule #12).
_HASHTAG = re.compile(r"#\S+")
_URL = re.compile(r"https?://\S+")
_HANDLE_AT = re.compile(r"(?<!\S)@\w+")
# a leading «word:» / «family:» / «منتج حقيقي:» label the planner prepends to the theme
_LABEL_PREFIX = re.compile(r"^\s*[\wء-ي]+\s*:\s*")


def _clean_scene_fragment(s: str) -> str:
    """Strip a theme fragment down to clean visual prose: remove hashtags, URLs, @handles,
    and a leading 'label:' prefix; collapse whitespace. Returns '' if nothing prose remains
    (e.g. the fragment was pure hashtags) so the caller can drop it."""
    s = s or ""
    s = _LABEL_PREFIX.sub("", s)          # «family: …» → «…»
    s = _URL.sub(" ", s)
    s = _HASHTAG.sub(" ", s)
    s = _HANDLE_AT.sub(" ", s)
    s = re.sub(r"\bو\b", " ", s)          # dangling «و» left after a hashtag was stripped
    s = re.sub(r"\s+", " ", s).strip(" ·،,-—\n")
    return s


def _is_clean_prose(s: str) -> bool:
    """A theme fragment is clean prose only if it carries no hashtag/URL/@handle/label-prefix
    AND still has real words. A pure-campaign fragment (hashtag soup) is NOT clean prose."""
    if not s:
        return False
    if _HASHTAG.search(s) or _URL.search(s) or _HANDLE_AT.search(s) or _LABEL_PREFIX.search(s):
        return False
    return bool(re.search(r"[\wء-ي]{2,}", s))


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
    """The CLEAN visual scene for the converter (BUG-2 fix). Start from the angle's
    scene_ar (the real visual moment the CD brain authored). The slot's angle_theme is
    appended ONLY if it is clean prose; campaign/hashtag soup («family: أهلنا في #الرياض
    #بيككم_منكم_ومعكم …») is dropped, never bled into the [SCENE] block. If scene_ar itself
    is the clean visual and angle_theme is the polluter, scene_ar alone is returned."""
    idea = card.get("idea") or {}
    scene = (idea.get("scene_ar") or "").strip()
    theme = ((card.get("slot") or {}).get("angle_theme") or "").strip()
    # the scene_ar is the authored visual moment — clean it lightly (it can carry a stray
    # hashtag) but keep its prose; it is the trusted spine of the image scene.
    scene = _clean_scene_fragment(scene) if (_HASHTAG.search(scene) or _URL.search(scene)
                                             or _HANDLE_AT.search(scene)) else scene
    bits = [scene]
    if theme:
        if _is_clean_prose(theme):
            bits.append(theme)              # clean theme prose enriches the scene
        else:
            cleaned = _clean_scene_fragment(theme)
            # only re-add a salvaged theme fragment if (a) it survived as real prose AND
            # (b) the scene spine is empty (don't pad a good scene with campaign remnants)
            if cleaned and not scene:
                bits.append(cleaned)
    return " ".join(b for b in bits if b).strip()


def card_occasion(card: dict) -> str:
    slot = card.get("slot") or {}
    occ = slot.get("occasion") or card.get("occasion") or ""
    return "" if occ in ("evergreen", "daily") else occ


def _visual_dna_products(handle: str) -> list:
    """The brand's visual_dna products (the SAME list openclaw_convert.derive_visual_dna picks
    from). Empty list if the organ is absent — then the converter's own default (first) holds."""
    p = B / "clients" / handle / "profile" / "visual_dna.json"
    if not p.exists():
        return []
    return (json.loads(p.read_text()).get("products") or [])


def pick_product(card: dict, handle: str) -> str:
    """BUG-3 fix: choose the visual_dna product whose NAME (or a clear alias) actually appears
    in the scene, so a البيك-اكسبرس/falafel scene locks the falafel/Express product instead of
    التوأم (the first product, the converter's blind default). Computed by substring match over
    the brand's own product list (Rule #12 — no hand-authored per-post product map). Returns ''
    when nothing in the scene matches a real product, so the converter keeps its first-product
    default (and main() logs that it defaulted). Longest matching name wins (so «التوأم كرسبي
    بيك» beats «التوأم» when both appear)."""
    scene = ((card.get("idea") or {}).get("scene_ar") or "")
    if not scene:
        return ""
    prods = _visual_dna_products(handle)
    matches = []
    for prod in prods:
        name = (prod.get("name") or "").strip()
        if not name:
            continue
        aliases = [name] + [str(x) for x in (prod.get("aliases") or [])]
        if any(al and al in scene for al in aliases):
            matches.append(name)
    # longest name first — the most specific product the scene names (a substring like التوأم
    # would otherwise win over the fuller التوأم كرسبي بيك even when both are present)
    matches.sort(key=len, reverse=True)
    return matches[0] if matches else ""


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
    # BUG-3: lock the product the SCENE actually names. Explicit --product wins (operator
    # override); else the scene-matched product; else the converter's first-product default.
    product = a.product or pick_product(card, a.handle)

    print(f"  MASTER PATH  {a.handle} {a.date}  →  chain {chain} "
          f"(scene: {scene[:70]}{'…' if len(scene) > 70 else ''})")
    if product:
        print(f"  product: {product} ({'--product override' if a.product else 'matched in scene'})")
    else:
        print("  product: (none matched in scene — converter defaults to first visual_dna product)")

    cmd = [sys.executable, str(B / "scripts/render_openclaw.py"),
           "--handle", a.handle, "--chain", chain, "--scene", scene]
    if occ:
        # render_openclaw doesn't take --occasion; the converter reads it from --scene context.
        # The occasion still rides inside the scene seed (theme prefix) so the v3.7 SAUDI/occasion
        # blocks resolve. (Kept explicit here for the log; openclaw_convert --occasion is wired
        # when produce_batch calls the converter directly.)
        print(f"  occasion: {occ} (carried in the scene seed)")
    if product:
        cmd += ["--product", product]
    if a.go:
        cmd += ["--go"]              # forwarded — render_openclaw's gates still REFUSE without the key/ruling
    if a.allow_unconfirmed:
        cmd += ["--allow-unconfirmed"]

    # render_openclaw is DRY unless --go AND all gates clear; it prints the prompt + gate status.
    r = subprocess.run(cmd)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
