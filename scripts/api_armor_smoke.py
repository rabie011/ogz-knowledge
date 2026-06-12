#!/usr/bin/env python3
"""API ARMOR SMOKE HARNESS (D4-5 step c, June 12 — RABIE-ratified).
5-brand sample through the LIVE /api/create asserting the armor holds end-to-end:
v6 path taken, score present, generation logged (fatigue memory), captions clean.
Run BEFORE every future API change ships. Exit 1 = armor broken, do not commit.
Cost: 5 cheap calls per run — the price of never shipping a broken pipeline.

Usage: python3 scripts/api_armor_smoke.py [--base http://127.0.0.1:4100]
"""
import argparse, json, sys, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
GEN_LOG = BASE / "logs/generation_log.jsonl"


def sample_brands(n=5) -> list[str]:
    briefs = json.loads((BASE / "data/brief_matrix.json").read_text())
    brands = sorted({b.get("brand_en") or b["brand"] for b in briefs})
    step = max(len(brands) // n, 1)
    return brands[::step][:n]


def create(base: str, brand: str) -> dict:
    # product is required by CreateRequest; the brief's own product keeps it truthful
    briefs = json.loads((BASE / "data/brief_matrix.json").read_text())
    brief = next((b for b in briefs if (b.get("brand_en") or b["brand"]) == brand), {})
    body = json.dumps({"brand": brand, "product": brief.get("product") or "المنتج الأساسي",
                        "occasion": "اليوم الوطني"}).encode()
    rq = urllib.request.Request(f"{base}/api/create", data=body,
                                headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=180).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:4100")
    a = ap.parse_args()
    brands = sample_brands()
    log_before = len(GEN_LOG.read_text().strip().split("\n")) if GEN_LOG.exists() else 0
    failures = []
    for b in brands:
        try:
            r = create(a.base, b)
            gen = (r.get("proof") or {}).get("generation")
            score = (r.get("quality") or {}).get("score")
            caption = (r.get("content") or {}).get("caption") or ""
            checks = {"v6_path": gen == "v6", "scored": isinstance(score, (int, float)),
                      "has_caption": len(caption) > 10}
            bad = [k for k, v in checks.items() if not v]
            print(f"  {'✅' if not bad else '❌'} {b}: gen={gen} score={score} «{caption[:40]}»"
                  + (f" FAILED: {bad}" if bad else ""))
            if bad:
                failures.append((b, bad))
        except Exception as e:
            print(f"  ❌ {b}: CALL FAILED — {str(e)[:80]}")
            failures.append((b, ["call_failed"]))
    log_after = len(GEN_LOG.read_text().strip().split("\n")) if GEN_LOG.exists() else 0
    logged = log_after - log_before
    ok_calls = len(brands) - len(failures)
    print(f"\n  generation_log: +{logged} entries for {ok_calls} successful v6 calls")
    # ASSERT LAW: hard refusal, never eyes-only
    assert not failures, f"ARMOR BROKEN on {len(failures)} brands: {failures}"
    assert logged >= ok_calls, f"fatigue memory leak: {ok_calls} calls but only {logged} logged"
    print("🟢 ARMOR SMOKE: all brands pass — safe to ship")


if __name__ == "__main__":
    main()
