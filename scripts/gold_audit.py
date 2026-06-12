#!/usr/bin/env python3
"""B182 — GOLD VAULT AUDIT: every gold line traces to Mohamed or it leaves the fuel.

Law enforced: mohamed_only_ground_truth. Gold is the strongest few-shot signal the
renderer has — an unconfirmed line in gold teaches the pens with authority Mohamed
never granted. Found June 13: 9 entries with confirmer=? (occasion_gold_* seeds and
v2-era render picks) living beside his real confirmations.

Provenance classes:
  traced       — source portal:<card> with a matching mohamed answer row → stays
  historical   — confirmer=mohamed without a ledger row (early chat-era picks,
                 MOHAMED_PICK_* / mohamed_mint_* / ruling mint_anyway) → stays, tagged
  unconfirmed  — confirmer missing/'?' → moved to 'seed_unconfirmed' (quarantine,
                 NEVER deleted; his tap can restore)

Exit 1 if any unconfirmed entry remains in 'gold' (make_sure gate). Idempotent.
"""
import glob
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base


def audit(fix: bool = True) -> dict:
    b = base()
    ans_ids = set()
    af = b / "data/mohamed_answers.jsonl"
    if af.exists():
        for l in af.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("judge") == "mohamed":
                    ans_ids.add(r.get("item_id"))
    report = {"ts": datetime.now().isoformat(timespec="seconds"), "clients": {}}
    dirty = 0
    for f in sorted(glob.glob(str(b / "clients/*/profile/gold.json"))):
        handle = Path(f).parent.parent.name
        g = json.loads(Path(f).read_text())
        keep, quarantined = [], g.get("seed_unconfirmed", [])
        counts = {"traced": 0, "historical": 0, "unconfirmed": 0}
        for e in g.get("gold", []):
            src = str(e.get("source", ""))
            conf = e.get("confirmer")
            if src.startswith("portal:") and src.split("portal:", 1)[1] in ans_ids:
                counts["traced"] += 1
                keep.append(e)
            elif conf == "mohamed":
                counts["historical"] += 1
                e.setdefault("provenance_class", "historical_pick_pre_ledger")
                keep.append(e)
            else:
                counts["unconfirmed"] += 1
                dirty += 1
                if fix:
                    e["quarantined_by"] = ("gold_audit (law mohamed_only_ground_truth): "
                                           "no confirmer — his tap can restore")
                    e["quarantined_at"] = datetime.now().isoformat(timespec="seconds")
                    quarantined.append(e)
                else:
                    keep.append(e)
        if fix:
            g["gold"], g["seed_unconfirmed"] = keep, quarantined
            Path(f).write_text(json.dumps(g, ensure_ascii=False, indent=1))
            chk = json.loads(Path(f).read_text())
            assert all((str(e.get("source", "")).startswith("portal:")
                        and str(e.get("source")).split("portal:", 1)[1] in ans_ids)
                       or e.get("confirmer") == "mohamed"
                       for e in chk["gold"]), f"{handle}: unconfirmed entry survived in gold"
        report["clients"][handle] = {**counts, "gold_now": len(keep),
                                     "seed_unconfirmed": len(quarantined)}
    report["clean"] = (dirty == 0) if not fix else True
    report["moved_this_run"] = dirty if fix else 0
    return report


def main():
    fix = "--check-only" not in sys.argv
    r = audit(fix=fix)
    for h, c in r["clients"].items():
        print(f"  {h}: {c['gold_now']} gold (traced {c['traced']} + historical "
              f"{c['historical']}) · {c['seed_unconfirmed']} seed_unconfirmed")
    if fix and r["moved_this_run"]:
        print(f"  🧹 moved {r['moved_this_run']} unconfirmed seeds out of the fuel")
    print("🟢 GOLD VAULT: every line traces to Mohamed" if r["clean"]
          else "🔴 GOLD VAULT: unconfirmed lines in the fuel")
    raise SystemExit(0 if r["clean"] else 1)


if __name__ == "__main__":
    main()
