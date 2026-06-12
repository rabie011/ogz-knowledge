#!/usr/bin/env python3
"""RETRO ORDER-TAIL TAGGER (zoom-r6 follow-up, June 12 — RABIE's pick).
The CTA gate fixes future renders; this tags the PAST: existing cards that sell
on what is now a brand-build day get order_tail=true so D3 judging batches and
pick-sets prefer clean cards. TAG, never strip — text surgery breaks captions;
a tag is reversible and honest.

Usage: python3 scripts/tag_order_tails.py
"""
import json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from render_client_slot import cta_allowed
from truth_guards import CTA


def channel_names(handle: str) -> list[str]:
    tpf = BASE / "clients" / handle / "profile/truth_pack.json"
    if not tpf.exists():
        return []
    return [c["name"] for c in json.loads(tpf.read_text()).get("channels", [])
            if c.get("name") and c["name"] != "linktree"]


def main():
    tagged = cleared = scanned = 0
    for cdir in sorted((BASE / "clients").iterdir()):
        posts = cdir / "posts"
        if not posts.is_dir():
            continue
        chans = channel_names(cdir.name)
        chan_re = re.compile("|".join(map(re.escape, chans))) if chans else None
        for f in sorted(posts.glob("*.json")):
            try:
                card = json.loads(f.read_text())
            except Exception:
                continue
            caps = card.get("captions") or []
            if not caps:
                continue
            scanned += 1
            date = f.name.split("__")[0]
            slot = {"date": date, "occasion": card.get("occasion"), "type": card.get("type")}
            sells = any(CTA.search(c) or (chan_re and chan_re.search(c)) for c in caps)
            should_tag = sells and not cta_allowed(cdir.name, slot)
            if should_tag and not card.get("order_tail"):
                card["order_tail"] = True
                f.write_text(json.dumps(card, ensure_ascii=False, indent=2))
                tagged += 1
            elif not should_tag and card.get("order_tail"):
                card.pop("order_tail")
                f.write_text(json.dumps(card, ensure_ascii=False, indent=2))
                cleared += 1
    print(f"scanned {scanned} cards · tagged {tagged} order-tail · cleared {cleared}")
    return tagged


if __name__ == "__main__":
    main()
