#!/usr/bin/env python3
"""TTL REGISTRY + STALENESS REPORT (B067-69, June 12 — RABIE's pick).
The pyramid cited this script before it existed (the exact readiness-hallucination
the self-audit rule outlaws) — now it exists. Freshness law made enforceable:

TTL REGISTRY (pyramid Layer-4):
  offers/prices 7d · products 30d · channels 60d · bio 90d · voice stats 180d ·
  red lines NEVER auto-expire (re-confirm every 5th touch — counted, not timed)

Past-TTL facts auto-downgrade confirmed→inferred in the report (uncitable by the
citation gate). The report BLOCKS (exit 1) when expired-but-load-bearing facts
exist; it never edits organs — humans (or re-extraction) refresh, the report only
tells the truth about age.

Usage: python3 scripts/staleness_report.py [--handle X]
"""
import argparse, datetime, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
TODAY = datetime.date(2026, 6, 12)

TTL_DAYS = {"prices": 7, "products": 30, "channels": 60, "bio": 90, "voice_stats": 180}


def age_days(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        return (TODAY - datetime.date.fromisoformat(date_str[:10])).days
    except ValueError:
        return None


def check_client(handle: str) -> list[dict]:
    pdir = BASE / "clients" / handle / "profile"
    findings = []

    def f(node, ttl_key, date_str, detail=""):
        age = age_days(date_str)
        ttl = TTL_DAYS[ttl_key]
        if age is None:
            findings.append({"node": node, "status": "NO_DATE", "detail": "fact carries no date — uncitable"})
        elif age > ttl:
            findings.append({"node": node, "status": "EXPIRED", "age_days": age, "ttl": ttl,
                              "detail": f"{detail} confirmed→inferred (citation gate must refuse it)"})

    # born-expired law: a deep-dormant client's scraped truth is old the day we scrape it —
    # date_added measures OUR recording, not the fact's real-world age (myfitness: extracted
    # yesterday from 4.7-year-old posts must read EXPIRED, matching the renderer's stamp)
    st_pre = json.loads((pdir / "state.json").read_text())
    if (st_pre.get("silent_days") or 0) > 90:
        findings.append({"node": "truth_pack.ALL_SCRAPED", "status": "EXPIRED",
                          "age_days": st_pre["silent_days"], "ttl": 90,
                          "detail": f"deep-dormant {st_pre['silent_days']}d — scraped truth born-expired; client confirm only"})

    tp = json.loads((pdir / "truth_pack.json").read_text())
    for p in tp.get("product_candidates", []):
        f(f"truth_pack.product:{p['name'][:20]}", "products", p.get("provenance", {}).get("date_added"))
    for c in tp.get("channels", []):
        f(f"truth_pack.channel:{c['name']}", "channels", c.get("provenance", {}).get("date_added"))
    for pr in tp.get("prices", []):
        f(f"truth_pack.price:{str(pr)[:20]}", "prices", (pr.get("provenance") or {}).get("date_added") if isinstance(pr, dict) else None)

    st = json.loads((pdir / "state.json").read_text())
    f("state(bio/profile extract)", "bio", st.get("provenance", {}).get("date_added"))

    fp = json.loads((pdir / "fingerprint.json").read_text())
    v = fp.get("l2_voice", {})
    f("fingerprint.l2_voice(stats)", "voice_stats", (v.get("provenance") or {}).get("date_added"))

    # red lines: count-based re-confirm, not time-based
    rl = json.loads((pdir / "red_lines.json").read_text())
    touches = rl.get("touches_since_confirm", 0)
    if rl.get("lines") and touches >= 5:
        findings.append({"node": "red_lines", "status": "RECONFIRM_DUE",
                          "detail": f"{touches} touches since confirm — one-tap re-confirm question due"})
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               sorted(d.name for d in (BASE / "clients").iterdir() if (d / "profile").is_dir()))
    blocking = 0
    report = {}
    for h in clients:
        findings = check_client(h)
        report[h] = findings
        expired = [x for x in findings if x["status"] == "EXPIRED"]
        nodate = [x for x in findings if x["status"] == "NO_DATE"]
        blocking += len(expired)
        print(f"── {h}: {len(expired)} expired · {len(nodate)} undated · "
              f"{len([x for x in findings if x['status']=='RECONFIRM_DUE'])} reconfirm-due")
        for x in findings[:6]:
            print(f"   {'🔴' if x['status']=='EXPIRED' else '🟡'} {x['node']}: {x['status']} {x.get('detail','')[:60]}")
    # B070: every EXPIRED finding becomes a PROPOSAL event in the client ledger —
    # rot is visible history, never a silent state. Dedup: one event per node per day.
    for h, findings in report.items():
        lf = BASE / "clients" / h / "events/ledger.jsonl"
        existing = lf.read_text() if lf.exists() else ""
        for x in findings:
            if x["status"] != "EXPIRED":
                continue
            key = f'staleness:{x["node"]}:{TODAY}'
            if key in existing:
                continue
            ev = {"ts": str(TODAY), "type": "intake_answer",
                   "subject": key,
                   "note": f'PROPOSAL: downgrade confirmed→inferred ({x.get("detail","")[:60]})',
                   "confirmer": "staleness_report", "stamp": "PROPOSAL — pending human refresh"}
            with open(lf, "a") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    out = BASE / "data/staleness_report.json"
    out.write_text(json.dumps({"date": str(TODAY), "report": report}, ensure_ascii=False, indent=2))
    print(f"\n{'🔴 BLOCK' if blocking else '🟢 CLEAN'}: {blocking} expired load-bearing facts → data/staleness_report.json")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
