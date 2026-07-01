#!/usr/bin/env python3
"""B142 — DETERMINISTIC PER-CLIENT VISUAL-REVIEW CHECKLIST (the human-eyes gate, Rule #13).

Before any produced post reaches Mohamed, a human eye runs a yes/no visual review. Until now
that review was a single GENERIC checklist (advisor_playbook/review_checklist.md) — it did not
say, for THIS client, what the required answer is. The June-14 killed batch (face shown, dine-in
on a cloud kitchen, mixed-gender) proved the generic list lets client-specific breaches through.

This generator emits a checklist keyed to EACH client's own red_lines, derived from the SAME
source of truth the machine gate reads — 15_cultural_specs/defaults/brand_override_defaults_v1.yaml
(one boundary, all doors: deadly_defaults_gate.py reads the identical table). The human row and the
machine gate can never disagree, because both read one file.

Rule #12: the SYSTEM produces the checklist from the organs — no hand-authored per-client content.
Rule #6: its consumer is the human reviewer (the visual gate); test_visual_review_checklist.py
asserts coverage + determinism + gate-consistency end-to-end.

Usage:
  python3 scripts/build_visual_review_checklist.py            # write the file
  python3 scripts/build_visual_review_checklist.py --check    # exit 1 if on-disk file is stale
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).parent.parent
TABLE = BASE / "15_cultural_specs/defaults/brand_override_defaults_v1.yaml"
OUT = BASE / "15_cultural_specs/advisor_playbook/visual_review_checklist.md"

# product-truth is a visual dimension (an AI image can lie about the real product) but the table
# row carries no visual_gate_id — supply one so it joins the visual set.
SYNTHETIC_GATE = {"ai_imagery_of_real_products": (
    "product_truth", "لا منتج مولّد بالـAI يُعرض كأنه صورة حقيقية للمنتج (حتى حكم محمد)")}

# Human-readable PASS condition per effective setting, by field. Keyed to the STRICTEST default;
# a client-relaxed value flips to the relaxed allowance (see effective_setting).
_PASS_STRICT = {
    "face_visibility": "no human faces are visible in the image",
    "family_member_visibility": "no member of the client's family is visible",
    "mixed_gender_scenes": "any people-mixing is family / mahram only",
    "modesty_dress": "all dress is conservative by the Saudi standard",
    "music_in_video": "if a video: no music, or a permitted rhythm only",
    "ai_imagery_of_real_products": "no AI-rendered real product is shown as a real photo",
}


def visual_fields(table: dict) -> list[dict]:
    """Rows that a human reviews by LOOKING: every table field with a visual_gate_id, plus the
    product-truth row. Deterministic order = table order (the table is the law)."""
    out = []
    for row in table.get("fields", []):
        gid = row.get("visual_gate_id")
        check = row.get("visual_gate_check_ar")
        if not gid and row["field"] in SYNTHETIC_GATE:
            gid, check = SYNTHETIC_GATE[row["field"]]
        if gid:
            out.append({**row, "visual_gate_id": gid, "visual_gate_check_ar": check})
    return out


def _ledger_relaxes(handle: str, field: str, base: Path) -> bool:
    """Mirror deadly_defaults_gate.check_client: a red_line_relaxed event naming the field."""
    lf = base / "clients" / handle / "events/ledger.jsonl"
    ledger = lf.read_text(encoding="utf-8") if lf.exists() else ""
    return '"red_line_relaxed"' in ledger and field in ledger


def effective_setting(handle: str, field: str, strictest, base: Path) -> tuple[str, str]:
    """Return (effective_value, status). status ∈ {strict, relaxed, needs_event} — identical
    logic to the machine gate so the human row never contradicts the release block."""
    pdir = base / "clients" / handle / "profile"
    co_f = pdir / "cultural_overrides.json"
    overrides = json.loads(co_f.read_text(encoding="utf-8")) if co_f.exists() else {}
    val = overrides.get(field)
    if val is None:
        return str(strictest), "strict"  # absent = strictest governs
    if str(val) == str(strictest):
        return str(val), "strict"
    return str(val), ("relaxed" if _ledger_relaxes(handle, field, base) else "needs_event")


def client_rows(handle: str, vfields: list[dict], base: Path) -> list[dict]:
    rows = []
    for f in vfields:
        eff, status = effective_setting(handle, f["field"], f.get("strictest_default"), base)
        if status == "strict":
            pass_if = _PASS_STRICT.get(f["field"], f["visual_gate_check_ar"])
        elif status == "relaxed":
            pass_if = f"client RELAXED `{f['field']}`→`{eff}` via a logged event — verify the image stays within the relaxation"
        else:  # needs_event: override is non-strict but NO event authorizes it → treat as strict + flag
            pass_if = (_PASS_STRICT.get(f["field"], f["visual_gate_check_ar"])
                       + f"  ⚠️ override says `{eff}` but NO relaxation event — gate BLOCKS; hold")
        rows.append({
            "gate_id": f["visual_gate_id"],
            "field": f["field"],
            "check_ar": f["visual_gate_check_ar"],
            "deadly": bool(f.get("deadly_if_wrong")),
            "effective": eff,
            "status": status,
            "pass_if": pass_if,
        })
    return rows


def clients_with_profile(base: Path) -> list[str]:
    # Single boundary (Rule #3): synthetic fixtures (do_not_aggregate) are NOT real clients —
    # exclude them here exactly as fingerprint_status.real_clients() does, so census and checklist
    # never disagree on who a client is.
    from fingerprint_status import _is_synthetic_fixture
    cdir = base / "clients"
    return sorted(d.name for d in cdir.iterdir()
                  if (d / "profile" / "cultural_overrides.json").exists()
                  and not _is_synthetic_fixture(d / "profile"))


def build_checklist(base: Path = BASE) -> str:
    table = yaml.safe_load(TABLE.read_text(encoding="utf-8"))
    vfields = visual_fields(table)
    handles = clients_with_profile(base)
    L = []
    L.append("# Visual Review Checklist — per client, deterministic (B142)")
    L.append("")
    L.append("> GENERATED by `scripts/build_visual_review_checklist.py` from "
             "`brand_override_defaults_v1.yaml` + each client's `cultural_overrides.json`. "
             "Do not hand-edit — re-run the generator. The machine gate "
             "(`deadly_defaults_gate.py`) reads the SAME table, so a human PASS and a machine "
             "PASS can never disagree (one boundary, all doors).")
    L.append("")
    L.append("**How to use:** for the rendered image, answer each row yes/no with your eyes. "
             "A DEADLY row failing → hold for rewrite (do NOT let it reach Mohamed). "
             "A ⚠️ flag means the client's organ claims a relaxation that has no logged event — "
             "the release gate will block it.")
    L.append("")
    L.append(f"Visual dimensions ({len(vfields)}): "
             + ", ".join(f["visual_gate_id"] for f in vfields))
    L.append("")
    for h in handles:
        rows = client_rows(h, vfields, base)
        L.append(f"## {h}")
        L.append("")
        for r in rows:
            tag = "🔴 DEADLY" if r["deadly"] else "🟡 quality"
            L.append(f"- [ ] **{r['gate_id']}** ({tag}) — {r['check_ar']}")
            L.append(f"      setting: `{r['field']}={r['effective']}` [{r['status']}] · "
                     f"PASS if: {r['pass_if']}")
        L.append("")
    L.append("## Decision")
    L.append("")
    L.append("- All rows pass → clear for Mohamed's judging queue (Rule #13).")
    L.append("- Any 🔴 DEADLY fail or ⚠️ flag → hold for rewrite; log which gate_id failed.")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the on-disk checklist differs from a fresh generation")
    a = ap.parse_args()
    fresh = build_checklist()
    if a.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != fresh:
            print(f"🔴 STALE: {OUT.relative_to(BASE)} differs from generated — re-run the generator")
            sys.exit(1)
        print(f"🟢 FRESH: {OUT.relative_to(BASE)} matches the organs")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(fresh, encoding="utf-8")
    n = len(clients_with_profile(BASE))
    print(f"✅ wrote {OUT.relative_to(BASE)} — {n} clients, "
          f"{len(visual_fields(yaml.safe_load(TABLE.read_text(encoding='utf-8'))))} visual rows each")


if __name__ == "__main__":
    main()
