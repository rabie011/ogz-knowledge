#!/usr/bin/env python3
"""3-CLIENT CONNECTION TEST (June 28, 2026) — end-to-end test of the brain over the live HTTP bridge.

Designed WITH DeepSeek (Rule #15). Its #1 insight: the real risk a single-client test misses is
CROSS-CLIENT STATE LEAKAGE (one brand's prompt/product/caption/image bleeding into another). So this
tests all 3 pilots through the same live brain_api and asserts NO bleed. Assert-based (Rule #8): any
failure → non-zero exit, never a soft pass.

Per client: /extract sanity · v3.7 PROMPT grounded in THAT brand's organs (no cross-brand terms) ·
/produce returns a real post (image + caption + judges) · idempotency. Sparse myfitness must REFUSE
cleanly (structured reason), never crash or fake a post. One full live produce proves prompt→caption→2-judge.

Needs brain_api.py running (default http://127.0.0.1:4140). Run: python3 scripts/test_brain_connection.py
"""
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

B = Path(__file__).parent.parent
BASE = "http://127.0.0.1:4140"
SAMPLES = B / "data" / "openclaw_v37" / "samples"

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    return bool(cond)


def _req(method, path, body=None, timeout=30):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"_err": f"{type(e).__name__}: {str(e)[:120]}"}


def poll_job(job_id, timeout=220):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st, j = _req("GET", f"/job/{job_id}")
        if j.get("status") in ("done", "failed"):
            return j
        time.sleep(4)
    return {"status": "timeout"}


def client_prompt_text(handle):
    """Concatenated v3.7 system-written prompts for a brand (grounding evidence)."""
    out = []
    for p in SAMPLES.glob(f"{handle}_*.json"):
        try:
            d = json.loads(p.read_text())
            out.append((d.get("prompt") or "") + " " + (d.get("scene") or ""))
        except Exception:
            continue
    return " ".join(out).lower()


def test_ready_client(handle, min_cov, own_terms, forbidden_terms, product, chain):
    print(f"\n── {handle} (produce-ready) ─────────────────────────────")
    # 1. /extract
    st, prof = _req("GET", f"/extract?handle={urllib.parse.quote(handle)}", timeout=20)
    check(f"{handle}: /extract 200", st == 200, f"status {st}")
    cov = (prof.get("_coverage") or {}).get("pct", 0)
    check(f"{handle}: profile coverage ≥ {min_cov}%", cov >= min_cov, f"got {cov}%")
    check(f"{handle}: ig_username present", (prof.get("pre_fill") or {}).get("ig_username"),
          (prof.get("pre_fill") or {}).get("ig_username"))

    # 2. v3.7 PROMPT grounding (+ cross-brand leakage)
    pt = client_prompt_text(handle)
    check(f"{handle}: prompt exists", len(pt) > 100, f"{len(pt)} chars")
    check(f"{handle}: prompt grounded in own brand", any(t.lower() in pt for t in own_terms),
          "found: " + ", ".join(t for t in own_terms if t.lower() in pt))
    leaked = [t for t in forbidden_terms if t.lower() in pt]
    check(f"{handle}: NO cross-brand leak in prompt", not leaked, f"leaked: {leaked}" if leaked else "clean")

    # 3. /produce (wrap, fast) → real contract
    st, r = _req("POST", "/produce", {"handle": handle, "product": product, "chain": chain,
                                      "produce": False}, timeout=20)
    check(f"{handle}: /produce 202", st == 202, f"status {st}")
    job = poll_job(r.get("job_id", ""), timeout=40)
    rec = job.get("result") or {}
    check(f"{handle}: produce job done", job.get("status") == "done", job.get("status"))
    check(f"{handle}: post has image", rec.get("content", {}).get("image_url"),
          rec.get("content", {}).get("image_url"))
    check(f"{handle}: image is THIS brand's", str(rec.get("content", {}).get("image_url", "")).split("/")[-1].startswith(handle),
          rec.get("content", {}).get("image_url", "").split("/")[-1])
    check(f"{handle}: vision judged", (rec.get("judgments", {}).get("vision") or {}).get("verdict"),
          (rec.get("judgments", {}).get("vision") or {}).get("verdict"))

    # 4. idempotency
    st2, r2 = _req("POST", "/produce", {"handle": handle, "product": product, "chain": chain,
                                        "produce": False}, timeout=20)
    job2 = poll_job(r2.get("job_id", ""), timeout=40)
    pid1, pid2 = rec.get("post_id"), (job2.get("result") or {}).get("post_id")
    check(f"{handle}: idempotent (same post_id)", pid1 and pid1 == pid2, f"{pid1} == {pid2}")


def test_full_produce(handle, product, chain):
    """ONE full live produce, run LAST (sequential — never blocks the fast checks; DeepSeek). Proves the
    prompt→caption→2-judge pipeline end-to-end, incl. the «التوأم» grounded-vocab fix (caption survives)."""
    print(f"\n── {handle} · {product} — FULL live produce (caption + HUMAIN+GPT judges, ~1-3min) ──")
    st, r = _req("POST", "/produce", {"handle": handle, "product": product, "chain": chain,
                                      "produce": True, "regenerate": True}, timeout=20)
    job = poll_job(r.get("job_id", ""), timeout=300)
    rec = job.get("result") or {}
    cap = (rec.get("content", {}).get("caption") or {}).get("arabic")
    cj = rec.get("judgments", {}).get("caption") or {}
    check(f"{handle}: job done (no timeout)", job.get("status") == "done", job.get("status"))
    check(f"{handle}: live caption generated (التوأم fix)", bool(cap), (cap or "")[:70])
    check(f"{handle}: caption judged", cj.get("status") == "judged", cj.get("status"))
    check(f"{handle}: 2-judge present (HUMAIN+GPT)", cj.get("signals", 0) >= 2,
          f"signals={cj.get('signals')} judges={list((cj.get('judges') or {}).keys())}")


def test_sparse_client(handle):
    print(f"\n── {handle} (sparse — must refuse cleanly) ─────────────")
    st, prof = _req("GET", f"/extract?handle={urllib.parse.quote(handle)}", timeout=20)
    check(f"{handle}: /extract 200", st == 200, f"status {st}")
    cov = (prof.get("_coverage") or {}).get("pct", 100)
    check(f"{handle}: profile is sparse (<60%)", cov < 60, f"{cov}%")
    # produce must REFUSE (not crash, not fake a post)
    st, r = _req("POST", "/produce", {"handle": handle, "product": "منتج", "chain": "U01",
                                      "produce": False}, timeout=20)
    job = poll_job(r.get("job_id", ""), timeout=40)
    rec = job.get("result") or {}
    check(f"{handle}: job completed (no crash)", job.get("status") == "done", job.get("status"))
    check(f"{handle}: produce REFUSED (not a post)", rec.get("status") == "refused" or rec.get("ok") is False,
          json.dumps({k: rec.get(k) for k in ("ok", "status", "reason")}, ensure_ascii=False))
    check(f"{handle}: refusal has a clear reason", bool(rec.get("reason")), (rec.get("reason") or "")[:80])
    check(f"{handle}: refusal has NO leaked brand", not any(t in json.dumps(rec, ensure_ascii=False).lower()
          for t in ("albaik", "jurisha", "جريش", "بيك")), "clean")


def main():
    st, h = _req("GET", "/health", timeout=5)
    if st != 200:
        print(f"🛑 brain_api not reachable at {BASE} (start it: python3 scripts/brain_api.py)")
        sys.exit(2)
    print(f"brain_api healthy: {h}")

    # fast checks for all 3 clients FIRST (sequential, no slow produce to block the queue) …
    test_ready_client("albaik", 75, ["albaik", "بيك"], ["jurisha", "جريش", "كابلي", "سليق", "myfitness"],
                      "كومبو بيك", "T03")
    test_ready_client("eatjurisha", 65, ["jurisha", "جريش"], ["albaik", "البيك", "broasted", "myfitness"],
                      "جريش", "G03")
    test_sparse_client("myfitness.sa")
    # … THEN exactly one slow full-produce at the very end (DeepSeek: honest single-worker ordering)
    test_full_produce("albaik", "كومبو بيك", "T03")

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    nfail = len(RESULTS) - npass
    print(f"\n{'='*55}\n  {npass}/{len(RESULTS)} PASS · {nfail} FAIL")
    if nfail:
        print("  FAILURES:")
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"   ❌ {name} — {detail}")
        sys.exit(1)
    print("  ✅ ALL GREEN — the brain is connected end-to-end across 3 clients, no cross-brand leak.")


if __name__ == "__main__":
    main()
