#!/usr/bin/env python3
"""KILL REGISTRY — Phase 0 of the Scale On-ramp: the SUBTRACTIVE taste flywheel.

THE PROBLEM (verified June 24, confirmed by Claude+DeepSeek with grep evidence): RABIE/Mohamed
verdicts were LOGGED (data/rabie_verdicts.jsonl) but never CONSUMED before the next generation —
the system could be told a (brand, product, setup) is wrong, get it killed, and produce the exact
same thing again. And learned_gate_rules.json was GLOBAL (a food rule could kill a fitness post).

WHY SUBTRACTIVE, NOT A RANKER (the design decision, fact-grounded): the taste data is SPARSE
(53 pairwise prefs / 5 verdicts / 13 gold) and the AI judge scores ~random (+0.08) — a learned
ranker on this volume reproduces the 33%-below-coin collapse. So Phase 0 does NOT chase a score.
It SUBTRACTS Mohamed's explicit dislikes: every kill becomes a hard fingerprint the pipeline
refuses to repeat. Hard rules are safe on sparse data and can't make output worse. (The learned
ranker is Phase 2, once onboarding generates volume.)

THE SHAPE (Rule #6 consumer-law + Rule #14 judge-persists-feeds-forward + Rule #8 refuse):
  rabie_verdicts.jsonl  --ingest-->  data/kill_fingerprints.json  --get_pending_combo()-->
  produce_complete_post PRE-FLIGHT GATE (exit 1 before any FAL spend) + caption_filter lexical bans.

The fingerprint store has TWO scopes (fixing the global-bleed bug):
  "{handle}|{product}|{setup}"  exact-combo kills (e.g. "albaik|دبل بيك|*")
  "{scope}|lexical|all"         lexical bans, scope = a handle OR "global" (cross-brand Saudi no-nos)

Kills are PENDING until the machine is fixed (then resolve_kill marks them resolved → may run
again) — a pending kill BLOCKS that combo. A pending kill older than TTL_DAYS auto-resolves on
read (a forgotten kill must not permanently block a client). NEVER deletes — supersedes
learned_gate_rules.json, which is left intact for back-compat.

Usage:
  python3 scripts/kill_registry.py --ingest                 # rabie_verdicts.jsonl -> fingerprints
  python3 scripts/kill_registry.py --check albaik "دبل بيك" hero_studio
  python3 scripts/kill_registry.py --resolve "albaik|دبل بيك|*"
  python3 scripts/kill_registry.py --ban global "خمر,بيرة" "alcohol — Saudi red line"
  python3 scripts/kill_registry.py --list
"""
import argparse
import json
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
VERDICTS = B / "data/rabie_verdicts.jsonl"
KILL_FP = B / "data/kill_fingerprints.json"
TTL_DAYS = 7
TTL = TTL_DAYS * 86400

WILDCARD = "*"   # a kill logged without a specific setup applies to ALL setups of that product


# ── store I/O ────────────────────────────────────────────────────────────────────────────────
def load_kill_fingerprints() -> dict:
    if not KILL_FP.exists():
        return {}
    try:
        return json.loads(KILL_FP.read_text())
    except Exception:
        return {}


def save_kill_fingerprints(data: dict) -> None:
    KILL_FP.parent.mkdir(parents=True, exist_ok=True)
    KILL_FP.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _combo_key(handle: str, product: str, setup: str = WILDCARD) -> str:
    return f"{handle}|{product}|{setup or WILDCARD}"


def _now() -> int:
    return int(time.time())


# ── ingest: rabie verdicts -> pending combo kills (the WRITER) ─────────────────────────────────
def ingest_new_verdicts() -> dict:
    """Read every RABIE verdict; turn each fix/kill into a PENDING combo fingerprint. Idempotent:
    re-running updates the reason but NEVER overwrites a human-resolved/overridden entry (respects
    the fix). Banks are skipped (a bank is not a mistake to avoid)."""
    fp = load_kill_fingerprints()
    if not VERDICTS.exists():
        return fp
    ingested = 0
    for ln in VERDICTS.read_text().splitlines():
        if not ln.strip():
            continue
        try:
            v = json.loads(ln)
        except Exception:
            continue
        if v.get("verdict") not in ("fix", "kill"):
            continue
        handle, product = v.get("handle"), v.get("product")
        if not handle or not product:
            continue
        setup = v.get("setup") or WILDCARD   # image verdicts carry no setup → apply to all
        key = _combo_key(handle, product, setup)
        # never clobber a human resolution
        if fp.get(key, {}).get("status") in ("resolved", "overridden"):
            continue
        reason = (v.get("rabie_note") or "").strip()
        wrong = v.get("what_is_wrong") or []
        if wrong:
            reason = (reason + " — " if reason else "") + "; ".join(wrong[:2])
        fp[key] = {
            "status": "pending",
            "kill_reason": reason or "RABIE kill",
            "verdict_id": str(v.get("ts", "")),
            "overall": v.get("overall"),
            "created_at": int(v.get("ts") or _now()),
            "resolved_at": None,
            "fingerprint_type": "exact_combo",
        }
        ingested += 1
    save_kill_fingerprints(fp)
    return fp


# ── the READER (consumed by produce_complete_post pre-flight gate) ─────────────────────────────
def get_pending_combo(handle: str, product: str, setup: str = WILDCARD):
    """Return the blocking kill dict for (handle, product, setup), or None. Checks the exact key
    AND the product-wide wildcard. Auto-resolves (and persists) a pending kill older than TTL —
    a forgotten kill must never permanently block a client (Rule: never get stuck)."""
    fp = load_kill_fingerprints()
    changed = False
    for key in (_combo_key(handle, product, setup), _combo_key(handle, product, WILDCARD)):
        e = fp.get(key)
        if not e or e.get("status") != "pending":
            continue
        if _now() - int(e.get("created_at", 0)) > TTL:
            e["status"] = "auto_resolved"
            e["resolved_at"] = _now()
            changed = True
            continue
        if changed:
            save_kill_fingerprints(fp)
        return {**e, "_key": key}
    if changed:
        save_kill_fingerprints(fp)
    return None


def resolve_kill(kill_key: str) -> bool:
    """Mark a kill resolved (the machine was fixed) → the combo may run again. Returns True if found."""
    fp = load_kill_fingerprints()
    if kill_key not in fp:
        return False
    fp[kill_key]["status"] = "resolved"
    fp[kill_key]["resolved_at"] = _now()
    save_kill_fingerprints(fp)
    return True


# ── lexical bans (the caption-side, per-client + global) ───────────────────────────────────────
def add_lexical_ban(scope: str, terms, reason: str = "") -> None:
    """scope = a client handle OR 'global'. terms = list[str] or comma string. Active immediately."""
    if isinstance(terms, str):
        terms = [t.strip() for t in terms.split(",") if t.strip()]
    fp = load_kill_fingerprints()
    key = f"{scope}|lexical|all"
    entry = fp.get(key) or {"status": "active", "fingerprint_type": "lexical_ban",
                            "kill_reason": reason, "banned_terms": [], "created_at": _now(),
                            "resolved_at": None}
    have = set(entry.get("banned_terms", []))
    for t in terms:
        if t not in have:
            entry["banned_terms"].append(t)
            have.add(t)
    if reason:
        entry["kill_reason"] = reason
    entry["status"] = "active"
    fp[key] = entry
    save_kill_fingerprints(fp)


def get_lexical_bans(handle: str = "") -> list:
    """The banned terms a caption must avoid: global cross-brand bans + this client's own."""
    fp = load_kill_fingerprints()
    out = []
    for key in ("global|lexical|all", f"{handle}|lexical|all" if handle else None):
        if not key:
            continue
        e = fp.get(key)
        if e and e.get("status") == "active":
            out += e.get("banned_terms", [])
    # dedupe preserve order
    seen, res = set(), []
    for t in out:
        if t not in seen:
            seen.add(t); res.append(t)
    return res


def get_pending_killed_captions(handle: str, product: str) -> list:
    """Captions from pending kills for this product (for a future semantic-similarity check —
    Phase 0.5). Image-only verdicts carry no caption, so this is [] until caption-kills are logged."""
    fp = load_kill_fingerprints()
    out = []
    for key, e in fp.items():
        if e.get("status") == "pending" and e.get("caption") and key.startswith(f"{handle}|{product}|"):
            out.append(e["caption"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", action="store_true")
    ap.add_argument("--check", nargs="+", metavar=("HANDLE PRODUCT [SETUP]"))
    ap.add_argument("--resolve", metavar="KEY")
    ap.add_argument("--ban", nargs=3, metavar=("SCOPE", "TERMS", "REASON"))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.ingest:
        fp = ingest_new_verdicts()
        pend = sum(1 for e in fp.values() if e.get("status") == "pending")
        print(f"✅ ingested → {KILL_FP.relative_to(B)}  ·  {len(fp)} entries, {pend} pending")
        for k, e in fp.items():
            if e.get("status") == "pending":
                print(f"   ⛔ {k}  ←  {e.get('kill_reason','')[:80]}")
    elif a.check:
        h = a.check[0]; p = a.check[1]; s = a.check[2] if len(a.check) > 2 else WILDCARD
        hit = get_pending_combo(h, p, s)
        print(json.dumps(hit, ensure_ascii=False) if hit else f"clear — no pending kill for {h}|{p}|{s}")
    elif a.resolve:
        print("resolved ✅" if resolve_kill(a.resolve) else "key not found")
    elif a.ban:
        add_lexical_ban(a.ban[0], a.ban[1], a.ban[2])
        print(f"lexical ban added to {a.ban[0]}: {get_lexical_bans(a.ban[0] if a.ban[0]!='global' else '')}")
    elif a.list:
        print(json.dumps(load_kill_fingerprints(), ensure_ascii=False, indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
