#!/usr/bin/env python3
"""B_gate_state — PER-CLIENT, PER-OCCASION-FAMILY AUTONOMY STATE (the escalate/relax substrate).

A SEPARATE axis from trust.json (client-CONSENT, computed by trust_ladder.py). This is the
MACHINE's autonomy: how far the producer may self-run on a given occasion family before a human
eye is required. Like the trust ladder, it is COMPUTED from the append-only ledger, never
asserted. The level is only ever PROPOSED; the ACTIVE level starts BLOCKED and only a human
advances it — AI NEVER auto-advances (the trust-ladder / STRONG-CHAIR principle).

FAIL-CLOSED (Rule #8, REFUSE-DON'T-WARN): a missing/corrupt gate_state.json, an unknown client,
or a family with no clean record all read as SAMPLED — the producer must show that slot to the
human eye. Only an explicitly human-set active_level of "FULL" relaxes a family, and MAJOR
occasions (Ramadan / Eid / National / Founding) NEVER relax — that is the seam B_occasion_crit
formalizes (auto-force SAMPLED on the culturally critical dates).

  Writer:  rebuild()                         -> data/gate_state.json   (replay ledger per client)
  Reader:  gate_mode(handle, family)         -> "SAMPLED" | "FULL"     (fail-closed to SAMPLED)
           autonomy_for(handle, family)      -> the family's full state dict (fail-closed default)
  Wired:   produce_batch.py stamps gate_mode onto every manifest post (Rule #6, live consumer).

Usage:
  python3 scripts/gate_state.py                    # rebuild + print summary
  python3 scripts/gate_state.py --check            # exit 1 if the on-disk file is stale
  python3 scripts/gate_state.py --mode H FAMILY    # print the fail-closed gate_mode for one slot
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GATE_PATH = BASE / "data" / "gate_state.json"

# Same verdict vocabulary the trust ladder reads — only real human verdicts move autonomy.
APPROVE_TYPES = {"client_approved", "pick_selected"}
RESET_TYPES = {"client_rejected"}
# A recorded reason_code on a verdict is a breach signal (factual_error / too_generic /
# culture_breach all seen in the live ledgers) — it zeroes the clean-batch counter.
BREACH_REASONS = {"factual_error", "too_generic", "culture_breach", "red_line"}

# Clean approvals in a family before FULL autonomy is PROPOSED (never auto-granted).
CLEAN_BATCH_TO_PROPOSE = 5

# Culturally critical families that NEVER relax to FULL, whatever the counters say. This is the
# conservative floor B_occasion_crit will formalize into a live drift alarm.
MAJOR_FAMILIES = {
    "ramadan", "ramadan_evergreen", "eid_al_fitr", "eid_al_adha",
    "saudi_national_day", "saudi_founding_day",
}

FAIL_CLOSED_MODE = "SAMPLED"   # the answer whenever we are not certain a family earned FULL


def _real_clients():
    """Client handles with a profile, via fingerprint_status when importable, else a disk scan."""
    try:
        sys.path.insert(0, str(BASE / "scripts"))
        import fingerprint_status
        return list(fingerprint_status.real_clients())
    except Exception:
        cl = BASE / "clients"
        return sorted(p.name for p in cl.iterdir()
                      if p.is_dir() and (p / "events/ledger.jsonl").exists()) if cl.exists() else []


def _family_of(subject: str) -> str | None:
    """Parse the occasion family from a ledger subject 'DATE__family → caption'. None if absent."""
    if not subject or "__" not in subject:
        return None
    tail = subject.split("__", 1)[1]
    fam = tail.split("→")[0].split()[0].strip() if tail.split() else ""
    return fam or None


def _read_existing() -> dict:
    """Carry human-set active_level across rebuilds. Missing/corrupt -> empty (all BLOCKED)."""
    if not GATE_PATH.exists():
        return {}
    try:
        return json.loads(GATE_PATH.read_text(encoding="utf-8")).get("clients", {})
    except (json.JSONDecodeError, OSError):
        return {}


def replay(handle: str, prior: dict | None = None) -> dict:
    """Replay one client's ledger into per-family autonomy state. Computed, never asserted."""
    prior = prior or {}
    lf = BASE / "clients" / handle / "events" / "ledger.jsonl"
    fams: dict[str, dict] = {}
    corrupt = 0   # a torn ledger line could hide a breach -> would inflate cleanliness (fail-OPEN)

    def _f(name):
        return fams.setdefault(name, {"approved": 0, "clean_batch": 0,
                                      "breaches": 0, "last_breach": None})

    for line in (lf.read_text(encoding="utf-8").strip().split("\n") if lf.exists() else []):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1   # do NOT silently trust the rest — force this client fail-closed below
            continue
        if e.get("confirmer") not in ("mohamed", "client"):
            continue  # only real human verdicts move autonomy
        fam = _family_of(e.get("subject", ""))
        if not fam:
            continue
        rec = _f(fam)
        if e.get("reason_code") in BREACH_REASONS or e.get("type") in RESET_TYPES:
            rec["clean_batch"] = 0
            rec["breaches"] += 1
            rec["last_breach"] = {"ts": e.get("ts"), "reason": e.get("reason_code") or e.get("type")}
        elif e.get("type") in APPROVE_TYPES:
            rec["approved"] += 1
            rec["clean_batch"] += 1

    out = {}
    for fam, rec in fams.items():
        major = fam in MAJOR_FAMILIES
        earned = rec["clean_batch"] >= CLEAN_BATCH_TO_PROPOSE
        # Fail-CLOSED on a torn ledger: a corrupt line may have swallowed a breach, so never
        # PROPOSE relaxation off a ledger we couldn't fully read.
        proposed = "FULL" if (earned and not major and not corrupt) else "SAMPLED"
        # active_level is HUMAN-owned: preserve the prior value, default BLOCKED. AI never sets FULL.
        active = (prior.get(fam) or {}).get("active_level", "BLOCKED")
        out[fam] = {
            "active_level": active,
            "proposed_level": proposed,
            "clean_batch": rec["clean_batch"],
            "approved": rec["approved"],
            "breaches": rec["breaches"],
            "last_breach": rec["last_breach"],
            "confidence": round(min(1.0, rec["clean_batch"] / CLEAN_BATCH_TO_PROPOSE), 2),
            "major": major,
            "ledger_corrupt": corrupt,   # >0 => proposal pinned to SAMPLED, ledger needs a look
        }
    return out


def rebuild() -> dict:
    """Recompute every client's autonomy state and persist data/gate_state.json."""
    prior = _read_existing()
    clients = {h: replay(h, prior.get(h)) for h in _real_clients()}
    doc = {
        "_doc": "B_gate_state — machine autonomy per client/occasion-family. Computed from the "
                "ledger, never asserted; active_level is human-owned (AI never advances). "
                "FAIL-CLOSED: absent => SAMPLED.",
        "clean_batch_to_propose": CLEAN_BATCH_TO_PROPOSE,
        "major_families": sorted(MAJOR_FAMILIES),
        "clients": clients,
    }
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def _load() -> dict | None:
    if not GATE_PATH.exists():
        return None
    try:
        return json.loads(GATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def autonomy_for(handle: str, family: str) -> dict:
    """The family's stored state, or a fail-closed BLOCKED/SAMPLED default when unknown."""
    doc = _load()
    default = {"active_level": "BLOCKED", "proposed_level": "SAMPLED", "clean_batch": 0,
               "approved": 0, "breaches": 0, "last_breach": None, "confidence": 0.0,
               "major": family in MAJOR_FAMILIES, "fail_closed": True}
    if not doc:
        return default
    ent = (doc.get("clients", {}).get(handle, {}) or {}).get(family)
    return ent if ent else default


def gate_mode(handle: str, family: str) -> str:
    """SAMPLED (human eye required) or FULL (machine may self-run). Fail-closed to SAMPLED.

    Relaxes to FULL only when a human has set active_level=FULL AND the family is not MAJOR.
    Any uncertainty — no file, unknown client/family, a MAJOR occasion — stays SAMPLED."""
    if not family or family in MAJOR_FAMILIES:
        return FAIL_CLOSED_MODE
    ent = autonomy_for(handle, family)
    return "FULL" if ent.get("active_level") == "FULL" and not ent.get("major") else FAIL_CLOSED_MODE


def _summary(doc: dict) -> str:
    lines = []
    for h, fams in sorted(doc.get("clients", {}).items()):
        relaxable = sum(1 for f in fams.values() if f["proposed_level"] == "FULL")
        lines.append(f"  {h}: {len(fams)} famil(y/ies) tracked · {relaxable} propose FULL · "
                     f"active FULL: {sum(1 for f in fams.values() if f['active_level']=='FULL')}")
        for fam, s in sorted(fams.items()):
            flag = " [MAJOR]" if s["major"] else ""
            lines.append(f"     {fam:22} clean={s['clean_batch']} conf={s['confidence']} "
                         f"active={s['active_level']} proposed={s['proposed_level']}{flag}")
    return "\n".join(lines) or "  (no clients)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if on-disk file differs from a fresh recompute")
    ap.add_argument("--mode", nargs=2, metavar=("HANDLE", "FAMILY"), help="print the fail-closed gate_mode")
    a = ap.parse_args()

    if a.mode:
        print(gate_mode(a.mode[0], a.mode[1]))
        return

    if a.check:
        on_disk = _load()
        prior = (on_disk or {}).get("clients", {}) if on_disk else {}
        fresh = {h: replay(h, prior.get(h)) for h in _real_clients()}
        if not on_disk or on_disk.get("clients") != fresh:
            print("🔴 gate_state.json STALE — run: python3 scripts/gate_state.py", file=sys.stderr)
            sys.exit(1)
        print("✅ gate_state.json fresh")
        return

    doc = rebuild()
    print(f"✅ gate_state rebuilt — {len(doc['clients'])} client(s), fail-closed to {FAIL_CLOSED_MODE}")
    print(_summary(doc))


if __name__ == "__main__":
    main()
