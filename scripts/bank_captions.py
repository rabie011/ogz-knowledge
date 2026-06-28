#!/usr/bin/env python3
"""BANK CAPTIONS (June 28, 2026) — pre-generate + 2-judge captions OFFLINE so /produce serves a ready
post with NO live HUMAIN. This removes the single-HUMAIN-browser SPOF from the request path (DeepSeek's
readiness blocker #1) — /produce becomes the fast `wrap` path we already proved.

Designed with the RABIE+DeepSeek orchestra panel. The shape (DeepSeek):
- Bank N candidate captions per (brand,product,chain); 2-judge each (HUMAIN authority + GPT cross-check);
  bank the WINNER (highest combined score) WITH its judgment (caption↔judgment stays matched — bite #4).
- /produce reads the bank → no Playwright/HUMAIN in the serve path. Live gen is the offline batch only.
THE STALENESS GUARD (DeepSeek's sharpest risk, named live in the panel): a banked caption carries a
`source_hash` of the brand's caption organs (voice + red_lines + product truth). On serve we recompute
it; a mismatch = the brand drifted → the caption is FLAGGED stale (re-bank), never silently served.

Writer: data/caption_bank.json  ·  Reader: bank_lookup() (export_produce_post serves from it).

Usage:
  python3 scripts/bank_captions.py --handle eatjurisha --product جريش --chain G03 --n 3
  python3 scripts/bank_captions.py --all                 # bank every banked render (offline, slow)
  python3 scripts/bank_captions.py --status              # what's banked + freshness
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
BANK = B / "data" / "caption_bank.json"
ORGAN_FILES = ("profile/fingerprint.json", "profile/red_lines.json", "profile/product_truth.json")


def _key(handle, product, chain):
    return f"{handle}__{product.replace(' ', '_')}__{chain}"


def _source_hash(handle, product):
    """Hash the caption-relevant organs — if the brand's voice/red-lines/product truth changes, the
    banked caption is stale (DeepSeek's freshness guard)."""
    parts = []
    for rel in ORGAN_FILES:
        p = B / "clients" / handle / rel
        parts.append(p.read_text() if p.exists() else "")
    return hashlib.sha256(("||".join(parts) + "|" + product).encode()).hexdigest()[:16]


def _load():
    return json.loads(BANK.read_text()) if BANK.exists() else {}


def _save(d):
    BANK.parent.mkdir(parents=True, exist_ok=True)
    BANK.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def bank_lookup(handle, product, chain):
    """READER — the fresh banked caption for a post, or None. `fresh` is False if the brand drifted."""
    d = _load().get(_key(handle, product, chain))
    if not d:
        return None
    d = dict(d)
    d["fresh"] = d.get("source_hash") == _source_hash(handle, product)
    return d


def bank_one(handle, product, chain, n=3, occasion="everyday"):
    """Generate n captions (system engine), 2-judge each, bank the winner with its judgment + source_hash."""
    import export_produce_post as epp
    img = epp.find_image(handle, product, chain)
    if not img:
        return {"ok": False, "reason": f"no banked render for {handle} · {product} · {chain}"}
    cands = []
    for _ in range(max(1, n)):
        cap = epp.gen_caption(handle, product, occasion)   # the SYSTEM writes it (Rule #12)
        if not cap:
            continue
        judge = epp.rejudge(img, handle, product, cap, occasion)  # HUMAIN + GPT, matched to THIS caption
        cands.append({"caption": cap, "judge": judge, "score": judge.get("score") or 0})
    if not cands:
        return {"ok": False, "reason": "caption engine produced nothing (all killed / pens down)"}
    winner = max(cands, key=lambda c: c["score"])
    bank = _load()
    bank[_key(handle, product, chain)] = {
        "caption": winner["caption"], "judge": winner["judge"], "score": winner["score"],
        "candidates": len(cands), "source_hash": _source_hash(handle, product),
        "banked_at": int(time.time()),
        "_note": "served by /produce with NO live HUMAIN; re-bank if source_hash drifts (stale)",
    }
    _save(bank)
    return {"ok": True, "key": _key(handle, product, chain), "caption": winner["caption"],
            "score": winner["score"], "judge_status": winner["judge"].get("status"),
            "signals": winner["judge"].get("signals"), "from_candidates": len(cands)}


def bank_all(n=3):
    """Bank every banked render (offline batch)."""
    import export_produce_post as epp
    out = []
    for stem in epp.list_banked():
        parts = stem.split("_")
        # filename = handle_<product words>_chain.jpg → handle is first token, chain is last
        handle, chain = parts[0], parts[-1]
        product = " ".join(parts[1:-1])
        if not product:
            continue
        r = bank_one(handle, product, chain, n=n)
        out.append((stem, r.get("ok"), r.get("score") or r.get("reason")))
        print(f"  {'✅' if r.get('ok') else '⚠'} {stem}: {r.get('score') or r.get('reason')}")
    return out


def status():
    bank = _load()
    print(f"caption_bank: {len(bank)} posts")
    for key, d in bank.items():
        handle, *_ = key.split("__")
        product = key.split("__")[1].replace("_", " ")
        fresh = d.get("source_hash") == _source_hash(handle, product)
        print(f"  {'🟢 fresh' if fresh else '🔴 STALE'}  {key}  score={d.get('score')} "
              f"signals={(d.get('judge') or {}).get('signals')}  «{(d.get('caption') or '')[:40]}»")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--product", default="")
    ap.add_argument("--chain", default="")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        status()
    elif a.all:
        bank_all(n=a.n)
    elif a.handle and a.product and a.chain:
        print(json.dumps(bank_one(a.handle, a.product, a.chain, n=a.n), ensure_ascii=False, indent=2))
    else:
        sys.exit("need --handle --product --chain (+ --n), or --all, or --status")


if __name__ == "__main__":
    main()
