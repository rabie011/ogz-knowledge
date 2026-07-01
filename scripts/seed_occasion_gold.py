#!/usr/bin/env python3
"""Mint occasion-gold SEED lines for a client — the SYSTEM produces, never Claude by hand (Rule #12).

Backlog B203 (jurisha, done) / B204 (albaik) / B205 (myfitness): each client needs occasion-anchored
gold seed LINES (caption text only — NO fal render, so the no_fal_photos gate is irrelevant here).
Before this script those seeds were hand-invoked per-occasion in a prior session — a Rule #12 violation
waiting to repeat (DeepSeek audit, this fire). This script is the reusable machine:

    for each occasion:  slot -> rcs.make_angle(panel) -> rcs.render_captions  (the CD-brain pen, gates baked in)
    pick the best line -> append to gold.json['seed_unconfirmed'] with source=occasion_gold_<occ>, rated:false
    -> then RABIE rates (his eye is the only judge; seeds stay unconfirmed until he does).

The producing pen (render_client_slot.render_captions) already consumes the client's confirmed organs,
learned phrase-bans, and the founder taste law — so the lines come out clean, not produce->block->waste.

Idempotent: an occasion already carrying an occasion_gold_<occ> seed is skipped (never double-mint).

    python3 scripts/seed_occasion_gold.py --handle albaik \
        --occasions ramadan,white_friday,founding_day,eid_al_fitr,eid_al_adha --write

The core logic (select_line / already_seeded / make_seed_entry / merge_seed / mint_occasions) takes an
injectable producer + timestamp so it is unit-tested without any network/LLM cost (money-discipline).
"""
from __future__ import annotations
import argparse, datetime, json, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def gold_path(handle: str) -> Path:
    return BASE / "clients" / handle / "profile" / "gold.json"


def load_gold(handle: str) -> dict:
    p = gold_path(handle)
    g = json.loads(p.read_text()) if p.exists() else {}
    g.setdefault("gold", [])
    g.setdefault("seed_unconfirmed", [])
    return g


def already_seeded(gold: dict, occ: str) -> bool:
    """True if an occasion_gold seed for this occasion already exists (idempotency)."""
    src = f"occasion_gold_{occ}"
    for x in gold.get("seed_unconfirmed", []) + gold.get("gold", []):
        if isinstance(x, dict) and x.get("source") == src:
            return True
    return False


def select_line(caps, product: str) -> str:
    """Pick the best caption from the pen's options: prefer one that names the product, else the first
    non-empty. `caps` may be a list[str], list[dict], or {'options': [...]} (render_captions shapes)."""
    if isinstance(caps, dict):
        caps = caps.get("options", [])
    if not isinstance(caps, list):
        caps = [caps]
    lines = []
    for opt in caps:
        t = opt.get("caption") if isinstance(opt, dict) else opt
        if t and str(t).strip():
            lines.append(str(t).strip())
    if not lines:
        return ""
    if product:
        for t in lines:
            if product in t:
                return t
    return lines[0]


def make_seed_entry(occ: str, line: str, product: str, ts: str) -> dict:
    """The seed_unconfirmed record shape — matches the B203-jurisha seeds already in gold.json."""
    return {
        "occasion": occ,
        "source": f"occasion_gold_{occ}",
        "line": line,
        "product": product,
        "ts": ts,
        "rated": False,          # RABIE has not rated it yet; his eye confirms it into 'gold'
        "confirmed": False,
    }


def merge_seed(gold: dict, entry: dict) -> bool:
    """Append the seed iff its occasion isn't already minted. Returns True if it was added."""
    occ = entry.get("occasion", "")
    if already_seeded(gold, occ):
        return False
    gold.setdefault("seed_unconfirmed", []).append(entry)
    return True


def mint_occasions(handle: str, occasions, product: str, produce_fn, ts: str, gold: dict | None = None):
    """Drive the injectable producer once per occasion, merge the picked line as a seed.

    produce_fn(handle, occ, product) -> caption options (list[str]|list[dict]|dict). Injecting it keeps
    the whole loop unit-testable with a fake producer (no LLM / no network / no cost). The live CLI wires
    produce_fn to the real system pen (render_client_slot). Returns (gold, results-per-occasion)."""
    if gold is None:
        gold = load_gold(handle)
    results = []
    for occ in occasions:
        if already_seeded(gold, occ):
            results.append({"occasion": occ, "status": "skipped_exists"})
            continue
        try:
            caps = produce_fn(handle, occ, product)
        except Exception as e:  # a dead model/key must not abort the batch (never-block)
            results.append({"occasion": occ, "status": "produce_error", "error": f"{type(e).__name__}: {e}"})
            continue
        line = select_line(caps, product)
        if not line:
            results.append({"occasion": occ, "status": "no_line"})
            continue
        entry = make_seed_entry(occ, line, product, ts)
        merge_seed(gold, entry)
        results.append({"occasion": occ, "status": "minted", "line": line, "named_product": product in line})
    return gold, results


# ---- live wiring (only touched by the CLI; the tests never import the LLM) --------------------------

def _default_product(handle: str) -> str:
    """First product candidate from the client's truth = the brand's hero (same source produce uses)."""
    import render_client_slot as rcs
    c = rcs.load_client(handle)
    prods = [x["name"] for x in c["truth"]["product_candidates"]]
    return prods[0] if prods else ""


def _live_producer(handle: str, occ: str, product: str):
    """The REAL system pen: slot -> make_angle(panel) -> render_captions. Same path as
    produce_complete_post.py, minus the fal render (seeds are LINES only)."""
    import render_client_slot as rcs
    try:
        import openclaw_convert as oc
        sector = oc.load_brand(handle).get("sector", "")
    except Exception:
        sector = ""
    c = rcs.load_client(handle)
    slot = {"occasion": occ, "date": datetime.date.today().isoformat(), "type": "offer", "format": "image",
            "formula": "CF_01", "beat": occ, "angle_theme": product, "product_name": product}
    try:
        angle = rcs.make_angle(c, slot, sector, panel=True)
    except Exception:
        angle = {}
    if not isinstance(angle, dict):
        angle = {}
    angle.setdefault("brain", "firaasa")
    angle.setdefault("post_type", "product")
    angle.setdefault("core", "product")
    return rcs.render_captions(c, slot, angle)


def main():
    ap = argparse.ArgumentParser(description="Mint occasion-gold seed lines via the system pen (Rule #12).")
    ap.add_argument("--handle", required=True)
    ap.add_argument("--occasions", required=True, help="comma-separated occasion keys")
    ap.add_argument("--product", default="", help="hero product (default: first product candidate)")
    ap.add_argument("--write", action="store_true", help="persist to gold.json (default: dry preview)")
    a = ap.parse_args()

    sys.path.insert(0, str(BASE / "scripts"))
    occasions = [o.strip() for o in a.occasions.split(",") if o.strip()]
    product = a.product or _default_product(a.handle)
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    gold = load_gold(a.handle)

    gold, results = mint_occasions(a.handle, occasions, product, _live_producer, ts, gold)
    minted = [r for r in results if r["status"] == "minted"]
    for r in results:
        tag = {"minted": "🟢", "skipped_exists": "⏭️", "no_line": "⚪", "produce_error": "🔴"}.get(r["status"], "•")
        print(f"  {tag} {r['occasion']}: {r['status']}"
              + (f" — {'✓product' if r.get('named_product') else 'no-product'} — {r.get('line','')[:70]}"
                 if r["status"] == "minted" else ""))
    print(f"\n  product={product!r}  minted={len(minted)}  of {len(occasions)} requested")

    if a.write and minted:
        gold_path(a.handle).write_text(json.dumps(gold, ensure_ascii=False, indent=2))
        print(f"  💾 wrote {len(minted)} seed(s) -> {gold_path(a.handle)} (RABIE rates next; rated:false)")
    elif minted:
        print("  (dry run — pass --write to persist)")


if __name__ == "__main__":
    main()
