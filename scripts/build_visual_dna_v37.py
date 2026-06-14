#!/usr/bin/env python3
"""P3 — PRODUCE the v3.7 visual-DNA fields and fill the brand organs.

Replaces the old past-stats visual-DNA builder with one that emits the PRESCRIPTIVE v3.7
fields the converter consumes, in the brand_visual_dna_v37_v1 schema shape. Uses the canon's
OWN derivation logic (the same tables openclaw_convert uses). Every value is honestly tagged:
  GREEN  — read from a confirmed organ field on disk (a real fact)
  YELLOW — agent-derived candidate via the canon's logic (renderable default; never silently
           promoted to confirmed — RABIE/Mohamed anti-hallucination law)
  RED    — client-only truth no logic can invent (exact hex, wordmark, deep identity)
RED/YELLOW fields are exactly what the gap engine turns into confirm-questions.

Writes clients/<h>/profile/visual_dna.json, validated against the schema (prove before go).

Usage: python3 scripts/build_visual_dna_v37.py [--handle albaik] [--all]
"""
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).parent))
import openclaw_convert as oc   # reuse COMPANION/MATERIAL/DIMENSIONS/COLOR_FIELD/CAPTURE/_sectorize/load_brand

B = Path(__file__).parent.parent
SCHEMA = json.loads((B / "12_data_shapes/brand_visual_dna_v37_v1.schema.json").read_text())
TS = "2026-06-13"
PILOTS = ["albaik", "eatjurisha", "alnasserjewelry", "myfitness.sa"]


def prov(confirmer, confidence, scope, source):
    return {"source": source, "date_added": TS, "confirmer": confirmer,
            "confidence": confidence, "scope": scope}


def G(value, source):   # GREEN — confirmed organ fact
    return {"value": value, "status": "GREEN", "provenance": prov("data_organ", "confirmed", "brand", source)}

def Y(value, example=None):   # YELLOW — derived candidate
    f = {"value": value, "status": "YELLOW",
         "provenance": prov("agent_derived", "candidate", "brand", "openclaw_v3.7 derivation logic")}
    if example:
        f["example"] = example
    return f

def R(value=None):   # RED — client-only
    return {"value": value, "status": "RED",
            "provenance": prov("", "experimental", "brand", "client_only — cannot be inferred")}


def looks_real_product(name: str) -> bool:
    n = (name or "").strip()
    if not n or len(n) > 30 or len(n.split()) > 5:
        return False
    return not re.search(r"account|official|موثق|توصيل|اطلب|الدمام|الرياض|جدة|حساب|🇸🇦|⚜️|📦|♥|تستحق|اكسبرس|مجمع|صباحك", n)


def build(handle):
    brand = oc.load_brand(handle)
    pk, sector = oc._sectorize(brand)
    media = sorted((B / "clients" / handle / "media").glob("*.jpg"))[:5]

    # ── brand block ──
    brand_block = {
        "region": Y("KSA — " + (brand.get("dialect") or "gulf") + " register"),
        "tone_register": (G(brand["tone"], "fingerprint.l2_voice.tone") if brand.get("tone") else Y("celebratory")),
        "quality_tier": Y("universal"),
        "price_position": Y("mid-market"),
        "modesty_register": Y("STRICT (Saudi default — modest, no skin, no mixed-gender intimacy)"),
        "palette": {
            "primary": Y(oc.PALETTE_PRIMARY.get(pk, oc.PALETTE_PRIMARY["default"]),
                         example="exact hex is RED until client confirms"),
            "background_tone": Y("clean brand-owned neutral; not clinical white unless the brand owns it"),
        },
        "color_field_palette": Y(oc.COLOR_FIELD.get(pk) or oc.COLOR_FIELD.get(sector, oc.COLOR_FIELD["default"])),
        "capture_character": Y(oc.CAPTURE["default"]),
        "anti_attributes": (G(oc._anti(brand), "red_lines + cultural defaults") if brand.get("red_lines")
                            else Y(oc._anti(brand))),
    }

    # ── products ──
    real = [p for p in (brand.get("products") or []) if looks_real_product(p)][:8]
    products = []
    for name in real:
        products.append({
            "name": name,
            "identity_dna": R(f"«CLIENT: locked identity of {name} — reference image carries it; confirm wordmark/colour/form»"),
            "silhouette_description": Y(f"the recognizable form of {name}"),
            "material_finish": Y(oc.MATERIAL.get(pk, oc.MATERIAL["default"]).split(";")[0]),
            "material_texture": Y(oc.MATERIAL.get(pk, oc.MATERIAL["default"])),
            "dimensions": Y(oc.DIMENSIONS.get(pk, oc.DIMENSIONS["default"])),
            "companion_elements": Y(oc.COMPANION.get(pk, oc.COMPANION["default"])),
            "label_text_arabic": R(brand["name"]),   # candidate guess, but RED: wordmark = highest-risk, confirm every gen
            "label_text_latin": R(None),
            "reference_images": [],   # RED gap: which media shows THIS product needs human/vision — pick_reference fallback handles render
            "provenance": prov("agent_derived", "candidate", "product", "openclaw_v3.7 derivation"),
        })

    rec = {
        "schema_version": "brand_visual_dna_v37_v1",
        "brand_ulid": f"vdna_{handle}",
        "brand_name_normalized": brand["name"],
        "sector": sector,
        "brand": brand_block,
        "products": products,
        "provenance": prov("agent_derived", "candidate", "brand", "build_visual_dna_v37.py"),
        "_alignment": "openclaw_v3.7",
        "_media_pool": [str(m.relative_to(B)) for m in media],
        "_note": "v3.7 visual DNA — YELLOW=renderable candidate, RED=client-confirm. Feeds openclaw_convert + gap engine.",
    }

    # prove before go
    errs = list(Draft202012Validator(SCHEMA).iter_errors(rec))
    assert not errs, f"{handle} visual_dna fails schema: {errs[:2]}"
    out = B / "clients" / handle / "profile" / "visual_dna.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2))

    # status tally
    def tally(d, acc):
        if isinstance(d, dict):
            if "status" in d and d.get("status") in ("GREEN", "YELLOW", "RED"):
                acc[d["status"]] += 1
            else:
                for v in d.values():
                    tally(v, acc)
        elif isinstance(d, list):
            for v in d:
                tally(v, acc)
        return acc
    t = tally(rec, {"GREEN": 0, "YELLOW": 0, "RED": 0})
    print(f"  ✓ {handle:18} {len(products)} products · GREEN {t['GREEN']} / YELLOW {t['YELLOW']} / RED {t['RED']} · schema ✅")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    handles = [a.handle] if a.handle else (PILOTS if a.all else PILOTS)
    total = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for h in handles:
        if (B / "clients" / h / "profile").exists():
            t = build(h)
            for k in total:
                total[k] += t[k]
    print(f"  TOTAL: GREEN {total['GREEN']} / YELLOW {total['YELLOW']} / RED {total['RED']} "
          f"→ RED+YELLOW = the confirm-questions the gap engine will raise")


if __name__ == "__main__":
    main()
