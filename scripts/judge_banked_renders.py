#!/usr/bin/env python3
"""A5 BATCH JUDGE SESSION (C202, June 28 2026) — the SYSTEM judges every banked complete post
(render image + banked caption) through the mechanical RABIE vision judge, so the moat's feedback
circuit runs end-to-end on real output and the next render LEARNS from what the eye caught.

This is Rule #14 made operational: every verdict PERSISTS (rabie_judge.log_verdict →
data/rabie_verdicts.jsonl, the writer) and FEEDS FORWARD (rabie_judge.lessons_for →
render_openclaw's [LEARNED] pre-prompt, the reader). We do NOT hand-pick or hand-write — the
SYSTEM produces and the SYSTEM judges (Rules #12/#13); this driver only sequences the system's
own judge over the bank.

Input  : data/caption_bank.json (banked posts) × api/static/renders_v37/<handle>_<product>_<chain>.jpg
Writer : data/rabie_verdicts.jsonl (via rabie_judge.log_verdict)
Reader : rabie_judge.lessons_for() — proven to grow after this run

Usage:
  python3 scripts/judge_banked_renders.py            # judge the whole bank (<=20/round, money rule)
  python3 scripts/judge_banked_renders.py --handle albaik
  python3 scripts/judge_banked_renders.py --dry-run  # map posts->renders, no LLM, no spend
  python3 scripts/judge_banked_renders.py --limit 5
"""
import argparse
import json
import sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
BANK = B / "data" / "caption_bank.json"
RENDERS = B / "api" / "static" / "renders_v37"
MONEY_CAP = 20  # Rule: <=20 photos per judging round


def _posts(handle_filter=None):
    """Map each banked post to its render image. Returns list of (key, handle, product, chain, image, caption)."""
    bank = json.loads(BANK.read_text()) if BANK.exists() else {}
    out = []
    for key, v in bank.items():
        handle, product_us, chain = key.split("__")
        if handle_filter and handle != handle_filter:
            continue
        product = product_us.replace("_", " ")
        caption = (v.get("caption") or v.get("text") or "") if isinstance(v, dict) else ""
        # render naming is flat: <handle>_<product_underscored>_<chain>.jpg (also try spaced product)
        cands = [f"{handle}_{product_us}_{chain}.jpg", f"{handle}_{product}_{chain}.jpg"]
        img = next((RENDERS / c for c in cands if (RENDERS / c).exists()), None)
        out.append({"key": key, "handle": handle, "product": product, "chain": chain,
                    "image": img, "caption": caption})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    ap.add_argument("--limit", type=int, default=MONEY_CAP)
    ap.add_argument("--dry-run", action="store_true", help="map posts->renders only; no LLM, no spend")
    a = ap.parse_args()

    import rabie_judge as rj

    before = 0
    if rj.VERDICT_LOG.exists():
        before = sum(1 for ln in rj.VERDICT_LOG.read_text().splitlines() if ln.strip())

    posts = _posts(a.handle)
    ready = [p for p in posts if p["image"] and p["caption"]]
    skipped = [p for p in posts if not (p["image"] and p["caption"])]

    print(f"bank posts: {len(posts)}  ·  judgeable: {len(ready)}  ·  skipped(no render/caption): {len(skipped)}")
    for p in skipped:
        print(f"  ⏭️  {p['key']}  (image={'yes' if p['image'] else 'NO'}, caption={'yes' if p['caption'] else 'NO'})")

    if len(ready) > a.limit:
        print(f"  ⚠️  capping at {a.limit} this round (money rule); {len(ready)-a.limit} deferred")
        ready = ready[:a.limit]

    if a.dry_run:
        print("\n--dry-run: no LLM called, no verdict persisted.")
        for p in ready:
            print(f"  would judge: {p['key']}  ->  {p['image'].name}")
        return 0

    results = []
    for i, p in enumerate(ready, 1):
        print(f"\n[{i}/{len(ready)}] judging {p['key']} ...", flush=True)
        try:
            verdict = rj.judge(str(p["image"]), p["handle"], p["product"], p["caption"])
        except SystemExit as e:
            print(f"  🛑 {e}")
            continue
        except Exception as e:
            print(f"  🛑 judge failed: {e}")
            continue
        rj.log_verdict(p["handle"], p["product"], str(p["image"]), verdict)  # PERSIST (Rule #14 writer)
        v = verdict.get("verdict", "?")
        emoji = {"bank": "✅", "fix": "🔧", "kill": "💀"}.get(v, "?")
        print(f"  {emoji} {v.upper()} overall={verdict.get('overall')}/5  {verdict.get('rabie_note','')[:80]}")
        results.append({"key": p["key"], "verdict": v, "overall": verdict.get("overall"),
                        "handle": p["handle"], "product": p["product"]})

    after = sum(1 for ln in rj.VERDICT_LOG.read_text().splitlines() if ln.strip())

    # SUMMARY + the Rule #14 assertions (the loop must measurably grow + feed forward)
    from collections import Counter
    print(f"\n{'='*60}\nA5 BATCH JUDGE — SUMMARY")
    print(f"  verdicts: {Counter(r['verdict'] for r in results)}")
    approved = [r for r in results if r["verdict"] == "bank"]
    print(f"  ✅ approved (bank): {len(approved)}")
    print(f"  ledger grew: {before} → {after}  (+{after-before})")

    # READER proof: lessons now exist for products that got fix/kill
    fed = 0
    for hp in {(r["handle"], r["product"]) for r in results if r["verdict"] in ("fix", "kill")}:
        lessons = rj.lessons_for(*hp)
        if lessons:
            fed += 1
            print(f"  🔁 lessons_for{hp}: {len(lessons)} correction(s) will inject into next render")
    print(f"  feed-forward live for {fed} product(s)")
    print("=" * 60)

    # Rule #8 — refuse, don't warn: if we judged but the ledger did not grow, the writer is severed.
    if results and after <= before:
        print("🛑 RED: verdicts produced but ledger did not grow — writer severed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
