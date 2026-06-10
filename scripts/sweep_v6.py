#!/usr/bin/env python3
"""THE BIG SWEEP (overnight, June 11) — v6 generation for every DNA-covered brand
× its matrix occasions × {claude, gpt-4o}. SELF-GATE: pilot the first 5 brands,
halt if filter-drop rate > 25% (founder's glance replaced by a hard number).
Resumable: skips brands already swept this run (state file)."""
import json, subprocess, sys, time
from pathlib import Path

BASE = Path(__file__).parent.parent
STATE = BASE / "logs" / "sweep_v6_state.json"
GATE_DROP_PCT = 25
PILOT = 5

cov = json.loads((BASE / "logs/brand_dna/_COVERAGE.json").read_text())
done_brands = {"albaik", "barnscoffee"}  # already generated v6 tonight
brands = [b for b in cov["deep_dna_v3"] if b not in done_brands]
state = json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "halted": False}


def drop_rate(model_file: str) -> tuple[int, int]:
    q = json.loads((BASE / "logs" / model_file).read_text())
    dropped = kept = 0
    for it in q.get("pending", []) + q.get("approved", []):
        if it.get("prompt_version") != "v6":
            continue
        dropped += len(it.get("v5_dropped", {}) or {})
        kept += len([v for v in (it.get("options") or {}).values() if v])
    return dropped, kept


def run(brand: str):
    for model in ["claude", "gpt4o"]:
        r = subprocess.run(["python3", "scripts/multi_llm_collector.py",
                            "--model", model, "--brand", brand, "--force"],
                           capture_output=True, text=True, timeout=900, cwd=BASE)
        tail = (r.stdout or "").strip().split("\n")[-1]
        print(f"  {brand} × {model}: {tail[-70:]}", flush=True)


t0 = time.time()
for i, b in enumerate(brands):
    if b in state["done"]:
        continue
    print(f"[{i+1}/{len(brands)} · {int(time.time()-t0)}s] {b}", flush=True)
    try:
        run(b)
        state["done"].append(b)
    except Exception as e:
        print(f"  ✗ {b}: {e}", flush=True)
    STATE.write_text(json.dumps(state))
    if len(state["done"]) == PILOT:
        d1, k1 = drop_rate("claude_queue.json")
        d2, k2 = drop_rate("gpt4o_queue.json")
        rate = round(100 * (d1 + d2) / max(d1 + d2 + k1 + k2, 1))
        print(f"== PILOT GATE: drop rate {rate}% (dropped {d1+d2} / kept {k1+k2}) ==", flush=True)
        if rate > GATE_DROP_PCT:
            state["halted"] = True
            STATE.write_text(json.dumps(state))
            sys.exit(f"GATE HALT: {rate}% > {GATE_DROP_PCT}% — investigate before scaling")
    time.sleep(1)

d1, k1 = drop_rate("claude_queue.json")
d2, k2 = drop_rate("gpt4o_queue.json")
print(f"\nSWEEP DONE: {len(state['done'])} brands · final drop rate "
      f"{round(100*(d1+d2)/max(d1+d2+k1+k2,1))}% · kept options {k1+k2}", flush=True)
