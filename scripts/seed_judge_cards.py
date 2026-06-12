#!/usr/bin/env python3
"""SEED THE JUDGE LANE (June 12 zoom-out) — caption judge cards from posts ALREADY on
disk (zero-LLM). Without these the redesign's centerpiece («Your taste, applied»)
renders zeros on day one. One card = one caption: Approve/Reject + rating + chips +
correction — fully attributed to the producing MIND, carrying handle+caption so an
approve ★4+ mints straight into clients/<handle>/profile/gold.json (the organ the
renderer reads first).

Money discipline: small batches. Default 5 cards, diverse brains + clients.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base
import queue_decision as qd


def pick_posts(n: int) -> list:
    """Diverse picks: alternate clients, prefer distinct brains, recent dates."""
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
            caps = d.get("captions") or []
            brain = d.get("brain", "")
            if not caps or not brain:
                continue
            if brain in seen_brains and len(seen_brains) < 5:
                continue
            seen_brains.add(brain)
            picked.append((handle, d, Path(f).name))
            break
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5)
    a = ap.parse_args()
    for handle, d, fname in pick_posts(a.n):
        caption = d["captions"][0]
        brain = d["brain"]
        date = d.get("date", "")
        slot = str(d.get("slot", ""))
        occ = "evergreen" if "evergreen" in slot else (slot[:40] or "?")
        cid = f"judge_{handle}_{date}"
        item = {"id": cid, "title": f"{handle} · {date}",
                "tag": "Judge", "desc": "", "clock": "",
                "priority": "normal", "created": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "status": "open", "kind": "caption_judge",
                "judge_lane": True, "lane": "creative",
                "handle": handle, "caption": caption, "occasion": occ,
                "why": f"Approve ★4+ keeps this as a gold example for {handle}; a rejection opens a case on the mind that wrote it.",
                "need": "Your verdict on this caption — approve, reject, or correct it.",
                "did": f"The {brain} mind wrote it from {handle}'s truth + the brain's knowledge (post {fname}).",
                "island_text": caption}
        try:
            qd.push_attributed(item, made_by=f"mind:{brain}", via="scripts/seed_judge_cards.py",
                               reason=f"caption judge card — brain field of {fname} on disk")
            print(f"  ⚖️ {cid} — mind:{brain} · «{caption[:42]}»")
        except SystemExit as e:
            print(f"  🧊 skipped {cid}: {e}")


if __name__ == "__main__":
    main()
