#!/usr/bin/env python3
"""THE JUDGE STAGE — Rule #13 mechanized (Mohamed 2026-06-14: "make them all work; you+RABIE
judge before I see; prove it's BETTER than the previous, zero old mistakes"). Runs the FULL mind
panel on the system-produced batch (data/batch_manifest.json) BEFORE anything reaches the feedback
system:

  • deterministic gates (client_rules/occasion_align/pre_ship_gate) — the old-mistake net
  • CCO mind — Saudi cultural / Arabic-QC score per post
  • COO mind — confidence per post (its formula)
  • BETTER-THAN-PREVIOUS — compares this batch to the last judged batch (data/last_judged_batch.json)
    on measurable axes; must EQUAL-OR-BEAT each + carry zero old mistakes.

Verdict GO only if every post ships AND the batch beats/equals the previous. NO-GO returns it to
the machine (never hand-fixed). Writes data/batch_judgement.json. Usage: python3 scripts/judge_batch.py
"""
import json, glob, sys
from collections import Counter
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import c_suite as cs
import post_audit as pa
from render_client_slot import scene_core


def _posts():
    m = json.loads((B / "data/batch_manifest.json").read_text())
    out = []
    for p in m["posts"]:
        fs = glob.glob(str(B / f"clients/{p['handle']}/posts/{p['date']}__*{m['suffix']}.json"))
        if fs:
            out.append((p["handle"], p["date"], json.loads(Path(fs[0]).read_text())))
    return m, out


def _metrics(posts):
    """measurable axes for better-than-previous."""
    n = len(posts) or 1
    cores = Counter()
    for h, dt, d in posts:
        cs_ = scene_core((d.get("captions") or [""])[0]) or {"_uncore"}
        cores[sorted(cs_)[0] if cs_ else "_uncore"] += 1
    brains = Counter(d.get("brain") for h, dt, d in posts)
    clients = Counter(h for h, dt, d in posts)
    return {"n": n, "max_core_pct": round(max(cores.values()) / n * 100, 1),
            "max_brain_pct": round(max(brains.values()) / n * 100, 1),
            "n_brains": len(brains), "n_clients": len(clients)}


def main():
    m, posts = _posts()
    if not posts:
        sys.exit("🛑 no manifest posts")
    results = []
    old_mistakes = 0
    for h, dt, d in posts:
        hard = [i for i in pa.audit_post(d, h) if i[0] != "occasion_missing" and not i[0].endswith("_warn")]
        old_mistakes += len(hard)
        v = cs.judge_post(d, h)
        results.append({"post": f"{h} {dt}", "ship": v["ship"] and not hard,
                        "coo_confidence": v["coo_confidence"], "cco": v["cco"].get("saudi_score"),
                        "cco_verdict": v["cco"].get("verdict"), "hard_issues": [k for k, _ in hard]})
    n_ship = sum(1 for r in results if r["ship"])
    avg_conf = round(sum(r["coo_confidence"] for r in results) / len(results), 3)
    avg_cco = round(sum((r["cco"] or 0) for r in results) / len(results), 1)
    metrics = _metrics(posts)

    # BETTER-THAN-PREVIOUS
    prev_f = B / "data/last_judged_batch.json"
    prev = json.loads(prev_f.read_text()) if prev_f.exists() else None
    better = True
    compare = {}
    if prev:
        compare = {
            "avg_confidence": (avg_conf, prev.get("avg_conf", 0), avg_conf >= prev.get("avg_conf", 0)),
            "avg_cco": (avg_cco, prev.get("avg_cco", 0), avg_cco >= prev.get("avg_cco", 0)),
            "old_mistakes": (old_mistakes, prev.get("old_mistakes", 999), old_mistakes <= prev.get("old_mistakes", 999)),
            "max_core_pct": (metrics["max_core_pct"], prev.get("max_core_pct", 100), metrics["max_core_pct"] <= prev.get("max_core_pct", 100)),
            "n_brains": (metrics["n_brains"], prev.get("n_brains", 0), metrics["n_brains"] >= prev.get("n_brains", 0)),
        }
        better = all(ok for _, _, ok in compare.values())

    go = (n_ship == len(results)) and old_mistakes == 0 and better
    out = {"n": len(results), "n_ship": n_ship, "old_mistakes": old_mistakes,
           "avg_confidence": avg_conf, "avg_cco": avg_cco, "metrics": metrics,
           "better_than_previous": better, "compare": {k: {"now": v[0], "prev": v[1], "ok": v[2]} for k, v in compare.items()},
           "GO": go, "per_post": results}
    (B / "data/batch_judgement.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    print(f"JUDGE: {n_ship}/{len(results)} ship · {old_mistakes} old-mistakes · avg_conf {avg_conf} · avg_cco {avg_cco}")
    print(f"   metrics: {metrics}")
    if prev:
        print(f"   better-than-previous: {better}  {out['compare']}")
    else:
        print("   no previous batch — this becomes the baseline")
    print("🟢 GO — minds cleared it" if go else "🔴 NO-GO — back to the machine (never hand-fix)")
    if go:  # this batch becomes the new baseline ONLY when it passes
        (B / "data/last_judged_batch.json").write_text(json.dumps(
            {"avg_conf": avg_conf, "avg_cco": avg_cco, "old_mistakes": old_mistakes,
             "max_core_pct": metrics["max_core_pct"], "n_brains": metrics["n_brains"]}, ensure_ascii=False, indent=1))
    sys.exit(0 if go else 1)


if __name__ == "__main__":
    main()
