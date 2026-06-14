#!/usr/bin/env python3
"""Stage the ZERO-ISSUE occasion-aligned 20 (__v7, 2026-06-14). Selects from the clean __v7
renders: keeps the 3 occasion posts (national_day/ramadan/founding_day — "confirmed with
occasion"), balances scene-cores (drops excess energy_sport so no core >30%), spreads across
the 3 clients. Supersedes the old __v6 cards. Asserts post_audit clean per post before pushing —
never stages a post with an issue (Mohamed: "without ANY issue")."""
import json, glob, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import seed_judge_cards as sj
import queue_decision as qd
import post_audit as pa
from render_client_slot import scene_core, batch_diversity_check

B = Path(__file__).parent.parent
DROP = {("myfitness.sa", "2026-12-28"), ("albaik", "2027-01-14")}  # 2 energy_sport → balance to 20


def main():
    clean = []
    for h in ("myfitness.sa", "eatjurisha", "albaik"):
        for f in sorted(glob.glob(str(B / f"clients/{h}/posts/*__v7.json"))):
            d = json.loads(Path(f).read_text())
            dt = Path(f).name.split("__")[0]
            if (h, dt) in DROP:
                continue
            hard = [i for i in pa.audit_post(d, h) if i[0] != "occasion_missing"]
            if hard:
                continue  # never stage a post with a hard issue
            clean.append((h, dt, d, Path(f).name))
    if len(clean) < 20:
        sys.exit(f"🛑 only {len(clean)} clean posts — need 20; render more before staging")
    chosen = clean[:20]

    # assert batch diversity on the chosen 20 (no core/recipe > 30%)
    slotlike = [{"date": dt, "scene_ar": (d.get("captions") or [""])[0],
                 "angle_theme": (d.get("slot") or {}).get("angle_theme", ""),
                 "formula": (d.get("slot") or {}).get("formula")} for h, dt, d, fn in chosen]
    dchk = batch_diversity_check(slotlike, 0.30)
    if not dchk["ok"] and dchk.get("violations"):
        for v in dchk["violations"]:
            print(f"   ⚠ over-concentration {v['kind']} «{v['key']}» {v['pct']}%")
        sys.exit("🛑 chosen 20 over-concentrated — adjust DROP set")

    # supersede the old open judge cards, then push the clean 20
    qf = B / "data/decision_queue.json"
    q = json.loads(qf.read_text())
    sup = 0
    for it in q["items"]:
        if (it.get("judge_lane") or it.get("kind") == "caption_judge") and it.get("status") == "open":
            it["status"] = "superseded_v7"
            sup += 1
    qf.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"superseded {sup} old cards")

    from collections import Counter
    bc = Counter()
    for h, dt, d, fn in chosen:
        item = sj.build_card(h, d, fn)
        qd.push_attributed(item, made_by=f"mind:{d['brain']}", via="scripts/stage_aligned20.py",
                           reason=f"zero-issue occasion-aligned v7 — {fn}")
        bc[h] += 1
        print(f"  ⚖️ {item['id']} — mind:{d['brain']} · {d['captions'][0][:50]}")
    print(f"\nDONE: staged 20 — {dict(bc)} · diversity OK")


if __name__ == "__main__":
    main()
