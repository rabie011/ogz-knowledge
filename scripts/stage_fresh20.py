#!/usr/bin/env python3
"""Stage EXACTLY the 20 fresh fixed-pipeline renders (2026-06-14) to Mohamed's judge lane.
The auto-picker (seed_judge_cards) surfaced ~16 OLD pre-fix __v6 captions (the repetitive
delivery/family formula) instead of today's creative renders — caught by reading the actual
caption text before reporting (Rule #9). This stages the verified-fresh ones directly:
supersede the mis-staged batch, push the fresh 20, each gate-checked. NEVER ships a
gate-blocked or empty post.
"""
import json, glob, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seed_judge_cards as sj
import queue_decision as qd
import pre_ship_gate as g

B = Path(__file__).parent.parent
FRESH = {
    "myfitness.sa": ["2026-07-11", "2026-08-11", "2026-09-11", "2026-10-11", "2026-11-11", "2026-12-11", "2027-01-11"],
    "eatjurisha":   ["2026-07-11", "2026-08-11", "2026-09-11", "2026-10-11", "2026-11-11", "2026-12-11", "2027-01-11"],
    "albaik":       ["2026-08-11", "2026-09-11", "2026-10-11", "2026-11-11", "2026-12-11", "2027-01-11"],
}  # albaik 2026-07-11 excluded — pre_ship_gate BLOCKED it (the gate works); 20 total


def main():
    qf = B / "data/decision_queue.json"
    q = json.loads(qf.read_text())
    # 1. supersede the mis-staged batch (0 open judge cards existed before this session's
    #    erroneous stage, so every open judge card now IS the wrong batch — safe to retire)
    sup = 0
    for it in q["items"]:
        if (it.get("judge_lane") or it.get("kind") == "caption_judge") and it.get("status") == "open":
            it["status"] = "superseded_v6fix"
            sup += 1
    qf.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"superseded {sup} mis-staged old cards")

    # 2. push the fresh 20 (gate-checked, never empty)
    pushed = skipped = 0
    for handle, dates in FRESH.items():
        for d in dates:
            fs = glob.glob(str(B / f"clients/{handle}/posts/{d}__*__v6.json"))
            if not fs:
                print(f"  ⚠ {handle} {d}: no __v6 file"); skipped += 1; continue
            dd = json.loads(Path(fs[0]).read_text())
            if not (dd.get("captions") and dd.get("brain")):
                print(f"  ⚠ {handle} {d}: empty/no-brain — skipped"); skipped += 1; continue
            if g.gate(dd, handle).get("block"):
                print(f"  🛑 {handle} {d}: gate BLOCK — skipped (gate works)"); skipped += 1; continue
            item = sj.build_card(handle, dd, Path(fs[0]).name)
            qd.push_attributed(item, made_by=f"mind:{dd['brain']}", via="scripts/stage_fresh20.py",
                               reason=f"fresh v6-fix creative batch — {Path(fs[0]).name}")
            print(f"  ⚖️ {item['id']} — mind:{dd['brain']} · {dd['captions'][0][:55]}")
            pushed += 1
    print(f"\nDONE: {pushed} fresh creative cards staged, {skipped} skipped")


if __name__ == "__main__":
    main()
