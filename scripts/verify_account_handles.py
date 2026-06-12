#!/usr/bin/env python3
"""HANDLE VERIFICATION SWEEP (June 12 — the Excel scar, closed corpus-wide).
Every account_handle_internal in 11_who_to_learn_from/accounts/ gets checked against
LIVE Instagram (Apify profile scraper, one batched run). Verdicts:
  verified  — exists, public, fullName/followers captured
  dead      — page not found (likely prefix-mangled by the xlsx ingestion)
  restricted— exists but blocked/private
Output: 11_who_to_learn_from/handle_verification.json (per-handle records + summary).
Nothing deleted; the index is the truth layer the trust note promised.
"""
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def main():
    handles = {}
    for f in glob.glob(str(BASE / "11_who_to_learn_from/accounts/*/account_*.json")):
        try:
            d = json.loads(Path(f).read_text())
        except Exception:
            continue
        h = d.get("account_handle_internal")
        if h:
            handles[h] = {"file": f.split("11_who_to_learn_from/")[1],
                          "sector": d.get("sector"), "normalized": d.get("account_handle_normalized")}
    print(f"handles to verify: {len(handles)}")
    from apify_client import ApifyClient
    client = ApifyClient(env("APIFY_TOKEN"))
    run = client.actor("apify/instagram-profile-scraper").call(
        run_input={"usernames": sorted(handles)})
    ds = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    live = {}
    for item in client.dataset(ds).iterate_items():
        u = item.get("username")
        if not u:
            continue
        live[u.lower()] = {"name": item.get("fullName"), "followers": item.get("followersCount"),
                           "posts": item.get("postsCount"), "private": item.get("private"),
                           "bio": (item.get("biography") or "")[:120]}
    out, counts = {}, {"verified": 0, "dead": 0, "restricted": 0}
    for h, meta in handles.items():
        rec = live.get(h.lower())
        if rec and rec.get("followers") is not None:
            verdict = "verified"
        elif rec:
            verdict = "restricted"
        else:
            verdict = "dead"
        counts[verdict] += 1
        out[h] = {**meta, "verdict": verdict, **(rec or {})}
    result = {"generated": datetime.now().isoformat(timespec="seconds"),
              "summary": counts, "handles": out}
    (BASE / "11_who_to_learn_from/handle_verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1))
    # assert by re-read
    re = json.loads((BASE / "11_who_to_learn_from/handle_verification.json").read_text())
    assert len(re["handles"]) == len(handles)
    print(f"verdicts: {counts}")
    dead = [h for h, v in out.items() if v["verdict"] == "dead"]
    if dead:
        print("dead handles (mangling suspects):")
        for h in dead[:15]:
            print(f"  💀 {h}")


if __name__ == "__main__":
    main()
