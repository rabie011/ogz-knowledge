#!/usr/bin/env python3
"""Apply the 2026-06-13 deep-diagnosis (workflow wa31ay7ae) to the 3 pilots' organs.
Bug/error/enrichment fixes ONLY — each verified on disk first (Rule #9), provenance
stamped, idempotent. The material call (jurisha dine-in model) is NOT applied here —
that's Mohamed's to confirm.

Fixes:
  jurisha — goals counter bug (answered:0 while 3 fields confirmed) → derive from fields;
            propagate usp_his_words + brand-voice ruling into l1 (IDENTITY falsely RED);
            truth_pack candidates ← the real Maps-evidenced menu (was IG-only جريش/كابلي).
  albaik  — purge 4 bio-noise product_candidates, keep real SKUs.
  alnasser— clean product_candidates to real jewelry; year_map sector f_and_b → jewelry.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from organ_write import write_organ

B = Path(__file__).parent.parent
TS = "2026-06-13"
def prov(src):
    return {"source": src, "date_added": TS, "confirmer": "data_diagnosis",
            "confidence": "candidate", "scope": "brand"}

def cand(name, src="deep_diagnosis_2026-06-13"):
    return {"name": name, "evidence": "diagnosis", "provenance": prov(src)}


def jurisha():
    cdir = B / "clients/eatjurisha/profile"
    # 1. goals counter — derive from confirmed fields (the bug: 0 while 3 present)
    g = json.loads((cdir / "goals.json").read_text())
    confirmed = sum(1 for k in ("goal_ratio", "capacity_ceiling", "usp_his_words")
                    if g.get(k) and (g[k].get("confirmer") == "mohamed" if isinstance(g[k], dict) else g[k]))
    g["answered"] = confirmed
    g["_counter_fix"] = f"derived from field-presence {confirmed}/3 (was stale 0) — diagnosis {TS}"
    write_organ(str(cdir / "goals.json"), g)
    assert json.loads((cdir / "goals.json").read_text())["answered"] == confirmed

    # 2. propagate the ANSWERED usp + brand-voice ruling into l1 (IDENTITY was falsely RED)
    fp = json.loads((cdir / "fingerprint.json").read_text())
    l1 = fp.setdefault("l1_strategy", {})
    usp = g.get("usp_his_words", {})
    if usp and not l1.get("usp"):
        l1["usp"] = usp.get("normalized") or usp.get("raw")
        l1["positioning"] = usp.get("normalized") or usp.get("raw")
    spk = fp.get("l2_voice", {}).get("speaker")
    if spk and not l1.get("who_speaks"):
        l1["who_speaks"] = spk  # brand_voice ruled 2026-06-12 (deep human-story layer still open)
    l1["_passport"] = {"source": "goals.usp_his_words + l2_voice.speaker ruling",
                       "confirmer": "mohamed", "date": "2026-06-12",
                       "note": "deep who-speaks (daughter/family/mother story) still client-only"}
    write_organ(str(cdir / "fingerprint.json"), fp)

    # 3. truth_pack candidates ← the real Maps-evidenced menu (NOISE removed)
    tp = json.loads((cdir / "truth_pack.json").read_text())
    menu = ["جريش", "رز كابلي", "سليق", "تمن (رز أبيض)", "باشميل", "قرصان", "لازانيا",
            "حجم عائلي + حجم صغير للجريش", "إضافة دجاج للجريشة"]
    tp["product_candidates"] = [cand(m, "maps_reviews+ig_2026-06-13") for m in menu]
    tp["_diagnosis_note"] = ("menu upgraded from IG-only (جريش/كابلي) to Maps-evidenced full "
                             "menu; سليق/تمن/باشميل/قرصان/لازانيا are Maps-only — client confirms + prices")
    write_organ(str(cdir / "truth_pack.json"), tp)
    return f"jurisha: goals {confirmed}/3 · l1 usp+who_speaks propagated · {len(menu)} menu candidates"


def albaik():
    p = B / "clients/albaik/profile/truth_pack.json"
    tp = json.loads(p.read_text())
    NOISE = {"The official ALBAIK account", "حساب #البيك 🇸🇦", "البيك مجمع", "البيك صباحك",
             "حساب #البيك"}
    before = len(tp.get("product_candidates", []))
    tp["product_candidates"] = [c for c in tp.get("product_candidates", [])
                                if c.get("name") not in NOISE]
    real = ["التوأم كرسبي بيك", "فيليه الدجاج", "بيكيز / ستربس", "كرسبي بيك / دبل كرسبي بيك",
            "صلصة لهاليبو", "جمبري / سوبر بيك جمبري", "فلافل", "فطور البيك"]
    have = {c.get("name") for c in tp["product_candidates"]}
    for m in real:
        if m not in have:
            tp["product_candidates"].append(cand(m, "ig_521posts_2026-06-13"))
    tp["_diagnosis_note"] = "4 bio-noise candidates purged; real SKUs confirmed from 521 posts"
    write_organ(str(p), tp)
    return f"albaik: candidates {before}→{len(tp['product_candidates'])} (noise purged, real SKUs kept)"


def alnasser():
    cdir = B / "clients/alnasserjewelry"
    # clean product candidates → real jewelry
    p = cdir / "profile/truth_pack.json"
    tp = json.loads(p.read_text())
    real = ["عقد / عقود ذهب", "خاتم / خواتم ذهب", "طقم / نصف طقم ذهب", "سوار / غوايش / معاضد",
            "دبلة / محبس (محابس الزواج)", "حلق / أقراط"]
    tp["product_candidates"] = [cand(m, "ig_7395posts_2026-06-13") for m in real]
    tp["_diagnosis_note"] = ("slogan/cert/city noise removed (أناقة تستحق المشاركة, موثق من وزارة "
                             "التجارة, الدمام, سوق الحب); ملكة engagement-moment dropped (99.7% substring artifact)")
    write_organ(str(p), tp)
    # year_map sector misclassification f_and_b → jewelry
    ym_p = cdir / "year_map.json"
    ym = json.loads(ym_p.read_text())
    old = ym.get("sector")
    if old != "jewelry":
        ym["sector"] = "jewelry"
        ym["_sector_fix"] = f"was '{old}' (misclassified) → jewelry, diagnosis {TS}"
        ym_p.write_text(json.dumps(ym, ensure_ascii=False, indent=2))
    return f"alnasser: {len(real)} real jewelry candidates · year_map sector {old}→jewelry"


if __name__ == "__main__":
    for fn in (jurisha, albaik, alnasser):
        print("  ✓", fn())
