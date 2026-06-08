#!/usr/bin/env python3
"""
export_dpo.py — Export human preference pairs in DPO/RLHF training format.

Reads:
  - logs/cross_preferences.json  (cross-model: HUMAIN vs GPT-4o vs Claude)
  - logs/humain_pairwise.json    (within-HUMAIN: technique Elo comparisons)
  - logs/humain_queue.json       (approved items → positive examples)

Outputs:
  - logs/dpo_dataset.jsonl       (DPO format: prompt + chosen + rejected)
  - logs/sft_dataset.jsonl       (SFT format: approved gold outputs only)
  - logs/dataset_stats.json      (summary for review)

DPO format (each line is a JSON object):
  {
    "prompt":   "<the brief prompt in Arabic>",
    "chosen":   "<preferred caption>",
    "rejected": "<less-preferred caption>",
    "meta": {
      "brand": "...", "occasion": "...", "sector": "...",
      "winner_model": "...", "loser_model": "...",
      "source": "cross_model | pairwise_elo | human_review"
    }
  }

SFT format (each line):
  {
    "prompt":    "<the brief prompt in Arabic>",
    "completion": "<approved gold caption>",
    "meta": { "brand": "...", "occasion": "...", "sector": "...", "source": "humain_approved" }
  }

Usage:
  python3 scripts/export_dpo.py             # export all
  python3 scripts/export_dpo.py --stats     # show stats only, no file write
  python3 scripts/export_dpo.py --min-conf 2 # require ≥N Elo comparisons for pairwise
"""

import json
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from humain_collector import build_prompt, OCCASION_AR as _OCC_BASE

# Complete occasion map (12 occasions in matrix)
OCCASION_AR = {
    **_OCC_BASE,
    "back_to_school":    "العودة للمدارس",
    "evergreen":         "عام (دائم)",
    "graduation_season": "موسم التخرج",
    "summer_campaign":   "الصيف",
    "winter_seasonal":   "الشتاء",
}


def _build_brief_prompt(brand: str, occasion: str, brief_matrix: list) -> str:
    """Find the brief from the matrix and build its prompt."""
    for b in brief_matrix:
        if b["brand"] == brand and b["occasion"] == occasion:
            return build_prompt(b)
    # Fallback: minimal prompt
    occ_ar = OCCASION_AR.get(occasion, occasion)
    return f"اكتب كابشن إنستغرام لـ {brand} لمناسبة {occ_ar}. لهجة سعودية. بدون إنجليزي."


def export_cross_model(brief_matrix: list, min_conf: int = 1) -> list:
    """Export cross-model preference pairs (HUMAIN vs GPT-4o vs Claude)."""
    prefs_file = BASE / "logs" / "cross_preferences.json"
    if not prefs_file.exists():
        return []

    prefs = json.loads(prefs_file.read_text())
    pairs = []
    for c in prefs.get("comparisons", []):
        winner = c.get("winner_model", "")
        loser  = c.get("loser_model", "")
        if winner == "skip" or not c.get("winner_caption") or not c.get("loser_caption"):
            continue

        brand    = c.get("brief_key", "|").split("|")[0]
        occasion = c.get("brief_key", "|").split("|")[1] if "|" in c.get("brief_key", "") else ""

        prompt = _build_brief_prompt(brand, occasion, brief_matrix)

        pairs.append({
            "prompt":   prompt,
            "chosen":   c["winner_caption"],
            "rejected": c["loser_caption"],
            "meta": {
                "brand":         brand,
                "occasion":      occasion,
                "winner_model":  winner,
                "loser_model":   loser,
                "source":        "cross_model",
            }
        })
    return pairs


def export_pairwise_elo(brief_matrix: list, min_conf: int = 1) -> list:
    """Export within-HUMAIN pairwise Elo comparisons as preference pairs."""
    pairwise_file = BASE / "logs" / "pairwise_comparisons.json"
    if not pairwise_file.exists():
        return []

    data = json.loads(pairwise_file.read_text())
    pairs = []
    for c in data.get("comparisons", []):
        wk = c.get("winner_tech")
        lk = c.get("loser_tech")
        if not wk or not lk:
            continue

        win_cap  = c.get("winner_caption", "")
        lose_cap = c.get("loser_caption", "")
        brand    = c.get("winner_brand", "")
        sector   = c.get("winner_sector", "")
        occasion = c.get("winner_occ", "")

        if not win_cap or not lose_cap:
            continue

        prompt = _build_brief_prompt(brand, occasion, brief_matrix)

        pairs.append({
            "prompt":   prompt,
            "chosen":   win_cap,
            "rejected": lose_cap,
            "meta": {
                "brand":          brand,
                "occasion":       occasion,
                "sector":         sector,
                "winner_tech":    wk,
                "loser_tech":     lk,
                "winner_model":   "humain",
                "loser_model":    "humain",
                "source":         "pairwise_elo",
            }
        })
    return pairs


def export_approved_sft(brief_matrix: list) -> list:
    """Export approved HUMAIN outputs as SFT positive examples."""
    queue_file = BASE / "logs" / "humain_queue.json"
    if not queue_file.exists():
        return []

    q = json.loads(queue_file.read_text())
    items = q.get("approved", [])

    sft = []
    for item in items:
        brand    = item.get("brand", "")
        occasion = item.get("occasion", "")
        best_cap = item.get("best", "")
        if not best_cap:
            # Pick highest-scored option
            scores = item.get("scores", {})
            opts   = item.get("options", {})
            if scores:
                best_k = max(scores, key=lambda k: scores.get(k, 0))
                best_cap = opts.get(best_k, "")
        if not best_cap:
            continue

        prompt = _build_brief_prompt(brand, occasion, brief_matrix)

        sft.append({
            "prompt":     prompt,
            "completion": best_cap,
            "meta": {
                "brand":    brand,
                "occasion": occasion,
                "sector":   item.get("sector", ""),
                "source":   "humain_approved",
            }
        })
    return sft


def _item_avg_score(item: dict) -> float:
    """Compute avg quality score from either avg_score field or scores dict."""
    if "avg_score" in item:
        return item["avg_score"]
    scores = item.get("scores", {})
    if scores:
        vals = [v for v in scores.values() if isinstance(v, (int, float)) and v > 0]
        return sum(vals) / max(len(vals), 1)
    return 0.0


def export_pending_sft(brief_matrix: list, min_score: int = 75) -> list:
    """Export high-scoring pending items as SFT candidates (not yet human-approved)."""
    queue_file = BASE / "logs" / "humain_queue.json"
    if not queue_file.exists():
        return []

    q = json.loads(queue_file.read_text())
    items = [i for i in q.get("pending", [])
             if i.get("diversity_ok") and _item_avg_score(i) >= min_score]

    sft = []
    for item in items:
        brand    = item.get("brand", "")
        occasion = item.get("occasion", "")
        scores   = item.get("scores", {})
        opts     = item.get("options", {})
        if not scores or not opts:
            continue

        best_k = max(scores, key=lambda k: scores.get(k, 0))
        best_cap = opts.get(best_k, "")
        if not best_cap:
            continue

        prompt = _build_brief_prompt(brand, occasion, brief_matrix)
        avg_sc = _item_avg_score(item)

        sft.append({
            "prompt":     prompt,
            "completion": best_cap,
            "meta": {
                "brand":       brand,
                "occasion":    occasion,
                "sector":      item.get("sector", ""),
                "auto_score":  scores.get(best_k, 0),
                "avg_score":   avg_sc,
                "technique":   best_k,
                "source":      "humain_pending_high_score",
                "note":        "NOT human-approved — use carefully",
            }
        })
    return sft


def main():
    parser = argparse.ArgumentParser(description="Export DPO/SFT training datasets")
    parser.add_argument("--stats", action="store_true", help="Show stats only, no file write")
    parser.add_argument("--min-conf", type=int, default=1, help="Min comparisons for pairwise Elo pairs")
    parser.add_argument("--min-score", type=int, default=75, help="Min auto-score for pending SFT items")
    parser.add_argument("--include-pending-sft", action="store_true",
                        help="Include high-scoring pending (not yet approved) as SFT data")
    args = parser.parse_args()

    brief_matrix = json.loads((BASE / "data" / "brief_matrix.json").read_text())

    # Collect all data
    cross_pairs    = export_cross_model(brief_matrix, args.min_conf)
    pairwise_pairs = export_pairwise_elo(brief_matrix, args.min_conf)
    approved_sft   = export_approved_sft(brief_matrix)
    pending_sft    = export_pending_sft(brief_matrix, args.min_score) if args.include_pending_sft else []

    all_dpo = cross_pairs + pairwise_pairs
    all_sft = approved_sft + pending_sft

    print(f"\n{'='*55}")
    print(f"DPO DATASET EXPORT")
    print(f"{'='*55}")
    print(f"  DPO pairs:")
    print(f"    cross-model preferences: {len(cross_pairs)}")
    print(f"    within-HUMAIN Elo:       {len(pairwise_pairs)}")
    print(f"    TOTAL DPO:               {len(all_dpo)}")
    print(f"\n  SFT examples:")
    print(f"    human-approved gold:     {len(approved_sft)}")
    if args.include_pending_sft:
        print(f"    high-score pending (Q≥{args.min_score}): {len(pending_sft)}")
    print(f"    TOTAL SFT:               {len(all_sft)}")
    print(f"\n  ⚠  DPO training needs ~1000+ pairs for reliable signal")
    print(f"     Keep comparing at /cross-compare to build up the dataset")
    print(f"{'='*55}")

    if args.stats:
        return

    if not all_dpo and not all_sft:
        print("\n  Nothing to export yet. Start comparing at http://localhost:4100/cross-compare")
        return

    # Write DPO dataset
    if all_dpo:
        dpo_file = BASE / "logs" / "dpo_dataset.jsonl"
        with open(dpo_file, "w", encoding="utf-8") as f:
            for item in all_dpo:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"\n  ✅ DPO dataset: {dpo_file} ({len(all_dpo)} pairs)")

    # Write SFT dataset
    if all_sft:
        sft_file = BASE / "logs" / "sft_dataset.jsonl"
        with open(sft_file, "w", encoding="utf-8") as f:
            for item in all_sft:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  ✅ SFT dataset: {sft_file} ({len(all_sft)} examples)")

    # Summary JSON for review
    stats = {
        "exported_at": __import__("datetime").datetime.now().isoformat(),
        "dpo_pairs":   len(all_dpo),
        "sft_examples": len(all_sft),
        "breakdown": {
            "cross_model_pairs":    len(cross_pairs),
            "pairwise_elo_pairs":   len(pairwise_pairs),
            "approved_sft":         len(approved_sft),
            "pending_sft":          len(pending_sft),
        },
        "note": "DPO needs ~1000+ pairs. Keep running /cross-compare to grow the dataset."
    }
    stats_file = BASE / "logs" / "dataset_stats.json"
    stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"  ✅ Stats: {stats_file}")


if __name__ == "__main__":
    main()
