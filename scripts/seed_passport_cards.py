#!/usr/bin/env python3
"""CLIENT PASSPORT INTAKE — gap-report-driven (June 13, v2 after Mohamed's correction:
«deginous the brand and extract everything first and THEN ask questions ... the
questions is not [a template]»). The questions come FROM each brand's diagnosis
(gap_report.json), NOT a hardcoded list. Rules honored:
  - Rule #11 diagnose→show→wait: only what's RED after extraction becomes a question.
  - MEMORY LAW: never ask what the data already answers (jurisha's channels are in her
    bio → skipped; her products are mined → "confirm", not "what are they").
  - Per brand: bio-noise candidates (albaik/alnasser) become an OPEN "what are your real
    products", real candidates (jurisha) become a CONFIRM-or-correct.

Each card is a free-text question on the SAME shared feedback link; answers flow through
apply_rulings.h_passport into the organs (RED→green), attributed to who answered.

Usage: python3 scripts/seed_passport_cards.py --handle eatjurisha
       python3 scripts/seed_passport_cards.py --handle eatjurisha --clear   (remove old cards first)
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import queue_decision as qd
from feedback_lib import base

NAMES = {"eatjurisha": "جريش الرياض", "albaik": "البيك", "alnasserjewelry": "مجوهرات الناصر"}

# canonical gap → (organ, keyword-match on gap_report questions, base prompt).
# We dedup the gap_report's noisy questions into these, keep the richest phrasing,
# and enrich truth/channels from the brand's actual extracted data.
CANON = [
    ("identity", "fingerprint", r"يتكلم|ينطق|يميزكم|USP|باسم البراند",
     "مين يتكلم باسم البراند (البراند / صاحبه / شخصية)؟ ووش يميزكم عن أي منافس بسطر — بكلماتكم (الـUSP)؟"),
    ("goals", "goals", r"الهدف|نسبة العروض|بناء براند",
     "هدف الحساب: مبيعات مباشرة، بناء براند، ولا الاثنين؟ وكم بوست عروض من كل ١٠؟"),
    ("red_lines", "red_lines", r"الخطوط الحمراء|ما ننشر",
     "وش الشي اللي ما ننشره أبداً؟ (خطوط حمراء خاصة فيكم فوق الخطوط الثقافية)"),
    ("truth", "truth_pack", r"المنتجات|الأسعار",
     None),   # built per-brand below (confirm vs open)
    ("capacity", "goals", r"كم طلب|تستوعبون|طاقة",
     "كم طلب/عميل باليوم تقدرون تستوعبون؟ (يحدد كم نضغط على الطلب)"),
    ("competitors", "competitor_set", r"منافسين",
     "مين ٢-٣ منافسين تتابعونهم؟"),
]


def looks_real_product(name: str) -> bool:
    """A real product is a short noun, not a bio fragment / city / CTA / emoji line."""
    n = (name or "").strip()
    if len(n.split()) > 4:
        return False
    if re.search(r"account|official|موثق|توصيل|اطلب|الدمام|الرياض|جدة|حساب|🇸🇦|⚜️|📦|♥|تستحق", n):
        return False
    return bool(n) and len(n) <= 30


def already_answered(b, handle, field):
    """FIELD-PRESENCE check (June 13, RABIE's root fix): never re-ask what the organs
    already hold — the stale gap_report counter said 0/5 while goals were confirmed.
    Read the actual organ fields, not the counter (Memory Law: re-ask = trust death)."""
    pf = b / f"clients/{handle}/profile"
    g = json.loads((pf / "goals.json").read_text()) if (pf / "goals.json").exists() else {}
    fp = json.loads((pf / "fingerprint.json").read_text()) if (pf / "fingerprint.json").exists() else {}
    l1 = fp.get("l1_strategy", {})
    rl = json.loads((pf / "red_lines.json").read_text()).get("lines", []) if (pf / "red_lines.json").exists() else []
    return {
        "identity": bool(l1.get("who_speaks") and l1.get("usp")),
        "goals": bool(g.get("goal_ratio")),
        "capacity": bool(g.get("capacity_ceiling")),
        "red_lines": bool(rl),       # has ≥1 confirmed line → broad Q answered (narrow remains)
        "truth": False,              # always confirm/price the menu
        "competitors": False,        # client-only, never inferred
    }.get(field, False)


def build(handle: str):
    b = base()
    disp = NAMES.get(handle, handle)
    gr = json.loads((b / f"clients/{handle}/profile/gap_report.json").read_text())
    gap_text = " || ".join(gr.get("questions", []))
    answered = {f: already_answered(b, handle, f) for f in
                ("identity", "goals", "capacity", "red_lines", "truth", "competitors")}
    tp = json.loads((b / f"clients/{handle}/profile/truth_pack.json").read_text())
    cands = [c.get("name") for c in tp.get("product_candidates", [])]
    real = [c for c in cands if looks_real_product(c)]
    channels = [c.get("name") for c in (tp.get("channels") or []) if c.get("name") != "linktree"]

    staged, skipped = [], []
    for field, organ, kw, base_prompt in CANON:
        # only ask if this gap is actually in the brand's diagnosis
        if not re.search(kw, gap_text):
            skipped.append((field, "not a gap for this brand"))
            continue
        # FIELD-PRESENCE: never re-ask what the organs already confirm (trust death)
        if answered.get(field):
            skipped.append((field, "ALREADY ANSWERED on disk — Memory Law, not re-asked"))
            continue
        prompt = base_prompt
        if field == "red_lines" and json.loads((b / f"clients/{handle}/profile/red_lines.json").read_text()).get("lines"):
            # broad red-line already given → ask only the NARROW remaining
            prompt = ("عندكم خط أحمر واحد مسجّل. غيره — فيه شي ثاني ما ننشره أبداً؟ "
                      "(وجوه العائلة؟ قصة صاحبة المشروع؟)")
        if field == "truth":
            if real:   # data found real products → CONFIRM, don't ask (Memory Law)
                prompt = (f"أكّدوا أو صحّحوا منتجاتكم الأساسية (من حساباتكم): {'، '.join(real[:6])} "
                          "— وأضيفوا الأسعار لو ممكن.")
            else:      # bio-noise only → the mining found nothing real → OPEN ask
                prompt = ("وش منتجاتكم/خدماتكم الأساسية الحقيقية اللي ننشر عنها؟ (بأسمائها + الأسعار لو ممكن) "
                          "— ما لقينا منتجات واضحة في حساباتكم.")
        cid = f"passport_{handle}_{field}"
        qd.push_attributed({
            "id": cid, "title": f"📋 {disp} — {field}",
            "tag": "Passport", "clock": "", "priority": "normal",
            "created": datetime.now().isoformat(timespec="seconds"), "status": "open",
            "kind": "text", "judge_lane": False, "lane": "strategy",
            "handle": handle, "organ": organ, "field": field,
            "why": prompt,
            "need": "اكتبوا الجواب بكلماتكم — يُحفظ حرفياً ويعبّي ملف العميل.",
            "did": f"سؤال من تشخيص {disp} نفسه (gap_report) — يعبّي العضو «{organ}».",
            "placeholder": "جوابكم هنا…",
        }, made_by="claude", via="scripts/seed_passport_cards.py",
           reason=f"gap-driven passport — {handle} {field}")
        staged.append(field)
    # channels: ONLY if the data doesn't already have them (don't ask what we know)
    if not channels:
        cid = f"passport_{handle}_channels"
        qd.push_attributed({
            "id": cid, "title": f"📋 {disp} — channels", "tag": "Passport", "clock": "",
            "priority": "normal", "created": datetime.now().isoformat(timespec="seconds"),
            "status": "open", "kind": "text", "judge_lane": False, "lane": "strategy",
            "handle": handle, "organ": "truth_pack", "field": "channels",
            "why": "وين يطلبون منكم؟ (تطبيق توصيل، واتساب، متجر، معرض؟)",
            "need": "اكتبوا القنوات — ما لقيناها في حساباتكم.",
            "did": f"قناة الطلب غير موجودة في بيانات {disp}.",
            "placeholder": "جوابكم هنا…",
        }, made_by="claude", via="scripts/seed_passport_cards.py", reason=f"gap-driven passport — {handle} channels")
        staged.append("channels")
    else:
        skipped.append(("channels", f"data HAS: {channels} — never ask (Memory Law)"))

    print(f"  {handle} ({disp}): staged {staged}")
    for f, why in skipped:
        print(f"    ⏭  skipped {f}: {why}")
    return staged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--clear", action="store_true", help="remove existing passport_<handle>_* cards first")
    a = ap.parse_args()
    b = base()
    if a.clear:
        qf = b / "data/decision_queue.json"
        q = json.loads(qf.read_text())
        before = len(q["items"])
        q["items"] = [i for i in q["items"] if not i["id"].startswith(f"passport_{a.handle}_")]
        qf.write_text(json.dumps(q, ensure_ascii=False, indent=1))
        print(f"  cleared {before - len(q['items'])} old passport cards for {a.handle}")
    build(a.handle)


if __name__ == "__main__":
    main()
