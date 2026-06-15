#!/usr/bin/env python3
"""RESEARCH-OPEN — the missing READER for research_ledger.jsonl (Rule #6, June 15 RABIE shift).
client_strategy.py WRITES each strategy synth's research_requests to clients/<h>/profile/
research_ledger.jsonl, calling it "the audit trail Mohamed asked for" — but nothing read it and
it was surfaced nowhere, so 9 real research questions across the pilots sat invisible. This gives
the write-only ledger its intended reader: it reads every pilot's ledger and surfaces the open
requests. FULFILLING them is the (gated) research stage; this only makes the audit trail VISIBLE
so it can never silently vanish again. Zero-key, read-only.
Usage: python3 scripts/research_open.py
"""
import glob, json
from pathlib import Path

B = Path(__file__).parent.parent


def open_requests():
    """Read every client's research_ledger.jsonl → [{handle, request, ts}]. The Rule #6 consumer."""
    out = []
    for f in sorted(glob.glob(str(B / "clients/*/profile/research_ledger.jsonl"))):
        handle = Path(f).parent.parent.name
        for line in Path(f).read_text().splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            req = e.get("request") or e.get("q") or e.get("ask")
            if req:
                out.append({"handle": handle, "request": req, "ts": e.get("ts")})
    return out


def summary_line():
    """One informational line for the heartbeat surface (not an alarm — Rule #10 no-flood)."""
    reqs = open_requests()
    if not reqs:
        return "📋 research audit trail: empty"
    by_h = {}
    for r in reqs:
        by_h[r["handle"]] = by_h.get(r["handle"], 0) + 1
    breakdown = " · ".join(f"{h}:{n}" for h, n in sorted(by_h.items()))
    return f"📋 {len(reqs)} open research requests (audit trail, awaiting the research stage) — {breakdown}"


def main():
    reqs = open_requests()
    print(summary_line())
    for r in reqs:
        print(f"  [{r['handle']}] {r['request'][:90]}")


if __name__ == "__main__":
    main()
