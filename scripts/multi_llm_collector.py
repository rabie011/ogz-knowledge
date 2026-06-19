#!/usr/bin/env python3
"""
multi_llm_collector.py — Collect 221-brief outputs from GPT-4o and Gemini.
Uses the same V3 XML prompt as humain_collector.py so outputs are comparable.
Results stored in logs/gpt4o_queue.json and logs/gemini_queue.json.

Usage:
  python3 scripts/multi_llm_collector.py --model gpt4o       # collect all 221
  python3 scripts/multi_llm_collector.py --model gemini      # collect all 221
  python3 scripts/multi_llm_collector.py --model all         # both in parallel
  python3 scripts/multi_llm_collector.py --model gpt4o --batch 30   # limit batch
  python3 scripts/multi_llm_collector.py --model gpt4o --dry-run
  python3 scripts/multi_llm_collector.py --model gpt4o --report
  python3 scripts/multi_llm_collector.py --model gpt4o --recollect-bad
"""

import asyncio
import argparse

FORCE_RECOLLECT = False
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
LOG_DIR = BASE / "logs"

# Inject scripts/ into path so we can import from humain_collector
sys.path.insert(0, str(BASE / "scripts"))
from v5_prompt import build_messages_v5
from caption_filter import filter_options
from scorer_v2 import score_v2, pick_best
from humain_collector import (
    build_prompt,
    parse_response,
    _auto_score,
    _diversity_ok,
    ALL_KEYS,
    OCCASION_AR as _OCCASION_AR_BASE,
)

# Missing occasions that the 221-brief matrix adds beyond the original 8
_OCCASION_AR_EXTRA = {
    "back_to_school":    "العودة للمدارس",
    "evergreen":         "عام (دائم)",
    "graduation_season": "موسم التخرج",
    "summer_campaign":   "الصيف",
    "winter_seasonal":   "الشتاء",
}
OCCASION_AR = {**_OCCASION_AR_BASE, **_OCCASION_AR_EXTRA}

QUEUE_FILES = {
    "gpt-4o":  LOG_DIR / "gpt4o_queue.json",
    "gemini":  LOG_DIR / "gemini_queue.json",
    "claude":  LOG_DIR / "claude_queue.json",
}

CONCURRENCY = 4   # parallel API calls per model (keeps under 30k TPM)
MAX_RETRIES = 5   # more retries for rate-limit handling


# ── Queue helpers ──────────────────────────────────────────────────────────────

def _load_queue(model: str) -> dict:
    path = QUEUE_FILES[model]
    if path.exists():
        return json.loads(path.read_text())
    return {"pending": [], "approved": [], "source": model}


def _save_queue(model: str, q: dict):
    path = QUEUE_FILES[model]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(q, ensure_ascii=False, indent=2))


def _collected_keys(q: dict) -> set:
    keys = set()
    for item in q.get("pending", []) + q.get("approved", []):
        keys.add(f"{item.get('brand','')}|{item.get('occasion','')}")
    return keys


# ── GPT-4o client ──────────────────────────────────────────────────────────────

def _load_env() -> dict:
    env = {}
    env_file = Path.home() / ".abraham_env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    return env


_ENV = _load_env()


async def _call_gpt4o(prompt, semaphore: asyncio.Semaphore) -> str:
    from lib.openai_client import make_async_client
    # max_retries=0: this function runs its own bounded retry loop below; the factory's
    # job here is the timeout that was missing (B258) — never a hung socket again.
    client = make_async_client(_ENV.get("OPENAI_API_KEY", ""), max_retries=0)
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=(prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]),
                    temperature=0.9,
                    max_tokens=800,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                msg = str(e)
                wait = min(30, 5 * (attempt + 1)) if ("429" in msg or "rate" in msg.lower()) else 2 ** attempt
                await asyncio.sleep(wait)
    return ""


async def _call_gemini(prompt: str, semaphore: asyncio.Semaphore) -> str:
    from google import genai
    client = genai.Client(api_key=_ENV.get("GOOGLE_AI_STUDIO_KEY", ""))
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                # google.genai uses sync; run in executor
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt,
                        config={
                            "temperature": 0.9,
                            "max_output_tokens": 800,
                        },
                    )
                )
                return resp.text or ""
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    return ""


async def _call_claude(prompt, semaphore: asyncio.Semaphore) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=_ENV.get("ANTHROPIC_API_KEY", ""))
    if isinstance(prompt, list):  # V5 doctrine: messages with system + few-shot pairs
        system = "\n".join(m["content"] for m in prompt if m["role"] == "system")
        msgs = [m for m in prompt if m["role"] != "system"]
        kwargs = {"system": system, "messages": msgs}
    else:
        kwargs = {"messages": [{"role": "user", "content": prompt}]}
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=800,
                    temperature=0.9,
                    **kwargs,
                )
                return resp.content[0].text or ""
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    return ""


_CALLERS = {
    "gpt-4o": _call_gpt4o,
    "gemini": _call_gemini,
    "claude": _call_claude,
}


# ── Core collection ────────────────────────────────────────────────────────────

def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


async def _collect_brief(brief: dict, model: str, semaphore: asyncio.Semaphore) -> dict | None:
    caller = _CALLERS[model]
    # V5 doctrine path: messages w/ DNA few-shot when the brand has DNA v2
    from humain_collector import MAX_CHARS, OCCASION_AR
    _max = MAX_CHARS.get(brief["sector"], 160)
    _occ = OCCASION_AR.get(brief.get("occasion",""), brief.get("occasion",""))
    prompt = build_messages_v5(brief, _occ, _max) or build_prompt(brief)
    _v5 = isinstance(prompt, list)
    _log(f"  → {model}{' [V5]' if _v5 else ''}: {brief['brand']} × {brief['occasion']}")
    try:
        raw = await caller(prompt, semaphore)
    except Exception as e:
        _log(f"  ✗ {brief['brand']} × {brief['occasion']}: {e}")
        return None

    parsed = parse_response(raw)
    # DOCTRINE: bans live here, not in the prompt — filter + one regeneration
    survivors, dropped = filter_options(parsed["options"])
    if dropped:
        _log(f"    filter dropped {list(dropped)}: {[r for rs in dropped.values() for r in rs]}")
    if len(survivors) < 2:
        try:
            raw2 = await caller(prompt, semaphore)
            parsed2 = parse_response(raw2)
            s2, d2 = filter_options(parsed2["options"])
            if len(s2) > len(survivors):
                parsed, survivors, dropped = parsed2, s2, d2
        except Exception:
            pass
    parsed["options"] = survivors
    if parsed.get("best") and not filter_options({"x": parsed["best"]})[0]:
        parsed["best"] = next(iter(survivors.values()), "")
    parsed["v5_dropped"] = dropped
    n_opts = len([v for v in parsed["options"].values() if v and len(v) > 5])
    div_ok = _diversity_ok(parsed["options"])

    # Scorer v2 — DNA-aligned judge (June 11). No structural bonuses.
    scores = {}
    for key, cap in parsed["options"].items():
        if cap and len(cap) > 5:
            scores[key] = score_v2(cap, brief.get("brand_en",""), brief["brand"])
    # best = highest v2 score among survivors (the old scorer buried clean options 240x)
    if scores:
        _bk = max(scores, key=scores.get)
        parsed["best"] = parsed["options"][_bk]

    # Diversity retry if openers overlap (inline — same API call for consistency)
    if not div_ok and n_opts >= 3:
        first_words = []
        for cap in parsed["options"].values():
            if cap and len(cap) > 5:
                first_words.append(cap.split()[0].strip("؟!.،-"))
        banned_openers = " / ".join(set(first_words))
        _vary_note = f"""المشكلة: الكابشنات تبدأ بكلمات متشابهة ({banned_openers}).
أعد الكتابة — لازم كل كابشن يبدأ بكلمة مختلفة تماماً عن البقية."""
        if isinstance(prompt, list):  # V5 messages — append as a new user turn
            variation_prompt = prompt + [{"role": "user", "content": _vary_note}]
        else:
            variation_prompt = prompt + "\n\n---\n" + _vary_note
        try:
            raw2 = await caller(variation_prompt, semaphore)
            parsed2 = parse_response(raw2)
            # BUG FIX 2026-06-11: this path replaced FILTERED options with unfiltered
            # ones — banned/empty captions leaked back in. Filter here too.
            s2, d2 = filter_options(parsed2["options"])
            parsed2["options"] = s2
            parsed2["v5_dropped"] = d2
            n2 = len([v for v in parsed2["options"].values() if v and len(v) > 5])
            div2 = _diversity_ok(parsed2["options"])
            # Use whichever round had better diversity + more options
            if div2 and not div_ok:
                parsed, n_opts, div_ok = parsed2, n2, div2
                scores = {}
                for key, cap in parsed["options"].items():
                    if cap and len(cap) > 5:
                        scores[key] = _auto_score(cap, key, brief["brand"])
                _log(f"  ✓ diversity retry succeeded for {brief['brand']}")
            elif n2 > n_opts:
                parsed, n_opts = parsed2, n2
                _log(f"  ↑ more options after retry for {brief['brand']}")
        except Exception:
            pass

    avg_score = round(sum(scores.values()) / max(len(scores), 1), 1) if scores else 0
    ok_marker = "✓ diverse" if div_ok else "⚠ overlap"
    _log(f"  {'✓' if n_opts >= 3 else '✗'} {brief['brand']} × {brief['occasion']} "
         f"| {n_opts} opts | Q={avg_score} | {ok_marker}")

    return {
        "brand":         brief["brand"],
        "occasion":      brief["occasion"],
        "sector":        brief["sector"],
        "hashtags":      brief.get("hashtags", ""),
        "source":        model,
        "options":       parsed["options"],
        "best":          parsed["best"],
        "scores":        scores,
        "diversity_ok":  div_ok,
        "options_count": n_opts,
        "avg_score":     avg_score,
        "raw_response":  raw[:1200],
        "prompt_version": "v6" if _v5 else "v4",
        "collected_at":  datetime.now().isoformat(),
        "status":        "pending",
    }


async def collect_model(model: str, briefs: list, batch: int | None = None, dry_run: bool = False):
    q = _load_queue(model)
    already = _collected_keys(q)
    if globals().get("FORCE_RECOLLECT"):
        already = set()

    remaining = [b for b in briefs if f"{b['brand']}|{b['occasion']}" not in already]
    if batch:
        remaining = remaining[:batch]

    _log(f"\n{'='*55}")
    _log(f"Model: {model.upper()}  |  {len(remaining)} briefs to collect  (skip {len(already)} done)")
    _log(f"{'='*55}")

    if not remaining:
        _log("Nothing to collect — all done.")
        return

    if dry_run:
        for b in remaining[:3]:
            print(f"\n--- BRIEF: {b['brand']} × {b['occasion']} ---")
            print(build_prompt(b)[:500] + "...")
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [_collect_brief(b, model, sem) for b in remaining]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    added = 0
    for r in results:
        if isinstance(r, dict) and r is not None:
            q["pending"].append(r)
            added += 1
        elif isinstance(r, Exception):
            _log(f"  ✗ Exception: {r}")

    _save_queue(model, q)
    total = len(q["pending"]) + len(q.get("approved", []))
    _log(f"\n✅  {model}: added {added} | total in queue: {total}")


# ── Report ─────────────────────────────────────────────────────────────────────

def report(model: str):
    q = _load_queue(model)
    pending = q.get("pending", [])
    approved = q.get("approved", [])
    all_items = pending + approved

    print(f"\n{'='*55}")
    print(f"REPORT — {model.upper()}")
    print(f"{'='*55}")
    print(f"  Pending:  {len(pending)}")
    print(f"  Approved: {len(approved)}")
    print(f"  Total:    {len(all_items)}")

    if not all_items:
        return

    div_ok = sum(1 for i in all_items if i.get("diversity_ok"))
    avg_scores = [i.get("avg_score", 0) for i in all_items if i.get("avg_score")]
    avg = round(sum(avg_scores) / max(len(avg_scores), 1), 1)
    opt_counts = [i.get("options_count", 0) for i in all_items]
    avg_opts = round(sum(opt_counts) / max(len(opt_counts), 1), 1)

    print(f"\n  Quality:")
    print(f"    diverse:      {div_ok}/{len(all_items)} ({round(100*div_ok/max(len(all_items),1))}%)")
    print(f"    avg Q-score:  {avg}/100")
    print(f"    avg options:  {avg_opts}/5")

    # Best-pick distribution
    best_tech = {}
    for item in all_items:
        best_cap = item.get("best", "")
        scores = item.get("scores", {})
        if scores:
            best_key = max(scores, key=lambda k: scores.get(k, 0))
            best_tech[best_key] = best_tech.get(best_key, 0) + 1

    if best_tech:
        print(f"\n  Best-tech distribution (by auto-score):")
        for k in sorted(best_tech, key=lambda x: best_tech[x], reverse=True):
            pct = round(100 * best_tech[k] / len(all_items))
            bar = "█" * (best_tech[k] // max(1, len(all_items) // 20))
            print(f"    {k}: {best_tech[k]:3d} ({pct}%) {bar}")


# ── Recollect bad ──────────────────────────────────────────────────────────────

def recollect_bad(model: str, min_options: int = 3):
    q = _load_queue(model)
    pending = q.get("pending", [])
    bad = [i for i in pending
           if not i.get("diversity_ok") or i.get("options_count", 0) < min_options]
    good = [i for i in pending
            if i.get("diversity_ok") and i.get("options_count", 0) >= min_options]

    print(f"\n{model}: removing {len(bad)} bad items (diversity_ok=False or <{min_options} options)")
    print(f"  Keeping {len(good)} good items")

    q["pending"] = good
    _save_queue(model, q)
    print(f"  Done. Run collector again to re-collect removed items.")


# ── Cross-model stats ──────────────────────────────────────────────────────────

def cross_stats():
    """Compare model quality stats side-by-side."""
    models = ["gpt-4o", "gemini", "claude"]
    humain_q = BASE / "logs/humain_queue.json"

    print(f"\n{'='*65}")
    print(f"CROSS-MODEL COMPARISON")
    print(f"{'='*65}")
    print(f"{'Model':<12} {'Total':>6} {'Diverse%':>9} {'AvgQ':>6} {'AvgOpts':>8}")
    print(f"{'-'*65}")

    # HUMAIN
    if humain_q.exists():
        hq = json.loads(humain_q.read_text())
        items = hq.get("pending", []) + hq.get("approved", [])
        if items:
            div = sum(1 for i in items if i.get("diversity_ok"))
            avg_q = round(sum(i.get("avg_score", i.get("scores", {}) and
                               sum(i["scores"].values())/max(len(i["scores"]),1) or 0)
                              for i in items) / max(len(items), 1), 1)
            avg_o = round(sum(i.get("options_count", 0) for i in items) / max(len(items), 1), 1)
            pct = round(100 * div / max(len(items), 1))
            print(f"{'HUMAIN':<12} {len(items):>6} {pct:>8}% {avg_q:>6} {avg_o:>8}")

    for model in models:
        path = QUEUE_FILES.get(model)
        if not path or not path.exists():
            print(f"{model:<12} {'—':>6}")
            continue
        q = json.loads(path.read_text())
        items = q.get("pending", []) + q.get("approved", [])
        if not items:
            print(f"{model:<12} {0:>6}")
            continue
        div = sum(1 for i in items if i.get("diversity_ok"))
        avg_q = round(sum(i.get("avg_score", 0) for i in items) / max(len(items), 1), 1)
        avg_o = round(sum(i.get("options_count", 0) for i in items) / max(len(items), 1), 1)
        pct = round(100 * div / max(len(items), 1))
        print(f"{model:<12} {len(items):>6} {pct:>8}% {avg_q:>6} {avg_o:>8}")

    print(f"{'='*65}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Multi-LLM caption collector")
    parser.add_argument("--model", choices=["gpt4o", "gemini", "claude", "all"], default="gpt4o",
                        help="Which model(s) to collect from")
    parser.add_argument("--batch", type=int, default=None,
                        help="Limit to N new briefs (default: all remaining)")
    parser.add_argument("--brand", type=str, default=None,
                        help="Only collect briefs for this brand_en (e.g. albaik)")
    parser.add_argument("--force", action="store_true",
                        help="Re-collect even if brief already in queue (V4 testing)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, no API calls")
    parser.add_argument("--report", action="store_true", help="Show quality report")
    parser.add_argument("--recollect-bad", action="store_true",
                        help="Remove diversity_ok=False items for re-collection")
    parser.add_argument("--min-options", type=int, default=3,
                        help="Min options threshold for --recollect-bad (default 3)")
    parser.add_argument("--cross-stats", action="store_true",
                        help="Show cross-model quality comparison")
    args = parser.parse_args()

    # Normalize model name
    model_map = {"gpt4o": "gpt-4o", "gemini": "gemini", "claude": "claude", "all": "all"}
    model = model_map[args.model]

    if args.cross_stats:
        cross_stats()
        return

    briefs = json.loads((BASE / "data/brief_matrix.json").read_text())
    if args.brand:
        briefs = [b for b in briefs if b.get("brand_en") == args.brand]
        print(f"--brand {args.brand}: {len(briefs)} briefs")
    if args.force:
        global FORCE_RECOLLECT
        FORCE_RECOLLECT = True

    if args.report:
        models = ["gpt-4o", "gemini", "claude"] if model == "all" else [model]
        for m in models:
            report(m)
        return

    if args.recollect_bad:
        models = ["gpt-4o", "gemini", "claude"] if model == "all" else [model]
        for m in models:
            recollect_bad(m, args.min_options)
        return

    if model == "all":
        asyncio.run(_collect_all(briefs, args.batch, args.dry_run))
    else:
        asyncio.run(collect_model(model, briefs, args.batch, args.dry_run))


async def _collect_all(briefs: list, batch: int | None, dry_run: bool):
    await asyncio.gather(
        collect_model("gpt-4o", briefs, batch, dry_run),
        collect_model("gemini", briefs, batch, dry_run),
    )


if __name__ == "__main__":
    main()
