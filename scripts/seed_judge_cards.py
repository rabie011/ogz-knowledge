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
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base
import queue_decision as qd


def _parse(maybe_dict):
    """posts store some fields as str(dict) — parse, never truncate."""
    if isinstance(maybe_dict, dict):
        return maybe_dict
    try:
        return ast.literal_eval(str(maybe_dict))
    except Exception:
        return {}


def pick_posts(n: int) -> list:
    picked, seen_brains = [], set()
    pools = []
    for handle in ("eatjurisha", "albaik"):
        files = sorted(glob.glob(str(base() / f"clients/{handle}/posts/*__v[56].json")), reverse=True)
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
    occ_line = occ_name + (f" · beat: {slot['beat']}" if slot.get("beat") else "") \
        + (" · MAJOR day" if slot.get("major") else "")
    scene = idea.get("scene_ar") or str(d.get("idea"))[:400]
    shots = visual.get("phone_shoot_card") or []
    angle = slot.get("angle_theme", "")
    cid = f"judge2_{handle}_{slot.get('date', d.get('date',''))}"
    return {
        "id": cid, "title": f"{handle} · {slot.get('date', d.get('date',''))} · {occ_name}",
        "tag": "Judge", "clock": "", "priority": "normal",
        "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
        "kind": "caption_judge", "judge_lane": True, "lane": "creative",
        "handle": handle, "caption": caption, "occasion": occ_name,
        "why": "Approve ★4+ → gold example. Reject → opens a case on the mind's prompt file.",
        "need": "Your verdict on the FULL post below — occasion, idea, visual, then the caption.",
        "did": f"The {d['brain']} mind wrote it for this slot ({fname}).",
        # THE FULL POST — what he judges (structured, never truncated)
        "post_occasion": occ_line,
        "post_idea": scene[:600],
        "post_visual": shots[:4],
        "post_reasoning": (f"Slot angle: {angle[:200]}" if angle else "")
                          + (" · no AI photo: keys are dry — the visual is the phone-shoot plan"
                             if not d.get("image_url") else ""),
        "island_text": caption,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5)
    a = ap.parse_args()
    if a.n > 20:
        raise SystemExit("law batch_max_20: judging batches are 20 cards MAX per round "
                         "(Mohamed, June 12 — money + attention discipline)")
    for handle, d, fname in pick_posts(a.n):
        item = build_card(handle, d, fname)
        try:
            qd.push_attributed(item, made_by=f"mind:{d['brain']}", via="scripts/seed_judge_cards.py",
                               reason=f"judge card v2 (FULL POST) — brain field of {fname}")
            print(f"  ⚖️ {item['id']} — mind:{d['brain']} · {item['post_occasion']}")
        except SystemExit as e:
            print(f"  🧊 skipped {item['id']}: {e}")


if __name__ == "__main__":
    main()
