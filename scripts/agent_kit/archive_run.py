#!/usr/bin/env python3
"""Archive one agent run to ~/OGZ-Archive/agents/{AGENT_ID}/{date}_{run_ulid}/."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/agent_kit/registry.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive agent run to Mac OGZ-Archive")
    ap.add_argument("--agent", required=True)
    ap.add_argument("--run-ulid", required=True)
    ap.add_argument("--from-dir", required=True, help="Run folder to archive")
    ap.add_argument("--client", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--drive-folder-id", default="")
    args = ap.parse_args()

    if not REGISTRY.exists():
        raise SystemExit(f"missing registry: {REGISTRY}")

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    archive_root = Path(reg.get("mac_archive_root", "~/OGZ-Archive/agents")).expanduser()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest = archive_root / args.agent.upper() / f"{day}_{args.run_ulid}"
    src = Path(args.from_dir).expanduser()

    if not src.is_dir():
        print(f"source not found: {src}", file=sys.stderr)
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    manifest = {
        "agent_id": args.agent.upper(),
        "run_ulid": args.run_ulid,
        "client_slug": args.client or None,
        "archived_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_dir": str(src),
        "mac_archive_path": str(dest),
        "drive_folder_id": args.drive_folder_id or None,
        "summary": args.summary,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({"ok": True, "archive_path": str(dest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
