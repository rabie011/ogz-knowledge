#!/usr/bin/env python3
"""
generate_brand_dna_gpt.py
=========================
Per-account Brand DNA generation via GPT-4o-mini (OpenAI Batch API).

For each account with ≥10 obs, computes local stats, samples up to 20 captions,
builds a compact prompt payload, and submits one Batch API job for all accounts.
Results are written to logs/brand_dna/{handle}_gpt.json.

Usage:
    python3 scripts/generate_brand_dna_gpt.py --dry-run
    python3 scripts/generate_brand_dna_gpt.py
    python3 scripts/generate_brand_dna_gpt.py --handle barnscoffee
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO      = Path(__file__).parent.parent
OBS_ROOT  = REPO / "11_who_to_learn_from" / "observations"
DNA_DIR   = REPO / "logs" / "brand_dna"
BATCH_DIR = REPO / "logs" / "brand_dna_batches"
STATE_FILE = REPO / "logs" / "brand_dna_gpt_state.json"

MIN_OBS        = 10
MAX_CAPTIONS   = 20
BATCH_TIMEOUT  = 7200   # 2 hours
POLL_INTERVAL  = 30     # seconds

SYSTEM_PROMPT = (
    "You are a Saudi digital marketing strategist analysing Instagram brand data. "
    "Given structured data about an Instagram account's content, generate a strategic "
    "brand intelligence profile. Return ONLY valid JSON matching the schema provided. "
    "Be specific, data-driven, and actionable."
)

OUTPUT_SCHEMA_HINT = """{
  "handle": "<string>",
  "sector": "<string>",
  "obs_count": <int>,
  "generated_at": "<ISO datetime>",
  "brand_voice": {
    "summary": "<2-3 sentence brand voice description>",
    "language_style": "<arabic-first|english-first|bilingual>",
    "tone_tags": ["<tag>", ...],
    "signature_phrases": ["<phrase>", ...],
    "arabic_technique": "<colloquial_gulf|msa_formal|colloquial_hejazi|colloquial_najdi|mixed|none|unknown>"
  },
  "content_formula": {
    "top_formats": [{"type": "<string>", "pct": <int>}, ...],
    "top_patterns": ["<pattern_slug>", ...],
    "hook_distribution": {"<hook_type>": <int>, ...},
    "cta_distribution": {"<cta_type>": <int>, ...},
    "posting_rhythm": "<daily|3x_week|irregular|unknown>",
    "best_performing_type": "<video|image|carousel|unknown>"
  },
  "visual_identity": {
    "dominant_composition": "<string>",
    "human_presence_rate": <float 0-1>,
    "text_overlay_rate": <float 0-1>,
    "scene_preference": "<indoor|outdoor|studio|mixed>"
  },
  "occasion_calendar": {
    "ramadan": <bool>, "national_day": <bool>, "eid": <bool>,
    "founding_day": <bool>, "valentines": <bool>, "mothers_day": <bool>
  },
  "strategic_gaps": ["<opportunity>", ...],
  "ogz_recommendation": "<2-3 sentences on what OGZ would do differently/better for this brand>"
}"""

# ── OpenAI client (lazy import) ────────────────────────────────────────────────
def _get_client():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from lib.openai_client import make_client  # B258: bounded timeout/retries
    except ImportError:
        print("ERROR: openai not installed — pip install openai", file=sys.stderr)
        sys.exit(1)
    try:
        return make_client(os.environ.get("OPENAI_API_KEY", ""))
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


# ── State helpers ──────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ── Observation loading ────────────────────────────────────────────────────────
def load_all_obs() -> dict[str, list[dict]]:
    """
    Returns mapping: handle -> list of obs dicts, sorted by engagement_potential desc.
    """
    ENG_MAP = {
        "very_high": 4, "high": 3, "above_average": 2,
        "medium": 1, "below_average": 0, "low": 0,
    }
    grouped: dict[str, list] = defaultdict(list)
    for obs_file in OBS_ROOT.rglob("*.json"):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue
        handle = data.get("account_handle_normalized", "").strip()
        if not handle:
            continue
        eng_raw = (
            data.get("quality_assessment", {}) or {}
        ).get("engagement_potential", "medium")
        data["_eng_score"] = ENG_MAP.get(str(eng_raw).lower(), 1)
        grouped[handle].append(data)

    # Sort each account's obs by engagement desc
    for handle in grouped:
        grouped[handle].sort(key=lambda d: -d["_eng_score"])

    return dict(grouped)


# ── Local stat computation ─────────────────────────────────────────────────────
def _top(counter: dict, n: int = 5) -> list:
    return sorted(counter.keys(), key=lambda k: -counter[k])[:n]


def _pct(count: int, total: int) -> int:
    return round(count / total * 100) if total else 0


def compute_account_stats(obs_list: list[dict]) -> dict:
    """Aggregate structured stats from raw obs list."""
    n = len(obs_list)

    # Content type distribution
    type_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        ct = (d.get("content_ref", {}) or {}).get("content_type", "unknown")
        type_counts[str(ct).lower()] += 1

    top_formats = [
        {"type": t, "pct": _pct(c, n)}
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    # Pattern frequency
    pattern_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        for pm in d.get("pattern_matches", []) or []:
            slug = pm.get("pattern_slug", "") if isinstance(pm, dict) else str(pm)
            if slug:
                pattern_counts[slug.lower().strip()] += 1
    top_patterns = _top(pattern_counts, 8)

    # Hook distribution
    hook_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        vo = d.get("voice_observations", {}) or {}
        hook = vo.get("hook_type") or vo.get("opener_formula")
        if hook:
            hook_counts[str(hook).lower()] += 1

    # CTA distribution
    cta_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        vo = d.get("voice_observations", {}) or {}
        cta = vo.get("cta_type")
        if cta:
            cta_counts[str(cta).lower()] += 1
        elif vo.get("call_to_action_present"):
            cta_counts["generic_cta"] += 1

    # Visual fields
    human_count = 0
    text_overlay_count = 0
    setting_counts: dict[str, int] = defaultdict(int)
    composition_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        vv = d.get("visual_observations", {}) or {}
        # Human presence
        hp = vv.get("human_presence")
        cv = vv.get("characters_visible")
        if hp is True or (isinstance(cv, dict) and int(cv.get("count", 0) or 0) > 0):
            human_count += 1
        elif isinstance(cv, list) and len(cv) > 0:
            human_count += 1
        # Text overlay
        to = vv.get("text_overlays")
        if to and (isinstance(to, list) and len(to) > 0):
            text_overlay_count += 1
        # Setting
        s = vv.get("setting")
        if s:
            setting_counts[str(s).lower()] += 1
        # Composition
        comp = vv.get("composition_style")
        if comp:
            composition_counts[str(comp).lower()] += 1

    dominant_setting_raw = max(setting_counts, key=setting_counts.get) if setting_counts else "unknown"
    # Classify scene preference
    if dominant_setting_raw in ("indoor", "indoor_restaurant", "indoor_retail", "indoor_office"):
        scene_pref = "indoor"
    elif dominant_setting_raw in ("outdoor", "outdoor_urban", "street", "exterior"):
        scene_pref = "outdoor"
    elif dominant_setting_raw == "studio":
        scene_pref = "studio"
    else:
        scene_pref = "mixed"

    dominant_comp = max(composition_counts, key=composition_counts.get) if composition_counts else "unknown"

    # Occasion calendar
    occasion_calendar: dict[str, bool] = {
        "ramadan": False, "national_day": False, "eid": False,
        "founding_day": False, "valentines": False, "mothers_day": False,
    }
    for d in obs_list:
        cn = d.get("cultural_notes", {}) or {}
        occ_raw = str(cn.get("occasion_relevance", "") or "").lower()
        occ_field = str(d.get("occasion", "") or "").lower()
        combined = occ_raw + " " + occ_field
        if "ramadan" in combined:
            occasion_calendar["ramadan"] = True
        if "national" in combined or "saudi_national" in combined:
            occasion_calendar["national_day"] = True
        if "eid" in combined:
            occasion_calendar["eid"] = True
        if "founding" in combined:
            occasion_calendar["founding_day"] = True
        if "valentin" in combined:
            occasion_calendar["valentines"] = True
        if "mother" in combined:
            occasion_calendar["mothers_day"] = True

    # Engagement by type
    ENG_MAP = {"very_high": 4, "high": 3, "above_average": 2, "medium": 1, "below_average": 0, "low": 0}
    type_eng: dict[str, list] = defaultdict(list)
    for d in obs_list:
        ct = (d.get("content_ref", {}) or {}).get("content_type", "unknown")
        qa = d.get("quality_assessment", {}) or {}
        eng = ENG_MAP.get(str(qa.get("engagement_potential", "medium")).lower(), 1)
        type_eng[str(ct).lower()].append(eng)
    best_type = max(type_eng, key=lambda t: sum(type_eng[t]) / len(type_eng[t])) if type_eng else "unknown"

    # Language/dialect dominant
    lang_counts: dict[str, int] = defaultdict(int)
    dialect_counts: dict[str, int] = defaultdict(int)
    tone_counts: dict[str, int] = defaultdict(int)
    for d in obs_list:
        vo = d.get("voice_observations", {}) or {}
        if vo.get("language"):
            lang_counts[str(vo["language"]).lower()] += 1
        if vo.get("dialect_detected"):
            dialect_counts[str(vo["dialect_detected"]).lower()] += 1
        if vo.get("tone"):
            tone_counts[str(vo["tone"]).lower()] += 1

    dominant_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"
    dominant_dialect = max(dialect_counts, key=dialect_counts.get) if dialect_counts else None
    top_tones = _top(tone_counts, 4)

    # Sector from first obs
    sector = obs_list[0].get("sector", "unknown") if obs_list else "unknown"

    return {
        "obs_count": n,
        "sector": sector,
        "top_formats": top_formats,
        "top_patterns": top_patterns,
        "hook_distribution": dict(hook_counts),
        "cta_distribution": dict(cta_counts),
        "best_performing_type": best_type,
        "human_presence_rate": round(human_count / n, 3),
        "text_overlay_rate": round(text_overlay_count / n, 3),
        "dominant_composition": dominant_comp,
        "scene_preference": scene_pref,
        "occasion_calendar": occasion_calendar,
        "dominant_language": dominant_lang,
        "dominant_dialect": dominant_dialect,
        "top_tones": top_tones,
    }


# ── Caption sampling ───────────────────────────────────────────────────────────
def sample_captions(obs_list: list[dict], max_n: int = MAX_CAPTIONS) -> list[str]:
    """Return up to max_n non-empty captions (highest engagement first, already sorted)."""
    captions = []
    for d in obs_list:
        vo = d.get("voice_observations", {}) or {}
        cap = (vo.get("caption_text") or "").strip()
        if cap and len(captions) < max_n:
            # Truncate very long captions to keep token count lean
            captions.append(cap[:400])
    return captions


# ── GPT prompt builder ─────────────────────────────────────────────────────────
def build_user_prompt(handle: str, stats: dict, captions: list[str]) -> str:
    lines = [
        f"Analyse the Instagram account @{handle} (sector: {stats['sector']}, {stats['obs_count']} posts).",
        "",
        "=== CONTENT STATS ===",
        f"Format distribution: {json.dumps(stats['top_formats'])}",
        f"Top patterns used: {stats['top_patterns']}",
        f"Hook types: {json.dumps(stats['hook_distribution'])}",
        f"CTA types: {json.dumps(stats['cta_distribution'])}",
        f"Best performing format: {stats['best_performing_type']}",
        "",
        "=== VISUAL STATS ===",
        f"Human presence rate: {stats['human_presence_rate']} (0=none, 1=always)",
        f"Text overlay rate: {stats['text_overlay_rate']}",
        f"Dominant composition: {stats['dominant_composition']}",
        f"Scene preference: {stats['scene_preference']}",
        "",
        "=== VOICE / LANGUAGE ===",
        f"Dominant language: {stats['dominant_language']}",
        f"Dominant dialect: {stats['dominant_dialect'] or 'not detected'}",
        f"Top tones observed: {stats['top_tones']}",
        "",
        "=== OCCASIONS COVERED ===",
        json.dumps(stats['occasion_calendar']),
        "",
        f"=== SAMPLE CAPTIONS (top {len(captions)} by engagement) ===",
    ]
    for i, cap in enumerate(captions, 1):
        lines.append(f"{i}. {cap}")
    lines += [
        "",
        "=== OUTPUT SCHEMA ===",
        "Return ONLY a JSON object matching this exact schema (no markdown fences, no extra keys):",
        OUTPUT_SCHEMA_HINT,
        "",
        f'Fill "handle" with "{handle}", "sector" with "{stats["sector"]}", '
        f'"obs_count" with {stats["obs_count"]}, '
        '"generated_at" with the current ISO UTC datetime.',
    ]
    return "\n".join(lines)


# ── Batch API helpers ──────────────────────────────────────────────────────────
def submit_batch(client, requests_list: list[dict]) -> str:
    """Write JSONL, upload to OpenAI Files, create batch job. Returns batch_id."""
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    jsonl_path = BATCH_DIR / f"brand_dna_gpt_{ts}.jsonl"

    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for req in requests_list:
            fh.write(json.dumps(req, ensure_ascii=False) + "\n")

    size_kb = jsonl_path.stat().st_size // 1024
    print(f"  Uploading {len(requests_list)} requests ({size_kb} KB) ...")

    with open(jsonl_path, "rb") as fh:
        file_obj = client.files.create(file=fh, purpose="batch")

    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print(f"  Batch submitted: {batch.id} (status: {batch.status})")
    return batch.id


def poll_batch(client, batch_id: str, timeout_s: int = BATCH_TIMEOUT) -> list[dict]:
    """Poll until complete (or timeout). Returns list of raw result dicts."""
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > timeout_s:
            print(f"  WARNING: Batch {batch_id} timed out after {timeout_s}s — results not retrieved.")
            return []

        batch = client.batches.retrieve(batch_id)
        rc = batch.request_counts
        done  = rc.completed if rc else "?"
        total = rc.total     if rc else "?"
        print(f"  [{batch_id}] status={batch.status} completed={done}/{total} elapsed={int(elapsed)}s")

        if batch.status == "completed":
            raw = client.files.content(batch.output_file_id).text
            results = [
                json.loads(line)
                for line in raw.strip().splitlines()
                if line.strip()
            ]
            print(f"  Batch complete — {len(results)} results")
            return results

        if batch.status in ("failed", "expired", "cancelled"):
            print(f"  ERROR: Batch {batch_id} ended with status={batch.status}")
            # Attempt to retrieve error file if present
            if getattr(batch, "error_file_id", None):
                err_raw = client.files.content(batch.error_file_id).text
                print(f"  Error file content (first 500 chars): {err_raw[:500]}")
            return []

        interval = POLL_INTERVAL if elapsed < 300 else 60
        time.sleep(interval)


# ── Result parsing and writing ─────────────────────────────────────────────────
def parse_gpt_json(raw_content: str) -> dict | None:
    """
    Attempt to extract valid JSON from a GPT response string.
    GPT should return pure JSON, but defensively strip markdown fences.
    """
    text = raw_content.strip()
    # Strip ```json ... ``` fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        inner = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
        text = "\n".join(inner).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try finding the first { ... } block
        start = text.find("{")
        end   = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return None


def write_gpt_result(handle: str, profile: dict):
    DNA_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = handle.replace("/", "_").replace("@", "").strip()
    out_path = DNA_DIR / f"{safe_name}_gpt.json"
    out_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    print(f"  Wrote: {out_path.relative_to(REPO)}")


# ── Dry-run summary ────────────────────────────────────────────────────────────
def dry_run_summary(accounts: dict[str, dict], state: dict):
    already_done = set(state.get("done_handles", []))
    to_process   = [h for h in sorted(accounts) if h not in already_done]
    skipped_done = [h for h in sorted(accounts) if h in already_done]

    print("\n── DRY RUN ──────────────────────────────────────────────────")
    print(f"  Total accounts with ≥{MIN_OBS} obs: {len(accounts)}")
    print(f"  Already done (_gpt.json exists): {len(skipped_done)}")
    print(f"  Would process: {len(to_process)}")
    if to_process:
        print("\n  Accounts to process:")
        for h in to_process:
            info = accounts[h]
            print(f"    {h}: {info['stats']['obs_count']} obs  |  "
                  f"sector={info['stats']['sector']}  |  "
                  f"captions={len(info['captions'])}")
    if skipped_done:
        print("\n  Already done (skip):")
        for h in skipped_done:
            print(f"    {h}")

    # Token estimate
    est_tokens_per_account = 1000
    total_est = len(to_process) * est_tokens_per_account
    cost_est  = total_est / 1_000_000 * 0.075  # gpt-4o-mini batch input rate
    print(f"\n  Est. tokens: {total_est:,}  |  Est. cost: ${cost_est:.4f}")
    print("────────────────────────────────────────────────────────────\n")


# ── Core pipeline ──────────────────────────────────────────────────────────────
def build_account_payloads(
    grouped_obs: dict[str, list[dict]],
    filter_handle: str | None = None,
) -> dict[str, dict]:
    """
    For each eligible account, compute stats + sample captions.
    Returns: handle -> {"stats": ..., "captions": [...], "user_prompt": ...}
    """
    payloads: dict[str, dict] = {}

    for handle, obs_list in sorted(grouped_obs.items()):
        if filter_handle and handle != filter_handle:
            continue
        if len(obs_list) < MIN_OBS:
            continue

        stats   = compute_account_stats(obs_list)
        captions = sample_captions(obs_list, MAX_CAPTIONS)
        prompt  = build_user_prompt(handle, stats, captions)

        payloads[handle] = {
            "stats":       stats,
            "captions":    captions,
            "user_prompt": prompt,
        }

    return payloads


def build_batch_requests(payloads: dict[str, dict]) -> list[dict]:
    """Convert account payloads into OpenAI Batch JSONL request objects."""
    requests = []
    for handle, info in payloads.items():
        safe_id = handle.replace("/", "_").replace("@", "").replace(".", "_")
        req = {
            "custom_id": f"brand_dna_{safe_id}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "max_tokens": 1200,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": info["user_prompt"]},
                ],
            },
        }
        requests.append(req)
    return requests


def apply_batch_results(
    results: list[dict],
    payloads: dict[str, dict],
    state: dict,
) -> int:
    """Parse batch results and write _gpt.json files. Returns count written."""
    # Build reverse map: custom_id -> handle
    id_to_handle: dict[str, str] = {}
    for handle in payloads:
        safe_id = handle.replace("/", "_").replace("@", "").replace(".", "_")
        id_to_handle[f"brand_dna_{safe_id}"] = handle

    written = 0
    done_handles: list[str] = state.setdefault("done_handles", [])

    for result in results:
        custom_id = result.get("custom_id", "")
        handle    = id_to_handle.get(custom_id)
        if not handle:
            print(f"  WARNING: Unknown custom_id {custom_id!r} — skipping")
            continue

        error = result.get("error")
        if error:
            print(f"  ERROR [{handle}]: {error}")
            continue

        try:
            content = result["response"]["body"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            print(f"  ERROR [{handle}]: could not extract content — {exc}")
            continue

        profile = parse_gpt_json(content)
        if profile is None:
            print(f"  ERROR [{handle}]: JSON parse failed. Raw content (200 chars): {content[:200]!r}")
            continue

        # Inject authoritative fields (override anything GPT may have gotten wrong)
        stats = payloads[handle]["stats"]
        profile["handle"]       = handle
        profile["sector"]       = stats["sector"]
        profile["obs_count"]    = stats["obs_count"]
        profile["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

        write_gpt_result(handle, profile)
        written += 1
        if handle not in done_handles:
            done_handles.append(handle)

    return written


# ── Main entry point ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate Brand DNA profiles via GPT-4o-mini Batch API."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be processed without calling OpenAI.",
    )
    parser.add_argument(
        "--handle",
        metavar="HANDLE",
        help="Process a single account (e.g. --handle barnscoffee).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-process accounts that already have a _gpt.json file.",
    )
    args = parser.parse_args()

    # ── Load observations ──────────────────────────────────────────────────────
    print("Loading observations ...")
    grouped_obs = load_all_obs()
    print(f"  Loaded {sum(len(v) for v in grouped_obs.values())} obs "
          f"across {len(grouped_obs)} accounts.")

    # ── Load state ─────────────────────────────────────────────────────────────
    state = load_state()
    already_done: set[str] = set(state.get("done_handles", []))

    # Also check filesystem for existing _gpt.json files (source of truth)
    for existing_gpt in DNA_DIR.glob("*_gpt.json"):
        stem = existing_gpt.stem.replace("_gpt", "")
        # Reverse the safe_name transform (best effort; dots lost in transform)
        already_done.add(stem)

    # ── Build payloads ─────────────────────────────────────────────────────────
    all_payloads = build_account_payloads(grouped_obs, filter_handle=args.handle)

    # Filter out already-done unless --force
    if not args.force:
        payloads = {
            h: info
            for h, info in all_payloads.items()
            if h not in already_done
        }
        if len(payloads) < len(all_payloads):
            skipped = len(all_payloads) - len(payloads)
            print(f"  Skipping {skipped} account(s) already have _gpt.json "
                  f"(use --force to re-process).")
    else:
        payloads = all_payloads

    if args.dry_run:
        dry_run_summary(all_payloads, state)
        return

    if not payloads:
        print("Nothing to do — all eligible accounts already have _gpt.json files.")
        print("Use --force to regenerate.")
        return

    print(f"\nProcessing {len(payloads)} account(s) ...")

    # ── Resume existing batch if state has one ─────────────────────────────────
    client = _get_client()

    active_batch_id = state.get("active_batch_id")
    if active_batch_id and not args.force:
        print(f"\nResuming existing batch {active_batch_id} ...")
        results = poll_batch(client, active_batch_id)
        if results:
            written = apply_batch_results(results, all_payloads, state)
            state.pop("active_batch_id", None)
            save_state(state)
            print(f"\nDone — {written} _gpt.json file(s) written.")
        else:
            print("Batch returned no results. Check state file and retry.")
        return

    # ── Build and submit new batch ─────────────────────────────────────────────
    requests_list = build_batch_requests(payloads)
    print(f"\nSubmitting batch of {len(requests_list)} request(s) ...")
    batch_id = submit_batch(client, requests_list)

    state["active_batch_id"] = batch_id
    state["batch_submitted_at"] = datetime.now(tz=timezone.utc).isoformat()
    save_state(state)

    # ── Poll and apply ─────────────────────────────────────────────────────────
    print(f"\nPolling batch (poll every {POLL_INTERVAL}s, timeout {BATCH_TIMEOUT // 60}m) ...")
    results = poll_batch(client, batch_id)

    if not results:
        print(f"\nBatch did not complete within the timeout period.")
        print(f"Re-run the script to resume — batch_id stored in {STATE_FILE.relative_to(REPO)}")
        return

    written = apply_batch_results(results, payloads, state)
    state.pop("active_batch_id", None)
    save_state(state)

    print(f"\nComplete — {written} _gpt.json file(s) written to logs/brand_dna/")


if __name__ == "__main__":
    main()
