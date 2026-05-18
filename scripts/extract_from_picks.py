#!/usr/bin/env python3
"""
Build an extraction queue from picks files and inbox content.

Usage:
  python3 scripts/extract_from_picks.py --sector f_and_b --queue-only
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PICKS_DIR = REPO_ROOT / "11_who_to_learn_from" / "source_library" / "my_picks"
INBOX_DIR = REPO_ROOT / "11_who_to_learn_from" / "_inbox"
QUEUE_PATH = REPO_ROOT / "11_who_to_learn_from" / "_extraction_queue.json"

CONTENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".gif"}


def load_picks(sector: str) -> list[dict]:
    """Load all picks for a sector from my_picks/*.yaml."""
    all_picks: list[dict] = []
    for fp in PICKS_DIR.glob("*.yaml"):
        if fp.name == "MY_PICKS_TEMPLATE.yaml":
            continue
        with open(fp) as f:
            data = yaml.safe_load(f)
        if data is None:
            continue
        file_sector = data.get("sector")
        if file_sector != sector:
            continue
        for pick in data.get("picks", []):
            pick["_source_file"] = fp.name
            pick["_region_focus"] = data.get("region_focus")
            all_picks.append(pick)
    return all_picks


def scan_inbox(handle: str) -> list[dict]:
    """Find content files in _inbox/@handle/."""
    handle_dir = INBOX_DIR / handle
    if not handle_dir.exists():
        return []
    items = []
    for fp in sorted(handle_dir.iterdir()):
        if fp.suffix.lower() in CONTENT_EXTENSIONS and not fp.name.startswith("."):
            items.append({
                "filename": fp.name,
                "path": str(fp.relative_to(REPO_ROOT)),
                "status": "pending",
            })
    return items


def build_queue(sector: str) -> dict:
    """Build the full extraction queue for a sector."""
    picks = load_picks(sector)
    accounts = []
    total_items = 0

    for pick in picks:
        handle = pick.get("handle", "")
        inbox_items = scan_inbox(handle)
        total_items += len(inbox_items)
        accounts.append({
            "handle": handle,
            "platform": pick.get("platform", "instagram"),
            "tier": pick.get("tier"),
            "what_to_watch": pick.get("what_to_watch"),
            "red_flags": pick.get("red_flags"),
            "items": inbox_items,
        })

    return {
        "queue_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sector": sector,
        "total_accounts": len(accounts),
        "total_items": total_items,
        "accounts": accounts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build extraction queue from picks + inbox.")
    parser.add_argument("--sector", required=True, help="Sector slug (e.g. f_and_b)")
    parser.add_argument("--queue-only", action="store_true", help="Build queue and print summary only")
    args = parser.parse_args()

    queue = build_queue(args.sector)

    if queue["total_accounts"] == 0:
        print(f"No picks found for sector '{args.sector}'.")
        print(f"Create a picks file at: {PICKS_DIR}/{args.sector}.yaml")
        print(f"(Copy MY_PICKS_TEMPLATE.yaml and fill it in.)")
        return 0

    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    print(f"Queue written to: {QUEUE_PATH.relative_to(REPO_ROOT)}")

    print(f"\nSector: {args.sector}")
    print(f"Accounts: {queue['total_accounts']}")
    print(f"Content items: {queue['total_items']}")
    print()

    for acct in queue["accounts"]:
        handle = acct["handle"]
        tier = acct["tier"]
        count = len(acct["items"])
        status = f"{count} items" if count > 0 else "NO CONTENT — download to _inbox/{handle}/"
        print(f"  [{tier}] {handle}: {status}")

    if args.queue_only:
        return 0

    if queue["total_items"] == 0:
        print("\nNo content files found in _inbox/.")
        print("Download content for each account, then re-run.")
        return 0

    print("\nQueue ready. Run Claude Code with:")
    print("  Read CLAUDE.md completely.")
    print("  Read EXTRACTION_PROMPT_FOR_CLAUDE_CODE.md.")
    print(f"  Process the extraction queue at 11_who_to_learn_from/_extraction_queue.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
