#!/usr/bin/env python3
"""DEADLY-DEFAULTS RELEASE GATE (B106, June 12) — the B105 table gets teeth.
A DEADLY cultural field running anything but its strictest default, without a
client event (red_line_relaxed) authorizing it, is a release block. Deterministic:
the table is law, the ledger is the only key, AI relaxes nothing.

Usage: python3 scripts/deadly_defaults_gate.py [--handle X]   (exit 1 = blocked)
"""
import argparse, json, sys
from pathlib import Path
import fingerprint_status

import yaml

BASE = Path(__file__).parent.parent
TABLE = BASE / "15_cultural_specs/defaults/brand_override_defaults_v1.yaml"

# A value meaning "the risky behavior NEVER happens" is no-less-strict than the
# strictest default of EVERY deadly field — all 12 strict defaults are restrictive
# (never / off / no_music / blocked_permanent / conservative / family-only-mixing),
# so the risk is always the permissive direction. A total-prohibition value can
# therefore never be a RELAXATION; flagging it is a false positive (B106 fix, June 30:
# alnasserjewelry encoded mixed_gender_scenes=false (no mixing at all) — STRICTER than
# the 'family-only-mixing' string default, yet str(False)!='family-only-mixing' flagged
# it). This NARROWS violations only for provably-conservative values; a real relaxation
# (True / 'all' / 'allowed' / 'on' / 'mixed' / any permissive token) is still flagged —
# the opposite of a fail-open (the C221w scar). Verified by both chairs + the downstream
# consumer render_image.py (False -> 'none' bucket -> renders no mixed-gender = correct).
_STRICTER_OR_EQUAL = frozenset({
    "false", "none", "no", "never", "off", "disabled",
    "blocked", "blocked_permanent", "no_music", "no-mixing",
    "separate", "segregated",
    # face_visibility=faceless: faces may be in frame but NONE visible — a total prohibition
    # of the guarded risk (a visible face), no-less-strict than 'never'. render_image treats
    # never/faceless identically; no consumer reads it as permissive. Parallel to 'false' above.
    "faceless",
})


def load_deadly_fields(base=None) -> dict:
    root = Path(base) if base is not None else BASE
    table_path = root / "15_cultural_specs/defaults/brand_override_defaults_v1.yaml"
    try:
        table = yaml.safe_load(table_path.read_text()) or {}
    except Exception as exc:
        raise RuntimeError(f"deadly-default table unavailable: {table_path}: {exc}") from exc
    deadly = {r["field"]: r for r in table.get("fields", []) if r.get("deadly_if_wrong")}
    if not deadly:
        raise RuntimeError(f"deadly-default table has no deadly fields: {table_path}")
    return deadly


def _strict_or_stricter(value, strict) -> bool:
    return (
        str(value) == str(strict)
        or value is False
        or str(value).strip().lower() in _STRICTER_OR_EQUAL
    )


def has_relaxation_event(handle: str, field: str, base=None) -> bool:
    root = Path(base) if base is not None else BASE
    ledger_path = root / "clients" / handle / "events/ledger.jsonl"
    if not ledger_path.exists():
        return False
    for line in ledger_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") == "red_line_relaxed" and field in {
            row.get("field"), row.get("subject")
        }:
            return True
    return False


def effective_overrides(
    handle: str,
    deadly_fields=None,
    base=None,
) -> dict:
    """Return runtime-safe overrides; unconfirmed deadly relaxations become strict defaults."""
    root = Path(base) if base is not None else BASE
    overrides_path = root / "clients" / handle / "profile/cultural_overrides.json"
    try:
        overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cultural overrides unreadable for {handle}: {exc}") from exc
    if not isinstance(overrides, dict):
        raise RuntimeError(f"cultural overrides must be an object for {handle}")

    effective = dict(overrides)
    for field, row in (deadly_fields or load_deadly_fields(root)).items():
        value = overrides.get(field)
        strict = row.get("strictest_default")
        if value is None or (
            not _strict_or_stricter(value, strict)
            and not has_relaxation_event(handle, field, root)
        ):
            effective[field] = strict
    return effective


def check_client(handle: str, deadly_fields: dict) -> list[str]:
    pdir = BASE / "clients" / handle / "profile"
    violations = []
    co_f = pdir / "cultural_overrides.json"
    overrides = json.loads(co_f.read_text()) if co_f.exists() else {}
    for field, row in deadly_fields.items():
        val = overrides.get(field)
        if val is None:
            continue  # absent = strictest default governs — safe
        strict = row.get("strictest_default")
        if _strict_or_stricter(val, strict):
            continue  # explicit strict or total prohibition — safe
        # non-conservative: only a client relaxation event makes it legal
        if has_relaxation_event(handle, field):
            continue
        violations.append(f"{handle}.{field} = {val} (strict: {strict}) — NO client relaxation event")
    return violations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    deadly = load_deadly_fields()
    clients = ([a.handle] if a.handle else
               fingerprint_status.real_clients())
    all_v = []
    for h in clients:
        v = check_client(h, deadly)
        all_v += v
        print(f"  {'✅' if not v else '🔴'} {h}: {len(v)} deadly violations ({len(deadly)} fields checked)")
        for x in v:
            print(f"     → {x}")
    print(f"\n{'🟢 RELEASE CLEAR' if not all_v else '🔴 RELEASE BLOCKED'}: {len(all_v)} violations")
    sys.exit(1 if all_v else 0)


if __name__ == "__main__":
    main()
