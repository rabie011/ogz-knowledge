#!/usr/bin/env python3
"""VISUAL GATE CHECKLIST (FLANK-01 deterministic half, June 11).
The ruling (AI image of a real product = truth or lie?) is PARKED for Mohamed.
Interim law from the pyramid: HUMAN EYES ARE THE VISUAL GATE. This gives those
eyes a fixed tool — a deterministic pre-publish checklist per post card, built
ONLY from data we hold (cultural override fields, client red lines, forbidden
lists, the parked ruling itself). No AI judges anything. The human ticks boxes.

Usage: python3 scripts/visual_gate_checklist.py --handle albaik [--all]
"""
import argparse, json, glob, sys
from pathlib import Path

BASE = Path(__file__).parent.parent

# the ~10 brand-must-override cultural fields, pinned strictest until the client relaxes
STRICT_CHECKS = [
    ("faces", "لا وجوه ظاهرة (الافتراضي الصارم — ما لم يرخّص العميل كتابةً)"),
    ("family_visibility", "لا أفراد عائلة العميل في الصورة (ترخيص العميل فقط)"),
    ("mixed_gender", "لا اختلاط رجال/نساء في مشهد واحد (الافتراضي العائلي)"),
    ("modesty", "اللبس محتشم بالمعيار السعودي المحافظ"),
    ("music_context", "إن كان فيديو: المقطع بلا موسيقى أو بإيقاع مسموح"),
]
FOOD_CHECKS = [
    ("left_hand", "لا تقديم/تناول طعام باليد اليسرى في أي لقطة"),
    ("alcohol_lookalike", "لا كؤوس/قوارير توحي بمشروبات محظورة"),
]
ALWAYS = [
    ("brand_truth", "كل منتج ظاهر = منتج حقيقي للعميل (طابق مع truth_pack)"),
    ("text_in_image", "أي نص داخل الصورة: إملاء سليم + لا ادعاء عرض/سعر غير مؤكد"),
    ("ai_render_parked", "⛔ هل الصورة AI لمنتج حقيقي؟ الحكم محفوظ لمحمد — لا تنشر صور منتجات AI حتى يحكم"),
]


def checklist_for(handle: str, card: dict) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    red = json.loads((pdir / "red_lines.json").read_text())
    state = json.loads((pdir / "state.json").read_text())
    sector = json.loads((BASE / "clients" / handle / "year_map.json").read_text()).get("sector", "")
    items = [{"id": k, "check": v, "source": "cultural_spec strictest default"} for k, v in STRICT_CHECKS]
    if sector == "f_and_b":
        items += [{"id": k, "check": v, "source": "forbidden_lists (food)"} for k, v in FOOD_CHECKS]
    items += [{"id": k, "check": v, "source": "truth/parked-ruling"} for k, v in ALWAYS]
    for i, line in enumerate(red.get("lines", [])):
        items.append({"id": f"client_red_{i}", "check": f"خط أحمر من العميل: {line}", "source": "client verbatim"})
    return {"law": "HUMAN EYES ARE THE VISUAL GATE — automated checks may BLOCK, never PASS",
            "client_state": state["state"],
            "scene_being_checked": (card.get("idea") or {}).get("scene_ar", "")[:120],
            "items": items,
            "verdict": {"checked_by": None, "date": None, "all_clear": None,
                          "note": "unchecked checklist = unpublishable card"}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(BASE / "clients" / a.handle / "posts" / "*.json")))
    if not a.all:
        files = files[:3]
    done = 0
    for f in files:
        card = json.loads(open(f).read())
        if "visual_gate" in card:
            continue
        card["visual_gate"] = checklist_for(a.handle, card)
        Path(f).write_text(json.dumps(card, ensure_ascii=False, indent=2))
        done += 1
    print(f"✓ {a.handle}: visual gate attached to {done}/{len(files)} cards")
    if files:
        c = json.loads(open(files[0]).read())
        vg = c["visual_gate"]
        print(f"  sample ({Path(files[0]).name}): {len(vg['items'])} checks")
        for it in vg["items"][:4]:
            print(f"   ☐ {it['check'][:80]}")


if __name__ == "__main__":
    main()
