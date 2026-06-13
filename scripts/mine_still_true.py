#!/usr/bin/env python3
"""B019 — STILL-TRUE CHECKLIST: mine an expired archive for factual claims.

myfitness.sa: 372 posts, last one 2021-09-28 (4.7y silent). 100% of its truth is
EXPIRED — but the archive is the only source of what the brand USED to claim.
Each claim becomes a one-tap checklist line: the client confirms still-true / dead.
No claim enters the truth pack without that confirmation (truth law).

Deterministic pattern mining — claims, not vibes. Each item carries the verbatim
quote + post date (provenance, always).

Usage: python3 scripts/mine_still_true.py [handle]   (default myfitness.sa)
Output: clients/<handle>/presentations/still_true_checklist.md + .json
"""
import glob
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent

# claim patterns → checklist category (Arabic + English, the brand wrote both)
CLAIM_PATTERNS = [
    ("services", r"(تدريب|مدرب|كوتش|حصة|حصص|كلاس|برنامج|اشتراك|عضوية|جلسة|"
                 r"class(es)?|coach|train(ing|er)|session|subscription|membership|program)"),
    ("location_hours", r"(تبوك|فرع|موقعنا|عنوان|دوام|ساعات|نفتح|نغلق|من الساعة|"
                       r"Tabuk|branch|location|open|hours|am|pm)"),
    ("prices_offers", r"(ريال|سعر|أسعار|عرض|خصم|مجان|باقة|باقات|"
                      r"SAR|SR|price|offer|discount|free|package)"),
    ("facilities", r"(صالة|نادي|أجهزة|معدات|مسبح|ساونا|مساحة|قسم نساء|قسم رجال|"
                   r"gym|studio|equipment|pool|sauna|ladies|women|men)"),
    ("contact_booking", r"(واتس|رقم|تواصل|حجز|احجز|للاستفسار|الرابط|سناب|"
                        r"whats ?app|dm|book|contact|link in bio|snap)"),
]


def main():
    handle = sys.argv[1] if len(sys.argv) > 1 else "myfitness.sa"
    raw_dirs = sorted(glob.glob(str(BASE / f"clients/{handle}/raw/instagram/*")))
    assert raw_dirs, f"no raw archive for {handle}"
    posts_f = Path(raw_dirs[-1]) / "posts.jsonl"
    posts = [json.loads(l) for l in posts_f.read_text(encoding="utf-8").splitlines() if l.strip()]

    claims = defaultdict(list)
    for p in posts:
        cap = (p.get("caption") or "").strip()
        ts = (p.get("timestamp") or "")[:10]
        if len(cap) < 10:
            continue
        for cat, pat in CLAIM_PATTERNS:
            m = re.search(pat, cap, re.IGNORECASE)
            if m:
                # the claim line = the sentence around the match, not the whole caption
                seg = next((s.strip() for s in re.split(r"[.\n!؟]", cap)
                            if m.group(0) in s), cap[:120])
                claims[cat].append({"quote": seg[:160], "date": ts, "term": m.group(0)})

    # dedupe near-identical claims per category (same normalized quote head)
    out = {}
    for cat, items in claims.items():
        seen, uniq = set(), []
        for it in sorted(items, key=lambda x: x["date"], reverse=True):
            key = re.sub(r"\s+", " ", it["quote"])[:60]
            if key not in seen:
                seen.add(key)
                uniq.append(it)
        out[cat] = uniq[:15]   # the checklist is for a human — cap per category

    pdir = BASE / f"clients/{handle}/presentations"
    pdir.mkdir(exist_ok=True)
    last_post = max((p.get("timestamp") or "" for p in posts), default="")[:10]
    # identity facts the archive DOES carry (hashtags + named-person captions) — for a
    # claim-poor archive these few lines are the whole harvest, say so honestly
    idn = []
    all_tags = {t.strip("\u202c\u2069") for p in posts for t in (p.get("hashtags") or [])}
    if any("لياقتي" in t for t in all_tags):
        idn.append({"quote": "الاسم: مركز لياقتي (هاشتاق المركز نفسه)", "date": last_post})
    if any("تبوك" in t for t in all_tags):
        idn.append({"quote": "المدينة: تبوك (#تبوك + #تبوك_الان + بايو «يا أهل تبوك»)", "date": last_post})
    if any("جامعة_تبوك" in t for t in all_tags):
        idn.append({"quote": "قرب/علاقة بجامعة تبوك (#جامعة_تبوك) — يؤكدها العميل", "date": last_post})
    captains = sorted({m for c2 in (p.get("caption") or "" for p in posts)
                       for m in re.findall(r"الكابتن\s+(\S+)", c2)})
    if captains:
        idn.append({"quote": f"مدربون بالاسم وقتها: {('، '.join('الكابتن ' + c3 for c3 in captains))} — "
                             "موجودون اليوم؟ (4.7 سنة مرت)", "date": last_post})
    if any("كمال الاجسام" in (p.get("caption") or "") for p in posts):
        idn.append({"quote": "التخصص الظاهر: كمال أجسام / قسم رجال — ما زال التركيز؟", "date": last_post})
    if idn:
        out["identity_from_archive"] = idn
    (pdir / "still_true_checklist.json").write_text(json.dumps({
        "generated": datetime.now().isoformat(timespec="seconds"),
        "handle": handle, "posts_mined": len(posts), "last_post": last_post,
        "doc": "every claim needs the client's still-true/dead tap before it can enter "
               "the truth pack — the archive is 100% expired",
        "claims": out}, ensure_ascii=False, indent=1))


    lines = [f"# {handle} — STILL TRUE? checklist",
             f"*mined {len(posts)} posts (archive ends {last_post} — everything below is "
             f"{round((datetime.now() - datetime.fromisoformat(last_post)).days / 365, 1)} years old "
             "and needs the client's confirmation)*", ""]
    AR = {"services": "الخدمات والاشتراكات", "location_hours": "الموقع والدوام",
          "prices_offers": "الأسعار والعروض", "facilities": "المرافق",
          "contact_booking": "التواصل والحجز", "identity_from_archive": "هوية من الأرشيف"}
    total_claims = sum(len(v) for v in out.values())
    if total_claims < 12:
        lines.append("> ⚠️ **الأرشيف فقير بالحقائق**: "
                     f"{sum(1 for p in posts if (p.get('caption') or '').strip())}/{len(posts)} "
                     "بوست فقط فيها كابشن، وأغلبها قصير. هذي القائمة ليست بديل مكالمة العميل — "
                     "حقيقة myfitness لازم تجي من العميل مباشرة.\n")
    for cat, items in out.items():
        lines.append(f"## {AR.get(cat, cat)} ({len(items)})")
        for it in items:
            lines.append(f"- ☐ «{it['quote']}» *(آخر ظهور {it['date']})*")
        lines.append("")
    (pdir / "still_true_checklist.md").write_text("\n".join(lines))

    total = sum(len(v) for v in out.values())
    print(f"mined {len(posts)} posts → {total} unique claims across {len(out)} categories")
    for cat, items in out.items():
        print(f"  {cat}: {len(items)}")
    assert total > 0, "zero claims AND zero identity facts — patterns are wrong"


if __name__ == "__main__":
    main()
