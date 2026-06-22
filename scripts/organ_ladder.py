#!/usr/bin/env python3
"""ORGAN LADDER MECHANICS (backlog B087, June 22) — the promotion/demotion engine.

B086 (provenance_ladder.py) is the CENSUS: where each organ's file *currently*
stands (the 🟢/🟡/🔴 light fingerprint_status asserts). This module is the
MECHANICS: it replays the *evidence stream* (events/ledger.jsonl) and computes
what rung each organ has actually EARNED, by the rule:

  confirmed  ← a real human (mohamed/client) has spoken FOR that organ, uncontradicted
  inferred   ← ≥3 evidences accrued (any confirmer, incl. rabie_provisional/machine)
  default    ← fewer than 3 evidences, or the organ was just contradicted
  demotion   ← a contradiction event (reason_code breach) INSTANTLY resets the organ
               (counter→0, confirmed claim cleared) — exactly trust_ladder's demote law

This is pure replay — counted, never asserted (Rule #9): it invents no new
inference, it only tallies events the ledger already carries. `rabie_provisional`
stamps are PROVISIONAL and so can lift an organ to *inferred* but NEVER to
*confirmed* — only the real Mohamed/client advances an organ to confirmed
(mirrors trust_ladder: "AI never advances a level").

The CONSUMER (Rule #6 — every writer needs a reader, same cycle): `pending_moves`
joins the EARNED rung against the organ file's CURRENT fingerprint light and
surfaces the GAP — organs the evidence says should be promoted (the file lags the
proof) or demoted (a contradiction the file hasn't absorbed). That gap list IS the
work-queue for the gap-question loop (Rule #11). It is PROVISIONAL and never
auto-applied to the organ file — promotion stays a human/PR step (Rules #7/#11).

Usage: python3 scripts/organ_ladder.py [--handle X]
"""
import argparse
import json
from pathlib import Path

from fingerprint_status import status, G, Y, R

BASE = Path(__file__).parent.parent

# Event type -> the fingerprint organ row it bears on. Only types that map to a
# real fingerprint_status row are listed, so `pending_moves` can compare earned
# vs current on the SAME organ name. (occasion_gold / intake_answer / capacity
# carry no fingerprint row of their own and are intentionally excluded — counting
# them here would invent a rung the census can't reconcile.)
ORGAN_EVENTS = {
    "voice_rating": "VOICE",
    "red_line_added": "RED LINES",
    "goal_declared": "GOALS",
    "truth_confirmed": "TRUTH",
    "payment_received": "PAYMENT",
    "renewal": "PAYMENT",
}

# Only a real human verdict can carry an organ to *confirmed* (Rule: AI/RABIE
# provisional never self-promotes to production-grade truth).
HUMAN_CONFIRMERS = {"mohamed", "client"}

# A breach reason_code is a contradiction → instant demotion of that organ.
CONTRADICTION_RC = {"culture_breach", "off_voice", "factual_error", "wrong_goal", "too_generic"}

# current fingerprint light -> rung name (same mapping provenance_ladder uses)
_LIGHT_TO_RUNG = {G: "confirmed", Y: "inferred", R: "default"}
_RUNG_ORDER = {"default": 0, "inferred": 1, "confirmed": 2}

INFERRED_AT = 3  # ≥3 evidences earns inferred


def _events(handle: str) -> list[dict]:
    lf = BASE / "clients" / handle / "events" / "ledger.jsonl"
    if not lf.exists():
        return []
    out = []
    for line in lf.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue  # a malformed line never silently miscounts an organ
    return out


def earned_rungs(handle: str, events: list[dict] | None = None) -> dict:
    """Replay the evidence stream → the rung each mapped organ has EARNED.

    Returns {organ: {rung, evidence, human, contradicted, reason}}. Chronological
    replay (ledger is append-only/ordered): each evidence increments the organ;
    a contradiction event resets it on the spot (counter→0, confirmed claim gone).
    """
    events = events if events is not None else _events(handle)
    state: dict[str, dict] = {}
    for e in events:
        organ = ORGAN_EVENTS.get(e.get("type"))
        if organ is None:
            continue
        st = state.setdefault(organ, {"evidence": 0, "human": 0, "contradicted": False, "reason": None})
        if e.get("reason_code") in CONTRADICTION_RC:        # instant demotion
            st["evidence"] = 0
            st["human"] = 0
            st["contradicted"] = True
            st["reason"] = e.get("reason_code")
            continue
        st["evidence"] += 1
        st["contradicted"] = False                          # a clean evidence clears prior breach
        st["reason"] = None
        if e.get("confirmer") in HUMAN_CONFIRMERS:
            st["human"] += 1

    out = {}
    for organ, st in state.items():
        if st["human"] >= 1 and not st["contradicted"]:
            rung = "confirmed"
        elif st["evidence"] >= INFERRED_AT:
            rung = "inferred"
        else:
            rung = "default"
        out[organ] = {"rung": rung, "evidence": st["evidence"], "human": st["human"],
                      "contradicted": st["contradicted"], "reason": st["reason"]}
    return out


def _current_rungs(handle: str) -> dict:
    """The organ file's CURRENT rung (the light fingerprint_status already asserts)."""
    out = {}
    for name, light, _note in status(handle)["rows"]:
        rung = _LIGHT_TO_RUNG.get(light)
        if rung is not None:
            out[name] = rung
    return out


def pending_moves(handle: str, events: list[dict] | None = None) -> list[dict]:
    """CONSUMER: earned rung vs current fingerprint rung → the move queue.

    A 'promote' = evidence has earned a higher rung than the file shows (the file
    lags the proof). A 'demote' = the file claims more than the (contradicted)
    evidence now supports. Equal rungs are not surfaced. All PROVISIONAL — the
    actual organ-file move is a human/PR step (Rules #7/#11), never auto-applied.
    """
    earned = earned_rungs(handle, events)
    current = _current_rungs(handle)
    moves = []
    for organ, e in earned.items():
        cur = current.get(organ)
        if cur is None:
            continue
        d = _RUNG_ORDER[e["rung"]] - _RUNG_ORDER[cur]
        if d == 0:
            continue
        moves.append({"handle": handle, "organ": organ, "current": cur,
                      "earned": e["rung"], "direction": "promote" if d > 0 else "demote",
                      "evidence": e["evidence"], "human": e["human"],
                      "contradicted": e["contradicted"], "reason": e["reason"]})
    return moves


def _clients() -> list[str]:
    return sorted(d.name for d in (BASE / "clients").iterdir() if (d / "profile").is_dir())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    args = ap.parse_args()
    handles = [args.handle] if args.handle else _clients()

    print("═══ ORGAN LADDER — earned-vs-current moves (PROVISIONAL, human/PR applies) ═══")
    total = 0
    for h in handles:
        moves = pending_moves(h)
        if not moves:
            print(f"  {h:18} — no pending moves (file matches the evidence)")
            continue
        for m in moves:
            arrow = "▲" if m["direction"] == "promote" else "▼"
            why = (f"{m['evidence']} ev / {m['human']} human"
                   + (f" / CONTRADICTED:{m['reason']}" if m["contradicted"] else ""))
            print(f"  {h:18} {arrow} {m['organ']:10} {m['current']} → {m['earned']}   ({why})")
            total += 1
    print(f"\n{total} pending organ move(s) across {len(handles)} client(s) — "
          "feed the gap-question loop (Rule #11); none auto-applied (Rules #7/#11).")


if __name__ == "__main__":
    main()
