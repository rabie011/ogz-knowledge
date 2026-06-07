"""
routing_manager.py — technique routing based on human approval history

Tracks which technique wins for each sector × occasion combo.
After ≥5 examples per combo, collector sends only top-2 + 1 wildcard
instead of all 5 techniques.

Schema in logs/routing_scores.json:
{
  "sector:occasion": {
    "أ": {"wins": 3, "total": 8},
    "ب": {"wins": 5, "total": 8},
    ...
  }
}
"""

import json
from pathlib import Path
from typing import Optional

BASE = Path(__file__).parent.parent
ROUTING_FILE = BASE / "logs" / "routing_scores.json"
ALL_TECHNIQUES = ["أ", "ب", "ج", "د", "هـ"]
MIN_EXAMPLES = 5   # minimum before routing kicks in
TOP_N = 2          # send top N + 1 wildcard when routing active


def load_scores() -> dict:
    if not ROUTING_FILE.exists():
        return {}
    return json.loads(ROUTING_FILE.read_text())


def save_scores(scores: dict) -> None:
    ROUTING_FILE.write_text(json.dumps(scores, ensure_ascii=False, indent=2))


def record(technique: str, sector: str, occasion: str, approved: bool) -> None:
    """Record one human decision. approved=True for gold, False for weak/skip."""
    scores = load_scores()
    key = f"{sector}:{occasion}"
    if key not in scores:
        scores[key] = {t: {"wins": 0, "total": 0} for t in ALL_TECHNIQUES}
    combo = scores[key].setdefault(technique, {"wins": 0, "total": 0})
    combo["total"] += 1
    if approved:
        combo["wins"] += 1
    save_scores(scores)


def get_route(sector: str, occasion: str) -> Optional[list[str]]:
    """
    Return ordered list of techniques to use for this sector × occasion.
    Returns None if not enough data yet (send all 5).
    """
    scores = load_scores()
    key = f"{sector}:{occasion}"
    combo = scores.get(key, {})

    # Need at least MIN_EXAMPLES total decisions to route
    total = sum(v.get("total", 0) for v in combo.values())
    if total < MIN_EXAMPLES:
        return None

    # Rank by win rate, break ties by total (more data = more confident)
    def win_rate(t: str) -> float:
        d = combo.get(t, {"wins": 0, "total": 0})
        if d["total"] == 0:
            return 0.0
        return d["wins"] / d["total"]

    ranked = sorted(ALL_TECHNIQUES, key=win_rate, reverse=True)

    # Top 2 + 1 wildcard (lowest-ranked — explore to avoid getting stuck)
    top = ranked[:TOP_N]
    wildcard = ranked[-1]
    if wildcard in top:
        wildcard = ranked[TOP_N] if len(ranked) > TOP_N else ranked[-1]

    result = list(dict.fromkeys(top + [wildcard]))  # deduplicate, preserve order
    return result


def summary() -> dict:
    """Return win-rate summary for all combos with enough data."""
    scores = load_scores()
    out = {}
    for key, combo in scores.items():
        total = sum(v.get("total", 0) for v in combo.values())
        if total < MIN_EXAMPLES:
            continue
        rates = {t: round(combo[t]["wins"] / combo[t]["total"], 2)
                 if combo[t]["total"] > 0 else 0.0
                 for t in ALL_TECHNIQUES if t in combo}
        best = max(rates, key=rates.get)
        out[key] = {"total_decisions": total, "win_rates": rates, "best": best}
    return out


if __name__ == "__main__":
    s = summary()
    if not s:
        print("No routing data yet — need ≥5 approvals per sector:occasion combo.")
    else:
        for k, v in s.items():
            print(f"{k}: best={v['best']} | rates={v['win_rates']}")
