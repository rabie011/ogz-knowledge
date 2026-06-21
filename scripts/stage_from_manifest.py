#!/usr/bin/env python3
"""GATED staging — sends the system-produced batch (data/batch_manifest.json) to Mohamed's
feedback system. Run ONLY after produce_batch + verify_feedback_fixed + the RABIE/orchestra
check are all green (Mohamed 2026-06-14: "don't send to feedback system till tested + checked
with rabie + all my feedback fixed"). Re-asserts every post is clean before pushing; flips the
manifest staged:true. The producer never stages — this is the one door to the feedback system."""
import json, glob, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seed_judge_cards as sj
import queue_decision as qd
import post_audit as pa
import pre_ship_gate as psg

B = Path(__file__).parent.parent


def main():
    mf = B / "data/batch_manifest.json"
    if not mf.exists():
        sys.exit("🛑 no batch_manifest.json — run produce_batch.py first")
    man = json.loads(mf.read_text())
    posts = man["posts"]
    if len(posts) < man.get("n", 20):
        sys.exit("🛑 manifest short — refuse")

    # Rule #13: the MIND PANEL must have cleared this batch (judge_batch GO) before it can reach
    # the feedback system — better-than-previous + zero old-mistakes + COO/CCO ship. Never bypass.
    jf = B / "data/batch_judgement.json"
    j = json.loads(jf.read_text()) if jf.exists() else {}
    if not j.get("GO"):
        sys.exit("🛑 REFUSED: judge_batch has not returned GO (run judge_batch.py; NO-GO → fix the machine, re-produce). "
                 "Nothing reaches Mohamed un-judged (Rule #13).")

    # re-assert clean at stage time (never send a post with an issue to the feedback system)
    loaded = []
    for p in posts:
        fs = glob.glob(str(B / f"clients/{p['handle']}/posts/{p['date']}__*{man['suffix']}.json"))
        if not fs:
            sys.exit(f"🛑 missing render for {p['handle']} {p['date']} — refuse")
        d = json.loads(Path(fs[0]).read_text())
        # HARD CULTURAL STOP (Rule #6 + #8) — the typed pre-ship verdict is consumed as a hard
        # block at the one door to the feedback system. A royal / modesty / red-line / learned-
        # rejection kill RAISES here; there is no warn-and-stage path. assert_shippable also
        # REFUSES on a malformed verdict (F3), so a broken gate result can't slip a post through.
        psg.assert_shippable(d, p["handle"])
        hard = [i for i in pa.audit_post(d, p["handle"]) if i[0] != "occasion_missing"]
        if hard:
            sys.exit(f"🛑 {p['handle']} {p['date']} has issues {hard} — refuse to stage")
        loaded.append((p["handle"], d, Path(fs[0]).name))

    # supersede the old open judge cards, then push the system-produced batch
    qf = B / "data/decision_queue.json"
    q = json.loads(qf.read_text())
    sup = 0
    for it in q["items"]:
        if (it.get("judge_lane") or it.get("kind") == "caption_judge") and it.get("status") == "open":
            it["status"] = "superseded_auto"
            sup += 1
    qf.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"superseded {sup} old cards")

    from collections import Counter
    bc = Counter()
    for handle, d, fn in loaded:
        item = sj.build_card(handle, d, fn)
        qd.push_attributed(item, made_by=f"mind:{d['brain']}", via="scripts/stage_from_manifest.py",
                           reason=f"system-produced batch (produce_batch.py) — {fn}")
        bc[handle] += 1
        print(f"  ⚖️ {item['id']} — mind:{d['brain']}")
    man["staged"] = True
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1))
    print(f"\n✅ staged {sum(bc.values())} system-produced posts — {dict(bc)}")


if __name__ == "__main__":
    main()
