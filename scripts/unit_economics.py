#!/usr/bin/env python3
"""UNIT ECONOMICS COLLECTOR (B090, June 12 — RABIE's pick).
Mohamed's money law («be very careful with spending the money») as numbers.
Three honesty tiers: REAL (logged receipts), ESTIMATED (derived counts × stated
per-call assumptions), UNKNOWN (untracked — named, never guessed silently).

Usage: python3 scripts/unit_economics.py
"""
import json, glob
from pathlib import Path

BASE = Path(__file__).parent.parent

# stated assumptions (June 2026 list prices, conservative)
EST = {"gpt4o_call": 0.01, "gpt4o_mini_call": 0.001, "sonnet_call": 0.012,
        "calls_per_client_card": 3,      # angle gpt + captions gpt + captions sonnet
        "fal_schnell_image": 0.003}


def main():
    report = {"_assumptions": EST, "_tiers": "REAL=logged · EST=derived · UNKNOWN=named"}

    # REAL: fal image spend
    img = 0.0
    f = BASE / "data/image_cost_log.jsonl"
    if f.exists():
        img = sum(json.loads(l).get("usd", 0) for l in f.read_text().strip().split("\n") if l.strip())
    report["images_usd_REAL"] = round(img, 3)

    # EST: client pipeline (cards × calls)
    clients = {}
    for cdir in sorted((BASE / "clients").iterdir()):
        posts = list((cdir / "posts").glob("*.json")) if (cdir / "posts").is_dir() else []
        if not posts:
            continue
        n = len(posts)
        est = n * EST["calls_per_client_card"] * (EST["gpt4o_call"] + EST["sonnet_call"]) / 2
        clients[cdir.name] = {"cards": n, "est_llm_usd": round(est, 2),
                                "usd_per_card": round(est / n, 4)}
    report["clients_EST"] = clients

    # EST: 41-brand API generations
    gl = BASE / "logs/generation_log.jsonl"
    gen_n = len(gl.read_text().strip().split("\n")) if gl.exists() else 0
    report["api_generations_EST"] = {"calls": gen_n, "usd": round(gen_n * EST["gpt4o_call"], 2)}

    # EST: the pair's own thinking (rabie rulings + cold consults)
    rb = sum(len(open(f).read().strip().split("\n"))
             for f in glob.glob(str(Path.home() / "agents/rabie/sessions/*.jsonl")))
    cc = sum(1 for l in (BASE / "data/make_sure_log.jsonl").read_text().strip().split("\n")
             if "cold" in l.lower()) if (BASE / "data/make_sure_log.jsonl").exists() else 0
    report["orchestra_EST"] = {"rabie_rulings": rb, "cold_consults": cc,
                                 "usd": round(rb * EST["gpt4o_call"] + cc * EST["gpt4o_mini_call"], 2)}

    # UNKNOWN: named, not guessed
    report["UNKNOWN"] = ["Apify credits (dashboard only — no local receipt)",
                          "audience-mirror mini calls (3 one-shot runs, ~$0.01 class)"]

    total = (report["images_usd_REAL"] + sum(c["est_llm_usd"] for c in clients.values())
             + report["api_generations_EST"]["usd"] + report["orchestra_EST"]["usd"])
    report["week_total_usd_lower_bound"] = round(total, 2)
    out = BASE / "data/unit_economics.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"  images REAL: ${report['images_usd_REAL']}")
    for h, c in clients.items():
        print(f"  {h}: {c['cards']} cards · ~${c['est_llm_usd']} (${c['usd_per_card']}/card)")
    print(f"  api gens: {gen_n} ≈ ${report['api_generations_EST']['usd']} · orchestra: ≈ ${report['orchestra_EST']['usd']}")
    print(f"  WEEK TOTAL (lower bound): ≈ ${report['week_total_usd_lower_bound']} → data/unit_economics.json")


if __name__ == "__main__":
    main()
