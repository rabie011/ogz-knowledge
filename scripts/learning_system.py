#!/usr/bin/env python3
"""
learning_system.py — OGZ Knowledge Learning Framework

6 learning loops that run automatically or on-demand:
  1. Decision Journal — log decisions, revisit outcomes
  2. Success Log — capture what worked and why
  3. Daemon Analytics — mine operational data from enricher.log
  4. User Patterns — track how Mohamed works for better collaboration
  5. Time Tracking — estimate vs actual for calibration
  6. Prediction Calibration — compare forecasts to reality

Usage:
  python3 scripts/learning_system.py --all              # run all analytics
  python3 scripts/learning_system.py --daemon-analytics  # mine daemon log
  python3 scripts/learning_system.py --calibration       # prediction review
  python3 scripts/learning_system.py --report            # print summary

Data lives in: logs/learning/
"""
import json, os, sys, re, glob
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(__file__).parent.parent
LEARNING_DIR = BASE / "logs" / "learning"
LEARNING_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
# 1. DECISION JOURNAL
# ═══════════════════════════════════════════════════════════

def log_decision(title: str, options: list, chosen: str, reasoning: str,
                 confidence: int = 50, predicted_outcome: str = "",
                 revisit_days: int = 30):
    """Log a decision for future review."""
    journal_path = LEARNING_DIR / "decision_journal.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "options": options,
        "chosen": chosen,
        "reasoning": reasoning,
        "confidence_pct": confidence,
        "predicted_outcome": predicted_outcome,
        "revisit_after": (datetime.now() + timedelta(days=revisit_days)).isoformat(),
        "actual_outcome": None,
        "outcome_recorded_at": None,
    }
    with open(journal_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def review_decisions():
    """Find decisions due for review (past revisit_after, no outcome recorded)."""
    journal_path = LEARNING_DIR / "decision_journal.jsonl"
    if not journal_path.exists():
        return []
    due = []
    now = datetime.now().isoformat()
    for line in journal_path.read_text().strip().split("\n"):
        if not line:
            continue
        d = json.loads(line)
        if d.get("actual_outcome") is None and d.get("revisit_after", "") <= now:
            due.append(d)
    return due


# ═══════════════════════════════════════════════════════════
# 2. SUCCESS LOG
# ═══════════════════════════════════════════════════════════

def log_success(what: str, why_it_worked: str, repeat_when: str):
    """Log something that worked well — for replication, not just bug avoidance."""
    success_path = LEARNING_DIR / "success_log.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "what": what,
        "why_it_worked": why_it_worked,
        "repeat_when": repeat_when,
    }
    with open(success_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


# ═══════════════════════════════════════════════════════════
# 3. DAEMON ANALYTICS — mine enricher.log
# ═══════════════════════════════════════════════════════════

def analyze_daemon_log():
    """Mine enricher.log for operational patterns."""
    log_path = BASE / "logs" / "enricher.log"
    if not log_path.exists():
        return {}

    lines = log_path.read_text().split("\n")

    cycles = []
    current_cycle = None
    cycle_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*CYCLE (\d+)")
    sleep_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Sleeping")
    obs_re = re.compile(r"@(\w[\w.]*): (\d+) obs written")
    timeout_re = re.compile(r"@(\w[\w.]*).*(timeout|timed out)", re.I)
    zero_re = re.compile(r"@(\w[\w.]*): 0 obs")
    validation_fail_re = re.compile(r"Validation FAILED|Validation failed")
    analytics_re = re.compile(r"Rebuilt (\d+) analytics")

    total_cycles = 0
    cycle_durations = []
    account_times = defaultdict(list)
    timeouts = Counter()
    zero_results = Counter()
    validation_fails = 0
    analytics_rebuilds = 0
    errors_by_hour = Counter()

    for line in lines:
        cycle_m = cycle_re.search(line)
        if cycle_m:
            if current_cycle:
                # close previous cycle
                pass
            current_cycle = {
                "start": cycle_m.group(1),
                "num": int(cycle_m.group(2)),
            }
            total_cycles += 1

        sleep_m = sleep_re.search(line)
        if sleep_m and current_cycle:
            start = datetime.strptime(current_cycle["start"], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(sleep_m.group(1), "%Y-%m-%d %H:%M:%S")
            duration = (end - start).total_seconds()
            cycle_durations.append(duration)
            current_cycle = None

        obs_m = obs_re.search(line)
        if obs_m:
            account_times[obs_m.group(1)].append(int(obs_m.group(2)))

        if timeout_re.search(line):
            tm = timeout_re.search(line)
            timeouts[tm.group(1)] += 1
            hour = line[:13]
            errors_by_hour[hour] += 1

        if zero_re.search(line):
            zm = zero_re.search(line)
            zero_results[zm.group(1)] += 1

        if validation_fail_re.search(line):
            validation_fails += 1

        am = analytics_re.search(line)
        if am:
            analytics_rebuilds += 1

    # Compute stats
    avg_cycle = sum(cycle_durations) / len(cycle_durations) if cycle_durations else 0
    p50 = sorted(cycle_durations)[len(cycle_durations) // 2] if cycle_durations else 0
    p95 = sorted(cycle_durations)[int(len(cycle_durations) * 0.95)] if cycle_durations else 0

    report = {
        "total_cycles": total_cycles,
        "avg_cycle_seconds": round(avg_cycle, 1),
        "p50_cycle_seconds": round(p50, 1),
        "p95_cycle_seconds": round(p95, 1),
        "total_timeouts": sum(timeouts.values()),
        "timeout_accounts": dict(timeouts.most_common(10)),
        "total_zero_results": sum(zero_results.values()),
        "zero_result_accounts": dict(zero_results.most_common(10)),
        "validation_failures": validation_fails,
        "analytics_rebuilds": analytics_rebuilds,
        "accounts_extracted": {k: sum(v) for k, v in sorted(account_times.items(), key=lambda x: -sum(x[1]))[:15]},
        "generated_at": datetime.now().isoformat(),
    }

    out_path = LEARNING_DIR / "daemon_analytics.json"
    out_path.write_text(json.dumps(report, indent=2))
    return report


# ═══════════════════════════════════════════════════════════
# 4. USER PATTERNS (Mohamed)
# ═══════════════════════════════════════════════════════════

def analyze_work_patterns():
    """Analyze git commit patterns for work schedule insights."""
    import subprocess

    result = subprocess.run(
        ["git", "log", "--format=%ai", "--since=2026-05-01"],
        capture_output=True, text=True, cwd=BASE
    )

    hours = Counter()
    days = Counter()
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            dt = datetime.fromisoformat(line.strip().replace(" +", "+").split("+")[0])
            hours[dt.hour] += 1
            days[dt.strftime("%A")] += 1
        except:
            pass

    peak_hours = sorted(hours, key=hours.get, reverse=True)[:3]
    peak_days = sorted(days, key=days.get, reverse=True)[:3]

    report = {
        "peak_hours": {str(h): hours[h] for h in peak_hours},
        "peak_days": {d: days[d] for d in peak_days},
        "total_commits": sum(hours.values()),
        "commits_by_hour": {str(h): hours[h] for h in sorted(hours)},
        "commits_by_day": {d: days.get(d, 0) for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]},
        "generated_at": datetime.now().isoformat(),
    }

    out_path = LEARNING_DIR / "work_patterns.json"
    out_path.write_text(json.dumps(report, indent=2))
    return report


# ═══════════════════════════════════════════════════════════
# 5. TIME TRACKING
# ═══════════════════════════════════════════════════════════

def log_time(task: str, estimated_minutes: int, actual_minutes: int, notes: str = ""):
    """Log estimated vs actual time for a task."""
    time_path = LEARNING_DIR / "time_tracking.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "estimated_minutes": estimated_minutes,
        "actual_minutes": actual_minutes,
        "ratio": round(actual_minutes / estimated_minutes, 2) if estimated_minutes > 0 else None,
        "notes": notes,
    }
    with open(time_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def time_calibration_report():
    """Analyze estimation accuracy over time."""
    time_path = LEARNING_DIR / "time_tracking.jsonl"
    if not time_path.exists():
        return {"message": "No time entries yet"}

    entries = []
    for line in time_path.read_text().strip().split("\n"):
        if line:
            entries.append(json.loads(line))

    if not entries:
        return {"message": "No time entries yet"}

    ratios = [e["ratio"] for e in entries if e.get("ratio")]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0
    overestimates = sum(1 for r in ratios if r < 0.8)
    underestimates = sum(1 for r in ratios if r > 1.2)
    accurate = sum(1 for r in ratios if 0.8 <= r <= 1.2)

    return {
        "total_entries": len(entries),
        "avg_actual_to_estimated_ratio": round(avg_ratio, 2),
        "interpretation": (
            f"On average, tasks take {avg_ratio:.1f}x the estimated time. "
            f"Multiply estimates by {avg_ratio:.1f} for better accuracy."
            if avg_ratio > 1.1 else
            f"Estimates are well calibrated (ratio {avg_ratio:.2f})"
        ),
        "overestimates": overestimates,
        "underestimates": underestimates,
        "accurate_within_20pct": accurate,
    }


# ═══════════════════════════════════════════════════════════
# 6. PREDICTION CALIBRATION
# ═══════════════════════════════════════════════════════════

def log_prediction(what: str, predicted_value, confidence_pct: int = 50):
    """Log a prediction for later comparison."""
    pred_path = LEARNING_DIR / "predictions.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "what": what,
        "predicted_value": predicted_value,
        "confidence_pct": confidence_pct,
        "actual_value": None,
        "recorded_at": None,
    }
    with open(pred_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def calibration_report():
    """Compare predictions to actual outcomes."""
    pred_path = LEARNING_DIR / "predictions.jsonl"
    if not pred_path.exists():
        return {"message": "No predictions yet"}

    entries = []
    for line in pred_path.read_text().strip().split("\n"):
        if line:
            entries.append(json.loads(line))

    resolved = [e for e in entries if e.get("actual_value") is not None]
    unresolved = [e for e in entries if e.get("actual_value") is None]

    return {
        "total_predictions": len(entries),
        "resolved": len(resolved),
        "unresolved": len(unresolved),
        "unresolved_items": [{"what": e["what"], "predicted": e["predicted_value"]} for e in unresolved[:10]],
    }


# ═══════════════════════════════════════════════════════════
# MAIN — run analytics and print report
# ═══════════════════════════════════════════════════════════

def print_report():
    """Print a summary of all learning systems."""
    print("=" * 60)
    print("OGZ LEARNING SYSTEM — STATUS REPORT")
    print("=" * 60)

    # Decision journal
    journal_path = LEARNING_DIR / "decision_journal.jsonl"
    if journal_path.exists():
        entries = [json.loads(l) for l in journal_path.read_text().strip().split("\n") if l]
        resolved = sum(1 for e in entries if e.get("actual_outcome"))
        due = review_decisions()
        print(f"\n📋 Decisions: {len(entries)} logged, {resolved} resolved, {len(due)} due for review")
        for d in due[:3]:
            print(f"   ⏰ DUE: {d['title']} (decided {d['timestamp'][:10]})")
    else:
        print("\n📋 Decisions: no journal yet")

    # Success log
    success_path = LEARNING_DIR / "success_log.jsonl"
    if success_path.exists():
        entries = [json.loads(l) for l in success_path.read_text().strip().split("\n") if l]
        print(f"\n✅ Successes: {len(entries)} logged")
        for e in entries[-3:]:
            print(f"   • {e['what']}")
    else:
        print("\n✅ Successes: no entries yet")

    # Daemon analytics
    daemon_path = LEARNING_DIR / "daemon_analytics.json"
    if daemon_path.exists():
        d = json.loads(daemon_path.read_text())
        print(f"\n🤖 Daemon: {d['total_cycles']} cycles | avg {d['avg_cycle_seconds']}s | p95 {d['p95_cycle_seconds']}s")
        print(f"   Timeouts: {d['total_timeouts']} | Zero-results: {d['total_zero_results']} | Val fails: {d['validation_failures']}")
    else:
        print("\n🤖 Daemon: no analytics yet (run --daemon-analytics)")

    # Work patterns
    wp_path = LEARNING_DIR / "work_patterns.json"
    if wp_path.exists():
        wp = json.loads(wp_path.read_text())
        print(f"\n📊 Work patterns: {wp['total_commits']} commits")
        print(f"   Peak hours: {', '.join(f'{h}:00' for h in wp['peak_hours'])}")
        print(f"   Peak days: {', '.join(wp['peak_days'])}")
    else:
        print("\n📊 Work patterns: not analyzed yet")

    # Time tracking
    tc = time_calibration_report()
    if tc.get("total_entries"):
        print(f"\n⏱️  Time calibration: {tc['total_entries']} entries, ratio {tc['avg_actual_to_estimated_ratio']}")
        print(f"   {tc['interpretation']}")
    else:
        print("\n⏱️  Time tracking: no entries yet")

    # Predictions
    pc = calibration_report()
    print(f"\n🔮 Predictions: {pc.get('total_predictions', 0)} total, {pc.get('resolved', 0)} resolved")

    print(f"\n{'=' * 60}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Run all analytics")
    parser.add_argument("--daemon-analytics", action="store_true")
    parser.add_argument("--work-patterns", action="store_true")
    parser.add_argument("--calibration", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    if args.all or args.daemon_analytics:
        print("Mining daemon log...")
        r = analyze_daemon_log()
        print(f"  {r['total_cycles']} cycles analyzed → logs/learning/daemon_analytics.json")

    if args.all or args.work_patterns:
        print("Analyzing work patterns...")
        r = analyze_work_patterns()
        print(f"  {r['total_commits']} commits analyzed → logs/learning/work_patterns.json")

    if args.all or args.calibration:
        print("Calibration report...")
        tc = time_calibration_report()
        print(f"  {json.dumps(tc, indent=2)}")

    if args.report or args.all:
        print_report()

    if not any(vars(args).values()):
        print_report()


if __name__ == "__main__":
    main()
