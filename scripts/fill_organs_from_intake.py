#!/usr/bin/env python3
"""PHASE 1 — fill_organs_from_intake: maps a flat self-service INTAKE FORM → the client organs,
WITHOUT a human hand-writing JSON. The piece that lets a new brand onboard itself (the verified
gap: albaik/jurisha organs were hand-built; myfitness.sa sits EMPTY because no human filled it).

Designed + fact-checked with DeepSeek (the Scale On-ramp, Phase 1). The critical fact: organ_write.py
already exists as the ONE atomic, versioned, NEVER-deletes writer — so this module does NOT rewrite
persistence; it builds the organ dicts from the form and FEEDS write_organ(). Every write is
versioned (.versions/) so nothing is ever lost (honors Mohamed's "delete nothing").

Provenance: a self-service answer is the CLIENT's confirmed truth → confirmer="client",
confidence="confirmed" (the client said it). Research-derived fields stay experimental (filled by
research_fill_established, not here).

Intake form shape (flat JSON the self-service UI produces):
{
  "handle": "mynewcafe",
  "brand_ar": "اسم البراند",
  "identity": "Modern Saudi comfort food",
  "sector": "f_and_b",
  "products": [{"name":"...", "identity_dna":"...", "signature":"...", "texture":"...",
                "components":[...], "format":"burger"}],
  "visual_dna": {"palette":["#..."], "modesty_register":"conservative", "quality_tier":"premium"},
  "cultural_overrides": {"face_visibility":"never|faceless|visible", "mixed_gender_scenes":false,
                         "modesty_dress":"conservative"},
  "red_lines": ["no alcohol", "..."]
}

Usage:
  from fill_organs_from_intake import fill_all_organs
  written = fill_all_organs(form_dict)               # writes to clients/<handle>/profile/*.json
  python3 scripts/fill_organs_from_intake.py --form /tmp/mynewcafe_intake.json
  python3 scripts/fill_organs_from_intake.py --form ... --base /tmp/test   # test to a sandbox dir
"""
import argparse
import json
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
from organ_write import write_organ   # the ONE write path: atomic, versioned, never-deletes


def _prov(confirmer="client", confidence="confirmed", source="intake_form"):
    """The 5-field provenance mixin every record carries (the data law)."""
    return {"source": source, "date_added": time.strftime("%Y-%m-%d"),
            "confirmer": confirmer, "confidence": confidence, "scope": "brand"}


def _profile_dir(handle: str, base: Path = None) -> Path:
    root = (base or B) / "clients" / handle / "profile"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_product_truth(handle: str, products: list, base: Path = None) -> str:
    """Form products → product_truth.json (nested {"products":{}} shape, the jurisha-style the
    render assembly-lock reads — verified June 24). Each product keyed by its name."""
    out = {"_meta": {"organ": "product_truth", "handle": handle, "built": time.strftime("%Y-%m-%d"),
                     "_prov": _prov(), "keys_source": "self_service_intake_form"},
           "products": {}}
    for p in products or []:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        out["products"][name] = {
            "identity_dna": p.get("identity_dna", ""),
            "components": p.get("components", []),
            "signature": p.get("signature", ""),
            "texture": p.get("texture", ""),
            "format": p.get("format", ""),
        }
    path = _profile_dir(handle, base) / "product_truth.json"
    write_organ(path, out)
    return str(path)


def write_visual_dna(handle: str, vdna: dict, base: Path = None) -> str:
    vdna = vdna or {}
    out = {"_meta": {"organ": "visual_dna", "handle": handle, "_prov": _prov()},
           "palette": vdna.get("palette", []),
           "modesty_register": vdna.get("modesty_register", "conservative"),
           "quality_tier": vdna.get("quality_tier", "universal"),
           "color_field_palette": vdna.get("color_field_palette", "")}
    path = _profile_dir(handle, base) / "visual_dna.json"
    write_organ(path, out)
    return str(path)


def write_cultural_overrides(handle: str, co: dict, base: Path = None) -> str:
    """face_visibility is PER-CLIENT (Mohamed's June 24 ruling: 'face visible is based on client')."""
    co = co or {}
    out = {"_meta": {"organ": "cultural_overrides", "handle": handle, "_prov": _prov()},
           "face_visibility": co.get("face_visibility", "never"),
           "mixed_gender_scenes": bool(co.get("mixed_gender_scenes", False)),
           "modesty_dress": co.get("modesty_dress", "conservative")}
    out.update({k: v for k, v in co.items() if k not in out})
    path = _profile_dir(handle, base) / "cultural_overrides.json"
    write_organ(path, out)
    return str(path)


def write_red_lines(handle: str, lines, base: Path = None) -> str:
    if isinstance(lines, str):
        lines = [l.strip() for l in lines.split(",") if l.strip()]
    out = {"_meta": {"organ": "red_lines", "handle": handle, "_prov": _prov()},
           "lines": [{"text": l, "_prov": _prov()} for l in (lines or [])]}
    path = _profile_dir(handle, base) / "red_lines.json"
    write_organ(path, out)
    return str(path)


def fill_all_organs(form: dict, base: Path = None) -> dict:
    """Top-level: a self-service form → every organ this module owns. Returns {organ: path}.
    Research-derived organs (l1_strategy/fingerprint/audience_mirror) are filled by
    research_fill_established (the orchestrator runs it alongside) — not here."""
    handle = (form.get("handle") or "").strip()
    if not handle:
        raise ValueError("intake form missing 'handle'")
    written = {
        "product_truth": write_product_truth(handle, form.get("products"), base),
        "visual_dna": write_visual_dna(handle, form.get("visual_dna"), base),
        "cultural_overrides": write_cultural_overrides(handle, form.get("cultural_overrides"), base),
        "red_lines": write_red_lines(handle, form.get("red_lines"), base),
    }
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True, help="path to the intake form JSON")
    ap.add_argument("--base", default="", help="sandbox base dir (for testing; default = real repo)")
    a = ap.parse_args()
    form = json.loads(Path(a.form).read_text())
    base = Path(a.base) if a.base else None
    written = fill_all_organs(form, base=base)
    print(json.dumps({"handle": form.get("handle"), "written": written}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
