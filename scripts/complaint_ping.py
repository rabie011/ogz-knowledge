#!/usr/bin/env python3
"""B014 — COMPLAINT-DETECTED SERVICE PING: street reviews → a client-value insight.

The consultative moat: we read the client's street (Maps reviews) and bring them an
insight their feed can't see — «your pain is SERVICE, not food». This generates the
ping as an INTERNAL presentation draft per client (presentations/service_ping.md)
+ data/service_pings.json (read by the morning brief). NO card is staged and NOTHING
goes near a client: B201 (albaik outreach ruling — dry-run vs real contact) is an
OPEN mohamed_must; until he rules, drafts stay internal. (Docstring corrected June 13
— the earlier «stages a card» claim was false: self-audit law.)

Thresholds (counts, never feelings):
  ping-worthy   — top complaint ≥ 3% of total reviews AND ≥ 10 absolute
  star-alarm    — 1-star share ≥ 15%

Deterministic, recompute-idempotent. Usage: python3 scripts/complaint_ping.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base

AR = {"service": "الخدمة", "slow": "البطء", "quality_drop": "نزول الجودة",
      "cold_food": "الأكل البارد", "انتظار": "الانتظار", "price": "السعر"}


def main():
    b = base()
    rd = b / "data/reviews_digest.json"
    if not rd.exists():
        raise SystemExit("no reviews_digest.json — run the reviews sweep first")
    digest = json.loads(rd.read_text())
    pings = []
    for handle, d in digest.items():
        total = d.get("total", 0)
        if not total:
            continue
        comps = {k: v for k, v in (d.get("complaints") or {}).items() if v}
        if not comps:
            continue
        top_k, top_n = max(comps.items(), key=lambda kv: kv[1])
        one_star = int(d.get("stars", {}).get("1", 0))
        ping_worthy = top_n >= 10 and (top_n / total) >= 0.03
        star_alarm = total >= 50 and (one_star / total) >= 0.15
        if not (ping_worthy or star_alarm):
            continue
        five = int(d.get("stars", {}).get("5", 0))
        lines = [
            f"# {handle} — صوت الشارع (مراجعات الخرائط)",
            f"*مبني على {total} مراجعة عامة · توليد آلي {datetime.now().isoformat(timespec='minutes')} — "
            "مسودة داخلية: لا تُرسل للعميل إلا بموافقة محمد*", "",
            f"## الخلاصة بسطر",
            f"**الوجع الأول: {AR.get(top_k, top_k)}** ({top_n} شكوى) — مو الأكل. "
            f"النجمة الواحدة: {one_star}/{total} ({round(one_star/total*100)}%).", "",
            "## الأرقام",
            f"- ⭐ التوزيع: 5★={five} · 1★={one_star} (من {total})",
        ]
        for k, v in sorted(comps.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {AR.get(k, k)}: {v}")
        lines += ["", "## ليش يهم المحتوى؟",
                  f"المحتوى يبيع تجربة، والشارع يقول التجربة تنكسر عند {AR.get(top_k, top_k)}. "
                  "بوست يوعد بسرعة/خدمة وهي مكسورة = حرق ثقة. التقويم يحتاج يتجنب وعود "
                  f"{AR.get(top_k, top_k)} لين تتحسن، ويركز على نقاط القوة المثبتة (5★ غالبة)."]
        pdir = b / "clients" / handle / "presentations"
        pdir.mkdir(exist_ok=True)
        (pdir / "service_ping.md").write_text("\n".join(lines))
        pings.append({"handle": handle, "top_complaint": top_k, "n": top_n,
                      "one_star_pct": round(one_star / total * 100),
                      "path": f"clients/{handle}/presentations/service_ping.md"})
        print(f"  📍 {handle}: {top_k} ×{top_n} · 1★ {round(one_star/total*100)}% → service_ping.md")
    (b / "data/service_pings.json").write_text(json.dumps(
        {"generated": datetime.now().isoformat(timespec="seconds"), "pings": pings},
        ensure_ascii=False, indent=1))
    if not pings:
        print("  no client crosses the ping threshold")
    print(f"🟢 {len(pings)} ping(s) drafted (internal — Mohamed's gate before any client sees one)")


if __name__ == "__main__":
    main()
