#!/usr/bin/env python3
"""Mac → GitHub status bridge for Cursor mobile.

Run ON THE MAC MINI. Refreshes unified_status, records sync metadata,
optionally commits and pushes so cloud agents read live Mac truth.

  python3 scripts/mac_sync.py           # local refresh only
  python3 scripts/mac_sync.py --push    # commit + push status files
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAC_STATUS = ROOT / "data/mac_status"
SYNC_META = MAC_STATUS / "sync_meta.json"
PYTHON = os.environ.get("OGZ_PYTHON", "/opt/homebrew/bin/python3")
if not Path(PYTHON).exists():
    PYTHON = sys.executable

TRACKED = (
    "data/unified_status.txt",
    "data/unified_status.json",
    "data/mac_status/sync_meta.json",
    "data/mac_status/latest.txt",
    "data/cursor_missions/artifacts/validate_stack.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out.strip()
    except Exception as e:
        return 1, str(e)


def _git_sha() -> str:
    rc, out = _run(["git", "rev-parse", "--short", "HEAD"])
    return out if rc == 0 else "unknown"


def _launchctl_summary() -> dict[str, str]:
    launchctl = shutil.which("launchctl")
    if not launchctl:
        return {"note": "not macOS"}
    labels = (
        "com.ogz.brain-api",
        "com.ogz.mac-sync",
        "com.ogz.executor",
        "com.ogz.consult-shift",
        "com.ogz.memory-keeper",
        "com.ogz.orchestra",
    )
    out: dict[str, str] = {}
    for label in labels:
        rc, _ = _run([launchctl, "list", label])
        out[label] = "loaded" if rc == 0 else "unloaded"
    return out


def _current_branch() -> str:
    rc, out = _run(["git", "branch", "--show-current"])
    branch = out.strip() if rc == 0 else ""
    if branch:
        return branch
    return os.environ.get("OGZ_GIT_BRANCH", "main")


def _git_pull() -> dict:
    branch = _current_branch()
    rc_f, out_f = _run(["git", "fetch", "origin", branch])
    rc, out = _run(["git", "rebase", f"origin/{branch}"])
    detail = ((out_f or "") + "\n" + (out or "")).strip()[:500]
    return {"ok": rc_f == 0 and rc == 0, "detail": detail, "branch": branch}


def refresh_status() -> dict:
    MAC_STATUS.mkdir(parents=True, exist_ok=True)
    rc_status, _ = _run([PYTHON, str(ROOT / "scripts/unified_status.py"), "--plain"])
    rc_val, val_out = _run([PYTHON, str(ROOT / "scripts/validate_stack.py")])

    plain_path = ROOT / "data/unified_status.txt"
    latest = MAC_STATUS / "latest.txt"
    if plain_path.exists():
        latest.write_text(plain_path.read_text(encoding="utf-8"), encoding="utf-8")

    meta = {
        "ts": _now(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "git_sha": _git_sha(),
        "unified_status_rc": rc_status,
        "validate_stack_rc": rc_val,
        "launchagents": _launchctl_summary(),
        "pull": _git_pull(),
    }
    SYNC_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def push_status(meta: dict) -> dict:
    env_push = os.environ.get("MAC_SYNC_PUSH", "").strip() in ("1", "true", "yes")
    paths = [ROOT / p for p in TRACKED if (ROOT / p).exists()]
    if not paths:
        return {"ok": False, "detail": "no status files to push"}

    _run(["git", "add", *TRACKED])
    rc, diff = _run(["git", "diff", "--cached", "--quiet"])
    if rc == 0:
        return {"ok": True, "detail": "nothing to commit", "skipped": True}

    msg = f"mac-sync: status snapshot {meta.get('ts', '')[:19]}"
    rc, out = _run(["git", "commit", "-m", msg])
    if rc != 0:
        return {"ok": False, "detail": out[:500]}

    if not env_push:
        return {
            "ok": True,
            "detail": "committed locally — set MAC_SYNC_PUSH=1 or use --push to git push",
            "committed": True,
        }

    rc, out = _run(["git", "push", "origin", "HEAD"])
    return {"ok": rc == 0, "detail": out[:500], "pushed": rc == 0}


def main() -> int:
    ap = argparse.ArgumentParser(description="Mac status sync for Cursor mobile")
    ap.add_argument("--push", action="store_true", help="Commit and push status files to origin")
    ap.add_argument("--no-pull", action="store_true", help="Skip git pull before refresh")
    args = ap.parse_args()

    if args.push:
        os.environ["MAC_SYNC_PUSH"] = "1"

    if not args.no_pull:
        _git_pull()

    meta = refresh_status()
    result = {"refresh": meta}

    if args.push or os.environ.get("MAC_SYNC_PUSH", "").strip() in ("1", "true", "yes"):
        result["push"] = push_status(meta)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    push_ok = result.get("push", {}).get("ok", True)
    return 0 if push_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
