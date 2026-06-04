#!/usr/bin/env python3
"""
overnight_improver.py — Autonomous improvement loop.

Runs for N hours, each cycle does one improvement task:
  1. Test creative pipeline on every sector × occasion combo
  2. Deepen WHY analysis with GPT for each top pattern
  3. Fix chain selector to match intelligence visual recommendations
  4. Generate sector comparison reports
  5. Build cross-sector transfer recommendations
  6. Rebuild intelligence layer with new insights
  7. Regenerate weekly report
  8. Run full verification suite

Usage:
  python3 scripts/overnight_improver.py --hours 10
  python3 scripts/overnight_improver.py --hours 1 --task deep_why  # one specific task
"""
import json, os, sys, time, subprocess, glob
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent.parent
LOGS = BASE / "logs"
IMPROVE_LOG = LOGS / "improvement_runs.jsonl"

def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if not os.environ.get(k):
                    os.environ[k] = v
_load_env()

def log_improvement(task, result, duration_s):
    entry = {
        "task": task, "result": result, "duration_s": round(duration_s),
        "timestamp": datetime.now().isoformat(),
    }
    with open(IMPROVE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  Logged: {task} ({duration_s:.0f}s)")


def run(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(BASE))
    return r.returncode, r.stdout, r.stderr


# ═══════════════════════════════════════════════════════════
# TASK 1: Test all sector × occasion combos
# ═══════════════════════════════════════════════════════════
def task_test_all_combos():
    """Score every sector × occasion combo and find weak spots."""
    import urllib.request
    API = "http://localhost:4100"

    sectors = ["f_and_b", "beauty_personal_care", "retail_lifestyle", "fashion", "real_estate", "healthcare_wellness"]
    occasions = ["evergreen", "ramadan", "founding_day", "national_day", "eid_al_fitr", "jeddah_season", "riyadh_season"]

    results = []
    for sector in sectors:
        for occasion in occasions:
            try:
                data = json.dumps({"sector": sector, "content_type": "carousel_slide",
                    "patterns": ["product_hero"], "occasion": occasion}).encode()
                req = urllib.request.Request(f"{API}/api/score", data=data,
                    headers={"Content-Type": "application/json"}, method="POST")
                resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
                score = resp.get("score", 0)
                results.append({"sector": sector, "occasion": occasion, "score": score})
            except:
                results.append({"sector": sector, "occasion": occasion, "score": -1})

    # Save matrix
    out_path = LOGS / "score_matrix.json"
    out_path.write_text(json.dumps({"matrix": results, "generated_at": datetime.now().isoformat()}, indent=2))

    # Find weak spots
    weak = [r for r in results if 0 <= r["score"] < 30]
    strong = [r for r in results if r["score"] >= 60]

    return f"Tested {len(results)} combos. Strong (≥60): {len(strong)}. Weak (<30): {len(weak)}. Saved to score_matrix.json"


# ═══════════════════════════════════════════════════════════
# TASK 2: Deep WHY analysis with GPT
# ═══════════════════════════════════════════════════════════
def task_deep_why():
    """Use GPT to analyze WHY each top pattern works."""
    import openai
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Skipped — no OPENAI_API_KEY"

    intel = json.loads((BASE / "11_who_to_learn_from" / "intelligence_layer.json").read_text())
    universal = intel.get("universal_rules", [])

    client = openai.OpenAI(api_key=api_key)
    deep_whys = []

    for rule in universal[:5]:
        pattern = rule["pattern"]
        engagement = rule["engagement"]

        prompt = f"""Analyze WHY the Instagram content pattern "{pattern.replace('_',' ')}" consistently gets {engagement}% high engagement with Saudi audiences.

Consider:
- Cultural psychology (Saudi values, tribal honor, community, hospitality)
- Visual psychology (what the brain responds to)
- Social media behavior (what triggers likes/comments/saves)
- Emotional resonance (what emotion does this tap?)
- Saudi-specific context (Vision 2030, cultural shift, generation gap)

Give me 3 specific reasons, each 1-2 sentences. Be concrete, not generic."""

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            analysis = resp.choices[0].message.content
            deep_whys.append({
                "pattern": pattern, "engagement": engagement,
                "why_analysis": analysis,
            })
        except Exception as e:
            deep_whys.append({"pattern": pattern, "error": str(e)})

    out_path = LOGS / "deep_why_analysis.json"
    out_path.write_text(json.dumps(deep_whys, indent=2, ensure_ascii=False))
    return f"Analyzed {len(deep_whys)} patterns. Saved to deep_why_analysis.json"


# ═══════════════════════════════════════════════════════════
# TASK 3: Generate sector comparison report
# ═══════════════════════════════════════════════════════════
def task_sector_comparison():
    """Generate cross-sector intelligence comparison."""
    intel = json.loads((BASE / "11_who_to_learn_from" / "intelligence_layer.json").read_text())

    report = {"sectors": {}, "generated_at": datetime.now().isoformat()}
    for sector, pb in intel.get("sector_playbooks", {}).items():
        report["sectors"][sector] = {
            "obs": pb.get("obs_count", 0),
            "must_use_count": len(pb.get("must_use", [])),
            "never_use_count": len(pb.get("never_use", [])),
            "formula_count": len(pb.get("winning_formulas", [])),
            "visual_dna_count": len(pb.get("visual_dna", [])),
            "top_pattern": pb["must_use"][0]["pattern"] if pb.get("must_use") else "none",
            "top_engagement": pb["must_use"][0]["engagement"] if pb.get("must_use") else 0,
            "strength": "strong" if len(pb.get("must_use", [])) >= 10 else "moderate" if pb.get("must_use") else "weak",
        }

    # Rank sectors
    ranked = sorted(report["sectors"].items(), key=lambda x: x[1]["must_use_count"], reverse=True)
    report["ranking"] = [{"sector": s, "intelligence_depth": d["must_use_count"]} for s, d in ranked]

    out_path = LOGS / "sector_comparison.json"
    out_path.write_text(json.dumps(report, indent=2))
    return f"Compared {len(report['sectors'])} sectors. Strongest: {ranked[0][0]}. Weakest: {ranked[-1][0]}"


# ═══════════════════════════════════════════════════════════
# TASK 4: Rebuild analytics
# ═══════════════════════════════════════════════════════════
def task_rebuild_analytics():
    """Run all 92 analytics scripts."""
    rc, out, err = run([sys.executable, "scripts/run_all_analytics.py", "--fast"], timeout=120)
    return f"Analytics rebuild: rc={rc}. {out.strip().split(chr(10))[-1] if out else err[:100]}"


# ═══════════════════════════════════════════════════════════
# TASK 5: Generate weekly report
# ═══════════════════════════════════════════════════════════
def task_weekly_report():
    """Generate fresh intelligence report."""
    rc, out, err = run([sys.executable, "scripts/generate_weekly_report.py"], timeout=30)
    return f"Report: {out.strip() if out else err[:100]}"


# ═══════════════════════════════════════════════════════════
# TASK 6: Run full verification
# ═══════════════════════════════════════════════════════════
def task_verify():
    """Run all verification scripts."""
    rc1, out1, _ = run([sys.executable, "scripts/validate_all.py"], timeout=120)
    rc2, out2, _ = run([sys.executable, "scripts/guard_data_quality.py", "--quick"], timeout=120)
    rc3, out3, _ = run([sys.executable, "scripts/verify_ship_ready.py", "--quick"], timeout=120)

    v1 = "PASS" if rc1 == 0 else "FAIL"
    v2 = "PASS" if rc2 == 0 else "FAIL"
    v3 = "PASS" if rc3 == 0 else "FAIL"
    return f"Validation: {v1} | Guard: {v2} | Ship-ready: {v3}"


# ═══════════════════════════════════════════════════════════
# TASK 7: Creative pipeline tests across sectors
# ═══════════════════════════════════════════════════════════
def task_creative_tests():
    """Run creative pipeline for each sector and save outputs."""
    tests = [
        {"brand": "AlBaik", "sector": "f_and_b", "occasion": "ramadan", "product": "chicken meal"},
        {"brand": "NiceOne", "sector": "beauty_personal_care", "occasion": "evergreen", "product": "skincare set"},
        {"brand": "MaxFashion", "sector": "fashion", "occasion": "national_day", "product": "abaya collection"},
        {"brand": "ROSHN", "sector": "real_estate", "occasion": "founding_day", "product": "luxury villa"},
        {"brand": "FitnessTime", "sector": "healthcare_wellness", "occasion": "evergreen", "product": "gym membership"},
    ]

    results = []
    for t in tests:
        try:
            rc, out, err = run([
                sys.executable, "scripts/creative_pipeline.py",
                "--brand", t["brand"], "--sector", t["sector"],
                "--occasion", t["occasion"], "--product", t["product"],
            ], timeout=120)
            results.append({"brand": t["brand"], "status": "ok" if rc == 0 else "error"})
        except Exception as e:
            results.append({"brand": t["brand"], "status": f"error: {e}"})

    ok = sum(1 for r in results if r["status"] == "ok")
    return f"Creative tests: {ok}/{len(results)} passed. {[r['brand'] for r in results if r['status'] != 'ok']}"


# ═══════════════════════════════════════════════════════════
# TASK 8: Learning system update
# ═══════════════════════════════════════════════════════════
def task_learning_update():
    """Update learning system analytics."""
    rc, out, err = run([sys.executable, "scripts/learning_system.py", "--all"], timeout=60)
    return f"Learning: {out.strip().split(chr(10))[-1] if out else err[:100]}"


# ═══════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════

TASKS = [
    ("verify", task_verify),
    ("test_all_combos", task_test_all_combos),
    ("deep_why", task_deep_why),
    ("sector_comparison", task_sector_comparison),
    ("creative_tests", task_creative_tests),
    ("rebuild_analytics", task_rebuild_analytics),
    ("weekly_report", task_weekly_report),
    ("learning_update", task_learning_update),
]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=10)
    parser.add_argument("--task", default=None, help="Run one specific task")
    args = parser.parse_args()

    if args.task:
        task_fn = dict(TASKS).get(args.task)
        if task_fn:
            start = time.time()
            result = task_fn()
            log_improvement(args.task, result, time.time() - start)
            print(f"\n✅ {result}")
        else:
            print(f"Unknown task: {args.task}. Available: {[t[0] for t in TASKS]}")
        return

    end_time = datetime.now() + timedelta(hours=args.hours)
    cycle = 0

    print(f"{'═' * 60}")
    print(f"  OVERNIGHT IMPROVER — running for {args.hours} hours")
    print(f"  {len(TASKS)} tasks per cycle | End time: {end_time.strftime('%H:%M')}")
    print(f"{'═' * 60}")

    while datetime.now() < end_time:
        cycle += 1
        print(f"\n{'─' * 40}")
        print(f"  Cycle {cycle} — {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'─' * 40}")

        for task_name, task_fn in TASKS:
            if datetime.now() >= end_time:
                break
            print(f"\n  [{task_name}]")
            start = time.time()
            try:
                result = task_fn()
                duration = time.time() - start
                log_improvement(task_name, result, duration)
                print(f"  ✅ {result} ({duration:.0f}s)")
            except Exception as e:
                duration = time.time() - start
                log_improvement(task_name, f"ERROR: {e}", duration)
                print(f"  ❌ {e} ({duration:.0f}s)")

        # Wait 30 min between cycles
        wait_until = datetime.now() + timedelta(minutes=30)
        if wait_until < end_time:
            wait_secs = (wait_until - datetime.now()).total_seconds()
            print(f"\n  Sleeping {wait_secs/60:.0f} min until next cycle...")
            time.sleep(wait_secs)

    print(f"\n{'═' * 60}")
    print(f"  DONE — {cycle} cycles completed")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
