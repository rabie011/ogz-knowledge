#!/usr/bin/env python3
"""
health_check.py
OGZ Knowledge Base — automated health check.
Runs every 30 min via Claude CronCreate.
Sends Telegram alert if anything is wrong.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"
LOGS        = BASE / "logs"

# Telegram config from ~/.abraham_env
def _load_env():
    env_path = Path.home() / ".abraham_env"
    cfg = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

def _send_telegram(token: str, chat_id: str, text: str):
    import urllib.request, urllib.parse
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=10)
    except Exception as e:
        print(f"  [Telegram error] {e}")


def run_validation() -> tuple[bool, str]:
    """Run validate_all.py, return (passed, summary_line)."""
    result = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "validate_all.py")],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    # Look for the summary line
    for line in output.splitlines():
        if "valid" in line.lower() or "error" in line.lower() or "invalid" in line.lower():
            return result.returncode == 0, line.strip()
    return result.returncode == 0, output.strip()[-120:]


def check_obs_count() -> tuple[int, int, int]:
    """Return (total, accounts, sectors)."""
    obs_files = list(OBS_ROOT.rglob("*.json"))
    accounts  = set()
    sectors   = set()
    for f in obs_files:
        try:
            d = json.loads(f.read_text())
            accounts.add(d.get("account_handle_normalized", ""))
            sectors.add(d.get("sector", ""))
        except Exception:
            pass
    return len(obs_files), len(accounts), len(sectors)


def check_git() -> tuple[bool, str]:
    """Return (clean, status_summary)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(BASE), "status", "--short", "--untracked-files=no"],
            capture_output=True, text=True, timeout=10
        )
        dirty = r.stdout.strip()
        if dirty:
            lines = dirty.splitlines()
            return False, f"{len(lines)} uncommitted change(s)"
        # Check how far ahead/behind from origin
        r2 = subprocess.run(
            ["git", "-C", str(BASE), "log", "origin/main..HEAD", "--oneline"],
            capture_output=True, text=True, timeout=10
        )
        unpushed = r2.stdout.strip().splitlines()
        if unpushed:
            return False, f"{len(unpushed)} unpushed commit(s)"
        return True, "clean & synced"
    except Exception as e:
        return False, str(e)


def check_schema() -> tuple[bool, str]:
    """Schema file readable and valid JSON."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
        fields = list(schema.get("properties", {}).keys())
        return True, f"OK ({len(fields)} top-level props)"
    except Exception as e:
        return False, str(e)


def check_key_logs() -> list[str]:
    """Check that key log files exist and are non-empty."""
    key_logs = [
        "occasion_playbook.json",
        "visual_decision_tree.json",
        "caption_intelligence_by_sector.json",
        "arabic_copywriting_by_sector.json",
        "video_audio_analysis.json",
        "winning_formula_analysis.json",
    ]
    missing = []
    for name in key_logs:
        p = LOGS / name
        if not p.exists() or p.stat().st_size < 100:
            missing.append(name)
    return missing


def main():
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    issues = []
    lines  = []

    lines.append(f"🕐 *OGZ Health Check* — {now}")
    lines.append("")

    # 1. Validation
    val_ok, val_msg = run_validation()
    status = "✅" if val_ok else "❌"
    lines.append(f"{status} *Validation:* {val_msg}")
    if not val_ok:
        issues.append(f"Validation failed: {val_msg}")

    # 2. Obs count
    total, accounts, sectors = check_obs_count()
    lines.append(f"✅ *Obs:* {total} | Accounts: {accounts} | Sectors: {sectors}")

    # 3. Git
    git_ok, git_msg = check_git()
    status = "✅" if git_ok else "⚠️"
    lines.append(f"{status} *Git:* {git_msg}")
    if not git_ok:
        issues.append(f"Git: {git_msg}")

    # 4. Schema
    schema_ok, schema_msg = check_schema()
    status = "✅" if schema_ok else "❌"
    lines.append(f"{status} *Schema:* {schema_msg}")
    if not schema_ok:
        issues.append(f"Schema: {schema_msg}")

    # 5. Embedding drift
    emb_idx = LOGS / "obs_search_index.json"
    if emb_idx.exists():
        import json as _json
        emb_count = len(_json.loads(emb_idx.read_text()))
        gap = total - emb_count
        gap_pct = 100 * gap / total if total else 0
        if gap_pct > 5:
            lines.append(f"⚠️ *Embedding drift:* {emb_count}/{total} embedded ({gap_pct:.0f}% gap)")
            issues.append(f"Embedding drift: {gap} obs not embedded ({gap_pct:.0f}%)")
        else:
            lines.append(f"✅ *Embeddings:* {emb_count}/{total}")
    else:
        lines.append("⚠️ *Embeddings:* index file missing")
        issues.append("Embedding index missing")

    # 6. Key logs
    missing_logs = check_key_logs()
    if missing_logs:
        lines.append(f"⚠️ *Missing logs:* {', '.join(missing_logs)}")
        issues.append(f"Missing logs: {', '.join(missing_logs)}")
    else:
        lines.append(f"✅ *Analytics logs:* all present")

    lines.append("")
    if issues:
        lines.append(f"🚨 *{len(issues)} issue(s) detected — action needed*")
    else:
        lines.append("✅ *All systems OK*")

    report = "\n".join(lines)
    print(report)

    # Send Telegram ONLY if there are issues (to avoid spam)
    env = _load_env()
    token   = env.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")

    if issues and token and chat_id:
        _send_telegram(token, chat_id, report)
        print("\n  ⚡ Alert sent to Telegram.")
    elif not token:
        print("\n  [No Telegram token — skipping notification]")

    # Save report to logs
    LOGS.mkdir(exist_ok=True)
    report_path = LOGS / "health_check_last.json"
    report_path.write_text(json.dumps({
        "timestamp":    now,
        "obs_total":    total,
        "accounts":     accounts,
        "sectors":      sectors,
        "validation":   val_ok,
        "git_clean":    git_ok,
        "schema_ok":    schema_ok,
        "missing_logs": missing_logs,
        "issues":       issues,
        "healthy":      len(issues) == 0,
    }, ensure_ascii=False, indent=2))

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
