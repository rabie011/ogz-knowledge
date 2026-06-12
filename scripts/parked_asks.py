#!/usr/bin/env python3
"""STUCK-AT-INFERRED PARKED-ASK GENERATOR (B088, June 12 — RABIE's pick).
A fact downgraded confirmed→inferred is supposed to be refreshed; one that stays
inferred 90+ days is a question nobody asked. This reads each client's staleness
history (ledger events), finds nodes still expired whose FIRST downgrade is 90+
days old, and parks ONE ask per node in the client's parked_asks.json — surfaced
to the portal only when asks exist (no card spam).

Usage: python3 scripts/parked_asks.py [--threshold-days 90]
"""
import argparse, datetime, json
from pathlib import Path

BASE = Path(__file__).parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-days", type=int, default=90)
    a = ap.parse_args()
    today = datetime.date.today()
    rep_f = BASE / "data/staleness_report.json"
    current = json.loads(rep_f.read_text()).get("report", {}) if rep_f.exists() else {}
    total_parked = 0
    for cdir in sorted((BASE / "clients").iterdir()):
        lf = cdir / "events/ledger.jsonl"
        if not lf.exists():
            continue
        first_seen = {}
        for line in lf.read_text().strip().split("\n"):
            try:
                e = json.loads(line)
            except Exception:
                continue
            subj = e.get("subject") or ""
            if not subj.startswith("staleness:"):
                continue
            # subject = staleness:<node-which-may-contain-colons>:<date> — date is LAST
            node = subj[len("staleness:"):].rsplit(":", 1)[0]
            try:
                d = datetime.date.fromisoformat(e.get("ts", "")[:10])
            except ValueError:
                continue
            if node not in first_seen or d < first_seen[node]:
                first_seen[node] = d
        still_expired = {x["node"] for x in current.get(cdir.name, []) if x.get("status") == "EXPIRED"}
        stuck = {n: d for n, d in first_seen.items()
                 if (today - d).days >= a.threshold_days and n in still_expired}
        if not stuck:
            continue
        paf = cdir / "parked_asks.json"
        pa = json.loads(paf.read_text()) if paf.exists() else {"asks": []}
        seen = {x["node"] for x in pa["asks"]}
        added = 0
        for n, d in stuck.items():
            if n in seen:
                continue
            pa["asks"].append({"node": n, "stuck_since": str(d),
                                 "days": (today - d).days,
                                 "ask": f"الحقيقة «{n}» نازلة لمستوى استنتاج من {d} — نحتاج تأكيد العميل أو نشيلها من الاستشهاد نهائياً",
                                 "status": "PARKED — awaiting client/Mohamed"})
            added += 1
        if added:
            paf.write_text(json.dumps(pa, ensure_ascii=False, indent=2))
            total_parked += added
            print(f"  📌 {cdir.name}: {added} stuck node(s) parked")
    if total_parked:
        import subprocess
        subprocess.run(["python3", str(BASE / "scripts/queue_decision.py"),
                        "--id", "stuck_inferred_asks", "--title", f"حقائق عالقة {a.threshold_days}+ يوم بدون تأكيد",
                        "--tag", "حقيقة", "--desc", f"{total_parked} حقيقة نازلة لاستنتاج من {a.threshold_days}+ يوم — التفاصيل في parked_asks.json لكل عميل.",
                        "--buttons", "review:👁 أراجعها,drop:🗑 شيلوها من الاستشهاد"], capture_output=True)
        print(f"  → portal card raised ({total_parked} asks)")
    else:
        print(f"  ✅ no facts stuck {a.threshold_days}+ days — honest zero (ledgers are young)")


if __name__ == "__main__":
    main()
