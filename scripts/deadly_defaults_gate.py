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
})


def check_client(handle: str, deadly_fields: dict) -> list[str]:
    pdir = BASE / "clients" / handle / "profile"
    violations = []
    co_f = pdir / "cultural_overrides.json"
    overrides = json.loads(co_f.read_text()) if co_f.exists() else {}
    lf = BASE / "clients" / handle / "events/ledger.jsonl"
    ledger = lf.read_text() if lf.exists() else ""
    for field, row in deadly_fields.items():
        val = overrides.get(field)
        if val is None:
            continue  # absent = strictest default governs — safe
        strict = row.get("strictest_default")
        if str(val) == str(strict):
            continue  # explicitly conservative — safe
        if val is False or str(val).strip().lower() in _STRICTER_OR_EQUAL:
            continue  # total-prohibition value — no-less-strict than strict, never a relaxation
        # non-conservative: only a client relaxation event makes it legal
        if f'"red_line_relaxed"' in ledger and field in ledger:
            continue
        violations.append(f"{handle}.{field} = {val} (strict: {strict}) — NO client relaxation event")
    return violations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    table = yaml.safe_load(TABLE.read_text())
    deadly = {r["field"]: r for r in table.get("fields", []) if r.get("deadly_if_wrong")}
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
