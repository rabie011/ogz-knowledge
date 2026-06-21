#!/usr/bin/env python3
"""B164 — FEED-vs-DOOR DIVERGENCE → reputation_alert + warm-kitchen WARN.

The brand's FEED promises a warm experience; the DOOR (Maps reviews) may say the
food arrives COLD or the rating is weak. When the street and the feed diverge, a
caption that leans on warm-home / just-out-of-the-oven / "served hot" imagery
over-promises EXACTLY where the brand is fragile → a soft WARN (not a kill: Rule #8
reserves EXIT for verified rule-breaks; reputation is signal, not law).

Writer (already exists): data/reviews_digest.json (reviews_digest.py — the deterministic
street read; counts «بارد/باردة» as cold_food).
Consumers (Rule #6 — built THIS cycle, never a write-only organ):
  1. clients/{handle}/gap_report.json   ← reputation_alert block (the diagnosis Mohamed reads)
  2. post_audit.audit_post()            ← reputation_warm_kitchen_warn issue (soft, _warn-suffixed)

Thresholds (counts, never feelings — Rule #9):
  cold-door  — cold_food ≥ 5 absolute AND cold_food/with_text ≥ 1%   (repeated «بارد»)
  weak-star  — avg stars < 3.5 (computed from the star distribution) AND total ≥ 50

Deterministic, recompute-idempotent. Usage: python3 scripts/reputation_alert.py
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIGEST_PATH = BASE / "data" / "reviews_digest.json"
ALERTS_PATH = BASE / "data" / "reputation_alerts.json"

COLD_MIN_ABS = 5
COLD_MIN_SHARE = 0.01
WEAK_STAR_MAX = 3.5
WEAK_STAR_MIN_TOTAL = 50

# Warm-home / fresh-from-oven / served-hot imagery — what a cold-door brand must not over-promise.
WARM_KITCHEN = re.compile(
    r"دافئ|الدفء|دفا|ساخن|سخّ|سخن|حامي|طازج من الفرن|طالع من الفرن|خارج الفرن|"
    r"من قلب المطبخ|مطبخ البيت|دفء البيت|لسه حار|لسة حار|على نار|طازة من الفرن",
)


def avg_stars(stars: dict) -> float | None:
    """Weighted average from a {star: count} distribution. None if no rated reviews."""
    tot = sum(int(v) for v in stars.values())
    if tot <= 0:
        return None
    return sum(int(k) * int(v) for k, v in stars.items()) / tot


def compute(digest: dict) -> dict:
    """digest = reviews_digest.json content. Returns {handle: alert} for TRIGGERED handles only."""
    alerts = {}
    for handle, d in digest.items():
        stars = d.get("stars") or {}
        total = int(d.get("total", 0))
        with_text = int(d.get("with_text", 0))
        cold = int((d.get("complaints") or {}).get("cold_food", 0))
        avg = avg_stars(stars)
        triggers = []
        if with_text and cold >= COLD_MIN_ABS and cold / with_text >= COLD_MIN_SHARE:
            triggers.append("cold_door")
        if avg is not None and total >= WEAK_STAR_MIN_TOTAL and avg < WEAK_STAR_MAX:
            triggers.append("weak_star")
        if not triggers:
            continue
        alerts[handle] = {
            "handle": handle,
            "triggers": triggers,
            "avg_stars": round(avg, 2) if avg is not None else None,
            "cold_food": cold,
            "with_text": with_text,
            "cold_share": round(cold / with_text, 4) if with_text else 0.0,
            "one_star": int(stars.get("1", 0)),
            "total": total,
            "severity": "warn",
        }
    return alerts


def load_alerts(path: Path | None = None) -> dict:
    p = path or ALERTS_PATH
    if not Path(p).exists():
        return {}
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return {}


def warm_kitchen_warn(handle: str, caption: str, alerts: dict | None = None) -> str | None:
    """A cold-door brand + a warm-kitchen caption = the divergence over-promise → WARN detail, else None."""
    alerts = load_alerts() if alerts is None else alerts
    a = alerts.get(handle)
    if not a or "cold_door" not in a.get("triggers", []):
        return None
    m = WARM_KITCHEN.search(caption or "")
    if not m:
        return None
    return (f"warm-kitchen imagery «{m.group(0)}» but the street says cold "
            f"({a['cold_food']}/{a['with_text']} «بارد») — over-promise where the brand is fragile")


def warm_kitchen_for_post(handle: str, caps, alerts: dict | None = None) -> str | None:
    """First warm-kitchen WARN across a post's captions (used by post_audit). None if clean."""
    alerts = load_alerts() if alerts is None else alerts
    for c in caps or []:
        w = warm_kitchen_warn(handle, c, alerts)
        if w:
            return w
    return None


def for_gap_report(handle: str, alerts: dict) -> dict | None:
    """The reputation_alert block to embed in the diagnosis gap_report.json."""
    a = alerts.get(handle)
    if not a:
        return None
    parts = []
    if "cold_door" in a["triggers"]:
        parts.append(f"وصلت باردة: {a['cold_food']} من {a['with_text']} مراجعة "
                     f"({round(a['cold_share']*100)}%) — تجنّب وعود السخونة/الطزاجة في الفيد")
    if "weak_star" in a["triggers"]:
        parts.append(f"التقييم {a['avg_stars']}★ ({a['one_star']} نجمة واحدة من {a['total']}) — "
                     "السمعة هشّة، المحتوى ما يعالج الشارع")
    return {
        "triggers": a["triggers"],
        "severity": a["severity"],
        "avg_stars": a["avg_stars"],
        "cold_food": a["cold_food"],
        "with_text": a["with_text"],
        "summary_ar": " · ".join(parts),
    }


def main():
    if not DIGEST_PATH.exists():
        raise SystemExit("no data/reviews_digest.json — run scripts/reviews_digest.py first")
    digest = json.loads(DIGEST_PATH.read_text())
    alerts = compute(digest)
    ALERTS_PATH.write_text(json.dumps(alerts, ensure_ascii=False, indent=2))

    # CONSUMER WIRE (Rule #6): inject the reputation_alert block into each client's gap_report.json.
    injected = []
    for handle in alerts:
        grf = BASE / "clients" / handle / "gap_report.json"
        if not grf.exists():
            continue
        gr = json.loads(grf.read_text())
        block = for_gap_report(handle, alerts)
        if gr.get("reputation_alert") != block:  # idempotent: only rewrite on change
            gr["reputation_alert"] = block
            grf.write_text(json.dumps(gr, ensure_ascii=False, indent=2))
        injected.append(handle)

    summary = ", ".join(h + ":" + "+".join(a["triggers"]) for h, a in alerts.items()) or "none"
    print(f"reputation_alert: {len(alerts)} triggered ({summary}) "
          f"→ {ALERTS_PATH.name}; gap_report wired for {injected or 'none'}")


if __name__ == "__main__":
    main()
