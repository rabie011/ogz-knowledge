#!/usr/bin/env python3
"""PROVENANCE LADDER CENSUS (backlog B086, June 19) — where is each client's
profile still standing on defaults, and where has the CLIENT actually spoken?

This is a CONSUMER, not a new source of truth (Rule #6): it reads the exact
🟢/🟡/🔆 lights that fingerprint_status.status() already asserts and aggregates
them into a census — per organ (across clients) and per client (across organs).
It invents NO new inference; a rung here is the same light the quarantine view
already shows, just counted (Rule #9 — no number the system hasn't already earned).

The ladder (honest mapping, anchored to fingerprint_status):
  🟢 confirmed  — the client (or founder tap) has spoken; production-grade truth
  🟡 inferred   — stats/speaker-ruled only; describes the past, not a contract
  🔴 default    — strictest conservative defaults govern; the client is silent here

Reading it: an organ heavy with 🔴 across clients is where the gap-question loop
(Rule #11) should aim first; a client heavy with 🔴 is not production-ready
(LAW: production-ready only when no row is 🔴).

Usage: python3 scripts/provenance_ladder.py
"""
import json
from pathlib import Path

import fingerprint_status
from fingerprint_status import status, G, Y, R

BASE = Path(__file__).parent.parent

# the light fingerprint_status emits -> the rung name. ONE source, no re-inference.
_LIGHT_TO_RUNG = {G: "confirmed", Y: "inferred", R: "default"}
RUNGS = ("confirmed", "inferred", "default")


def _clients() -> list[str]:
    # Route through the ONE canonical real-client list (Rule #3 — single boundary).
    # A bare profile/ dir (test scratch like testbrand, empty typo-dups) is NOT a client
    # and must never pollute the census. Not fail-open: a real client always carries
    # cultural_overrides; if it carries that but lacks fingerprint.json, status() raises
    # LOUD (fail-closed, Rule #8).
    return fingerprint_status.real_clients()


def census(handles: list[str] | None = None) -> dict:
    """Aggregate fingerprint lights into a provenance census.

    Returns {per_organ, per_client, overall}, each carrying confirmed/inferred/
    default counts, a total, and pct_confirmed (0 when the organ/client is empty).
    """
    handles = handles if handles is not None else _clients()
    per_organ: dict[str, dict] = {}
    per_client: dict[str, dict] = {}
    overall = _blank()

    for h in handles:
        s = status(h)
        crow = _blank()
        for organ, light, _note in s["rows"]:
            rung = _LIGHT_TO_RUNG.get(light)
            if rung is None:                       # unknown light — never silently miscount
                continue
            per_organ.setdefault(organ, _blank())
            per_organ[organ][rung] += 1
            per_organ[organ]["total"] += 1
            crow[rung] += 1
            crow["total"] += 1
            overall[rung] += 1
            overall["total"] += 1
        per_client[h] = _finalize(crow)

    for organ in per_organ:
        per_organ[organ] = _finalize(per_organ[organ])

    return {"per_organ": per_organ, "per_client": per_client, "overall": _finalize(overall)}


def _blank() -> dict:
    return {"confirmed": 0, "inferred": 0, "default": 0, "total": 0}


def _finalize(d: dict) -> dict:
    d["pct_confirmed"] = round(100 * d["confirmed"] / d["total"], 1) if d["total"] else 0.0
    return d


def main():
    c = census()
    print("═══ PROVENANCE LADDER — per organ (across clients) ═══")
    print(f"  {'ORGAN':12} {'🟢conf':>7} {'🟡inf':>7} {'🔴def':>7}  %confirmed")
    for organ, d in sorted(c["per_organ"].items(), key=lambda kv: kv[1]["pct_confirmed"]):
        print(f"  {organ:12} {d['confirmed']:>7} {d['inferred']:>7} {d['default']:>7}  {d['pct_confirmed']:>5}%")

    print("\n═══ per client (across organs) ═══")
    for h, d in sorted(c["per_client"].items(), key=lambda kv: kv[1]["pct_confirmed"], reverse=True):
        ready = "PRODUCTION-READY" if d["default"] == 0 else f"{d['default']}🔴 — not ready"
        print(f"  {h:18} {d['pct_confirmed']:>5}% confirmed  ({d['confirmed']}🟢/{d['inferred']}🟡/{d['default']}🔴)  {ready}")

    o = c["overall"]
    print(f"\nOVERALL: {o['pct_confirmed']}% of organ-slots client-confirmed "
          f"({o['confirmed']}🟢 / {o['inferred']}🟡 / {o['default']}🔴 of {o['total']}).")
    print("LAW: a client is production-ready only when its 🔴 default count is 0 "
          "(provenance_mixin_v1: confirmed beats inferred beats default).")


if __name__ == "__main__":
    main()
