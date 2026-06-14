#!/usr/bin/env python3
"""Apply the orchestra's corpus-GROUNDED v3.7 candidates onto the pilot organs.

Consumes data/openclaw_v37/grounded.json (the GROUND-phase workflow output: an array of
{handle, brand:{field:{value,evidence}}, products:[{name, field:{value,evidence}}]}). It
UPGRADES the YELLOW values in each visual_dna.json from generic sector-defaults to
evidence-grounded candidates — status STAYS YELLOW (still a candidate, still needs client
confirm — RABIE/Mohamed anti-hallucination law), but provenance becomes corpus_grounded with
the cited evidence. Schema-validated before write (prove before go).

Usage: python3 scripts/apply_grounded_v37.py            # applies data/openclaw_v37/grounded.json
       python3 scripts/apply_grounded_v37.py --dry       # show the diff, write nothing
"""
import argparse, json, sys
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator

B = Path(__file__).parent.parent
SCHEMA = json.loads((B / "12_data_shapes/brand_visual_dna_v37_v1.schema.json").read_text())
GROUNDED = B / "data/openclaw_v37/grounded.json"
TS = "2026-06-13"

BRAND_FIELDS = {"color_field_palette": ("color_field_palette",),
                "palette_primary": ("palette", "primary"),
                "background_tone": ("palette", "background_tone"),
                "capture_character": ("capture_character",)}
PROD_FIELDS = ["material_texture", "dimensions", "companion_elements"]


def gprov(evidence):
    return {"source": f"corpus_grounded: {evidence[:160]}", "date_added": TS,
            "confirmer": "agent_derived", "confidence": "candidate", "scope": "brand"}


def nav(d, path):
    for k in path[:-1]:
        d = d.setdefault(k, {})
    return d, path[-1]


def apply_one(g, dry):
    h = g["handle"]
    vf = B / "clients" / h / "profile" / "visual_dna.json"
    if not vf.exists():
        print(f"  ⏭  {h}: no visual_dna.json"); return 0
    vd = json.loads(vf.read_text())
    changed = []
    # brand-level
    for gkey, path in BRAND_FIELDS.items():
        gv = (g.get("brand") or {}).get(gkey)
        if not gv or not gv.get("value"):
            continue
        parent, leaf = nav(vd["brand"], list(path))
        sf = parent.get(leaf) or {}
        if sf.get("status") == "GREEN":            # never overwrite a client-confirmed value
            continue
        old = sf.get("value")
        sf["value"] = gv["value"]; sf["status"] = "YELLOW"; sf["provenance"] = gprov(gv["evidence"])
        sf["example"] = (sf.get("example") or "exact value RED until client confirms")
        parent[leaf] = sf
        changed.append(f"brand.{'.'.join(path)}: «{str(old)[:30]}» → «{gv['value'][:40]}»")
    # product-level (fuzzy match — grounded names differ from organ names, e.g.
    # "جريش / جريشة (signature…)" vs organ "جريش"; match on a shared ≥3-char token)
    def toks(n):
        return {t for t in (n or "").replace("/", " ").split() if len(t) >= 3}
    gprods = list(g.get("products") or [])
    def match(pname):
        pt = toks(pname)
        for gp in gprods:
            if pt & toks(gp.get("name")):
                return gp
        return None
    for prod in vd.get("products", []):
        gp = match(prod.get("name"))
        if not gp:
            continue
        for f in PROD_FIELDS:
            gv = gp.get(f)
            if not gv or not gv.get("value"):
                continue
            sf = prod.get(f) or {}
            if sf.get("status") == "GREEN":
                continue
            sf["value"] = gv["value"]; sf["status"] = "YELLOW"; sf["provenance"] = gprov(gv["evidence"])
            prod[f] = sf
            changed.append(f"{prod['name']}.{f} grounded")
    # prove before write
    errs = list(Draft202012Validator(SCHEMA).iter_errors(vd))
    assert not errs, f"{h} grounded organ fails schema: {errs[:2]}"
    if dry:
        print(f"  [dry] {h}: {len(changed)} upgrades")
    else:
        vf.write_text(json.dumps(vd, ensure_ascii=False, indent=2))
        print(f"  ✓ {h}: {len(changed)} fields grounded (schema ✅)")
    for c in changed[:6]:
        print(f"       · {c}")
    return len(changed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if not GROUNDED.exists():
        sys.exit(f"no {GROUNDED.relative_to(B)} — write the workflow's grounded[] there first")
    data = json.loads(GROUNDED.read_text())
    data = data if isinstance(data, list) else data.get("grounded", [])
    total = sum(apply_one(g, a.dry) for g in data)
    print(f"  TOTAL {total} fields upgraded generic→corpus-grounded "
          f"(status stays YELLOW — still client-confirm; provenance now cites evidence)")


if __name__ == "__main__":
    main()
