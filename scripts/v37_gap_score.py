#!/usr/bin/env python3
"""P4 — score each brand's v3.7 PROMPT-READINESS and stage the confirm-questions.

The gap engine, re-defined through the v3.7 lens: a "gap" is no longer only a missing
strategy organ — it's a v3.7 placeholder that is RED (client-only) or YELLOW (derived
candidate, needs confirm). Reads visual_dna.json, writes a `v37_visual` readiness block
into gap_report.json (the diagnosis), and emits CONSOLIDATED confirm-questions (≤3 per
brand — true-minimum, grouped, never per-field) to a STAGED file.

NOT pushed live (18 cards already open — Rule #10 don't-flood). Staged to flow in as the
portal queue drains (the low-queue bridge), deduped by id (Memory Law: never re-ask).

Usage: python3 scripts/v37_gap_score.py [--all]
"""
import json, sys
from datetime import datetime
from pathlib import Path

B = Path(__file__).parent.parent
TS = "2026-06-13"
PILOTS = ["albaik", "eatjurisha", "alnasserjewelry", "myfitness.sa"]
NAMES = {"albaik": "البيك", "eatjurisha": "جريش الرياض",
         "alnasserjewelry": "مجوهرات الناصر", "myfitness.sa": "ماي فتنس"}
STAGE = B / "data/v37_confirm_staged.json"


def status_of(sf):
    return sf.get("status") if isinstance(sf, dict) else None


def score(handle):
    p = B / "clients" / handle / "profile"
    vf = p / "visual_dna.json"
    if not vf.exists():
        return None
    vd = json.loads(vf.read_text())
    vb = vd.get("brand") or {}
    prods = vd.get("products") or []
    disp = NAMES.get(handle, handle)

    # tally per group
    red, yellow, green = [], [], []
    def walk(prefix, obj):
        if isinstance(obj, dict):
            if "status" in obj and obj["status"] in ("RED", "YELLOW", "GREEN"):
                {"RED": red, "YELLOW": yellow, "GREEN": green}[obj["status"]].append(prefix)
            else:
                for k, v in obj.items():
                    walk(f"{prefix}.{k}" if prefix else k, v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(f"{prefix}[{i}]", v)
    walk("brand", vb)
    for i, pr in enumerate(prods):
        walk(f"product[{i}]", pr)

    # consolidated questions (grouped, true-minimum)
    questions = []
    pal_unconfirmed = status_of((vb.get("palette") or {}).get("primary")) != "GREEN" or \
                      status_of(vb.get("color_field_palette")) != "GREEN"
    if pal_unconfirmed:
        prim = ((vb.get("palette") or {}).get("primary") or {}).get("value", "")
        cf = (vb.get("color_field_palette") or {}).get("value", "")
        questions.append({
            "id": f"v37_{handle}_palette", "group": "colour",
            "q": (f"ألوان البراند للصورة: نقترح اللون الأساسي = «{prim}»، وحقل اللون للخلفية = «{cf}». "
                  "صح؟ صححوا أو أعطونا الـ HEX الدقيق لو موجود."),
        })
    # products materials/dimensions confirm (one card, lists them)
    if prods:
        names = "، ".join(p.get("name", "") for p in prods[:8])
        questions.append({
            "id": f"v37_{handle}_products_phys", "group": "product_physical",
            "q": (f"المنتجات اللي بنصوّرها: {names}. لكل واحد نحتاج تأكيد: الخامة (لمعة/قماش/ذهب…) "
                  "والحجم التقريبي. أكّدوا أو صححوا."),
        })
    # identity + reference photo + wordmark (the RED lock)
    if prods:
        questions.append({
            "id": f"v37_{handle}_identity_ref", "group": "identity_lock",
            "q": ("قفل الهوية: لكل منتج نحتاج (١) صورة حقيقية وحدة هي نفس المنتج بالضبط — رابط/صورة، "
                  "(٢) الشعار/الكلمة بالعربي بالضبط كما يكتب. هذي ما نقدر نخمنها — لازم منكم."),
        })

    block = {
        "scored": TS, "schema": "openclaw_v3.7",
        "red": len(red), "yellow": len(yellow), "green": len(green),
        "red_fields": red[:20],
        "renderable": "yes — YELLOW candidates render as working defaults; RED carried by reference image",
        "confirm_questions": [q["id"] for q in questions],
    }
    # merge into gap_report
    grf = p / "gap_report.json"
    gr = json.loads(grf.read_text()) if grf.exists() else {"questions": []}
    gr["v37_visual"] = block
    grf.write_text(json.dumps(gr, ensure_ascii=False, indent=2))

    print(f"  {handle:18} v3.7 readiness — GREEN {len(green)} / YELLOW {len(yellow)} / RED {len(red)} "
          f"· {len(questions)} consolidated questions")
    return {"handle": handle, "disp": disp, "block": block, "questions": questions}


def main():
    results = [r for r in (score(h) for h in PILOTS) if r]
    # stage the consolidated cards (dedup by id), do NOT push live
    staged = {"staged": TS, "note": "v3.7 confirm-questions — flow to portal as queue drains; deduped by id",
              "cards": []}
    seen = set()
    for r in results:
        for q in r["questions"]:
            if q["id"] in seen:
                continue
            seen.add(q["id"])
            staged["cards"].append({
                "id": q["id"], "handle": r["handle"], "title": f"🎨 {r['disp']} — {q['group']}",
                "tag": "v3.7 Visual", "lane": "strategy", "kind": "text",
                "why": q["q"], "need": "اكتبوا الجواب — يعبّي visual_dna ويخلّي الصورة تطابق v3.7.",
                "organ": "visual_dna", "group": q["group"],
            })
    STAGE.write_text(json.dumps(staged, ensure_ascii=False, indent=2))
    print(f"\n  STAGED {len(staged['cards'])} v3.7 confirm-cards → {STAGE.relative_to(B)} "
          f"(NOT pushed — 18 already open; flow as queue drains)")
    assert len(staged["cards"]) <= 12, "too many cards — would flood"


if __name__ == "__main__":
    main()
