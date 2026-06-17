#!/usr/bin/env python3
"""GENERATE PORTAL KEYS — first-run setup for the feedback portal (June 17 handover).
A fresh clone has NO data/portal_team.json / data/portal_keys.json (they're gitignored so the live
founder key never ships). Without them every /approvals request is 403. Run this once to mint your
own keys and write both files locally, then open the printed URL.

Usage:
  python3 scripts/gen_portal_key.py                 # mint a shared key + a 'dev' per-judge key
  python3 scripts/gen_portal_key.py --judge alice    # add another per-judge key
"""
import argparse, datetime, hashlib, json, secrets
from pathlib import Path

B = Path(__file__).parent.parent
TEAM = B / "data/portal_team.json"
KEYS = B / "data/portal_keys.json"


def _load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="dev", help="per-judge identity for the new key")
    ap.add_argument("--port", default="4199")
    a = ap.parse_args()

    # shared (legacy) key — opens the page; lives in portal_team.json
    team = _load(TEAM, {"key": "", "members": []})
    if not team.get("key"):
        team["key"] = "ogz-" + secrets.token_hex(6)
    TEAM.write_text(json.dumps(team, ensure_ascii=False, indent=1))

    # per-judge key — server stores only the sha256 HASH (the plaintext is shown once, here)
    keys = _load(KEYS, {"legacy_write": True, "_doc": "per-judge portal keys; only hashes stored", "keys": []})
    judge_key = "ogz-" + a.judge[:3] + "-" + secrets.token_hex(6)
    keys["keys"].append({
        "key_hash": hashlib.sha256(judge_key.encode()).hexdigest(),
        "judge": a.judge,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "revoked": None,
    })
    KEYS.write_text(json.dumps(keys, ensure_ascii=False, indent=1))

    print("✅ portal keys written (LOCAL only — gitignored, never committed)")
    print(f"   shared key : {team['key']}")
    print(f"   {a.judge} key   : {judge_key}   (save it — only the hash is stored)")
    print(f"   open       : http://localhost:{a.port}/approvals?k={judge_key}")
    print(f"   start portal: python3 -m uvicorn api.portal_mini:app --port {a.port} --host 127.0.0.1")


if __name__ == "__main__":
    main()
