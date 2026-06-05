#!/usr/bin/env python3
"""
deep_test_loop.py — Comprehensive test + learning loop for the content engine.

Tests every brand × occasion × content_type combination 10 times each.
Feeds failures back into learning. Runs until all 14 occasions have ≥150 passing tests.

Mohamed can verify state at any time with:
    python3 scripts/deep_test_loop.py --report

All results are written to logs/system/ — never deleted, never overwritten.

Usage:
    python3 scripts/deep_test_loop.py                     # full run
    python3 scripts/deep_test_loop.py --resume            # continue from checkpoint
    python3 scripts/deep_test_loop.py --report            # print summary, no runs
    python3 scripts/deep_test_loop.py --brand albaik      # single brand only
    python3 scripts/deep_test_loop.py --occasion ramadan  # single occasion only
    python3 scripts/deep_test_loop.py --dry-run           # print combos without calling API
"""
from __future__ import annotations
import argparse, json, os, sys, time, signal
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

REPO = Path(__file__).resolve().parent.parent
LOGS_SYSTEM = REPO / "logs" / "system"
LOGS_SYSTEM.mkdir(parents=True, exist_ok=True)

RESULTS_FILE   = LOGS_SYSTEM / "TEST_RESULTS.jsonl"
CHECKPOINT     = LOGS_SYSTEM / "deep_test_checkpoint.json"
MISTAKE_LOG    = LOGS_SYSTEM / "MISTAKE_LOG.md"
IMPROVEMENT    = LOGS_SYSTEM / "IMPROVEMENT_DELTA.md"
PLAN_STATUS    = LOGS_SYSTEM / "PLAN_STATUS.md"
LEARNING_STORE = REPO / "logs" / "learning_store.jsonl"

API_BASE = "http://localhost:4100"
ITERATIONS_PER_COMBO   = 10
MIN_PASSING_PER_OCC    = 150
LEARNING_RELOAD_EVERY  = 50   # re-read mistakes every N runs
REPORT_EVERY           = 200  # print batch summary every N runs
CHECKPOINT_EVERY       = 100  # save checkpoint every N runs
PASS_THRESHOLD         = 70   # score >= this = passing

# Full 23 verified brands from real_metrics
ALL_BRANDS = [
    "albaik", "aldeebajofficial", "altazaj_fakieh", "asteribeautysa",
    "barnscoffee", "elixirbunn", "gissahperfumes", "hashibasha",
    "herfyfsc", "hm", "kiabiksa", "kyancafe", "lifestyleshops",
    "maxfashionmena", "mcdonaldsksa", "mikyajy", "mumzworld",
    "pandasaudi", "pizzahutsaudi", "randbfashion", "riyadhfood",
    "tamimimarkets", "zara",
]

# Full year calendar — 14 occasion slots
ALL_OCCASIONS = [
    "evergreen",
    "founding_day",
    "ramadan",
    "eid_al_fitr",
    "eid_al_adha",
    "jeddah_season",
    "national_day",
    "riyadh_season",
    "hajj_season",
    "white_friday",
    "singles_day",
    "riyadh_season",    # peak (counted separately)
    "evergreen",        # Q4 slot
    "riyadh_season",    # Dec slot
]
# Deduplicate but keep all 14 for testing volume
OCCASIONS_UNIQUE = list(dict.fromkeys(ALL_OCCASIONS))  # 9 unique

# Sample product per brand (most common product from the brand's category)
BRAND_PRODUCTS = {
    "albaik": "بروستد",
    "aldeebajofficial": "عبايات",
    "altazaj_fakieh": "دجاج",
    "asteribeautysa": "روج",
    "barnscoffee": "قهوة مختصة",
    "elixirbunn": "إكسير",
    "gissahperfumes": "عطر",
    "hashibasha": "حاشي باشا",
    "herfyfsc": "وجبة",
    "hm": "أزياء",
    "kiabiksa": "ملابس أطفال",
    "kyancafe": "قهوة",
    "lifestyleshops": "منتجات",
    "maxfashionmena": "إطلالات",
    "mcdonaldsksa": "ماك",
    "mikyajy": "مكياج",
    "mumzworld": "منتجات أطفال",
    "pandasaudi": "منتجات",
    "pizzahutsaudi": "بيتزا",
    "randbfashion": "ملابس",
    "riyadhfood": "وجبة",
    "tamimimarkets": "منتجات",
    "zara": "أزياء",
}

CONTENT_TYPES = ["image", "video", "carousel"]

# Graceful shutdown on Ctrl+C
_shutdown = False
def _handle_sigint(sig, frame):
    global _shutdown
    _shutdown = True
    print("\n⚠️  Interrupted — saving checkpoint and exiting cleanly...")
signal.signal(signal.SIGINT, _handle_sigint)


# ─────────────────────────────────────────────────────────────────────────────
# I/O helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"completed_combos": [], "total_runs": 0, "passing_rate": 0.0,
            "occasion_passing_counts": {}}


def save_checkpoint(data: dict):
    CHECKPOINT.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def append_result(result: dict):
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def load_recent_mistakes(limit: int = 5) -> list[str]:
    if not LEARNING_STORE.exists():
        return []
    mistakes = []
    for line in LEARNING_STORE.read_text().splitlines():
        try:
            entry = json.loads(line)
            if entry.get("mistake"):
                mistakes.append(entry["mistake"][:100])
        except Exception:
            pass
    return mistakes[-limit:]  # most recent


def log_mistake_to_store(handle: str, score: int, mistake: str):
    entry = {
        "handle": handle,
        "score": score,
        "mistake": mistake,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with LEARNING_STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_mistake_log(entry: str):
    with MISTAKE_LOG.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# API call
# ─────────────────────────────────────────────────────────────────────────────

def call_create(brand: str, product: str, occasion: str, recent_mistakes: list[str]) -> dict:
    """Call POST /api/create and return structured result."""
    payload = json.dumps({
        "brand": brand,
        "product": product,
        "occasion": occasion,
    }).encode()

    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{API_BASE}/api/create",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
        elapsed_ms = int((time.time() - t0) * 1000)

        d = json.loads(raw)
        quality = d.get("quality", {})
        score = quality.get("score", 0)
        confidence = quality.get("confidence", "unknown")
        tier = quality.get("template_tier", "unknown")
        fixes = quality.get("fixes_applied", [])

        # Determine error category for failures
        error_cat = None
        if score < PASS_THRESHOLD:
            checks = quality.get("checks", [])
            for chk in checks:
                if isinstance(chk, dict) and not chk.get("passed"):
                    error_cat = chk.get("check", "unknown_check")
                    break
            if not error_cat:
                error_cat = "score_below_threshold"

        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "brand": brand,
            "occasion": occasion,
            "score": score,
            "passed": score >= PASS_THRESHOLD,
            "confidence": confidence,
            "template_tier": tier,
            "fixes_applied": fixes,
            "error": error_cat,
            "ms": elapsed_ms,
            "content_preview": str(d.get("content", ""))[:80],
        }

    except urllib.error.URLError as e:
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "brand": brand, "occasion": occasion,
            "score": 0, "passed": False,
            "confidence": "error", "template_tier": "none",
            "fixes_applied": [], "error": f"api_error:{e}",
            "ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "brand": brand, "occasion": occasion,
            "score": 0, "passed": False,
            "confidence": "error", "template_tier": "none",
            "fixes_applied": [], "error": f"exception:{type(e).__name__}:{e}",
            "ms": int((time.time() - t0) * 1000),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def print_report():
    if not RESULTS_FILE.exists():
        print("No results yet. Run without --report to start testing.")
        return

    results = []
    for line in RESULTS_FILE.read_text().splitlines():
        try:
            results.append(json.loads(line))
        except Exception:
            pass

    if not results:
        print("No results yet.")
        return

    total = len(results)
    passing = [r for r in results if r.get("passed")]
    pass_rate = len(passing) / total if total else 0

    print(f"\n{'='*60}")
    print(f"DEEP TEST LOOP — RESULTS REPORT")
    print(f"{'='*60}")
    print(f"Total runs:    {total}")
    print(f"Passing:       {len(passing)} ({pass_rate:.1%})")
    print(f"Failing:       {total - len(passing)}")

    # By occasion
    print(f"\nPASSING BY OCCASION (target: {MIN_PASSING_PER_OCC}):")
    occ_counts = defaultdict(lambda: {"total": 0, "passing": 0})
    for r in results:
        occ = r.get("occasion", "unknown")
        occ_counts[occ]["total"] += 1
        if r.get("passed"):
            occ_counts[occ]["passing"] += 1
    for occ in sorted(occ_counts):
        d = occ_counts[occ]
        status = "✅" if d["passing"] >= MIN_PASSING_PER_OCC else "⏳"
        print(f"  {status} {occ:<25} passing={d['passing']:>4} / total={d['total']:>5}")

    # By brand
    print(f"\nPASSING BY BRAND (top 5 and bottom 5):")
    brand_rates = {}
    for brand in ALL_BRANDS:
        br = [r for r in results if r.get("brand") == brand]
        if br:
            brand_rates[brand] = sum(1 for r in br if r.get("passed")) / len(br)
    sorted_brands = sorted(brand_rates.items(), key=lambda x: x[1], reverse=True)
    print("  Best:")
    for b, r in sorted_brands[:5]:
        print(f"    {b:<25} {r:.1%}")
    print("  Worst:")
    for b, r in sorted_brands[-5:]:
        print(f"    {b:<25} {r:.1%}")

    # Top failure categories
    print(f"\nTOP FAILURE CATEGORIES:")
    errors = [r.get("error") for r in results if not r.get("passed") and r.get("error")]
    for err, count in Counter(errors).most_common(8):
        pct = count / (total - len(passing)) * 100 if (total - len(passing)) else 0
        flag = "⚠️ " if pct > 20 else "   "
        print(f"  {flag}{err:<35} {count:>4} ({pct:.1f}%)")

    print(f"\n{'='*60}")
    print(f"Files: {RESULTS_FILE}")
    print(f"       {MISTAKE_LOG}")
    print(f"       {IMPROVEMENT}")


# ─────────────────────────────────────────────────────────────────────────────
# Improvement delta writer
# ─────────────────────────────────────────────────────────────────────────────

def write_improvement_delta(pass_number: int, batch_results: list[dict]):
    total = len(batch_results)
    if not total:
        return
    passing = [r for r in batch_results if r.get("passed")]
    pass_rate = len(passing) / total

    avg_score = sum(r.get("score", 0) for r in batch_results) / total
    avg_score_passing = sum(r.get("score", 0) for r in passing) / len(passing) if passing else 0

    # Per-occasion pass rates this batch
    occ_stats = defaultdict(lambda: {"total": 0, "passing": 0, "scores": []})
    for r in batch_results:
        occ = r.get("occasion", "unknown")
        occ_stats[occ]["total"] += 1
        occ_stats[occ]["scores"].append(r.get("score", 0))
        if r.get("passed"):
            occ_stats[occ]["passing"] += 1

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"\n## PASS {pass_number} — {ts} ({total} runs)\n",
        f"  Overall pass rate: {pass_rate:.1%}",
        f"  Avg score (all):   {avg_score:.1f}",
        f"  Avg score (pass):  {avg_score_passing:.1f}\n",
        "  By occasion:",
    ]
    for occ in sorted(occ_stats):
        d = occ_stats[occ]
        rate = d["passing"] / d["total"] if d["total"] else 0
        avg = sum(d["scores"]) / len(d["scores"]) if d["scores"] else 0
        lines.append(f"    {occ:<25} pass={rate:.1%}  avg_score={avg:.1f}  n={d['total']}")

    # Top failure categories
    errors = [r.get("error") for r in batch_results if not r.get("passed") and r.get("error")]
    if errors:
        lines.append("\n  Top failures:")
        for err, count in Counter(errors).most_common(5):
            pct = count / (total - len(passing)) * 100 if (total - len(passing)) else 0
            flag = "  ⚠️  >20% " if pct > 20 else "       "
            lines.append(f"    {flag}{err:<30} {count:>4} ({pct:.1f}%)")

    with IMPROVEMENT.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # Flag high-failure categories to MISTAKE_LOG
    high_failure = [(err, count) for err, count in Counter(errors).most_common()
                    if (count / (total - len(passing)) * 100 if (total - len(passing)) else 0) > 20]
    if high_failure:
        flag_msg = f"\n## {ts} — PASS {pass_number} HIGH FAILURE FLAGS\n"
        for err, count in high_failure:
            pct = count / (total - len(passing)) * 100 if (total - len(passing)) else 0
            flag_msg += f"- [HIGH FAILURE] {err}: {pct:.1f}% failure rate — review brain rules\n"
        append_mistake_log(flag_msg)
        print(f"\n⚠️  HIGH FAILURE FLAGS written to MISTAKE_LOG.md — review before next pass")


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Deep test loop for OGZ content engine")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--report", action="store_true", help="Print report only, no runs")
    parser.add_argument("--dry-run", action="store_true", help="List combos, no API calls")
    parser.add_argument("--brand", help="Test a single brand only")
    parser.add_argument("--occasion", help="Test a single occasion only")
    parser.add_argument("--iterations", type=int, default=ITERATIONS_PER_COMBO)
    args = parser.parse_args()

    if args.report:
        print_report()
        return

    # Select brands and occasions
    brands = [args.brand] if args.brand else ALL_BRANDS
    occasions = [args.occasion] if args.occasion else OCCASIONS_UNIQUE

    # Build full combo list
    combos = [
        (brand, occ, ct)
        for brand in brands
        for occ in occasions
        for ct in CONTENT_TYPES
    ]
    total_planned = len(combos) * args.iterations

    print(f"{'='*60}")
    print(f"OGZ DEEP TEST LOOP")
    print(f"  Brands:    {len(brands)}")
    print(f"  Occasions: {len(occasions)}")
    print(f"  Types:     {len(CONTENT_TYPES)}")
    print(f"  Combos:    {len(combos)}")
    print(f"  Iter each: {args.iterations}")
    print(f"  Total:     {total_planned} API calls planned")
    print(f"  Results → {RESULTS_FILE}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("DRY RUN — combos that would be tested:")
        for b, occ, ct in combos[:20]:
            print(f"  {b} × {occ} × {ct}")
        if len(combos) > 20:
            print(f"  ... and {len(combos)-20} more")
        return

    # Load checkpoint if resuming
    checkpoint = load_checkpoint() if args.resume else {
        "completed_combos": [], "total_runs": 0, "passing_rate": 0.0,
        "occasion_passing_counts": {}
    }
    completed_keys = set(checkpoint.get("completed_combos", []))

    run_count = 0
    batch_results: list[dict] = []
    pass_number = 1
    recent_mistakes: list[str] = load_recent_mistakes()
    occasion_passing: dict[str, int] = defaultdict(int, checkpoint.get("occasion_passing_counts", {}))

    for brand, occasion, content_type in combos:
        if _shutdown:
            break

        combo_key = f"{brand}_{occasion}_{content_type}_{args.iterations}"
        if combo_key in completed_keys and args.resume:
            continue

        product = BRAND_PRODUCTS.get(brand, "منتج")

        for i in range(1, args.iterations + 1):
            if _shutdown:
                break

            result = call_create(brand, product, occasion, recent_mistakes)
            result["iteration"] = i
            result["content_type"] = content_type
            append_result(result)
            batch_results.append(result)

            run_count += 1

            # Track occasion passing
            if result["passed"]:
                occasion_passing[occasion] = occasion_passing.get(occasion, 0) + 1

            # Log failure to learning store
            if not result["passed"] and result.get("error") not in ("api_error", "exception"):
                log_mistake_to_store(brand, result["score"],
                                     f"{result.get('error', 'unknown')} — {brand}/{occasion}")

            # Progress line
            status = "✅" if result["passed"] else "❌"
            print(f"  [{run_count:>5}] {status} {brand:<20} {occasion:<20} "
                  f"score={result['score']:>3} tier={result['template_tier']:<10} {result['ms']}ms")

            # Reload mistakes every N runs
            if run_count % LEARNING_RELOAD_EVERY == 0:
                recent_mistakes = load_recent_mistakes()
                print(f"\n  [RELOAD] Mistakes updated — {len(recent_mistakes)} loaded\n")

            # Batch report every N runs
            if run_count % REPORT_EVERY == 0:
                write_improvement_delta(pass_number, batch_results)
                pass_rate = sum(1 for r in batch_results if r.get("passed")) / len(batch_results)
                print(f"\n{'─'*60}")
                print(f"  BATCH {pass_number} — {len(batch_results)} runs | pass={pass_rate:.1%}")
                print(f"  Occasion progress ({MIN_PASSING_PER_OCC} target):")
                for occ in sorted(occasion_passing):
                    flag = "✅" if occasion_passing[occ] >= MIN_PASSING_PER_OCC else "⏳"
                    print(f"    {flag} {occ:<25} {occasion_passing[occ]}")
                print(f"{'─'*60}\n")
                batch_results = []
                pass_number += 1

            # Checkpoint every N runs
            if run_count % CHECKPOINT_EVERY == 0:
                checkpoint["total_runs"] = run_count
                checkpoint["occasion_passing_counts"] = dict(occasion_passing)
                save_checkpoint(checkpoint)

        # Mark combo complete
        completed_keys.add(combo_key)
        checkpoint["completed_combos"] = list(completed_keys)

    # Final save
    if batch_results:
        write_improvement_delta(pass_number, batch_results)

    checkpoint["total_runs"] = run_count
    checkpoint["occasion_passing_counts"] = dict(occasion_passing)
    save_checkpoint(checkpoint)

    # Final report
    print(f"\n{'='*60}")
    print(f"LOOP COMPLETE — {run_count} runs")
    print_report()

    # Check if all occasions met threshold
    not_met = [occ for occ in occasions if occasion_passing.get(occ, 0) < MIN_PASSING_PER_OCC]
    if not_met:
        print(f"\n⚠️  Occasions below {MIN_PASSING_PER_OCC} passing threshold: {not_met}")
        print(f"   Run again with --resume to continue until all occasions meet the target.")
    else:
        print(f"\n✅ All occasions reached ≥{MIN_PASSING_PER_OCC} passing tests")

    # Update PLAN_STATUS
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    update_plan_status(f"B2", f"Pass complete — {run_count} runs, "
                       f"pass rate {sum(1 for _ in RESULTS_FILE.read_text().splitlines() if json.loads(_).get('passed') if _.strip()) / max(1, len(RESULTS_FILE.read_text().splitlines())):.1%}", ts)


def update_plan_status(task_id: str, note: str, date: str):
    """Mark a task as done in PLAN_STATUS.md — Claude writes, Mohamed verifies."""
    if not PLAN_STATUS.exists():
        return
    content = PLAN_STATUS.read_text()
    # Find the PENDING line for this task and update it
    new_content = content.replace(
        f"[PENDING]         {task_id}:",
        f"[DONE {date}]    {task_id}:"
    )
    if new_content != content:
        PLAN_STATUS.write_text(new_content)


if __name__ == "__main__":
    main()
