#!/usr/bin/env python3
"""SEED THE JUDGE LANE v2 (June 12 — rebuilt the same night after Mohamed's own words:
"i need to see the photo the ocassion and the idea and the creitve and the resinning
behind the full post not the captions" + the cold-consult catch: v1 cards carried the
occasion as a TRUNCATED str(dict) (slot[:40]) so all 5 first verdicts were collected
BLIND and are quarantined (data/verdict_quarantine.json).

v2 card = THE FULL POST (Rule #9: he judges complete posts, never drafts):
  occasion (structured: name/beat/major) · the idea/scene · the visual plan
  (phone-shoot card — no AI photos while keys are dry, honestly labeled) · the
  reasoning (why this idea for this slot) · THEN the caption to judge.
Cards carry handle+caption+occasion for the gold wire. Attribution: the post's own
brain field (on-disk evidence). Money discipline: small batches (default 5).
"""
import argparse
import ast
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base
import queue_decision as qd

B = Path(__file__).parent.parent
# THE PIXEL GATE AT THE JUDGE-CARD SEAM (2026-06-21 — the adversarial audit's missing tooth).
# A rendered image may not reach Mohamed's judge card until the pixel modesty gate has cleared
# it (a loosened-hijab/mixed-gender/exposed-skin/real-person render the PROMPT gates can't see).
# COVERAGE (June 22): an UNGATED image (the DRAFT /static/renders/ schnell path, which has no
# render-time gate) is ALWAYS enforced here — this seam is its only pixel check (Rule #13). A
# render-time-gated MASTER image (/static/renders_v37/, render_openclaw already asserted it) is
# exercised in $0 skip-mode to avoid a double-spend, unless JUDGE_CARD_PIXEL_VISION=1 forces a
# re-check. Either way a violating pixel never becomes a judge card (Rule #8). See _gate_card_image.
_PIXEL_VISION = os.environ.get("JUDGE_CARD_PIXEL_VISION") == "1"


def _local_image_path(image_url):
    """Resolve a card's image_url (e.g. /static/renders_v37/x.jpg) to an on-disk path under
    api/static, or None if it's not a local static render we can inspect."""
    if not image_url or not isinstance(image_url, str):
        return None
    if image_url.startswith("/static/"):
        p = B / "api" / image_url.lstrip("/")
        return p if p.exists() else None
    return None


def _gate_card_image(image_url, handle):
    """Pixel-gate a card's image before it ships to the judge lane. Returns the image_url on a
    clear pass; RAISES (SystemExit) on any violation — a violating render never becomes a judge
    card (Rule #8 + Rule #13: nothing reaches Mohamed's eye unchecked).

    GATED-AT-RENDER vs UNGATED (June 22 audit hole). The MASTER path (/static/renders_v37/,
    render_openclaw) already RAN assert_image_clear at render time, so re-spending here is waste —
    we exercise the wire in $0 skip-mode (unless JUDGE_CARD_PIXEL_VISION=1 forces a re-check). But
    the DRAFT path (/static/renders/, render_image/schnell) has NO render-time gate, so THIS seam is
    the ONLY pixel check standing between a loosened-hijab/mixed-gender/exposed-skin/real-person
    schnell render and Mohamed's judge surface → it MUST enforce, regardless of the $0 default."""
    lp = _local_image_path(image_url)
    if lp is None:
        return image_url   # phone-shoot-plan card (no AI photo) — nothing to pixel-gate
    import image_modesty_gate as img_gate
    # an image is render-time-gated ONLY if it came from the master path (renders_v37); every
    # other local render (the DRAFT renders/ path, or anything new) is UNGATED → must be enforced.
    render_time_gated = isinstance(image_url, str) and image_url.startswith("/static/renders_v37/")
    if _PIXEL_VISION or not render_time_gated:
        # ENFORCED: a real gpt-4o pass is required; assert_image_clear RAISES on any violation.
        # Forced for UNGATED draft images even at the $0 default — they have no other gate, and a
        # bad pixel reaching his eye is a cultural kill (worth the ~$0.001 vision call).
        img_gate.assert_image_clear(str(lp), handle, skip_vision=False)
    else:
        # $0 seam for an ALREADY render-time-gated (renders_v37) image: exercise the wire in
        # skip-mode (no spend, no block) — the render-time hook was the enforcer.
        img_gate.check(str(lp), handle, skip_vision=True)
    return image_url


def _parse(maybe_dict):
    """posts store some fields as str(dict) — parse, never truncate."""
    if isinstance(maybe_dict, dict):
        return maybe_dict
    try:
        return ast.literal_eval(str(maybe_dict))
    except Exception:
        return {}


def pick_from_manifest(n: int) -> list:
    """MANIFEST-DRIVEN pick (June 18 — the judge lane now consumes produce_batch's COMPUTED pick
    instead of re-globbing the whole posts dir, which let OLD posts drift in). Reads
    data/batch_manifest.json, takes its posts IN ORDER, slices the first n — a DETERMINISTIC
    first-N slice of the computed manifest (Rule #12: a slice, never a hand-pick), and loads each
    card from its absolute card_path. Skips post-dates already in the queue (back-compat)."""
    mf = base() / "data/batch_manifest.json"
    man = json.loads(mf.read_text())
    qf = base() / "data/decision_queue.json"
    existing = {it["id"] for it in json.loads(qf.read_text())["items"]} if qf.exists() else set()
    picked = []
    for p in man.get("posts", [])[:n]:          # FIRST-N of the computed order — deterministic
        cp = p.get("card_path")
        if not cp or not Path(cp).exists():
            print(f"  🛑 manifest post {p.get('handle')} {p.get('date')}: card_path missing on disk — skip ({cp})")
            continue
        try:
            d = json.loads(Path(cp).read_text())
        except Exception as e:
            print(f"  🛑 manifest post {cp}: unreadable — skip ({e})")
            continue
        handle = p.get("handle") or d.get("handle", "")
        slot = _parse(d.get("slot"))
        date = slot.get("date", d.get("date", ""))
        if f"judge2_{handle}_{date}" in existing:
            continue
        picked.append((handle, d, Path(cp).name))
    return picked


def pick_posts(n: int) -> list:
    # skip post-dates already judged (their judge2_ card exists in the queue, any status)
    qf = base() / "data/decision_queue.json"
    existing = {it["id"] for it in json.loads(qf.read_text())["items"]} if qf.exists() else set()
    picked, seen_brains = [], set()
    pools = []
    # myfitness.sa LEADS the rotation (June 14): it was excluded entirely, so his judge queue
    # was 100% food (jurisha + albaik) — a direct cause of his "why everything home and food".
    # The only non-food pilot now opens every batch so the queue isn't a food monoculture.
    for handle in ("myfitness.sa", "eatjurisha", "albaik"):
        # sort by RENDER TIME (newest first), not filename: today's fixed-pipeline renders must
        # lead, or the ~160 old pre-fix __v6 posts on disk would dominate the date-sorted pick
        # and his "new batch" would be the OLD repetitive captions (June 14).
        files = sorted(glob.glob(str(base() / f"clients/{handle}/posts/*__v[56].json")),
                       key=lambda f: -Path(f).stat().st_mtime)
        pools.append((handle, files))
    i = 0
    while len(picked) < n and any(f for _, f in pools):
        handle, files = pools[i % len(pools)]
        i += 1
        while files:
            f = files.pop(0)
            try:
                d = json.loads(Path(f).read_text())
            except Exception:
                continue
            if not (d.get("captions") and d.get("brain")):
                continue
            # PRE-SHIP GATE (auto, 2026-06-14): no post reaches his judge lane without passing —
            # the cultural/occasion misses (royal family, Hajj hook) get blocked by the SYSTEM,
            # not by Mohamed's eye or by Claude pulling cards after the fact.
            try:
                import pre_ship_gate as _g
                if _g.gate(d, handle).get("block"):   # KILL (cultural) OR a learned-rejection pattern
                    continue
            except Exception as e:
                # FAIL CLOSED (Rule #13, Rule #8): if the pre-ship gate raises we CANNOT prove the
                # post is safe for his judge lane — skip it, never fall through to picked.append.
                print(f"  🛑 manifest post {Path(f).name}: pre-ship gate raised — skip ({e})")
                continue
            slot = _parse(d.get("slot"))
            date = slot.get("date", d.get("date", ""))
            if f"judge2_{handle}_{date}" in existing:
                continue
            if d["brain"] in seen_brains and len(seen_brains) < 5:
                continue
            seen_brains.add(d["brain"])
            picked.append((handle, d, Path(f).name))
            break
    return picked


def build_card(handle: str, d: dict, fname: str) -> dict:
    slot = _parse(d.get("slot"))
    idea = _parse(d.get("idea"))
    visual = _parse(d.get("visual"))
    caption = d["captions"][0]
    occ_name = slot.get("type", "?")
    # Mohamed struck «evergreen» twice («saudi doesn't have evergreen») — never print it
    # to him; the taxonomy replacement awaits his ruling, display says «daily» meanwhile
    occ_display = "daily" if "evergreen" in occ_name else occ_name
    occ_line = occ_display + (f" · beat: {slot['beat']}" if slot.get("beat") else "") \
        + (" · MAJOR day" if slot.get("major") else "")
    scene = idea.get("scene_ar") or str(d.get("idea"))[:400]
    shots = visual.get("phone_shoot_card") or []
    # THE PHOTO WIRE (June 18, Rule #6): the post's image = the card's OWN visual.image_url
    # (set by render_image.py at /static/renders/<stem>.jpg). The old wrong-key check read
    # d.get("image_url") TOP-LEVEL — a key that is never set, so the dry-keys line printed even
    # after a real render. Read it from the parsed visual, the one place it actually lives.
    img = visual.get("image_url")
    # PIXEL GATE (Rule #6 reader at the judge boundary): a rendered image must clear the modesty
    # pixel gate before it can ride on a judge card. $0 by default; enforced under JUDGE_CARD_PIXEL_VISION=1.
    img = _gate_card_image(img, handle)
    angle = slot.get("angle_theme", "")
    cid = f"judge2_{handle}_{slot.get('date', d.get('date',''))}"
    return {
        "id": cid, "title": f"{handle} · {slot.get('date', d.get('date',''))} · {occ_name}",
        "tag": "Judge", "clock": "", "priority": "normal",
        "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
        "kind": "caption_judge", "judge_lane": True, "lane": "creative",
        "handle": handle, "caption": caption, "occasion": occ_name,
        "image_url": img,                            # the portal renders this <img> above the visual text
        "why": "Approve ★4+ → gold example. Reject → opens a case on the mind's prompt file.",
        "need": "Your verdict on the FULL post below — occasion, idea, visual, then the caption.",
        "did": f"The {d['brain']} mind wrote it for this slot ({fname}).",
        # THE FULL POST — what he judges (structured, never truncated)
        "post_occasion": occ_line,
        "post_idea": f"[{handle}] " + scene[:580],   # his 01:12 note: say the client name
        "post_visual": shots[:4],
        "post_reasoning": (f"Slot angle: {angle[:200]}" if angle else "")
                          + ("" if img
                             else " · no AI photo: keys are dry — the visual is the phone-shoot plan"),
        "island_text": caption,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5)
    ap.add_argument("--from-manifest", action="store_true",
                    help="consume produce_batch's computed pick (data/batch_manifest.json) IN ORDER, "
                         "first-n slice — instead of re-globbing the posts dir (June 18, Rule #12)")
    a = ap.parse_args()
    if a.n > 20:
        raise SystemExit("law batch_max_20: judging batches are 20 cards MAX per round "
                         "(Mohamed, June 12 — money + attention discipline)")
    posts = pick_from_manifest(a.n) if getattr(a, "from_manifest", False) else pick_posts(a.n)
    for handle, d, fname in posts:
        item = build_card(handle, d, fname)
        try:
            qd.push_attributed(item, made_by=f"mind:{d['brain']}", via="scripts/seed_judge_cards.py",
                               reason=f"judge card v2 (FULL POST) — brain field of {fname}")
            print(f"  ⚖️ {item['id']} — mind:{d['brain']} · {item['post_occasion']}")
        except SystemExit as e:
            print(f"  🧊 skipped {item['id']}: {e}")


if __name__ == "__main__":
    main()
