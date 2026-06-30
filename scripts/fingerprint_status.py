#!/usr/bin/env python3
"""FINGERPRINT STATUS (pyramid GAP-08, June 11) — the inference quarantine view.
Voice and identity rendered side-by-side per client so statistics can never
impersonate completeness: voice can be GREEN from data; identity is RED until
the CLIENT speaks. The albaik lesson made visible, permanently.

Usage: python3 scripts/fingerprint_status.py            # all clients
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
G, Y, R = "🟢", "🟡", "🔴"

# B149 (June 21) — the PAYMENT row. The commercial pulse, computed ONLY from payment-
# relevant events so it is INDEPENDENT of approval activity: a client who keeps tapping
# انشر/approve but stopped paying must look different from a healthy one — the existing
# approval rows (Q-RATIO, TRUST) stay green off approvals while PAYMENT independently
# goes red. Append-only semantics (CONVENTIONS rule #6): the MOST RECENT payment-relevant
# event is the live state — a later payment_received clears an earlier late/overdue mark.
_PAY_TYPES = {"payment_received", "renewal", "scope_change"}
_LATE_TOKENS = ("overdue", "past_due", "late", "lapsed", "delinquent", "unpaid")
_PENDING_TOKENS = ("invoice_sent", "invoice_issued", "invoice", "pending", "sent", "awaiting")


def _is_payment_event(e: dict) -> bool:
    t = (e.get("type") or "").lower()
    return t in _PAY_TYPES or t.startswith("invoice") or "payment" in t or t == "renewal_lapsed"


def _late_signal(e: dict) -> bool:
    t = (e.get("type") or "").lower()
    if any(tok in t for tok in _LATE_TOKENS):
        return True
    status_field = str(e.get("status") or "").lower()
    if any(tok in status_field for tok in _LATE_TOKENS):
        return True
    return bool(e.get("overdue") or e.get("late") or e.get("lapsed"))


def _pending_signal(e: dict) -> bool:
    t = (e.get("type") or "").lower()
    status_field = str(e.get("status") or "").lower()
    if t == "payment_received" or t == "renewal":
        return False
    return any(tok in t for tok in _PENDING_TOKENS) or any(tok in status_field for tok in _PENDING_TOKENS)


def payment_status(events: list) -> tuple:
    """(light, note) for the PAYMENT row. RED = invoice past due / payment late / renewal
    lapsed. GREEN = a payment on record and the latest commercial signal is clean. YELLOW =
    no commercial ledger yet (pre-commercial pilot) or an invoice still pending — never green,
    never red, so an unpaid pilot is not mistaken for a paying client."""
    pay = [e for e in events if isinstance(e, dict) and _is_payment_event(e)]
    if not pay:
        return (Y, "no payment ledger — pre-commercial")
    # append-only: most recent payment-relevant event is the live commercial state
    latest = sorted(pay, key=lambda e: str(e.get("ts") or ""))[-1]
    if _late_signal(latest):
        t = (latest.get("type") or "").lower()
        why = "renewal lapsed" if "renewal" in t or "lapsed" in t else "invoice past due / payment late"
        return (R, f"{why} (latest: {latest.get('ts','?')})")
    if _pending_signal(latest):
        return (Y, f"invoice pending — awaiting payment ({latest.get('ts','?')})")
    return (G, f"paid — current ({latest.get('ts','?')})")


def _load_events(handle: str) -> list:
    p = BASE / "clients" / handle / "events" / "ledger.jsonl"
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def real_clients() -> list[str]:
    """The ONE canonical list of real clients (Rule #3 — a single boundary across the
    whole system). A real client is gated by a confirmed profile spine
    (cultural_overrides.json), matching build_visual_review_checklist.clients_with_profile.
    A bare profile/ dir (test scratch like testbrand, empty typo-dups) is NOT a client.
    Every census/report/test must enumerate through this, never re-glob profile/ inline."""
    return sorted(d.name for d in (BASE / "clients").iterdir()
                  if (d / "profile" / "cultural_overrides.json").exists())


def status(handle: str) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    fpf = pdir / "fingerprint.json"
    if not fpf.exists():
        # Fail-CLOSED and LOUD (Rule #8): a real client (one with cultural_overrides.json)
        # must never be silently dropped from any census just because its fingerprint
        # build broke. Callers enumerate real clients via cultural_overrides; reaching
        # here means the spine is missing — alarm, don't skip.
        raise FileNotFoundError(
            f"{handle}: profile/fingerprint.json missing — real client without a "
            f"fingerprint spine (rebuild it); if this is test scratch it must not live "
            f"under clients/ with a profile/.")
    fp = json.loads(fpf.read_text())
    tp = json.loads((pdir / "truth_pack.json").read_text())
    rl = json.loads((pdir / "red_lines.json").read_text())
    go = json.loads((pdir / "goals.json").read_text())
    st = json.loads((pdir / "state.json").read_text())
    v = fp["l2_voice"]
    voice = (G if v.get("love_lines") else (Y if (v.get("dialect") or v.get("speaker")) else R),
             "client-confirmed" if v.get("love_lines") else
             (f"speaker RULED ({v.get('speaker')}) — love/hate lines pending"
              if v.get("speaker") else
              ("stats only — describes the past, not a contract" if v.get("dialect") else
               "no voice — needs birth (newborn) or extraction")))
    l1 = fp["l1_strategy"]
    identity = (G if l1.get("who_speaks") else R,
                "confirmed" if l1.get("who_speaks") else "client-only: who-speaks/USP/positioning all empty")
    truth = (G if tp["confirmed"] else (Y if tp["product_candidates"] else R),
             f"{len(tp['confirmed'])} confirmed / {len(tp['product_candidates'])} candidates / {len(tp['channels'])} channels")
    red = (G if rl["lines"] else R,
           f"{len(rl['lines'])} lines — strictest defaults govern" if not rl["lines"] else f"{len(rl['lines'])} lines")
    goals = (G if go["answered"] >= 4 else (Y if go["answered"] else R), f"{go['answered']}/{go['of']} answered")
    trust = (G, "0 violations — budget intact")
    tv = BASE / "data/trust_violations.jsonl"
    if tv.exists():
        n = sum(1 for l in tv.read_text(encoding="utf-8").splitlines()
                if l.strip() and json.loads(l).get("handle") == handle)
        if n:
            # B030: trust budget — target 0 FOREVER; any violation is red, no amnesty
            trust = (R, f"{n} violation(s) — a re-asked question is on record")
    ratio = (G, "no outbound drafts staged")
    drafts = BASE / "clients" / handle / "presentations" / "outbound_questions.json"
    if drafts.exists():
        qs = json.loads(drafts.read_text())
        choice = sum(1 for q in qs if q.get("kind") == "choice")
        open_q = sum(1 for q in qs if q.get("kind") == "open")
        ok = open_q == 0 or choice >= 4 * open_q
        ratio = (G if ok else R,
                 f"{choice} choice : {open_q} open" + ("" if ok else " — BELOW 4:1, redraft"))
    payment = payment_status(_load_events(handle))
    return {"handle": handle, "state": st["state"], "silent_days": st.get("silent_days"),
            "rows": [("VOICE", *voice), ("IDENTITY", *identity), ("TRUTH", *truth),
                      ("RED LINES", *red), ("GOALS", *goals), ("TRUST", *trust),
                      ("PAYMENT", *payment), ("Q-RATIO", *ratio)]}


def main():
    clients = real_clients()
    for h in clients:
        s = status(h)
        print(f"\n═══ {h} — {s['state']}" + (f" (silent {s['silent_days']}d)" if s.get("silent_days") else ""))
        for name, light, note in s["rows"]:
            print(f"  {light} {name:10} {note}")
    print("\nLAW: a profile is PRODUCTION-READY only when no row is 🔴. "
          "Stats may light VOICE yellow — never green, never identity.")


if __name__ == "__main__":
    main()
