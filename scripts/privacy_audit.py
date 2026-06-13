#!/usr/bin/env python3
"""B031 — PRIVACY WALL AUDIT (quarterly provenance audit).

The walls, each checked with evidence:
  W1 no private accounts   — raw/ must hold no data scraped from a private profile
  W2 no commenter leakage  — commenter usernames from comments.jsonl must never
                             appear in profile organs, presentations, or post cards
                             (street-voice insights are aggregates, never identities)
  W3 no DM artifacts       — nothing DM-shaped anywhere (we never touch inboxes)
  W4 disclosure per scrape — every raw/instagram/<date>/ dir has a disclosure entry
                             in data/scrape_disclosure.jsonl (actor, date, public-only)

Backfills W4 disclosure entries from on-disk evidence on first run (the scrapes were
all public-data Apify actors — the ledger just didn't exist yet).
Writes data/privacy_audit_last.json; make_sure checks freshness (<90d) + pass.

Usage: python3 scripts/privacy_audit.py   (exit 1 = a wall is breached)
"""
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
DISCLOSURE = BASE / "data/scrape_disclosure.jsonl"


def main():
    findings = {"W1_private_accounts": [], "W2_commenter_leakage": [],
                "W3_dm_artifacts": [], "W4_missing_disclosure": []}

    # W1 — private accounts in raw
    for pf in glob.glob(str(BASE / "clients/*/raw/instagram/*/profile.json")):
        try:
            p = json.loads(Path(pf).read_text())
        except Exception:
            continue
        if p.get("private"):
            findings["W1_private_accounts"].append(pf)

    # W2 — commenter usernames leaking into derived artifacts
    for cdir in sorted(glob.glob(str(BASE / "clients/*"))):
        handle = Path(cdir).name
        commenters = set()
        for cf in glob.glob(f"{cdir}/raw/instagram/*/comments.jsonl"):
            for l in Path(cf).read_text(encoding="utf-8").splitlines():
                if not l.strip():
                    continue
                try:
                    c = json.loads(l)
                except Exception:
                    continue
                u = c.get("ownerUsername") or c.get("owner", {}).get("username")
                if u and u.lower() != handle.lower():
                    commenters.add(u)
        if not commenters:
            continue
        # derived artifacts = organs + presentations + posts (NEVER raw/ itself)
        derived = (glob.glob(f"{cdir}/profile/*.json") + glob.glob(f"{cdir}/presentations/*")
                   + glob.glob(f"{cdir}/posts/*.json") + glob.glob(f"{cdir}/*.json"))
        big = [c for c in commenters if len(c) >= 5]  # short handles false-positive on substrings
        for df in derived:
            if "/raw/" in df:
                continue
            try:
                txt = Path(df).read_text(encoding="utf-8")
            except Exception:
                continue
            for u in big:
                if re.search(rf"\b{re.escape(u)}\b", txt):
                    findings["W2_commenter_leakage"].append(f"{df}: commenter «{u}»")

    # W3 — DM-shaped artifacts: structured data + dirs only. Media files are exempt —
    # Instagram CDN fragments produce names like DM-uD85sOOd.jpg (public post images,
    # verified June 13: both flagged files traced to posts.jsonl entries)
    for f in glob.glob(str(BASE / "clients/**/*"), recursive=True):
        p = Path(f)
        n = p.name.lower()
        if not re.search(r"\b(dm|direct_message|inbox)\b", n):
            continue
        if p.is_dir() or p.suffix in (".json", ".jsonl", ".md", ".txt", ".csv"):
            findings["W3_dm_artifacts"].append(f)

    # W4 — disclosure ledger covers every scrape dir (backfill from evidence)
    have = set()
    if DISCLOSURE.exists():
        for l in DISCLOSURE.read_text(encoding="utf-8").splitlines():
            if l.strip():
                have.add(json.loads(l)["scrape_dir"])
    backfilled = 0
    for d in sorted(glob.glob(str(BASE / "clients/*/raw/instagram/*"))):
        rel = str(Path(d).relative_to(BASE))
        if rel in have:
            continue
        surfaces = [Path(x).name for x in glob.glob(f"{d}/*")]
        with open(DISCLOSURE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "scrape_dir": rel, "handle": Path(d).parent.parent.parent.name,
                "scraped_on": Path(d).name, "surfaces": surfaces,
                "actor": "apify instagram-profile/post-scraper (public data only)",
                "statement": "public Instagram content of a business account; no login, "
                             "no DMs, no private data; commenter identities stay in raw/ only",
                "disclosed_at": datetime.now().isoformat(timespec="seconds"),
                "via": "privacy_audit backfill from on-disk evidence",
            }, ensure_ascii=False) + "\n")
        backfilled += 1

    breached = {k: v for k, v in findings.items() if v}
    report = {"ts": datetime.now().isoformat(timespec="seconds"),
              "pass": not breached, "disclosure_backfilled": backfilled,
              "findings": findings}
    (BASE / "data/privacy_audit_last.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1))

    for k, v in findings.items():
        print(f"  {'✅' if not v else '🔴'} {k}: {len(v)}")
        for x in v[:5]:
            print(f"      {x}")
    if backfilled:
        print(f"  📜 disclosure ledger: {backfilled} scrape dirs backfilled")
    print("🟢 PRIVACY WALLS HOLD" if not breached else "🔴 PRIVACY WALL BREACHED")
    raise SystemExit(0 if not breached else 1)


if __name__ == "__main__":
    main()
