#!/usr/bin/env python3
"""Generate and validate the canonical client-organ schemas.

Production validation follows fingerprint_status.real_clients(); synthetic fixtures
have a separate marker contract. ``--validate-only`` never rewrites schema files.
Repo law: save generators and name additive fields explicitly.
"""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = BASE / "12_data_shapes"

PROV = {"type": "object", "required": ["source", "date_added", "confirmer", "confidence", "scope"],
        "properties": {"source": {"type": "string"}, "date_added": {"type": "string"},
                        "confirmer": {"type": "string"}, "confidence": {"type": "string"},
                        "scope": {"type": "string"}},
        "additionalProperties": False}
PRODUCT_PROV = {
    **PROV,
    # 2026-06-12: the product-confirmation writer preserves its append timestamp.
    "properties": {**PROV["properties"], "confirmed_ts": {"type": "string"}},
}

S = lambda: {"type": "string"}
SN = lambda: {"type": ["string", "null"]}
N = lambda: {"type": ["number", "null"]}
ARR = lambda items: {"type": "array", "items": items}

META = {"type": "object", "required": ["organ", "handle", "_prov"],
        "properties": {"organ": S(), "handle": S(), "_prov": PROV},
        "additionalProperties": False}
RESEARCHED_GOAL = {
    "type": "object",
    "required": ["value", "source", "date_added", "confirmer", "confidence", "scope"],
    "properties": {"value": S(), "source": S(), "date_added": S(), "confirmer": S(),
                   "confidence": S(), "scope": S()},
    "additionalProperties": False,
}
DECLARED_GOAL = {
    "type": "object",
    "required": ["goal", "offers_ratio", "source", "confirmer", "date"],
    "properties": {"goal": S(), "offers_ratio": S(), "source": S(),
                   "confirmer": S(), "date": S()},
    "additionalProperties": False,
}
DECLARED_CAPACITY = {
    "type": "object",
    "required": ["orders_per_day", "source", "confirmer", "date"],
    "properties": {"orders_per_day": {"type": "number"}, "source": S(),
                   "confirmer": S(), "date": S()},
    "additionalProperties": False,
}
DECLARED_USP = {
    "type": "object",
    "required": ["raw", "normalized", "source", "confirmer", "date"],
    "properties": {"raw": S(), "normalized": S(), "source": S(),
                   "confirmer": S(), "date": S()},
    "additionalProperties": False,
}

SCHEMAS = {
    "client_state_v1": {
        "required": ["state", "posts_count", "followers", "last_post", "silent_days", "method", "human_checkpoint", "provenance"],
        "properties": {"state": {"enum": ["newborn", "newborn-dormant", "active", "active_dormant", "active_unclassified",
                                            "active_messy", "active_strong"]},
                        "posts_count": N(), "followers": N(), "last_post": SN(), "silent_days": N(),
                        "method": {"const": "countables_only"},
                        "human_checkpoint": S(),
                        "ogz_account_owner": {"type": ["string", "null"], "description":
                            "OGZ team member who owns this account; null until Mohamed names names (B160). "
                            "Consumed by the red-client human-touch alert (B093)."},
                        # Additive fields learned from real profiles, 2026-06-13.
                        "outreach_ruling": {"type": "object", "required": ["value", "ruled_at", "source"],
                                             "properties": {"value": S(), "ruled_at": S(), "source": S()},
                                             "additionalProperties": False},
                        "archive_claim_poor": {"type": "object", "required": ["verdict", "evidence", "implication"],
                                               "properties": {"verdict": {"type": "boolean"},
                                                              "evidence": S(), "implication": S()},
                                               "additionalProperties": False},
                        "provenance": PROV}},
    "client_truth_pack_v1": {
        "required": ["confirmed", "product_candidates", "recurring_caption_terms", "channels", "real_hashtags", "prices", "note"],
        "properties": {"confirmed": ARR({"type": "object"}),
                        "product_candidates": ARR({"type": "object", "required": ["name", "evidence", "provenance"],
                                                     "properties": {"name": S(), "evidence": S(), "provenance": PRODUCT_PROV},
                                                     "additionalProperties": False}),
                        "recurring_caption_terms": ARR(S()),
                        "brand_language": ARR({"type": "object"}),
                        "channels": ARR({"type": "object", "required": ["name", "evidence", "provenance"],
                                          "properties": {"name": S(), "evidence": S(), "provenance": PROV},
                                          "additionalProperties": False}),
                        "real_hashtags": ARR(S()), "prices": ARR({"type": "object"}), "note": S(),
                        # Additive diagnosis fields, 2026-06-13/14.
                        "_diagnosis_note": S(),
                        "format": {"type": "object", "required": ["value", "confirmer", "date", "note"],
                                   "properties": {"value": S(), "confirmer": S(), "date": S(), "note": S()},
                                   "additionalProperties": False}}},
    "client_red_lines_v1": {
        "required": ["lines", "defaults_pinned", "note"],
        "properties": {"lines": ARR({"type": "object"}), "defaults_pinned": S(), "note": S(),
                        "touches_since_confirm": {"type": "number"},
                        "proposed_lines": ARR({"type": "object"}),
                        "prices_not_redline": {"type": "boolean"}, "confirmer": S(),
                        # Named additive provenance/metadata fields, 2026-06-14/30.
                        "_research": PROV, "_meta": META}},
    "client_goals_v1": {
        "required": ["goal_ratio", "capacity_ceiling", "forward_calendar", "usp_his_words", "answered", "of"],
        "properties": {
            # Rich declarations landed 2026-06-12/14; scalar forms remain backward compatible.
            "goal_ratio": {"oneOf": [SN(), RESEARCHED_GOAL, DECLARED_GOAL]},
            "capacity_ceiling": {"oneOf": [N(), DECLARED_CAPACITY]},
            "forward_calendar": ARR({"type": "object"}),
            "usp_his_words": {"oneOf": [SN(), DECLARED_USP]},
            "answered": {"type": "number"}, "of": {"type": "number"},
            # Named additive passport/diagnosis fields, 2026-06-13.
            "_passport": {"type": "object", "required": ["source", "confirmer", "confidence", "date"],
                          "properties": {"source": S(), "confirmer": S(), "confidence": S(), "date": S()},
                          "additionalProperties": False},
            "capacity": N(), "primary": SN(), "_counter_fix": S(),
        }},
    "client_moments_bank_v1": {
        "required": ["moments"],
        "properties": {"moments": ARR({"type": "object", "required": ["occasion", "evidence", "provenance"],
                                         "properties": {"occasion": S(), "evidence": S(), "engagement": N(),
                                                         "provenance": PROV}, "additionalProperties": False})}},
    "client_audience_mirror_v1": {
        "required": ["comments_count", "sample", "note"],
        "properties": {"comments_count": {"type": "number"}, "sample": ARR(S()), "note": S(),
                        "customer_language": ARR(S()), "pains_aggregate": ARR(S()),
                        "theme_tally": ARR({"type": "object"}), "machine_note": S(),
                        "maps_signals": {"type": "object"},
                        # Named audience annotations, 2026-06-13.
                        "_status": S(), "segments": ARR({"type": "object"}),
                        "sources_enum": ARR(S())}},
    "client_taste_v1": {
        "required": ["floor", "kills", "client_calibration"],
        "properties": {"floor": S(), "kills": ARR(S()), "client_calibration": ARR({"type": "object"}),
                        # Structured learned kills, 2026-06-13.
                        "kill_patterns": ARR({"type": "object"})}},
    "client_gap_report_v1": {
        "required": ["questions", "organs_red", "organs_yellow"],
        "properties": {"questions": ARR(S()), "organs_red": ARR(S()), "organs_yellow": ARR(S()),
                        # Named machine annotations, 2026-06-13.
                        "auto_filled": {"type": "object"},
                        "established_research": {"type": "object"},
                        "v37_visual": {"type": "object"}}},
    "client_fingerprint_v1": {
        # B016: the most-read organ (every render loads it) finally has a contract.
        # Inner layers lenient — the composer evolves; the LAYER SET is the contract.
        "required": ["l1_strategy", "l2_voice", "l3_visual"],
        "properties": {"l1_strategy": {"type": "object"},
                        "l2_voice": {"type": "object"},
                        "l3_visual": {"type": "object"}},
        "_additional_ok": True},
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
                                            "blackout_flip", "crystallize_accepted", "crystallize_rejected",
                                            "published", "publish_failed", "review_received"]},
                        "subject": S(), "rating": {"type": ["number", "null"]},
                        "reason_code": {"enum": ["culture_breach", "off_voice", "wrong_goal",
                                                   "too_generic", "factual_error", "unexplained", None]},
                        "note": S()}},
    "client_synthetic_fixture_v1": {
        # Canonical exclusion marker. Fixtures may exercise readers but never enter
        # production census/ladder/checklist aggregates.
        "required": ["handle", "tier", "sector", "purpose", "do_not_aggregate", "_prov"],
        "properties": {"handle": S(), "tier": {"enum": ["ready", "sparse"]},
                        "sector": S(),
                        "purpose": {"enum": ["fake_platform_sector_coverage",
                                              "rfp_synthetic_content_fixture"]},
                        "do_not_aggregate": {"const": True}, "_prov": PROV}},
}

ORGAN_TO_SCHEMA = {"state": "client_state_v1", "truth_pack": "client_truth_pack_v1",
                    "fingerprint": "client_fingerprint_v1",
                    "red_lines": "client_red_lines_v1", "goals": "client_goals_v1",
                    "moments_bank": "client_moments_bank_v1", "audience_mirror": "client_audience_mirror_v1",
                    "taste": "client_taste_v1", "gap_report": "client_gap_report_v1",
                    "competitor_set": "client_competitor_set_v1",
                    "trust": "client_trust_v1"}


SUMMARY_PREFIX = "ORGAN_VALIDATION_SUMMARY="


def generate(out: Path = OUT):
    out.mkdir(parents=True, exist_ok=True)
    for name, body in SCHEMAS.items():
        body = dict(body)
        additional = body.pop("_additional_ok", False)
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                   "$id": f"{name}.schema.json", "title": name, "type": "object",
                   "additionalProperties": additional, **body}
        (out / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ 12_data_shapes/{name}.schema.json")


def check_inference_quarantine(base: Path = BASE, handles: list[str] | None = None):
    """B009: an IDENTITY field citing stats provenance = violation — stats may
    inform voice, never assert identity (the +0.08 scar, structural edition)."""
    if handles is None:
        from fingerprint_status import real_clients
        handles = real_clients()
    bad = []
    for handle in handles:
        f = base / "clients" / handle / "profile" / "fingerprint.json"
        try:
            fp = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        l1 = fp.get("l1_strategy") or {}
        prov = str(l1.get("provenance", "")) + str(l1)
        for marker in ("voice_stats", "brand_dna", "health_score", "engagement"):
            if marker in prov and any(l1.get(k) for k in ("who_speaks", "positioning", "contrarian_belief")):
                bad.append(f"{handle}/profile/fingerprint.json: identity cites {marker}")
    return bad


def validate_all(base: Path = BASE, out: Path = OUT,
                 handles: list[str] | None = None) -> dict:
    """Validate only canonical production clients and count findings directly."""
    import jsonschema
    if handles is None:
        from fingerprint_status import real_clients
        handles = real_clients()
    findings = []
    for handle in handles:
        pdir = base / "clients" / handle / "profile"
        for organ, sname in ORGAN_TO_SCHEMA.items():
            f = pdir / f"{organ}.json"
            if not f.exists():
                print(f"  ⚠ {handle}/{organ}.json MISSING")
                findings.append({"kind": "missing", "handle": handle, "organ": organ})
                continue
            schema = json.loads((out / f"{sname}.schema.json").read_text(encoding="utf-8"))
            try:
                jsonschema.validate(json.loads(f.read_text(encoding="utf-8")), schema)
                print(f"  ✅ {handle}/{organ}")
            except jsonschema.ValidationError as e:
                path = "/".join(str(p) for p in e.absolute_path)
                print(f"  ❌ {handle}/{organ}: {e.message[:90]} @ {path}")
                findings.append({"kind": "invalid", "handle": handle, "organ": organ,
                                 "validator": e.validator, "path": path,
                                 "message": e.message})
    return {
        "production_clients": handles,
        "invalid_files": sum(f["kind"] == "invalid" for f in findings),
        "missing_files": sum(f["kind"] == "missing" for f in findings),
        "findings": findings,
    }


def validate_synthetic_fixtures(base: Path = BASE, out: Path = OUT) -> dict:
    """Validate fixture identity separately; fixtures never inherit production organs."""
    import jsonschema
    schema = json.loads(
        (out / "client_synthetic_fixture_v1.schema.json").read_text(encoding="utf-8"))
    markers = sorted((base / "clients").glob("*/profile/.synthetic_fixture.json"))
    findings = []
    for marker in markers:
        handle = marker.parent.parent.name
        try:
            row = json.loads(marker.read_text(encoding="utf-8"))
            jsonschema.validate(row, schema)
            if row["handle"] != handle:
                raise jsonschema.ValidationError(
                    f"marker handle {row['handle']!r} does not match directory {handle!r}")
            print(f"  ✅ fixture/{handle}")
        except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
            print(f"  ❌ fixture/{handle}: {str(exc)[:120]}")
            findings.append({"kind": "fixture_invalid", "handle": handle,
                             "message": str(exc)})
    return {"synthetic_fixtures": [p.parent.parent.name for p in markers],
            "fixture_invalid": len(findings), "findings": findings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-only", action="store_true",
                    help="validate existing schemas without rewriting them")
    ap.add_argument("--json-summary", action="store_true",
                    help="emit the machine-readable direct-count summary")
    args = ap.parse_args(argv)

    if not args.validate_only:
        print(f"── generating {len(SCHEMAS)} client schemas:")
        generate()

    from fingerprint_status import real_clients
    handles = real_clients()
    print(f"── validating production clients ({len(handles)}): {', '.join(handles)}")
    profile = validate_all(handles=handles)
    print("── validating synthetic fixture markers:")
    fixtures = validate_synthetic_fixtures()
    quarantine = check_inference_quarantine(handles=handles)
    for finding in quarantine:
        print(f"  ❌ inference-quarantine: {finding}")

    summary = {
        "production_clients": profile["production_clients"],
        "production_client_count": len(profile["production_clients"]),
        "invalid_files": profile["invalid_files"],
        "missing_files": profile["missing_files"],
        "synthetic_fixtures": fixtures["synthetic_fixtures"],
        "synthetic_fixture_count": len(fixtures["synthetic_fixtures"]),
        "fixture_invalid": fixtures["fixture_invalid"],
        "inference_findings": len(quarantine),
    }
    summary["total_findings"] = (
        summary["invalid_files"] + summary["missing_files"]
        + summary["fixture_invalid"] + summary["inference_findings"])
    if args.json_summary:
        print(SUMMARY_PREFIX + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if summary["total_findings"] == 0:
        print("\n✅ ALL ORGANS VALIDATE")
        return 0
    print(f"\n❌ {summary['total_findings']} findings — fix before claiming done")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
