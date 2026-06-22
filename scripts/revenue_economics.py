#!/usr/bin/env python3
"""REVENUE SIDE of unit economics (B091, June 23 — RABIE's pick).

unit_economics.py answers "what does the pair SPEND?". This answers the other half Mohamed
asked for: "what does each client BRING, beside cost-per-YES?" — and, crucially, the two
truth-views that matter while the pilots are unsigned:

  • approving_but_not_paying — clients whose work we APPROVE/produce but who carry NO confirmed
    commercial terms (the real state of all 3 pilots right now). Cost with no contracted revenue.
  • paying_but_silent       — clients on confirmed PAID terms but with no recent positive verdict
    (revenue with no engagement — the churn-risk view). Empty today; the reader exists for when
    a tier gets confirmed.

HONESTY TIERS (same discipline as unit_economics):
  REAL    — Mohamed-pinned tier price for a CONFIRMED client (data/commercial_tiers.json).
  UNKNOWN — tier not confirmed → revenue is NAMED as unknown, never guessed (Rule #9).

Nothing here invents a per-client number. A client's revenue is REAL only once its
commercial_terms.json carries a confirmed tier; until then it is honestly UNKNOWN. The pinned
TIER prices are real (his pin), the per-client ASSIGNMENT is what's missing.

Usage: python3 scripts/revenue_economics.py
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
PILOTS = ["eatjurisha", "albaik", "myfitness.sa"]
_CONFIRMED = {"confirmed", "active", "signed", "paying"}


def load_tiers(path: Path = None) -> dict:
    """The REAL pinned tier price table {tier: monthly_sar}. {} if absent (named, not faked)."""
    path = path or (BASE / "data/commercial_tiers.json")
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in (doc.get("tiers") or {}).items() if isinstance(v, (int, float))}


def client_terms(clients_dir: Path = None, pilots=PILOTS) -> dict:
    """Per-client commercial_terms organ as read off disk. Missing organ → status 'no_organ'
    (a real Rule #6 severance signal, never silently treated as zero)."""
    clients_dir = clients_dir or (BASE / "clients")
    out = {}
    for h in pilots:
        p = Path(clients_dir) / h / "profile" / "commercial_terms.json"
        if not p.exists():
            out[h] = {"tier": None, "status": "no_organ", "monthly_sar": None}
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            out[h] = {"tier": None, "status": "unreadable", "monthly_sar": None}
            continue
        out[h] = {"tier": d.get("tier"),
                  "status": (d.get("status") or "no_terms_confirmed"),
                  "monthly_sar": d.get("monthly_sar")}
    return out


def _client_approving(h: str, clients_dir: Path) -> bool:
    """Does this client have produced/approved work? Proxy: any post cards on disk. Cheap +
    zero-LLM; the cost side (unit_economics) already keys off the same 'posts' dir."""
    return (Path(clients_dir) / h / "posts").is_dir() and \
           any((Path(clients_dir) / h / "posts").glob("*.json"))


def revenue_per_client(clients_dir: Path = None, tiers_path: Path = None, pilots=PILOTS) -> dict:
    """REAL monthly_sar for a confirmed tier; else UNKNOWN. Honesty-tiered, never guessed."""
    clients_dir = clients_dir or (BASE / "clients")
    tiers = load_tiers(tiers_path)
    terms = client_terms(clients_dir, pilots)
    out = {}
    for h, t in terms.items():
        status = t["status"]
        tier = t["tier"]
        if status.lower() in _CONFIRMED and tier in tiers:
            out[h] = {"tier": tier, "monthly_sar": tiers[tier], "honesty": "REAL"}
        elif status.lower() in _CONFIRMED and t.get("monthly_sar"):
            out[h] = {"tier": tier, "monthly_sar": t["monthly_sar"], "honesty": "REAL"}
        else:
            out[h] = {"tier": tier, "monthly_sar": None, "honesty": "UNKNOWN",
                      "why": f"status={status} — no confirmed tier"}
    return out


def views(clients_dir: Path = None, tiers_path: Path = None, pilots=PILOTS) -> dict:
    """The two truth-views Mohamed named."""
    clients_dir = clients_dir or (BASE / "clients")
    rev = revenue_per_client(clients_dir, tiers_path, pilots)
    approving = {h for h in pilots if _client_approving(h, Path(clients_dir))}
    paying = {h for h, r in rev.items() if r["honesty"] == "REAL"}
    return {
        "approving_but_not_paying": sorted(approving - paying),
        "paying_but_silent": sorted(paying - approving),
        "approving_and_paying": sorted(approving & paying),
    }


def cost_per_yes(unit_econ_path: Path = None, answers_path: Path = None) -> dict:
    """Total lower-bound spend ÷ Mohamed's positive verdicts. UNKNOWN (named) if either input
    is missing or YES==0 — a ratio over zero approvals is a lie, not a big number (Rule #9)."""
    unit_econ_path = unit_econ_path or (BASE / "data/unit_economics.json")
    cost = None
    if unit_econ_path.exists():
        try:
            cost = json.loads(unit_econ_path.read_text(encoding="utf-8")).get("week_total_usd_lower_bound")
        except Exception:
            cost = None
    yes = None
    try:
        import intel_consumer_health as ich
        yes = ich.portal_positive_verdicts(*( (answers_path,) if answers_path else () ))
    except Exception:
        yes = None
    if cost is None or not yes:
        return {"cost_usd": cost, "yes": yes, "usd_per_yes": None, "honesty": "UNKNOWN",
                "why": "missing cost or zero positive verdicts"}
    return {"cost_usd": cost, "yes": yes, "usd_per_yes": round(cost / yes, 3), "honesty": "EST"}


def build_report(clients_dir: Path = None, tiers_path: Path = None,
                 unit_econ_path: Path = None, answers_path: Path = None, pilots=PILOTS) -> dict:
    return {
        "_tiers_REAL": load_tiers(tiers_path),
        "revenue_per_client": revenue_per_client(clients_dir, tiers_path, pilots),
        "cost_per_yes": cost_per_yes(unit_econ_path, answers_path),
        "views": views(clients_dir, tiers_path, pilots),
        "_note": "Revenue per client is UNKNOWN until Mohamed confirms a tier. All 3 pilots are "
                 "currently approving_but_not_paying — cost with no contracted revenue.",
    }


def main():
    rep = build_report()
    out = BASE / "data/revenue_economics.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    tiers = rep["_tiers_REAL"]
    print(f"  tiers REAL (SAR/mo): {tiers}")
    for h, r in rep["revenue_per_client"].items():
        print(f"  {h}: revenue {r['honesty']} ({r.get('monthly_sar')}) tier={r.get('tier')}")
    cpy = rep["cost_per_yes"]
    print(f"  cost/YES: {cpy['honesty']} (${cpy.get('usd_per_yes')} over {cpy.get('yes')} YES)")
    print(f"  approving_but_not_paying: {rep['views']['approving_but_not_paying']}")
    print(f"  → data/revenue_economics.json")
    return rep


if __name__ == "__main__":
    main()
