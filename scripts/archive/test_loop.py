#!/usr/bin/env python3
"""
test_loop.py — Run the brain on a real scenario and capture learnings.

The loop:
  1. GENERATE — brain produces a brief + score + captions
  2. REVIEW — human grades the output (1-5)
  3. LEARN — store the review, compare prediction vs judgment
  4. IMPROVE — if score is low, analyze why and log improvement

Usage:
  python3 scripts/test_loop.py --sector f_and_b --occasion ramadan --brand AlBaik
  python3 scripts/test_loop.py --sector beauty_personal_care --brand NiceOne
  python3 scripts/test_loop.py --review          # review past runs
  python3 scripts/test_loop.py --report          # learning report
"""
import json, argparse, os, sys, urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
RUNS_DIR = BASE / "logs" / "test_runs"
RUNS_DIR.mkdir(exist_ok=True)
API = "http://localhost:4100"


def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{API}{path}", data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def run_test(sector, occasion, brand, content_type="carousel_slide"):
    """Generate a full brain output for a scenario."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'═' * 60}")
    print(f"  TEST RUN: {brand} | {sector} | {occasion}")
    print(f"  Run ID: {run_id}")
    print(f"{'═' * 60}")

    results = {"run_id": run_id, "sector": sector, "occasion": occasion,
               "brand": brand, "content_type": content_type,
               "timestamp": datetime.now().isoformat()}

    # 1. Score
    print("\n── 1. SCORE")
    patterns = []
    try:
        rules = api("GET", f"/api/intelligence/rules/{sector}")
        patterns = [p["pattern"] for p in rules.get("must_use", [])[:3]]
    except:
        pass

    score = api("POST", "/api/score", {
        "sector": sector, "content_type": content_type,
        "patterns": patterns, "occasion": occasion,
    })
    results["score"] = score
    ml = score.get("ml_score", {})
    print(f"  Score: {score['score']}/100 | ML: {ml.get('high_probability', 'N/A')}%")
    print(f"  {score['interpretation']}")
    print(f"  Patterns used: {patterns}")

    # 2. Brief
    print("\n── 2. DATA-DRIVEN BRIEF")
    brief = api("POST", "/api/brief", {
        "sector": sector, "occasion": occasion, "count": 2,
    })
    results["brief"] = brief
    for b in brief.get("briefs", []):
        print(f"  {b['content_type']} + {b['pattern']} = {b['engagement_rate']}%")
        print(f"    Visual: {b['visual_direction']['lighting']} + {b['visual_direction']['setting']}")

    # 3. AI Brief
    print("\n── 3. AI CREATIVE BRIEF")
    try:
        ai_brief = api("POST", "/api/brief/ai", {
            "sector": sector, "brand_name": brand,
            "occasion": occasion, "content_type": content_type,
        })
        results["ai_brief"] = ai_brief["brief"]
        lines = ai_brief["brief"].split("\n")
        for line in lines[:15]:
            if line.strip():
                print(f"  {line.strip()[:80]}")
        if len(lines) > 15:
            print(f"  ... ({len(lines)} total lines)")
    except Exception as e:
        print(f"  ⚠️ AI Brief failed: {e}")
        results["ai_brief"] = None

    # 4. Captions
    print("\n── 4. ARABIC CAPTIONS")
    try:
        caps = api("POST", "/api/caption", {
            "sector": sector, "pattern": patterns[0] if patterns else "product_hero",
            "occasion": occasion, "tone": "inviting", "count": 3,
        })
        results["captions"] = caps["captions"]
        for c in caps["captions"]:
            print(f"  {c[:80]}")
    except Exception as e:
        print(f"  ⚠️ Captions failed: {e}")
        results["captions"] = []

    # 5. Calendar
    print("\n── 5. CONTENT CALENDAR (next 4 posts)")
    cal = api("POST", "/api/calendar", {"sector": sector, "posts_per_week": 3})
    results["calendar"] = cal["calendar"][:4]
    for e in cal["calendar"][:4]:
        print(f"  {e['date']} ({e['day_of_week'][:3]}): {e['content_type']} + {e['pattern']}")

    # 6. Intelligence context
    print("\n── 6. BRAIN CONTEXT (what the agent sees)")
    ctx = api("POST", "/api/intelligence/context", {
        "sector": sector, "occasion": occasion, "agent_role": "ceo",
    })
    results["context_tokens"] = ctx["token_count"]
    print(f"  {ctx['token_count']} tokens | {ctx['obs_backing']} obs backing")

    # Save run
    run_path = RUNS_DIR / f"run_{run_id}.json"
    run_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✅ Run saved: {run_path}")

    # Ask for review
    print(f"\n{'─' * 60}")
    print("  REVIEW THIS OUTPUT")
    print(f"{'─' * 60}")
    print("  Rate each dimension 1-5 (5=excellent, 1=wrong):")
    print("  Or press Enter to skip review for now.")
    print()

    try:
        scores_input = input("  Score relevance (1-5): ").strip()
        if scores_input:
            review = {
                "score_relevance": int(scores_input),
                "brief_quality": int(input("  Brief quality (1-5): ").strip() or "0"),
                "caption_quality": int(input("  Caption quality (1-5): ").strip() or "0"),
                "cultural_fit": int(input("  Cultural fit (1-5): ").strip() or "0"),
                "would_use": input("  Would you use this brief? (y/n): ").strip().lower() == "y",
                "notes": input("  Notes (what's wrong/right): ").strip(),
                "reviewed_at": datetime.now().isoformat(),
            }
            results["review"] = review
            run_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

            avg = sum(v for k, v in review.items() if isinstance(v, int) and v > 0) / max(1, sum(1 for k, v in review.items() if isinstance(v, int) and v > 0))
            print(f"\n  Average score: {avg:.1f}/5")

            if avg < 3:
                print("  ⚠️ Below threshold — logging for improvement")
                _log_improvement(results)
            else:
                print("  ✅ Acceptable — logging success")

            # Log to learning system
            sys.path.insert(0, str(BASE / "scripts"))
            from learning_system import log_prediction, log_time
            log_prediction(
                f"Brain score {score['score']}/100 for {brand} {sector} {occasion}",
                predicted_value=score["score"],
                confidence_pct=70
            )
    except (EOFError, KeyboardInterrupt):
        print("\n  Review skipped — run saved for later review")

    return results


def _log_improvement(results):
    """Log what needs improving based on a bad review."""
    imp_path = RUNS_DIR / "improvements.jsonl"
    entry = {
        "run_id": results["run_id"],
        "sector": results["sector"],
        "occasion": results["occasion"],
        "brain_score": results["score"]["score"],
        "review_avg": sum(v for k, v in results.get("review", {}).items() if isinstance(v, int) and v > 0) / max(1, sum(1 for k, v in results.get("review", {}).items() if isinstance(v, int) and v > 0)),
        "notes": results.get("review", {}).get("notes", ""),
        "timestamp": datetime.now().isoformat(),
    }
    with open(imp_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def review_past_runs():
    """Show all runs and their review status."""
    runs = sorted(RUNS_DIR.glob("run_*.json"), reverse=True)
    if not runs:
        print("No test runs yet. Run: python3 scripts/test_loop.py --sector f_and_b --brand AlBaik")
        return

    print(f"\n{'═' * 60}")
    print(f"  TEST RUNS ({len(runs)} total)")
    print(f"{'═' * 60}")

    reviewed = 0
    unreviewed = 0
    total_score = 0

    for rp in runs[:20]:
        r = json.loads(rp.read_text())
        rev = r.get("review")
        brain_score = r.get("score", {}).get("score", "?")
        status = "✅ reviewed" if rev else "⏳ pending"
        if rev:
            reviewed += 1
            avg = sum(v for k, v in rev.items() if isinstance(v, int) and v > 0) / max(1, sum(1 for k, v in rev.items() if isinstance(v, int) and v > 0))
            total_score += avg
            print(f"  {r['run_id']} | {r['brand']:12} | {r['sector']:20} | brain={brain_score} | review={avg:.1f}/5 | {status}")
        else:
            unreviewed += 1
            print(f"  {r['run_id']} | {r['brand']:12} | {r['sector']:20} | brain={brain_score} | {'—':>13} | {status}")

    if reviewed > 0:
        print(f"\n  Average review score: {total_score/reviewed:.1f}/5 across {reviewed} reviewed runs")
    print(f"  {unreviewed} runs pending review")


def learning_report():
    """Show what we've learned from all test runs."""
    runs = sorted(RUNS_DIR.glob("run_*.json"))
    if not runs:
        print("No test runs yet.")
        return

    reviewed_runs = []
    for rp in runs:
        r = json.loads(rp.read_text())
        if r.get("review"):
            reviewed_runs.append(r)

    if not reviewed_runs:
        print("No reviewed runs yet. Run tests and review them first.")
        return

    print(f"\n{'═' * 60}")
    print(f"  LEARNING REPORT ({len(reviewed_runs)} reviewed runs)")
    print(f"{'═' * 60}")

    # Brain accuracy: does high brain score correlate with high review?
    brain_scores = [r["score"]["score"] for r in reviewed_runs]
    review_scores = []
    for r in reviewed_runs:
        rev = r["review"]
        avg = sum(v for k, v in rev.items() if isinstance(v, int) and v > 0) / max(1, sum(1 for k, v in rev.items() if isinstance(v, int) and v > 0))
        review_scores.append(avg)

    print(f"\n  Brain avg score: {sum(brain_scores)/len(brain_scores):.0f}/100")
    print(f"  Review avg score: {sum(review_scores)/len(review_scores):.1f}/5")

    # Correlation
    high_brain = [r for bs, rs in zip(brain_scores, review_scores) if bs >= 60 for r in [rs]]
    low_brain = [r for bs, rs in zip(brain_scores, review_scores) if bs < 60 for r in [rs]]
    if high_brain:
        print(f"  High brain score (≥60): avg review = {sum(high_brain)/len(high_brain):.1f}/5")
    if low_brain:
        print(f"  Low brain score (<60): avg review = {sum(low_brain)/len(low_brain):.1f}/5")

    # What sectors score best/worst?
    sector_scores = {}
    for r, rev_score in zip(reviewed_runs, review_scores):
        s = r["sector"]
        sector_scores.setdefault(s, []).append(rev_score)
    print(f"\n  By sector:")
    for s in sorted(sector_scores, key=lambda x: -sum(sector_scores[x])/len(sector_scores[x])):
        avg = sum(sector_scores[s]) / len(sector_scores[s])
        print(f"    {s}: {avg:.1f}/5 ({len(sector_scores[s])} runs)")

    # Improvements needed
    imp_path = RUNS_DIR / "improvements.jsonl"
    if imp_path.exists():
        imps = [json.loads(l) for l in imp_path.read_text().strip().split("\n") if l]
        print(f"\n  Improvements logged: {len(imps)}")
        for imp in imps[-5:]:
            print(f"    [{imp['sector']}] brain={imp['brain_score']} review={imp['review_avg']:.1f} — {imp['notes'][:60]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", default="f_and_b")
    parser.add_argument("--occasion", default="evergreen")
    parser.add_argument("--brand", default="TestBrand")
    parser.add_argument("--content-type", default="carousel_slide")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    if args.review:
        review_past_runs()
    elif args.report:
        learning_report()
    else:
        run_test(args.sector, args.occasion, args.brand, args.content_type)


if __name__ == "__main__":
    main()
