#!/usr/bin/env python3
"""
build_dialect_register_occasion_matrix.py
3D cross-tab: (dialect, register, occasion) → count of obs matching.
Output: logs/dialect_register_occasion_matrix.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

def main():
    # dialect → register → occasion → count
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # Also track accounts for each combo
    combo_accounts = defaultdict(set)  # (dialect, register, occasion) → set of accounts

    total_obs = 0
    null_dialect = 0
    null_register = 0
    null_occasion = 0

    # All unique values seen
    all_dialects = set()
    all_registers = set()
    all_occasions = set()

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total_obs += 1
        account = data.get("account_handle_normalized", "unknown")

        vo = data.get("voice_observations", {})
        dialect = vo.get("dialect_detected") or "null"
        register = vo.get("register") or "null"
        occasion = data.get("cultural_notes", {}).get("occasion_relevance") or "null"

        # Normalize to lowercase slug
        dialect = str(dialect).lower().strip()
        register = str(register).lower().strip().replace(" ", "_")
        occasion = str(occasion).lower().strip()

        if dialect == "null":
            null_dialect += 1
        if register == "null":
            null_register += 1
        if occasion == "null":
            null_occasion += 1

        all_dialects.add(dialect)
        all_registers.add(register)
        all_occasions.add(occasion)

        matrix[dialect][register][occasion] += 1
        combo_accounts[(dialect, register, occasion)].add(account)

    # Flatten to list of triples, sorted by count
    triples = []
    for dialect, reg_map in matrix.items():
        for register, occ_map in reg_map.items():
            for occasion, count in occ_map.items():
                accounts = sorted(combo_accounts[(dialect, register, occasion)])
                triples.append({
                    "dialect": dialect,
                    "register": register,
                    "occasion": occasion,
                    "count": count,
                    "account_count": len(accounts),
                    "accounts": accounts
                })

    triples.sort(key=lambda x: -x["count"])

    # Find anomalies: unexpected combos
    # Flag: MSA formal used for casual occasions (summer, everyday)
    anomalies = []
    for t in triples:
        if t["dialect"] in ("msa", "classical") and t["register"] == "formal" and \
           t["occasion"] in ("evergreen", "summer_campaign", "everyday") and t["count"] >= 3:
            anomalies.append({
                "type": "formal_msa_on_casual_occasion",
                "combo": f"{t['dialect']}/{t['register']}/{t['occasion']}",
                "count": t["count"],
                "note": "MSA formal used on casual occasion — may be overly stiff"
            })
        if t["dialect"] == "english_arabic_mixed" and \
           t["occasion"] in ("ramadan", "eid_al_fitr", "eid_al_adha", "national_day") and t["count"] >= 2:
            anomalies.append({
                "type": "english_mixed_on_sacred_occasion",
                "combo": f"{t['dialect']}/{t['register']}/{t['occasion']}",
                "count": t["count"],
                "note": "Mixed English/Arabic on sacred occasion — authenticity risk"
            })

    # Per-dialect summary
    dialect_summary = {}
    for d in sorted(all_dialects):
        d_triples = [t for t in triples if t["dialect"] == d]
        top_registers = defaultdict(int)
        top_occasions = defaultdict(int)
        for t in d_triples:
            top_registers[t["register"]] += t["count"]
            top_occasions[t["occasion"]] += t["count"]
        dialect_summary[d] = {
            "total_obs": sum(t["count"] for t in d_triples),
            "top_registers": dict(sorted(top_registers.items(), key=lambda x: -x[1])[:5]),
            "top_occasions": dict(sorted(top_occasions.items(), key=lambda x: -x[1])[:5])
        }

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "total_observations": total_obs,
        "null_rates": {
            "dialect_null": null_dialect,
            "register_null": null_register,
            "occasion_null": null_occasion
        },
        "unique_values": {
            "dialects": sorted(all_dialects),
            "registers": sorted(all_registers),
            "occasions": sorted(all_occasions)
        },
        "anomalies": anomalies,
        "dialect_summary": dialect_summary,
        "top_50_triples": triples[:50],
        "all_triples_count": len(triples),
        "all_triples": triples
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "dialect_register_occasion_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Total obs processed: {total_obs}")
    print(f"Unique (dialect × register × occasion) triples: {len(triples)}")
    print(f"Anomalies flagged: {len(anomalies)}")
    print(f"\nTop 10 triples:")
    for t in triples[:10]:
        print(f"  {t['dialect']}/{t['register']}/{t['occasion']}: {t['count']} obs")
    print(f"Output: logs/dialect_register_occasion_matrix.json")

if __name__ == "__main__":
    main()
