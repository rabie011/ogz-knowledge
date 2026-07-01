#!/usr/bin/env python3
"""RENDER A POST IMAGE — cheap, chain-prompted (June 12, Mohamed's laws).
"The LLM will change, the prompt will not": the image prompt is built from the
94-CHAIN LIBRARY (Ahmed's durable prompts) + the post's concrete scene — never
improvised. Model = fal flux/schnell (~$0.003/image, 4 steps). Every render is
cost-logged; the budget guard refuses past the batch cap.

Usage: python3 scripts/render_image.py --card clients/albaik/posts/X.json
       python3 scripts/render_image.py --batch /tmp/batch20.txt   # file of card paths
"""
import argparse, json, os, re, sys, time, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
import model_registry as mr   # single source of truth for the DRAFT render model + its fingerprint

RENDER_DIR = BASE / "api/static/renders"
COST_LOG = BASE / "data/image_cost_log.jsonl"
COST_PER_IMAGE = 0.003          # flux/schnell on fal
BATCH_CAP = 25                  # Mohamed's law: ~20/batch, hard stop at 25
MODEL = mr.RENDER_MODEL_DRAFT   # was hardcoded "fal-ai/flux/schnell"; the registry is the one place to swap it


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def spent_this_batch() -> int:
    if not COST_LOG.exists():
        return 0
    today = time.strftime("%Y-%m-%d")
    return sum(1 for l in COST_LOG.read_text().strip().split("\n")
               if l.strip() and json.loads(l).get("day") == today)


def _load_cultural_overrides(handle: str) -> dict:
    """Read the client's cultural_overrides organ — the READER for B145's render constraints
    (Rule #6: a red-line written with no consumer is a lie that looks like safety)."""
    f = BASE / "clients" / handle / "profile/cultural_overrides.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            return {}
    return {}


def cultural_constraint_clause(ov: dict) -> str:
    """B145 — map the client's cultural red-line organ → HARD render-prompt constraint strings
    appended pre-fal.ai. The organ's own law (cultural_overrides._law): 'absent field = strictest
    governs'. So a missing value is read as the MOST conservative option — the renderer never
    relaxes a constraint the client never relaxed. (Replaces the old generic 'no faces unless
    scene demands', which silently PERMITTED faces — a leak for a face_visibility:never brand.)"""
    parts = []
    face = str(ov.get("face_visibility") or "never").lower()
    if face in ("never", "faceless"):        # "faceless" = the client-confirmed strict form (myfitness.sa)
        parts.append("no human faces, no recognizable people")
    elif face in ("limited", "partial", "incidental"):
        parts.append("faces only incidental and out of focus, never the subject")
    # face in ("allowed", "yes", "ok") → no face constraint (client explicitly relaxed)
    mg = str(ov.get("mixed_gender_scenes") or "none").lower()
    if mg in ("none", "never", "separate", "segregated"):
        parts.append("no mixed-gender scenes")
    elif mg in ("family-only-mixing", "family-only", "family_only"):
        parts.append("no unrelated mixed-gender interaction")
    mod = str(ov.get("modesty_dress") or "conservative").lower()
    if mod == "conservative":
        parts.append("conservative modest dress, no exposed skin")
    return ("CULTURAL CONSTRAINTS: " + "; ".join(parts) + ".") if parts else ""


def chain_image_prompt(card: dict, overrides: dict | None = None) -> str:
    """The durable prompt: chain's visual language + the post's concrete scene + the client's
    cultural constraints (B145). overrides defaults to {} → strictest (per the organ law)."""
    chain_ref = (card.get("visual") or {}).get("pro_chain") or {}
    chain_block = ""
    cid = chain_ref.get("id")
    if cid:
        idx = json.loads((BASE / "02_what_to_build/INDEX.json").read_text())
        chains = idx if isinstance(idx, list) else idx.get("chains", [])
        ch = next((c for c in chains if c.get("chain_id_short") == cid), None)
        if ch:
            f = BASE / "02_what_to_build" / ch.get("family", "") / f"{ch.get('chain_id','')}.json"
            if f.exists():
                cd = json.loads(f.read_text())
                ip = cd.get("image_prompt") or {}
                # the chain's style blocks are the durable language
                chain_block = " ".join(str(ip.get(k, "")) for k in
                                        ("style", "lighting", "composition", "camera", "mood") if ip.get(k))[:600]
    scene = (card.get("idea") or {}).get("scene_ar", "")
    shots = (card.get("visual") or {}).get("phone_shoot_card") or []
    cultural = cultural_constraint_clause(overrides if overrides is not None else {})
    return (f"Authentic Saudi lifestyle photograph. Scene: {scene[:300]}. "
            f"Visual details: {' '.join(shots)[:300]}. "
            + (f"Style: {chain_block}. " if chain_block else "")
            + "Natural light, real textures, no text overlay, photorealistic, "
              "shot on phone aesthetic. "
            + cultural)


# B141 (Mohamed's case_by_case ruling, code-enforced): AI may never FAKE the
# client's product — a rendered burger that isn't their burger is a lie a client
# screenshots. Product-depicting scenes = real shoot only; everything else renders
# but carries ai_generated for the judge to see.
PRODUCT_VISUAL_AR = ["صحن", "وجبة", "برجر", "بروست", "ساندوتش", "سندويش", "أكلة",
                      "طبق", "عبوة", "منتج", "مكمل", "بروتين", "قارورة", "علبة",
                      "close-up of the product", "product shot", "food close"]
_JUNK = re.compile(r"حساب|account|snapchat|@|^على$|^في$", re.I)


def product_imagery_hit(card: dict, card_path: str) -> str | None:
    hay = ((card.get("idea") or {}).get("scene_ar", "") + " "
           + " ".join((card.get("visual") or {}).get("phone_shoot_card") or []))
    for kw in PRODUCT_VISUAL_AR:
        if kw in hay:
            return kw
    handle = Path(card_path).resolve().parent.parent.name
    tpf = BASE / "clients" / handle / "profile/truth_pack.json"
    if tpf.exists():
        for x in json.loads(tpf.read_text()).get("product_candidates", []):
            n = (x.get("name") or "").strip()
            if len(n) >= 3 and not _JUNK.search(n) and n in hay:
                return n
    return None


def render(card_path: str) -> str | None:
    # MOHAMED'S LIVE RULING (fal_key_go=no_photos, 2026-06-12 14:59): NO fal image
    # spend until he says otherwise. This gate was MISSING — the ruling had zero
    # consumers (zoom-out catch 2026-06-13). The script REFUSES, never warns.
    import sys as _sys
    from pathlib import Path as _P
    _rl = _P(__file__).parent.parent / "data/mohamed_rulings_live.json"
    if _rl.exists():
        _r = json.loads(_rl.read_text())
        if _r.get("no_fal_photos"):
            _sys.exit("🛑 REFUSED: Mohamed's live ruling no_fal_photos=true "
                      "(fal_key_go=no_photos, 2026-06-12) — zero image spend until his go. "
                      "Flip data/mohamed_rulings_live.json ONLY on his tap.")
    key = env("FAL_KEY") or env("FAL_API_KEY")
    if not key:
        print("NO FAL KEY — staged only (image_prompt saved to card)")
        key = None
    card = json.loads(open(card_path).read())
    handle = Path(card_path).resolve().parent.parent.name
    prompt = chain_image_prompt(card, _load_cultural_overrides(handle))
    card.setdefault("visual", {})["image_prompt"] = prompt
    hit = product_imagery_hit(card, card_path)
    if hit:
        card["visual"]["ai_imagery"] = {"blocked": True,
                                          "reason": f"product depiction «{hit}» — real shoot only (B141)"}
        Path(card_path).write_text(json.dumps(card, ensure_ascii=False, indent=2))
        print(f"  🚫 AI product imagery BLOCKED («{hit}») — shoot-card stays the path")
        return None
    if key:
        if spent_this_batch() >= BATCH_CAP:
            sys.exit(f"BUDGET GUARD: {BATCH_CAP} images today already — Mohamed's batch law")
        body = {"prompt": prompt, "image_size": "square_hd", "num_inference_steps": 4,
                "num_images": 1, "enable_safety_checker": True}
        rq = urllib.request.Request(f"https://fal.run/{MODEL}", data=json.dumps(body).encode(),
                                    headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(rq, timeout=120).read())
        url = out["images"][0]["url"]
        RENDER_DIR.mkdir(parents=True, exist_ok=True)
        name = Path(card_path).stem + ".jpg"
        urllib.request.urlretrieve(url, RENDER_DIR / name)
        card["visual"]["image_url"] = f"/static/renders/{name}"
        card["visual"]["ai_generated"] = True
        # FINGERPRINT (mirror render_openclaw's I2 stamp): stamp the DRAFT render with the model
        # id+version+date so check_model_drift.py can detect a silent schnell swap behind the live
        # draft renders. image_url is logged too so the drift reader counts this as a live render.
        log_line = {"day": time.strftime("%Y-%m-%d"), "card": Path(card_path).name,
                    "model": MODEL, "usd": COST_PER_IMAGE,
                    "image_url": f"/static/renders/{name}"}
        log_line.update(mr.fingerprint_render_draft(MODEL))   # adds {"model_fingerprint": {...}}
        with open(COST_LOG, "a") as f:
            f.write(json.dumps(log_line, ensure_ascii=False) + "\n")
    Path(card_path).write_text(json.dumps(card, ensure_ascii=False, indent=2))
    return card["visual"].get("image_url")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card")
    ap.add_argument("--batch", help="file with one card path per line")
    a = ap.parse_args()
    paths = [a.card] if a.card else [l.strip() for l in open(a.batch) if l.strip()]
    done = 0
    for p in paths:
        u = render(p)
        done += bool(u)
        print(f"  {'🖼' if u else '📝'} {Path(p).name}{' → ' + u if u else ' (prompt staged)'}")
        time.sleep(1)
    total = done * COST_PER_IMAGE
    print(f"\n{done} images rendered · cost ≈ ${total:.3f}")


if __name__ == "__main__":
    main()
