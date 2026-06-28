#!/usr/bin/env python3
"""PERFORMANCE INGESTOR (June 28, 2026) — the performance→profile feedback loop (the 2-way wire).

The connection's missing half (DeepSeek's "biggest miss"): the brain produced posts but never learned
from what actually got engagement. This ingests a published post's real engagement and feeds it back —
SUBTRACTIVELY and safely, the kill-registry way, NOT as an overfit ranker (the 33%-on-sparse-data scar).

DESIGNED WITH DEEPSEEK (June 28 consult, Rule #15). Its rulings, honored exactly:
- METRIC: engagement_rate = (likes + 2·saves + 3·comments + 4·shares) / reach  (saves/shares > likes).
- NORMALIZE per brand: z = (er − brand_mean) / brand_std over the brand's last 20 posts (Saudi vs global,
  big vs small account self-normalize). Raw likes are garbage across brands/time.
- PAID-BOOST GUARD: reach > 3× the brand's organic median reach → flag boosted, EXCLUDE from baseline
  (but still eligible to KILL if it bombs despite paid reach — that's a real signal).
- ACT ONLY ON EXTREMES: z ≤ −2.0 → KILL the (brand,product,setup) (kill_registry; the producer's
  pre-flight gate already reads it). z ≥ +2.5 AND brand has ≥5 posts → increment a confidence COUNTER
  (never the pre_fill value). −2 < z < +2.5 (≈87% of posts) → DO NOTHING.
- NEVER auto-adjust pre_fill values / producer weights / caption style — only FLAG for a human.
- The kill-registry's TTL auto-resolves stale kills (decay) so a forgotten kill never blocks forever.

Writer: data/outcome_events.jsonl (durable, append-only; aligns with 12_data_shapes/outcome_event_v1).
Readers: kill_registry.get_pending_combo (producer gate) + get_perf_signals(brand) (surfaced to human).

Usage:
  python3 scripts/perf_ingestor.py --post-id eatjurisha__جريش__G03 \
      --likes 40 --saves 2 --comments 1 --shares 0 --reach 5000
  python3 scripts/perf_ingestor.py --signals eatjurisha      # what perf has learned for a brand
  python3 scripts/perf_ingestor.py --simulate                # self-test the z-score + kill logic
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

OUTCOMES = B / "data" / "outcome_events.jsonl"
COUNTERS = B / "data" / "perf_counters.json"      # confidence counters — NEVER touch pre_fill values

KILL_Z = -2.0       # z at/below → kill the setup (bottom ~2.5% of the brand's own distribution)
PROMOTE_Z = 2.5     # z at/above → +1 confidence counter (top ~1%) — only with enough history
MIN_N_PROMOTE = 5   # require this many of the brand's posts before any POSITIVE signal counts
BOOST_REACH_MULT = 3.0  # reach > this × brand organic median → flag paid boost, exclude from baseline
MIN_REACH_KILL = 500    # never KILL a setup on a reach-starved post (DeepSeek: reach-starvation false-kill)
BASELINE_WINDOW = 20


def _er(e: dict):
    """Weighted engagement rate over reach. saves/comments/shares are less noisy than likes."""
    reach = e.get("reach") or 0
    if not reach:
        return None
    score = (e.get("likes", 0) + 2 * e.get("saves", 0)
             + 3 * e.get("comments", 0) + 4 * e.get("shares", 0))
    return score / reach


def _parse_post_id(post_id):
    parts = post_id.split("__")
    return (parts + ["", "", ""])[:3]   # handle, product, setup


def _load_outcomes():
    if not OUTCOMES.exists():
        return []
    out = []
    for ln in OUTCOMES.read_text().splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


def _brand_history(brand, rows=None):
    """The brand's prior posts (for baseline). Excludes paid-boosted (they corrupt the mean)."""
    rows = rows if rows is not None else _load_outcomes()
    return [r for r in rows if r.get("brand") == brand and not r.get("paid_boost")]


def _baseline(history):
    ers = [r["engagement_rate"] for r in history[-BASELINE_WINDOW:]
           if isinstance(r.get("engagement_rate"), (int, float))]
    if len(ers) < 2:
        return None, None, len(ers)
    return statistics.mean(ers), statistics.pstdev(ers), len(ers)


def _bump_counter(brand, feature, delta):
    data = json.loads(COUNTERS.read_text()) if COUNTERS.exists() else {}
    key = f"{brand}|{feature}"
    data[key] = (data.get(key, 0) or 0) + delta
    COUNTERS.parent.mkdir(parents=True, exist_ok=True)
    COUNTERS.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data[key]


def ingest(post_id, engagement, ts=None):
    """Ingest one published post's engagement → durable outcome event + safe feedback action."""
    import kill_registry as kr
    handle, product, setup = _parse_post_id(post_id)
    ts = ts or int(time.time())
    er = _er(engagement)

    rows = _load_outcomes()
    history = _brand_history(handle, rows)
    # paid-boost: reach far above the brand's organic median → exclude from baseline, but can still kill
    reaches = [r.get("reach") for r in history if r.get("reach")]
    med_reach = statistics.median(reaches) if reaches else None
    paid_boost = bool(med_reach and engagement.get("reach", 0) > BOOST_REACH_MULT * med_reach)

    mean, std, n = _baseline(history)
    z = None
    if er is not None and mean is not None and std and std > 0:
        z = round((er - mean) / std, 2)

    action, detail = None, None
    reach = engagement.get("reach", 0)
    if z is not None and z <= KILL_Z and reach < MIN_REACH_KILL:
        # reach-starved: a low-reach denominator inflates z → a false kill that exiles a fine setup
        # forever (no new posts to re-test). Warn, don't kill (DeepSeek's reach-starvation guard).
        action, detail = "low_reach_warning", f"z={z} but reach {reach} < {MIN_REACH_KILL} — NOT killing (starved, not bad)"
    elif z is not None and z <= KILL_Z:
        kr.add_perf_kill(handle, product, setup, "underperformed in feed", z_score=z)
        action, detail = "kill", f"{handle}|{product}|{setup} → kill-registry (producer will avoid it)"
    elif z is not None and z >= PROMOTE_Z and (n + 1) >= MIN_N_PROMOTE and not paid_boost:
        c = _bump_counter(handle, setup, +1)
        action, detail = "promote_signal", f"confidence counter {handle}|{setup} = {c} (flag for human; pre_fill untouched)"

    rec = {
        "schema_version": "outcome_event_v1",
        "event_type": "performance",
        "post_id": post_id, "brand": handle, "product": product, "setup": setup,
        "timestamp": ts,
        "performance_metrics": engagement,
        "engagement_rate": round(er, 5) if er is not None else None,
        "brand_baseline": {"mean_er": round(mean, 5) if mean else None,
                           "std_er": round(std, 5) if std else None, "n": n},
        "z_score": z,
        "paid_boost": paid_boost,
        "action": action,
        "action_detail": detail,
        "provenance": {"source": "perf_ingestor", "confidence": "measured",
                       "note": "subtractive feedback — kills on z≤-2, counters on z≥2.5; never edits pre_fill"},
    }
    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTCOMES, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def get_perf_signals(brand):
    """READER (Rule #6) — what performance has learned for a brand, for the producer + the human.
    kills come from kill_registry (the producer already obeys them); counters are HINTS for a human,
    never an auto-adjustment to the profile."""
    import kill_registry as kr
    fp = kr.load_kill_fingerprints()
    kills = [{"key": k, **v} for k, v in fp.items()
             if v.get("fingerprint_type") == "perf_kill" and v.get("status") == "pending"
             and k.startswith(brand + "|")]
    counters = {}
    if COUNTERS.exists():
        counters = {k: v for k, v in json.loads(COUNTERS.read_text()).items()
                    if k.startswith(brand + "|")}
    hist = _brand_history(brand)
    mean, std, n = _baseline(hist)
    return {"brand": brand, "posts_seen": len([r for r in _load_outcomes() if r.get("brand") == brand]),
            "baseline": {"mean_er": mean, "std_er": std, "n": n},
            "perf_kills": kills, "confidence_counters": counters,
            "note": "kills are enforced by the producer; counters are human-facing hints (pre_fill untouched)"}


def _simulate():
    """Self-test: feed a brand 6 average posts + 1 bomb + 1 hero, prove kill/promote fire correctly."""
    import kill_registry as kr
    sim_brand = "simbrand"
    # clean any prior sim rows so the test is deterministic
    if OUTCOMES.exists():
        keep = [ln for ln in OUTCOMES.read_text().splitlines()
                if ln.strip() and json.loads(ln).get("brand") != sim_brand]
        OUTCOMES.write_text("\n".join(keep) + ("\n" if keep else ""))
    base = {"likes": 100, "saves": 10, "comments": 5, "shares": 3, "reach": 10000}  # er≈0.0157
    print("feeding 6 average posts (build baseline)…")
    for i in range(6):
        ingest(f"{sim_brand}__prod__C{i:02d}", dict(base, likes=100 + i * 3), ts=1782600000 + i)
    print("\nfeeding a BOMB (reach 10k, almost no engagement → z should be ≤ -2 → KILL):")
    r = ingest(f"{sim_brand}__prod__BOMB", {"likes": 3, "saves": 0, "comments": 0, "shares": 0, "reach": 10000}, ts=1782600100)
    print(f"  z={r['z_score']}  action={r['action']}  → {r['action_detail']}")
    print("\nfeeding a HERO (huge engagement → z should be ≥ +2.5 → counter):")
    r = ingest(f"{sim_brand}__prod__HERO", {"likes": 900, "saves": 120, "comments": 60, "shares": 40, "reach": 10000}, ts=1782600200)
    print(f"  z={r['z_score']}  action={r['action']}  → {r['action_detail']}")
    print("\nsignals for simbrand:")
    print(json.dumps(get_perf_signals(sim_brand), ensure_ascii=False, indent=2))
    print(f"\nproducer pre-flight check for the bombed setup: "
          f"{kr.get_pending_combo(sim_brand, 'prod', 'BOMB')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-id")
    ap.add_argument("--likes", type=int, default=0)
    ap.add_argument("--saves", type=int, default=0)
    ap.add_argument("--comments", type=int, default=0)
    ap.add_argument("--shares", type=int, default=0)
    ap.add_argument("--reach", type=int, default=0)
    ap.add_argument("--signals", help="show what perf learned for a brand handle")
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args()

    if a.simulate:
        _simulate()
        return
    if a.signals:
        print(json.dumps(get_perf_signals(a.signals), ensure_ascii=False, indent=2))
        return
    if not a.post_id:
        sys.exit("need --post-id (+ engagement) or --signals <brand> or --simulate")
    rec = ingest(a.post_id, {"likes": a.likes, "saves": a.saves, "comments": a.comments,
                             "shares": a.shares, "reach": a.reach})
    print(f"✅ {a.post_id}: er={rec['engagement_rate']} z={rec['z_score']} "
          f"paid_boost={rec['paid_boost']} action={rec['action']}")
    if rec["action_detail"]:
        print(f"   → {rec['action_detail']}")


if __name__ == "__main__":
    main()
