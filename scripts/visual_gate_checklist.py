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

sys.path.insert(0, str(Path(__file__).parent))
# B144 — PERSON_AR is the ONE source (truth_guards), shared with post_audit/render.
# Never redefine an honorific-name detector here (one-boundary law).
from truth_guards import PERSON_AR

BASE = Path(__file__).parent.parent

# the deadly-defaults table (B105) — single source of truth for the strict checks
DEADLY_DEFAULTS_TABLE = BASE / "15_cultural_specs" / "defaults" / "brand_override_defaults_v1.yaml"

# fallback ONLY if the table file is missing — must stay in sync with the table's visual_gate rows
STRICT_CHECKS = [
    ("faces", "لا وجوه ظاهرة (الافتراضي الصارم — ما لم يرخّص العميل كتابةً)"),
    ("family_visibility", "لا أفراد عائلة العميل في الصورة (ترخيص العميل فقط)"),
    ("mixed_gender", "لا اختلاط رجال/نساء في مشهد واحد (الافتراضي العائلي)"),
    ("modesty", "اللبس محتشم بالمعيار السعودي المحافظ"),
    ("music_context", "إن كان فيديو: المقطع بلا موسيقى أو بإيقاع مسموح"),
]


def load_strict_checks():
    """Read the strict checks from the deadly-defaults table (rows carrying
    visual_gate_check_ar). Falls back to the hardcoded STRICT_CHECKS if the
    file is missing or unreadable — behavior stays identical either way."""
    try:
        import yaml
        rows = yaml.safe_load(DEADLY_DEFAULTS_TABLE.read_text())["fields"]
        checks = [(r["visual_gate_id"], r["visual_gate_check_ar"])
                  for r in rows if r.get("visual_gate_check_ar")]
        return checks or STRICT_CHECKS
    except Exception:
        return STRICT_CHECKS
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
    items = [{"id": k, "check": v, "source": "cultural_spec strictest default"} for k, v in load_strict_checks()]
    if sector == "f_and_b":
        items += [{"id": k, "check": v, "source": "forbidden_lists (food)"} for k, v in FOOD_CHECKS]
    items += [{"id": k, "check": v, "source": "truth/parked-ruling"} for k, v in ALWAYS]
    # B144 — person-mention check: a caption naming a real TITLED person
    # (الأمير/الشيخ/الدكتور/معالي/سمو + اسم) is a trust land-mine; "named real people" is a
    # recorded kill (Rule #13). The human MUST verify before publish — promised at
    # render_client_slot.py:209, implemented here.
    named = []
    for c in (card.get("captions") or []):
        if isinstance(c, str):
            named += [m.group(0).strip() for m in PERSON_AR.finditer(c)]
    if named:
        uniq = list(dict.fromkeys(named))
        items.append({"id": "person_named",
                      "check": "REQUIRES-HUMAN-VERIFY: شخص حقيقي مُسمّى في النص — " + "، ".join(uniq[:5]),
                      "source": "truth_guards.PERSON_AR (B144)"})
    for i, line in enumerate(red.get("lines", [])):
        items.append({"id": f"client_red_{i}", "check": f"خط أحمر من العميل: {line}", "source": "client verbatim"})
    return {"law": "HUMAN EYES ARE THE VISUAL GATE — automated checks may BLOCK, never PASS",
            "client_state": state["state"],
            "scene_being_checked": (card.get("idea") or {}).get("scene_ar", "")[:120],
            "items": items,
            "verdict": {"checked_by": None, "date": None, "all_clear": None,
                          "note": "unchecked checklist = unpublishable card"}}


def human_rejected(card: dict) -> bool:
    """CONSUMER of the visual-gate human verdict (B143 slice, June 19 — Rule #6).
    The checklist WRITES verdict.all_clear but nothing read it: a card a human
    explicitly REJECTED (all_clear == False) could still re-enter the judging batch
    that reaches Mohamed (Rule #13 chokepoint). True iff a human looked and said NO.
    all_clear None (unchecked) / True (cleared) / no gate attached are NOT rejections —
    the unchecked tick gates final PUBLISH downstream, not the pre-publish judging batch."""
    return ((card.get("visual_gate") or {}).get("verdict") or {}).get("all_clear") is False


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
