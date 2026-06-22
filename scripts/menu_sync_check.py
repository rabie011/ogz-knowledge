#!/usr/bin/env python3
"""MENU SYNC CHECK (B174, June 22 — RABIE's pick).
Diff a client's LIVE public delivery-app menu prices against the CONFIRMED
truth_pack prices. Every price delta is a PROPOSAL event (ledger/inbox, never
auto-applied — One Write Path): truth_pack is human-confirmed ground, a scraper
may NEVER overwrite it. A price we cite that silently drifts is exactly what
poisons a caption — so the drift surfaces as a card, and a human decides.

Design choices (Pre-Build Q2 — "what happens when it fails?"):
  * Live fetch is best-effort and isolated: ANY failure → arm-and-wait, never
    crash, never a false "no drift" (a missing menu is not an unchanged menu).
  * diff_menu + emit_proposals are pure of network and fully tested against a
    SEEDED menu; the live scrape is never exercised in tests.
  * truth_pack.json is opened READ-ONLY here. The sibling B074 drift-watch
    already proved the proposal path; this is the price mirror of it.

Usage: python3 scripts/menu_sync_check.py [--handle albaik]
"""
import argparse
import datetime
import json
from pathlib import Path

BASE = Path(__file__).parent.parent

# Module-top so tests can monkeypatch menu_sync_check.ledger_write without touching disk.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from ledger_write import ledger_write


def _norm_prices(prices):
    """Coerce truth_pack['prices'] OR a scraped menu into {item_name: float}.
    Tolerates list-of-dicts ([{'name':..,'price':..}]) or a flat {name: price}
    map; silently drops malformed rows rather than guessing."""
    out = {}
    if isinstance(prices, dict):
        for k, v in prices.items():
            try:
                out[str(k).strip()] = float(v)
            except (TypeError, ValueError):
                pass
    elif isinstance(prices, list):
        for it in prices:
            if not isinstance(it, dict):
                continue
            name = it.get("name") or it.get("item")
            val = it.get("price", it.get("sar"))
            if name is None or val is None:
                continue
            try:
                out[str(name).strip()] = float(val)
            except (TypeError, ValueError):
                pass
    return out


def diff_menu(truth_prices, live_menu):
    """Pure: return list of price deltas (changed / added / removed) between the
    confirmed truth prices and a live menu. Both args accept _norm_prices shapes."""
    truth = _norm_prices(truth_prices)
    live = _norm_prices(live_menu)
    deltas = []
    for name, lp in live.items():
        if name in truth:
            if abs(truth[name] - lp) > 1e-9:
                deltas.append({"item": name, "kind": "changed", "from": truth[name], "to": lp})
        else:
            deltas.append({"item": name, "kind": "added", "to": lp})
    for name, tp in truth.items():
        if name not in live:
            deltas.append({"item": name, "kind": "removed", "from": tp})
    return deltas


def _truth_pack_path(handle):
    return BASE / "clients" / handle / "profile/truth_pack.json"


def emit_proposals(handle, deltas, day_key=None):
    """Append each delta as a PROPOSAL ledger event. NEVER touches truth_pack.
    Mirrors client_drift_watch's intake_answer/PROPOSAL stamp so the same inbox
    consumer (human confirm) reads it. Returns count emitted."""
    if not deltas:
        return 0
    day_key = day_key or datetime.date.today().isoformat()
    n = 0
    for d in deltas:
        ev = {
            "ts": day_key,
            "type": "intake_answer",
            "subject": f"menu_price:{d['item']}:{day_key}",
            "note": f"PROPOSAL (menu sync): {json.dumps(d, ensure_ascii=False)[:160]}",
            "confirmer": "menu_sync",
            "stamp": "PROPOSAL — never auto-applied (One Write Path)",
        }
        ledger_write(handle, ev)
        n += 1
    return n


def fetch_live_menu(handle):
    """Best-effort live scrape of the public delivery-app menu. Returns a
    {name: price} map, or None on ANY failure (arm-and-wait, never a false zero).
    Per-client menu sources land here as they're confirmed; absent today → None,
    so the check arms and waits rather than inventing an empty menu."""
    return None


def check(handle, live_menu=None, day_key=None):
    """Diff one client's live menu vs truth_pack prices, emit proposals, return
    the deltas. truth_pack is read-only throughout."""
    tp_path = _truth_pack_path(handle)
    if not tp_path.exists():
        print(f"  ⏸ {handle}: no truth_pack — nothing to diff")
        return []
    truth_prices = json.loads(tp_path.read_text()).get("prices", [])
    if live_menu is None:
        live_menu = fetch_live_menu(handle)
    if live_menu is None:
        print(f"  ⏸ {handle}: no live menu source yet — armed, waiting")
        return []
    deltas = diff_menu(truth_prices, live_menu)
    n = emit_proposals(handle, deltas, day_key=day_key)
    print(f"  {'🔔' if deltas else '✅'} {handle}: {len(deltas)} menu delta(s) → {n} PROPOSAL event(s)")
    return deltas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               sorted(d.name for d in (BASE / "clients").iterdir()
                      if _truth_pack_path(d.name).exists()))
    for h in clients:
        check(h)


if __name__ == "__main__":
    main()
