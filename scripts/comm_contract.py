#!/usr/bin/env python3
"""CLIENT COMMUNICATION CONTRACT v1 (B158, Flanks) — the relationship layer's typed organ.

Before any real client is onboarded the system must know HOW it is allowed to talk to them:
on which channel, in which language, inside which time windows, how often it may ping, and how
fast each side answers. Today that knowledge lives nowhere — so every comm decision is improvised
(the opposite of "trust is the currency / never look unprofessional", Mohamed's instinct #5).

This file is BOTH halves of the wire (Rule #6 — a writer ships with its reader, same cycle):
  - WRITER:  write_stub(handle) / infer_defaults(handle) — lay down clients/<h>/profile/comm_contract.json
             with conservative defaults INFERRED from the manifest, stamped confirmer="inferred"
             (NEVER "mohamed" — a stub is not his truth; Rules #11/#13).
  - READER:  load(handle) + validate(contract) — the typed accessor any future comm/ping organ calls.
             A contract that does not validate is REFUSED, not warned (Rule #8): validate() returns the
             error list and main()/callers exit non-zero on a non-empty list.

The stub is INFERRED_UNCONFIRMED until Mohamed taps to confirm — a later gated step stages that card.
Zero-key, zero-LLM: pure manifest inference + schema validation.

Usage: python3 scripts/comm_contract.py stub|validate|status [--handle H]
"""
import argparse, json, re, sys
from datetime import date
from pathlib import Path

B = Path(__file__).parent.parent
CLIENTS = ["eatjurisha", "albaik", "myfitness.sa"]

CONTRACT_VERSION = "comm_contract_v1"

# ── the schema (one place; writer + every reader obey it, never drift — Rule #6) ──────────────
CHANNELS = ("instagram_dm", "whatsapp", "email", "snapchat", "portal", "link_in_bio")
LANGUAGES = ("ar", "en", "bilingual")
DIRECTIONS = ("us_to_client", "client_to_us")
# top-level keys every contract MUST carry
REQUIRED = ("version", "handle", "channel", "language", "time_windows",
            "ping_budget_per_week", "response_sla_hours", "provenance")


def _is_pos_int_or_null(v) -> bool:
    """A budget/SLA value: a non-negative int, or null meaning 'unbounded / not yet set'."""
    return v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0)


def validate(c) -> list:
    """Return the list of contract faults ([] == well-formed). The single reader-side gate: callers
    REFUSE a contract whose list is non-empty (Rule #8), they never proceed on a warning."""
    errs = []
    if not isinstance(c, dict):
        return ["contract is not an object"]
    for k in REQUIRED:
        if k not in c:
            errs.append(f"missing required key: {k}")
    if c.get("version") != CONTRACT_VERSION:
        errs.append(f"version must be {CONTRACT_VERSION!r}, got {c.get('version')!r}")
    if not c.get("handle"):
        errs.append("handle is empty")

    ch = c.get("channel")
    if not isinstance(ch, dict):
        errs.append("channel must be an object {primary, fallback}")
    else:
        if ch.get("primary") not in CHANNELS:
            errs.append(f"channel.primary must be one of {CHANNELS}, got {ch.get('primary')!r}")
        if ch.get("fallback") is not None and ch.get("fallback") not in CHANNELS:
            errs.append(f"channel.fallback must be null or one of {CHANNELS}, got {ch.get('fallback')!r}")

    if c.get("language") not in LANGUAGES:
        errs.append(f"language must be one of {LANGUAGES}, got {c.get('language')!r}")

    tw = c.get("time_windows")
    if not isinstance(tw, dict):
        errs.append("time_windows must be an object")
    else:
        if not tw.get("timezone"):
            errs.append("time_windows.timezone is empty")
        if not isinstance(tw.get("preferred"), list):
            errs.append("time_windows.preferred must be a list of [start,end] strings")
        if not isinstance(tw.get("blackout_days", []), list):
            errs.append("time_windows.blackout_days must be a list")

    # ping budget + SLA: BOTH directions present and well-typed (the contract is bidirectional)
    for field in ("ping_budget_per_week", "response_sla_hours"):
        d = c.get(field)
        if not isinstance(d, dict):
            errs.append(f"{field} must be an object with both directions")
            continue
        for dir_ in DIRECTIONS:
            if dir_ not in d:
                errs.append(f"{field}.{dir_} missing (contract must state both directions)")
            elif not _is_pos_int_or_null(d[dir_]):
                errs.append(f"{field}.{dir_} must be a non-negative int or null, got {d[dir_]!r}")

    prov = c.get("provenance")
    if not isinstance(prov, dict) or not prov.get("confirmer"):
        errs.append("provenance.confirmer is required (e.g. 'inferred' or 'mohamed')")
    return errs


# ── manifest-driven inference (conservative; never claims his confirmation) ────────────────────
def _manifest(handle):
    p = B / "clients" / handle / "manifest.json"
    if not p.exists():
        return {}
    try:
        with open(p) as f:
            return json.load(f).get("surfaces", {}).get("profile", {})
    except Exception:
        return {}


def _infer_language(bio: str) -> str:
    has_ar = bool(re.search(r"[؀-ۿ]", bio))
    # latin words of length >= 3 that aren't just a handle/url fragment
    has_en = bool(re.search(r"[A-Za-z]{3,}", re.sub(r"https?://\S+|@\S+|#\S+", " ", bio)))
    if has_ar and has_en:
        return "bilingual"
    if has_en and not has_ar:
        return "en"
    return "ar"  # Saudi default


def _infer_fallback(bio: str, url) -> str:
    b = (bio or "").lower()
    if "snapchat" in b:
        return "snapchat"
    if "whatsapp" in b or "wa.me" in b:
        return "whatsapp"
    if url:
        return "link_in_bio"
    return "email"


def infer_defaults(handle: str) -> dict:
    """Build a conservative, valid contract from the manifest. confirmer='inferred' — a stub, not truth."""
    prof = _manifest(handle)
    bio = prof.get("bio") or ""
    url = prof.get("external_url")
    today = date.today().isoformat()
    return {
        "version": CONTRACT_VERSION,
        "handle": handle,
        "status": "inferred_unconfirmed",          # consumers must not treat as his truth until confirmed
        "channel": {"primary": "instagram_dm", "fallback": _infer_fallback(bio, url)},
        "language": _infer_language(bio),
        "time_windows": {
            "timezone": "Asia/Riyadh",
            "preferred": [["09:00", "21:00"]],
            "blackout_days": [],                    # Hijri/blackout filled by the blackout gate later
        },
        # conservative: we ping rarely; the client is unbounded inbound (null) until they ask otherwise
        "ping_budget_per_week": {"us_to_client": 2, "client_to_us": None},
        "response_sla_hours": {"us_to_client": 24, "client_to_us": 48},
        "provenance": {
            "source": f"inferred:manifest({handle})",
            "confirmer": "inferred",
            "date": today,
            "note": "B158 stub — defaults from manifest; awaits Mohamed confirmation (gated card, later step)",
        },
    }


def _path(handle):
    return B / "clients" / handle / "profile" / "comm_contract.json"


def load(handle: str):
    """The typed accessor any future comm/ping organ calls. Returns the contract dict, or None if
    none exists. REFUSES (raises) a present-but-invalid contract — a corrupt organ is never served."""
    p = _path(handle)
    if not p.exists():
        return None
    with open(p) as f:
        c = json.load(f)
    errs = validate(c)
    if errs:
        raise ValueError(f"comm_contract for {handle} is invalid: {errs}")
    return c


def write_stub(handle: str) -> Path:
    c = infer_defaults(handle)
    errs = validate(c)
    if errs:                                         # never write an invalid organ (Rule #8)
        raise ValueError(f"refusing to write invalid stub for {handle}: {errs}")
    p = _path(handle)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2))
    return p


def status():
    rows = []
    for h in CLIENTS:
        p = _path(h)
        if not p.exists():
            rows.append((h, "MISSING", ""))
            continue
        try:
            c = load(h)
            rows.append((h, c.get("status", "ok"), f"{c['channel']['primary']}/{c['language']}"))
        except ValueError as e:
            rows.append((h, "INVALID", str(e)[:60]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["stub", "validate", "status"])
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    targets = [a.handle] if a.handle else CLIENTS

    if a.cmd == "stub":
        for h in targets:
            p = write_stub(h)
            print(f"✅ wrote {p.relative_to(B)}")
        return 0

    if a.cmd == "validate":
        bad = 0
        for h in targets:
            c = load(h)
            if c is None:
                print(f"⚠️  {h}: no contract")
                bad += 1
                continue
            errs = validate(c)
            if errs:
                print(f"🔴 {h}: {errs}")
                bad += 1
            else:
                print(f"✅ {h}: valid ({c['channel']['primary']}/{c['language']})")
        return 1 if bad else 0                       # REFUSE: non-zero exit on any fault

    # status
    for h, st, extra in status():
        print(f"  {h:16} {st:22} {extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
