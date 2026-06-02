#!/usr/bin/env python3
"""
ogz_enricher.py — OGZ Knowledge Base 24/7 Autonomous Enrichment Daemon

Runs forever in 30-min cycles. Every cycle:
  1. Extract new/thin accounts (Apify → Claude Batch classify → obs JSON)
  2. Fill missing captions (instaloader, 8-hr rate limit awareness)
  3. Fill orphaned pattern slugs (Claude Batch API)
  4. Detect chain gaps → generate new chains if needed
  5. Rebuild analytics if obs are newer than logs
  6. validate_all.py → must pass before any sync
  7. git commit + Drive rsync + git push
  8. Telegram report to Mohamed via Mira

Storage safety rule (enforced):
  WRITE LOCAL → VALIDATE → COMMIT → SYNC DRIVE → PUSH GITHUB
  Never sync unless validate_all.py passes.

Logs: logs/enricher.log
State: logs/enricher_state.json (tracks rate limits, last attempts, counts)

LaunchAgent: ~/Library/LaunchAgents/com.ogz.enricher.plist
"""
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Load env ───────────────────────────────────────────────────────────────────
def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if not os.environ.get(k):
                    os.environ[k] = v

_load_env()

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO       = Path(__file__).parent.parent
LOGS       = REPO / "logs"
OBS_ROOT   = REPO / "11_who_to_learn_from" / "observations"
PATTERNS   = REPO / "11_who_to_learn_from" / "patterns"
TARGET_ACCOUNTS_FILE = REPO / "11_who_to_learn_from" / "target_accounts.json"
STATE_FILE = LOGS / "enricher_state.json"
DRIVE_PATH = Path.home() / "Library/CloudStorage/GoogleDrive-rabie@ogzstudios.com/My Drive/ogz-knowledge"

ANALYTICS_SCRIPTS = [
    # ── Base intelligence (captions, patterns, hashtags) ──────────────────────
    "build_caption_intelligence.py",
    "build_caption_intelligence_by_sector.py",
    "build_caption_analysis.py",
    "build_caption_length_hashtag_analysis.py",
    "build_hashtag_strategy.py",
    "build_hashtag_cooccurrence.py",
    "build_arabic_copywriting.py",
    "build_arabic_copywriting_by_sector.py",
    # ── Pattern intelligence ──────────────────────────────────────────────────
    "build_pattern_engagement.py",
    "build_pattern_usage_analysis.py",
    "build_pattern_density.py",
    "build_pattern_cooccurrence.py",
    "build_pattern_sector_matrix.py",
    "build_pattern_trends.py",
    "build_pattern_adoption_gaps.py",
    "build_pattern_network.py",
    # ── Account intelligence ──────────────────────────────────────────────────
    "build_account_archetypes.py",
    "build_account_consistency.py",
    "build_account_performance_analysis.py",
    "build_account_similarity.py",
    "build_account_themes_index.py",
    "build_archetype_benchmark.py",
    "build_brand_dna_profiles.py",
    # ── Visual / composition ──────────────────────────────────────────────────
    "build_visual_complexity_analysis.py",
    "build_visual_dna_profiles.py",
    "build_visual_decision_tree.py",
    "build_visual_sector_intel.py",
    "build_composition_analysis.py",
    "build_composition_setting_synergy.py",
    "build_complexity_composition_matrix.py",
    "build_color_palette_analysis.py",
    "build_color_palette_dna.py",
    "build_setting_analysis.py",
    "build_setting_lighting_synergy.py",
    "build_lighting_analysis.py",
    "build_character_analysis.py",
    "build_character_library.py",
    "build_human_element_analysis.py",
    "build_wardrobe_gender_analysis.py",
    # ── Voice / copy / tone ───────────────────────────────────────────────────
    "build_voice_positioning.py",
    "build_tone_register_analysis.py",
    "build_register_tone_matrix.py",
    "build_notable_phrases_intelligence.py",
    "build_phrases_library.py",
    "build_phrase_engagement.py",
    "build_cta_language_signals.py",
    "build_dialect_register_occasion_matrix.py",
    "build_text_overlay_analysis.py",
    "build_text_overlay_intelligence.py",
    # ── Occasion / temporal ───────────────────────────────────────────────────
    "build_temporal_analysis.py",
    "build_day_of_week_analysis.py",
    "build_post_cadence.py",
    "build_posting_frequency_analysis.py",
    "build_occasion_readiness_report.py",
    "build_occasion_sector_matrix.py",
    "build_occasion_sector_format_matrix.py",
    "build_occasion_calendar.py",
    "build_occasion_format_grid.py",
    "build_occasion_playbook.py",
    "build_format_occasion_matrix.py",
    # ── Compliance / cultural ─────────────────────────────────────────────────
    "build_compliance_intelligence.py",
    "build_compliance_risk_report.py",
    "build_soft_flags_catalog.py",
    "build_cultural_signal_analysis.py",
    # ── Content format ────────────────────────────────────────────────────────
    "build_carousel_analysis.py",
    "build_video_audio_analysis.py",
    "build_video_pace_analysis.py",
    "build_video_strategy_analysis.py",
    "build_props_analysis.py",
    "build_props_taxonomy.py",
    "build_content_type_analysis.py",
    # ── Sector / competitive ──────────────────────────────────────────────────
    "build_sector_fingerprint.py",
    "build_content_pillars.py",
    "build_content_health_scores.py",
    "build_content_score_model.py",
    "build_competitive_gap.py",
    "build_cross_sector_benchmark.py",
    "build_cross_sector_opportunity.py",
    "build_elite_vs_weak_dna.py",
    # ── Quality / engagement ──────────────────────────────────────────────────
    "build_engagement_signals.py",
    "build_quality_signals.py",
    "build_winning_formula.py",
    "build_master_signal_table.py",
    "build_media_engagement_analysis.py",
    # ── Hospitality / heritage ────────────────────────────────────────────────
    "build_hospitality_analysis.py",
    "build_hospitality_intelligence.py",
    "build_hospitality_inventory.py",
    "build_heritage_spectrum.py",
    # ── Synthesis (run last — depend on everything above) ────────────────────
    "build_intelligence_playbook.py",
    "build_intelligence_playbook_v2.py",
    "build_calibration_extractions.py",
    "build_account_coach_reports.py",
    # NOTE: build_production_brief_engine.py excluded — calls Claude API
    # NOTE: build_content_calendar.py excluded — calls Claude API (check before adding)
]

CYCLE_INTERVAL_SECS = 1800   # 30 minutes
CAPTION_RATE_LIMIT_HRS = 8   # hours to wait after Instagram 401
MAX_ACCOUNTS_PER_CYCLE = 2   # rate limit caution


# ── Logging ────────────────────────────────────────────────────────────────────
LOGS.mkdir(exist_ok=True)
# When running via LaunchAgent, stdout is already redirected to enricher.log,
# so only use StreamHandler (avoid duplicate writes from FileHandler + stdout).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("enricher")


# ── State persistence ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ── Telegram (via Mira) ────────────────────────────────────────────────────────
def telegram(msg: str):
    """Send message to Mohamed via Telegram Mira bot."""
    token   = os.environ.get("TELEGRAM_TOKEN", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log.warning("Telegram not configured — skipping notification")
        return
    try:
        import urllib.request, urllib.parse
        payload = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Telegram send failed: {e}")


# ── Subprocess helper ──────────────────────────────────────────────────────────
def _run(cmd: list[str], timeout: int = 600) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "PYTHONPATH": str(REPO)},
    )
    return result.returncode, result.stdout or "", result.stderr or ""


# ── Helper: count obs per content-type bucket for handle ──────────────────────
def count_obs_by_type_for_handle(handle: str) -> dict:
    """Return {"image": N, "video": N, "carousel": N} for this handle."""
    counts = {"image": 0, "video": 0, "carousel": 0}
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            if d.get("account_handle_normalized", "").lower() != handle.lower():
                continue
            ct = (d.get("content_ref") or {}).get("content_type", "")
            if ct in ("video", "reel"):
                counts["video"] += 1
            elif ct == "carousel_slide":
                counts["carousel"] += 1
            else:
                counts["image"] += 1
        except Exception:
            pass
    return counts


def is_quota_met(handle: str, quota: dict) -> bool:
    counts = count_obs_by_type_for_handle(handle)
    return all(counts.get(k, 0) >= v for k, v in quota.items())


def count_missing_captions() -> int:
    missing = 0
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            voice = d.get("voice_observations") or {}
            ct = (d.get("content_ref") or {}).get("content_type", "image")
            if voice.get("caption_text") is None:  # only null — skip empty strings (caption script skips those too)
                missing += 1
        except Exception:
            pass
    return missing


def get_orphaned_slugs() -> list[str]:
    existing = {f.stem for f in PATTERNS.rglob("*.json")}
    slugs = set()
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            for pm in d.get("pattern_matches", []):
                slug = pm.get("pattern_slug") or pm.get("slug", "")
                if slug and slug not in existing:
                    slugs.add(slug)
        except Exception:
            pass
    return list(slugs)


# ── Module 1: Account extraction ──────────────────────────────────────────────
def module_extract_accounts() -> int:
    """Extract new/thin accounts. Returns obs written count."""
    if not TARGET_ACCOUNTS_FILE.exists():
        return 0

    try:
        target_accounts = json.loads(TARGET_ACCOUNTS_FILE.read_text())
        targets = target_accounts.get("accounts", [])
    except Exception:
        return 0

    def _save_target_accounts(ta: dict):
        TARGET_ACCOUNTS_FILE.write_text(json.dumps(ta, indent=2, ensure_ascii=False))

    DEFAULT_QUOTA = {"image": 50, "video": 50, "carousel": 25}

    # Find accounts that need extraction: pending OR any type below quota
    to_extract = []
    for a in targets:
        if a.get("handle") == "cafe.najd":
            continue  # CONFIRMED FAKE — never extract
        status = a.get("status", "")
        handle = a.get("handle", "")
        quota  = a.get("quota", DEFAULT_QUOTA)
        if status == "pending" or (status == "partial" and not is_quota_met(handle, quota)):
            to_extract.append(a)

    if not to_extract:
        log.info("  All accounts meet quota — nothing to extract")
        return 0

    # Check Apify token is set before starting
    if not os.environ.get("APIFY_TOKEN"):
        log.info("  APIFY_TOKEN not set — skipping account extraction")
        log.info("  → Get token at console.apify.com → Settings → Integrations → API token")
        return 0

    log.info(f"  {len(to_extract)} accounts need extraction — processing up to {MAX_ACCOUNTS_PER_CYCLE}/cycle")

    total_written = 0
    for acct in to_extract[:MAX_ACCOUNTS_PER_CYCLE]:
        handle = acct["handle"]
        sector = acct.get("sector", "f_and_b")
        quota  = acct.get("quota", DEFAULT_QUOTA)
        log.info(
            f"  Extracting @{handle} ({sector}) | "
            f"quota img={quota['image']} vid={quota['video']} car={quota['carousel']}"
        )

        try:
            rc, stdout, stderr = _run([
                sys.executable, "scripts/extract_account_obs.py",
                "--handle", handle,
                "--sector", sector,
            ], timeout=1800)  # Apify 11min + OpenAI batch up to 19min = 30min ceiling (batch can be slow)
        except Exception as e:
            # Timeout or crash on THIS account — log and continue to next
            log.warning(f"    ⚠ @{handle} extraction error: {e}")
            # Increment consecutive timeout counter — ALWAYS persist so the count
            # survives across daemon cycles (target_accounts.json is re-read each cycle).
            acct["_timeout_count"] = acct.get("_timeout_count", 0) + 1
            if acct["_timeout_count"] >= 3:
                log.warning(f"    ⚠ @{handle} timed out {acct['_timeout_count']}x — marking force_done to unblock queue")
                acct["status"] = "force_done"
                acct["obs_count"] = acct.get("obs_count", 0)
                acct["note"] = f"force_done: {acct['_timeout_count']} consecutive timeouts at 1800s"
            else:
                log.warning(f"    ⚠ @{handle} timeout #{acct['_timeout_count']} (force_done after 3)")
            _save_target_accounts(target_accounts)  # always save — count must persist
            continue

        # ── Apify budget sentinel ────────────────────────────────────────────
        if "APIFY_BUDGET_EXHAUSTED" in (stdout or ""):
            log.warning("  💸 Apify budget exhausted — disabling extraction for all remaining accounts")
            # Mark every remaining pending/partial account as skip
            skipped_handles = []
            for a in targets:
                if a.get("status") in ("pending", "partial"):
                    a["status"] = "skip"
                    a["note"] = a.get("note", "") + " [paused: Apify budget exhausted]"
                    skipped_handles.append(a["handle"])
            _save_target_accounts(target_accounts)
            if skipped_handles:
                log.warning(f"  Paused {len(skipped_handles)} accounts: {skipped_handles[:5]}...")
            break   # stop processing accounts this cycle

        m = re.search(r"Extracted (\d+) observations", stdout)
        n = int(m.group(1)) if m else 0

        # Also log per-type breakdown if present
        m2 = re.search(r"image=(\d+)\s+video=(\d+)\s+carousel=(\d+)", stdout)
        breakdown = f" (img={m2.group(1)} vid={m2.group(2)} car={m2.group(3)})" if m2 else ""

        if rc == 0 and n > 0:
            total_written += n
            acct["_zero_count"] = 0
            log.info(f"    ✅ @{handle}: {n} obs written{breakdown}")
        elif rc == 0 and n == 0:
            acct["_zero_count"] = acct.get("_zero_count", 0) + 1
            log.warning(f"    ⚠ @{handle}: 0 obs returned (zero #{acct['_zero_count']})")
            if acct["_zero_count"] >= 3:
                log.warning(f"    ⚠ @{handle}: 3 consecutive 0-result extractions — marking force_done")
                acct["status"] = "force_done"
                acct["note"] = f"force_done: {acct['_zero_count']} consecutive 0-result extractions. Handle may be wrong, private, or empty."
            _save_target_accounts(target_accounts)
        else:
            log.warning(f"    ⚠ @{handle} extraction failed (rc={rc})")
            if stderr:
                log.warning(f"       {stderr[:300]}")

    return total_written


# ── Module 2: Caption fill ────────────────────────────────────────────────────
def module_fill_captions(state: dict) -> tuple[int, dict]:
    """Fill missing captions. Returns (written_count, updated_state)."""
    missing = count_missing_captions()
    if missing == 0:
        return 0, state

    # Enforce 8-hr rate limit window
    last_attempt = state.get("last_caption_attempt")
    fail_count   = state.get("last_caption_fail_count", 0)
    if last_attempt and fail_count > 0:
        last_dt = datetime.fromisoformat(last_attempt)
        hrs_elapsed = (datetime.now() - last_dt).total_seconds() / 3600
        if hrs_elapsed < CAPTION_RATE_LIMIT_HRS:
            log.info(f"  Caption: rate limit active ({hrs_elapsed:.1f}/{CAPTION_RATE_LIMIT_HRS} hrs). Skipping.")
            return 0, state

    log.info(f"  Caption fill: {missing} missing captions")
    rc, stdout, stderr = _run(
        [sys.executable, "scripts/extract_captions_instaloader.py"],
        timeout=1800,
    )

    m_written = re.search(r"Written\s*:\s*(\d+)", stdout)
    m_failed  = re.search(r"Failed\s*:\s*(\d+)", stdout)
    written   = int(m_written.group(1)) if m_written else 0
    failed    = int(m_failed.group(1))  if m_failed  else 0

    state["last_caption_attempt"]     = datetime.now().isoformat()
    state["last_caption_fail_count"]  = failed

    if written > 0:
        log.info(f"    ✅ Captions written: {written}")
    if failed > 0:
        log.info(f"    ⚠ Captions failed: {failed} (rate limit may still be active)")

    return written, state


# ── Module 2.5: Video transcription ──────────────────────────────────────────
def module_fill_voiceovers(state: dict) -> tuple[int, dict]:
    """
    Transcribe pending video obs (50/cycle max) using Whisper + instaloader.
    Uses same 8-hr rate-limit state as captions (same Instagram session).
    Returns (transcribed_count, updated_state).
    """
    # Count pending voiceovers
    pending = 0
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            ct = d.get("content_ref", {}).get("content_type", "")
            if "video" in ct or "reel" in ct:
                vo = d.get("voice_observations") or {}
                if vo.get("voiceover_text") is None:
                    pending += 1
        except Exception:
            pass

    if pending == 0:
        return 0, state

    # Enforce same 8-hr rate limit as captions
    last_attempt = state.get("last_voiceover_attempt")
    fail_count   = state.get("last_voiceover_fail_count", 0)
    if last_attempt and fail_count > 0:
        last_dt = datetime.fromisoformat(last_attempt)
        hrs_elapsed = (datetime.now() - last_dt).total_seconds() / 3600
        if hrs_elapsed < CAPTION_RATE_LIMIT_HRS:
            log.info(f"  Voiceover: rate limit active ({hrs_elapsed:.1f}/{CAPTION_RATE_LIMIT_HRS} hrs), {pending} pending. Skipping.")
            return 0, state

    log.info(f"  Voiceover fill: {pending} pending — running batch of 50")
    rc, stdout, stderr = _run(
        [sys.executable, "scripts/run_video_transcription.py", "--batch", "50"],
        timeout=2400,   # 40-min ceiling: 50 downloads × 4s + Whisper processing
    )

    m_written  = re.search(r"Written\s*:\s*(\d+)", stdout)
    m_failed   = re.search(r"Download failed\s*:\s*(\d+)", stdout)
    transcribed = int(m_written.group(1)) if m_written else 0
    failed      = int(m_failed.group(1)) if m_failed else 0

    state["last_voiceover_attempt"]     = datetime.now().isoformat()
    state["last_voiceover_fail_count"]  = failed

    if transcribed > 0:
        log.info(f"    ✅ Videos transcribed: {transcribed}")
    if failed > 0:
        log.info(f"    ⚠ Download failures: {failed} — may be rate limited")

    return transcribed, state


# ── Module 3: Pattern gap fill ────────────────────────────────────────────────
def module_fill_patterns() -> int:
    """Detect orphaned slugs and generate pattern files. Max 10/cycle."""
    orphaned = get_orphaned_slugs()
    if not orphaned:
        return 0

    log.info(f"  Pattern fill: {len(orphaned)} orphaned slugs")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("  ANTHROPIC_API_KEY not set — skipping pattern generation")
        return 0

    rc, stdout, stderr = _run([
        sys.executable, "scripts/fill_missing_patterns.py",
        "--batch", "100",      # 100 slugs per API call (Batch API handles concurrently)
        "--max-slugs", "200",  # cap per cycle: 2 API calls × ~3-5 min = ~6-10 min
    ], timeout=1200)           # 20-min ceiling — generous for slow Batch API days

    m = re.search(r"Generated (\d+) pattern files", stdout)
    n = int(m.group(1)) if m else 0
    if n > 0:
        log.info(f"    ✅ Patterns generated: {n}")
    return n


# ── Module 4: Chain gap detection + generation ────────────────────────────────
def module_fill_chain_gaps() -> int:
    """Detect underserved content format × sector combos, generate chains."""
    rc, stdout, _ = _run(
        [sys.executable, "scripts/detect_chain_gaps.py"],
        timeout=120,
    )
    if rc != 0:
        return 0

    # Parse JSON from stdout (detect_chain_gaps prints JSON after "--- JSON OUTPUT ---")
    json_match = re.search(r"--- JSON OUTPUT ---\s*(\[.*?\])", stdout, re.DOTALL)
    if not json_match:
        return 0
    try:
        gaps = json.loads(json_match.group(1))
    except Exception:
        return 0

    if not gaps:
        return 0

    top_gap = gaps[0]["gap_id"]
    log.info(f"  Chain gap detected: {top_gap} — generating chains")

    # Generate new chain families to fill the gap
    rc2, stdout2, stderr2 = _run(
        [sys.executable, "scripts/write_new_chain_families.py"],
        timeout=120,
    )
    m = re.search(r"Wrote (\d+) new chain", stdout2)
    n = int(m.group(1)) if m else 0
    if n > 0:
        log.info(f"    ✅ Chains written: {n}")
        return n
    elif rc2 == 0:
        log.info(f"    ℹ No new chains needed (all files already exist)")
    else:
        log.warning(f"    ⚠ Chain generation failed: {stderr2[:200]}")
    return 0


# ── Module 5: Analytics rebuild ───────────────────────────────────────────────
def module_rebuild_analytics() -> bool:
    """Rebuild analytics logs if any obs is newer than the logs."""
    obs_files = list(OBS_ROOT.rglob("*.json"))
    if not obs_files:
        return False

    newest_obs_mtime = max(f.stat().st_mtime for f in obs_files)
    analytics_log = LOGS / "caption_intelligence.json"

    if analytics_log.exists() and newest_obs_mtime <= analytics_log.stat().st_mtime:
        return False  # logs are fresh

    log.info("  Analytics: rebuilding (obs newer than logs)")
    rebuilt_count = 0
    for script in ANALYTICS_SCRIPTS:
        script_path = REPO / "scripts" / script
        if not script_path.exists():
            continue
        rc, _, stderr = _run([sys.executable, f"scripts/{script}"], timeout=300)
        if rc == 0:
            rebuilt_count += 1
        else:
            log.warning(f"    ⚠ {script} failed: {stderr[:100]}")

    if rebuilt_count > 0:
        log.info(f"    ✅ Rebuilt {rebuilt_count} analytics scripts")
    return rebuilt_count > 0


# ── Validation ────────────────────────────────────────────────────────────────
def validate() -> bool:
    rc, stdout, stderr = _run(
        [sys.executable, "scripts/validate_all.py"],
        timeout=300,
    )
    passed = rc == 0 and ("All records valid" in stdout or "PASS" in stdout)
    if not passed:
        log.warning(f"  ❌ Validation FAILED")
        if stdout: log.warning(stdout[-500:])
        if stderr: log.warning(stderr[-200:])
    else:
        log.info("  ✅ Validation passed")
    if passed:
        rc2, stdout2, stderr2 = _run(
            [sys.executable, "scripts/guard_data_quality.py"],
            timeout=300,
        )
        if rc2 != 0:
            log.warning("  ⚠️ Data quality guard found issues (non-blocking)")
            if stdout2: log.warning(stdout2[-500:])
    return passed


# ── Commit + Sync ──────────────────────────────────────────────────────────────
def commit_and_sync(report: dict) -> bool:
    """git add → commit → rsync to Drive → git push. Returns success."""
    msg_parts = []
    if report.get("accounts_extracted"):
        msg_parts.append(f"accounts={report['accounts_extracted']}")
    if report.get("captions_filled"):
        msg_parts.append(f"captions={report['captions_filled']}")
    if report.get("patterns_generated"):
        msg_parts.append(f"patterns={report['patterns_generated']}")
    if report.get("analytics_rebuilt"):
        msg_parts.append("analytics")

    commit_msg = "auto: enricher — " + (", ".join(msg_parts) if msg_parts else "cycle")

    # Stage all changes
    rc_add, _, _ = _run(["git", "add", "-A"])
    if rc_add != 0:
        log.warning("  git add failed")
        return False

    # Commit
    rc_commit, stdout_c, stderr_c = _run(["git", "commit", "-m", commit_msg])
    if rc_commit != 0:
        if "nothing to commit" in stdout_c or "nothing to commit" in stderr_c:
            log.info("  No changes to commit")
            return True
        log.warning(f"  git commit failed: {stderr_c[:200]}")
        return False

    log.info(f"  ✅ Committed: {commit_msg}")

    # Sync to Drive
    drive_str = str(DRIVE_PATH)
    if Path(drive_str).exists():
        rc_sync, _, sync_err = _run([
            "rsync", "-a", "--delete",
            "--exclude=.git", "--exclude=.venv", "--exclude=__pycache__",
            str(REPO) + "/", drive_str + "/",
        ], timeout=300)
        if rc_sync == 0:
            log.info("  ✅ Drive synced")
        else:
            log.warning(f"  ⚠ Drive sync failed: {sync_err[:100]}")
    else:
        log.info(f"  ⏭ Drive path not mounted — skipping sync")

    # Push to GitHub
    rc_push, _, push_err = _run(["git", "push", "origin", "main"], timeout=120)
    if rc_push == 0:
        log.info("  ✅ GitHub pushed")
    else:
        log.warning(f"  ⚠ GitHub push failed: {push_err[:100]}")

    # Sync to local Postgres (if running)
    rc_db, db_out, db_err = _run(
        [sys.executable, "sync_to_supabase.py", "--execute"],
        timeout=300,
    )
    if rc_db == 0:
        log.info("  ✅ Postgres synced")
    else:
        log.info("  ⏭ Postgres sync skipped (DB may not be running)")

    # Update learning analytics (daemon log mining) every 10 cycles
    if cycle_num % 10 == 0:
        _run([sys.executable, "scripts/learning_system.py", "--daemon-analytics", "--work-patterns"], timeout=60)
        log.info("  ✅ Learning analytics updated")

    return True


# ── Telegram report ────────────────────────────────────────────────────────────
def telegram_report(report: dict, cycle_num: int):
    lines = [f"🤖 <b>OGZ Enricher — Cycle {cycle_num}</b>"]
    if report.get("accounts_extracted"):
        lines.append(f"📸 Extracted: {report['accounts_extracted']} obs")
    if report.get("captions_filled"):
        lines.append(f"📝 Captions filled: {report['captions_filled']}")
    if report.get("patterns_generated"):
        lines.append(f"🧩 Patterns generated: {report['patterns_generated']}")
    if report.get("chains_generated"):
        lines.append(f"🔗 Chains generated: {report['chains_generated']}")
    if report.get("analytics_rebuilt"):
        lines.append("📊 Analytics rebuilt")
    lines.append("✅ Validation passed, synced to Drive + GitHub")
    telegram("\n".join(lines))


# ── Main cycle ────────────────────────────────────────────────────────────────
def cycle(state: dict, cycle_num: int) -> dict:
    log.info(f"\n{'='*60}")
    log.info(f"  CYCLE {cycle_num} — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    log.info(f"{'='*60}")

    report = {}

    # 1. Account extraction
    try:
        n = module_extract_accounts()
        if n: report["accounts_extracted"] = n
    except Exception as e:
        log.error(f"  Module 1 error: {e}")

    # 2. Caption fill
    try:
        written, state = module_fill_captions(state)
        if written: report["captions_filled"] = written
    except Exception as e:
        log.error(f"  Module 2 error: {e}")

    # 2.5. Video transcription (50/cycle, rate-limit-aware)
    try:
        transcribed, state = module_fill_voiceovers(state)
        if transcribed: report["videos_transcribed"] = transcribed
    except Exception as e:
        log.error(f"  Module 2.5 error: {e}")

    # 3. Pattern fill
    try:
        n = module_fill_patterns()
        if n: report["patterns_generated"] = n
    except Exception as e:
        log.error(f"  Module 3 error: {e}")

    # 4. Chain gap detection
    try:
        n = module_fill_chain_gaps()
        if n: report["chains_generated"] = n
    except Exception as e:
        log.error(f"  Module 4 error: {e}")

    # 5. Analytics rebuild
    try:
        rebuilt = module_rebuild_analytics()
        if rebuilt: report["analytics_rebuilt"] = True
    except Exception as e:
        log.error(f"  Module 5 error: {e}")

    # 6. Only validate + sync if there were changes
    if report:
        log.info(f"  Changes this cycle: {report}")
        if validate():
            commit_and_sync(report)
            telegram_report(report, cycle_num)
        else:
            log.error("  ❌ Validation failed — rolling back changes")
            telegram(f"⚠️ <b>OGZ Enricher</b> — Cycle {cycle_num} validation FAILED. Changes rolled back. Manual check needed.")
            _run(["git", "checkout", "--", "."])
    else:
        log.info("  No changes this cycle")

    state["last_cycle_at"] = datetime.now().isoformat()
    state["total_cycles"]  = state.get("total_cycles", 0) + 1
    save_state(state)
    return state


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    log.info("🚀 OGZ Enricher daemon started")
    telegram("🤖 <b>OGZ Enricher</b> daemon started. Running every 30 minutes.")

    state     = load_state()
    cycle_num = state.get("total_cycles", 0)

    while True:
        try:
            state = cycle(state, cycle_num)
        except Exception as e:
            log.error(f"Cycle error: {e}")
            telegram(f"⚠️ <b>OGZ Enricher</b> cycle error: {e}")

        cycle_num += 1
        log.info(f"  Sleeping {CYCLE_INTERVAL_SECS//60} min until next cycle...")
        time.sleep(CYCLE_INTERVAL_SECS)


if __name__ == "__main__":
    main()
