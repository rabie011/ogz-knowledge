#!/usr/bin/env python3
"""Generate the 8 missing organ schemas (pyramid GAP-11, June 11).
Schemas mirror EXACTLY what build_brand_profile.py emits — the composer is the
contract. Additive only: new files in 12_data_shapes/, nothing existing touched.
After generation, validates all existing client profiles against them.
Repo law: save your generators — this regenerates the set deterministically.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = BASE / "12_data_shapes"

PROV = {"type": "object", "required": ["source", "date_added", "confirmer", "confidence", "scope"],
        "properties": {"source": {"type": "string"}, "date_added": {"type": "string"},
                        "confirmer": {"type": "string"}, "confidence": {"type": "string"},
                        "scope": {"type": "string"}}, "additionalProperties": False}

S = lambda: {"type": "string"}
SN = lambda: {"type": ["string", "null"]}
N = lambda: {"type": ["number", "null"]}
ARR = lambda items: {"type": "array", "items": items}

SCHEMAS = {
    "client_state_v1": {
        "required": ["state", "posts_count", "followers", "last_post", "silent_days", "method", "human_checkpoint", "provenance"],
        "properties": {"state": {"enum": ["newborn", "newborn-dormant", "active", "active_dormant", "active_unclassified",
                                            "active_messy", "active_strong"]},
                        "posts_count": N(), "followers": N(), "last_post": SN(), "silent_days": N(),
                        "method": {"const": "countables_only"},
                        "human_checkpoint": S(), "provenance": PROV}},
    "client_truth_pack_v1": {
        "required": ["confirmed", "product_candidates", "recurring_caption_terms", "channels", "real_hashtags", "prices", "note"],
        "properties": {"confirmed": ARR({"type": "object"}),
                        "product_candidates": ARR({"type": "object", "required": ["name", "evidence", "provenance"],
                                                     "properties": {"name": S(), "evidence": S(), "provenance": PROV},
                                                     "additionalProperties": False}),
                        "recurring_caption_terms": ARR(S()),
                        "channels": ARR({"type": "object", "required": ["name", "evidence", "provenance"],
                                          "properties": {"name": S(), "evidence": S(), "provenance": PROV},
                                          "additionalProperties": False}),
                        "real_hashtags": ARR(S()), "prices": ARR({"type": "object"}), "note": S()}},
    "client_red_lines_v1": {
        "required": ["lines", "defaults_pinned", "note"],
        "properties": {"lines": ARR({"type": "object"}), "defaults_pinned": S(), "note": S()}},
    "client_goals_v1": {
        "required": ["goal_ratio", "capacity_ceiling", "forward_calendar", "usp_his_words", "answered", "of"],
        "properties": {"goal_ratio": SN(), "capacity_ceiling": N(), "forward_calendar": ARR({"type": "object"}),
                        "usp_his_words": SN(), "answered": {"type": "number"}, "of": {"type": "number"}}},
    "client_moments_bank_v1": {
        "required": ["moments"],
        "properties": {"moments": ARR({"type": "object", "required": ["occasion", "evidence", "provenance"],
                                         "properties": {"occasion": S(), "evidence": S(), "engagement": N(),
                                                         "provenance": PROV}, "additionalProperties": False})}},
    "client_audience_mirror_v1": {
        "required": ["comments_count", "sample", "note"],
        "properties": {"comments_count": {"type": "number"}, "sample": ARR(S()), "note": S()}},
    "client_taste_v1": {
        "required": ["floor", "kills", "client_calibration"],
        "properties": {"floor": S(), "kills": ARR(S()), "client_calibration": ARR({"type": "object"})}},
    "client_gap_report_v1": {
        "required": ["questions", "organs_red", "organs_yellow"],
        "properties": {"questions": ARR(S()), "organs_red": ARR(S()), "organs_yellow": ARR(S())}},
    "client_competitor_set_v1": {
        "required": ["client_given", "proposed_from_corpus", "note", "requests_log"],
        "properties": {"client_given": ARR(S()), "proposed_from_corpus": ARR(S()),
                        "note": S(), "requests_log": S()}},
    # B077: events are heterogeneous append-only facts — base contract strict, payload open.
    # Type enum = census-found types + pyramid-specified future types (commercial spine,
    # referral, offboarding, approver, pick-sets). additionalProperties TRUE by design:
    # an event ledger must accept tomorrow's fact shapes; the base 4 fields are the law.
    "client_trust_v1": {
        "required": ["level", "ladder", "history", "law", "provenance"],
        "properties": {"level": {"enum": ["L0", "L1", "L2"]},
                        "ladder": {"type": "object"}, "history": ARR({"type": "object"}),
                        "law": S(), "provenance": PROV}},
    "client_event_v1": {
        "_additional_ok": True,
        "required": ["ts", "type", "confirmer", "stamp"],
        "properties": {"ts": S(), "confirmer": S(), "stamp": S(),
                        "type": {"enum": ["intake_answer", "client_approved", "client_rejected",
                                            "voice_rating", "batch_rating", "compare_verdict",
                                            "version_verdict", "occasion_gold", "competitor_reference",
                                            "pick_selected", "red_line_added", "red_line_relaxed",
                                            "goal_declared", "capacity_declared", "truth_confirmed",
                                            "payment_received", "renewal", "scope_change",
                                            "referral", "offboarding_request", "approver_change",
                                            "blackout_flip", "crystallize_accepted", "crystallize_rejected"]},
                        "subject": S(), "rating": {"type": ["number", "null"]},
                        "reason_code": {"enum": ["culture_breach", "off_voice", "wrong_goal",
                                                   "too_generic", "factual_error", "unexplained", None]},
                        "note": S()}},
}

ORGAN_TO_SCHEMA = {"state": "client_state_v1", "truth_pack": "client_truth_pack_v1",
                    "red_lines": "client_red_lines_v1", "goals": "client_goals_v1",
                    "moments_bank": "client_moments_bank_v1", "audience_mirror": "client_audience_mirror_v1",
                    "taste": "client_taste_v1", "gap_report": "client_gap_report_v1",
                    "competitor_set": "client_competitor_set_v1",
                    "trust": "client_trust_v1"}


def generate():
    for name, body in SCHEMAS.items():
        body = dict(body)
        additional = body.pop("_additional_ok", False)
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                   "$id": f"{name}.schema.json", "title": name, "type": "object",
                   "additionalProperties": additional, **body}
        (OUT / f"{name}.schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False))
        print(f"  ✓ 12_data_shapes/{name}.schema.json")


def validate_all():
    import jsonschema
    fails = 0
    for cdir in sorted((BASE / "clients").iterdir()):
        pdir = cdir / "profile"
        if not pdir.is_dir():
            continue
        for organ, sname in ORGAN_TO_SCHEMA.items():
            f = pdir / f"{organ}.json"
            if not f.exists():
                print(f"  ⚠ {cdir.name}/{organ}.json MISSING")
                fails += 1
                continue
            schema = json.loads((OUT / f"{sname}.schema.json").read_text())
            try:
                jsonschema.validate(json.loads(f.read_text()), schema)
                print(f"  ✅ {cdir.name}/{organ}")
            except jsonschema.ValidationError as e:
                print(f"  ❌ {cdir.name}/{organ}: {e.message[:90]} @ {'/'.join(str(p) for p in e.absolute_path)}")
                fails += 1
    return fails


if __name__ == "__main__":
    print("── generating 8 organ schemas:")
    generate()
    print("── validating all client profiles:")
    fails = validate_all()
    print(f"\n{'✅ ALL ORGANS VALIDATE' if fails == 0 else f'❌ {fails} failures — fix before claiming done'}")
    raise SystemExit(1 if fails else 0)
