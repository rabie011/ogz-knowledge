#!/usr/bin/env python3
"""LAW REGISTRY CHECK (June 12) — the registry must be EXECUTABLE or it's more paper.
For every law: (1) each enforcement point's symbol literally EXISTS in its file
(contract-level grep — a renamed/deleted function un-enforces a law silently otherwise),
(2) its test script (if any) exits 0, (3) paper_only laws are counted and surfaced
LOUDLY — they are debt, never invisible.

Exit 1 if any 'enforced' law's symbol is missing or its test fails (a law that
CLAIMS enforcement and isn't = the exact lie this registry exists to kill).
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent


def main():
    reg = json.loads((BASE / "data/law_registry.json").read_text())
    broken, paper, tested = [], [], set()
    for law in reg["laws"]:
        lid = law["id"]
        if law["status"] == "paper_only":
            paper.append(lid)
            continue
        for ep in law.get("enforcement", []):
            f = BASE / ep["file"]
            if not f.exists() or ep["symbol"] not in f.read_text():
                broken.append(f"{lid}: symbol {ep['symbol']!r} missing from {ep['file']}")
        t = law.get("test")
        if t and t not in tested:
            tested.add(t)
            r = subprocess.run([sys.executable, str(BASE / t)], capture_output=True, timeout=300)
            if r.returncode != 0:
                broken.append(f"{lid}: test {t} exit {r.returncode}")

    n = len(reg["laws"])
    print(f"laws: {n} · enforced/pending: {n - len(paper)} · paper_only: {len(paper)}")
    for p in paper:
        print(f"  📄 PAPER ONLY (debt): {p}")
    for b in broken:
        print(f"  🔴 BROKEN CLAIM: {b}")
    print("🟢 LAW REGISTRY: all enforcement claims verified" if not broken
          else "🔴 LAW REGISTRY: enforcement claims are LYING")
    raise SystemExit(1 if broken else 0)


if __name__ == "__main__":
    main()
