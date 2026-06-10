#!/usr/bin/env python3
"""Rescue the buried captions (June 11, 2026).
Audit finding: the old _auto_score picked filter-failing captions as 'best' in 46%
of V3-era sets while a clean option existed in the SAME set (240/240 of bad picks).
This script re-picks 'best' with scorer_v2 across all queue items. The old pick is
preserved as 'best_legacy_scorer'. Idempotent. Queues are backed up beforehand.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scorer_v2 import pick_best
from caption_filter import check

BASE = Path(__file__).parent.parent
BRAND_EN = {}  # brand_ar -> brand_en from the matrix
for b in json.loads((BASE / "data/brief_matrix.json").read_text()):
    BRAND_EN[b["brand"]] = b["brand_en"]

rescued, total = 0, 0
for qf in ["claude_queue.json", "gpt4o_queue.json", "humain_queue.json"]:
    p = BASE / "logs" / qf
    q = json.loads(p.read_text())
    for it in q.get("pending", []) + q.get("approved", []):
        opts = it.get("options", {})
        if not isinstance(opts, dict) or not opts:
            continue
        total += 1
        old_best = str(it.get("best", ""))
        brand_en = it.get("brand_en") or BRAND_EN.get(it.get("brand", ""), "")
        new_best, scores = pick_best(opts, brand_en, it.get("brand", ""))
        if not new_best:
            continue
        old_ok, _ = check(old_best)
        if new_best != old_best and (not old_ok):
            it["best_legacy_scorer"] = old_best
            it["best"] = new_best
            it["rescued_by"] = "scorer_v2_2026-06-11"
            rescued += 1
        it["scores_v2"] = scores
    p.write_text(json.dumps(q, ensure_ascii=False, indent=2))
print(f"items examined: {total} · RESCUED (bad best → clean best): {rescued}")
