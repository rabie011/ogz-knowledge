#!/usr/bin/env python3
"""
apply_brain_proposals.py — STUB applier for BRAIN_UPDATE_PROPOSALS.md

This script reads approved proposals from logs/system/BRAIN_UPDATE_PROPOSALS.md
and prints exactly what it would write to intelligence_layer.json.

It does NOT write anything until Mohamed explicitly passes --confirm.

Usage:
    python3 scripts/apply_brain_proposals.py --dry-run 001      # show what 001 would do
    python3 scripts/apply_brain_proposals.py --apply 001        # apply 001 (still previews first)
    python3 scripts/apply_brain_proposals.py --apply-all        # apply all APPROVED proposals
    python3 scripts/apply_brain_proposals.py --list             # list all proposals + status

IMPORTANT: This script NEVER auto-applies. It prints the diff, pauses, and waits
for a y/n confirmation unless --yes is passed explicitly.
"""

import json
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone


BASE            = Path(__file__).parent.parent
BRAIN_FILE      = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
PROPOSALS_FILE  = BASE / "logs" / "system" / "BRAIN_UPDATE_PROPOSALS.md"


# ─── Proposal Parser ──────────────────────────────────────────────────────────

def parse_proposals(md_text: str) -> list[dict]:
    """
    Parse BRAIN_UPDATE_PROPOSALS.md into a list of proposal dicts.
    Each proposal has: id, label, category, status, proposed_action, path_in_brain.
    """
    proposals = []
    # Split on ## PROPOSAL headings
    sections = re.split(r"^## PROPOSAL ", md_text, flags=re.MULTILINE)
    for section in sections[1:]:   # skip preamble
        lines = section.splitlines()
        header = lines[0] if lines else ""
        id_match = re.match(r"^(\d+)\s+[—–-]\s+(.+?)(?:\s*\[.+?\])?$", header)
        if not id_match:
            continue
        prop_id   = id_match.group(1).zfill(3)
        label     = id_match.group(2).strip()
        category  = ""
        status    = "PENDING"
        path      = ""
        action    = ""

        for line in lines:
            if line.startswith("**Category:**"):
                m = re.search(r"`([^`]+)`", line)
                category = m.group(1) if m else ""
            elif line.startswith("**Brain path:**"):
                m = re.search(r"`([^`]+)`", line)
                path = m.group(1) if m else ""
            elif line.startswith("**Status:**"):
                m = re.search(r"`\[([^\]]+)\]`", line)
                status = m.group(1) if m else "PENDING"
            elif line.startswith("> ") and not action:
                # First blockquote after "Proposed change:" is the action
                action = line[2:].strip()

        proposals.append({
            "id": prop_id,
            "label": label,
            "category": category,
            "path_in_brain": path,
            "proposed_action": action,
            "status": status,
        })
    return proposals


def load_proposals() -> list[dict]:
    if not PROPOSALS_FILE.exists():
        print(f"[ERROR] Proposals file not found: {PROPOSALS_FILE}")
        print("Run brain_update_from_learning.py first to generate proposals.")
        sys.exit(1)
    return parse_proposals(PROPOSALS_FILE.read_text(encoding="utf-8"))


# ─── Preview / Diff Printer ───────────────────────────────────────────────────

def preview_proposal(proposal: dict) -> None:
    """Print what applying this proposal would do — no writes."""
    SEP = "─" * 62
    print(SEP)
    print(f"  PROPOSAL {proposal['id']} — {proposal['label']}")
    print(SEP)
    print(f"  Category   : {proposal['category']}")
    print(f"  Brain path : {proposal['path_in_brain']}")
    print(f"  Status     : {proposal['status']}")
    print()
    print(f"  WHAT WOULD HAPPEN:")
    print(f"  {proposal['proposed_action']}")
    print()
    print(f"  TARGET FILE: {BRAIN_FILE.relative_to(BASE)}")
    print()
    print("  [STUB] No write will occur until this script is fully implemented.")
    print("  After Mohamed approves a proposal, a developer implements the")
    print("  specific JSON mutation here and adds a confirmation checkpoint.")
    print(SEP)


# ─── Apply (Confirmation Gate) ────────────────────────────────────────────────

def apply_proposal(proposal: dict, yes: bool = False) -> None:
    """Preview, confirm, then (stub) apply a single proposal."""
    preview_proposal(proposal)

    if proposal["status"] not in ("APPROVED", "PENDING Mohamed approval"):
        print(f"[SKIP] Proposal {proposal['id']} status is '{proposal['status']}' — skipping.")
        return

    if not yes:
        try:
            answer = input("Apply this proposal? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[CANCELLED]")
            return
        if answer != "y":
            print("[CANCELLED]")
            return

    # ── Stub: actual implementation goes here per proposal category ──────────
    # When a real implementation is ready, replace this block with:
    #
    #   brain = json.loads(BRAIN_FILE.read_text())
    #   _apply_<category>(brain, proposal)
    #   backup = BRAIN_FILE.with_suffix('.json.bak')
    #   backup.write_text(BRAIN_FILE.read_text())
    #   BRAIN_FILE.write_text(json.dumps(brain, ensure_ascii=False, indent=2))
    #   print(f"[APPLIED] {proposal['id']} — backup at {backup.name}")
    #
    print(f"[STUB] Would apply proposal {proposal['id']} to {BRAIN_FILE.name}")
    print(f"       Backup would be written to intelligence_layer.json.bak")
    print(f"       Actual JSON mutation is not yet implemented for category: {proposal['category']}")
    print()
    print("  To implement: edit apply_brain_proposals.py and add a")
    print(f"  _apply_{proposal['category']}(brain, proposal) function.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Preview and apply BRAIN_UPDATE_PROPOSALS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--list",       action="store_true", help="List all proposals and their status")
    parser.add_argument("--dry-run",    metavar="ID",        help="Preview a proposal without applying")
    parser.add_argument("--apply",      metavar="ID",        help="Preview then apply a specific proposal")
    parser.add_argument("--apply-all",  action="store_true", help="Apply all APPROVED proposals")
    parser.add_argument("--yes",        action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    proposals = load_proposals()
    if not proposals:
        print("[INFO] No proposals found in proposals file.")
        return

    if args.list:
        print(f"{'ID':>4}  {'Status':35}  Label")
        print(f"{'─'*4}  {'─'*35}  {'─'*40}")
        for p in proposals:
            print(f"  {p['id']:>3}  {p['status']:35}  {p['label']}")
        return

    if args.dry_run:
        target = next((p for p in proposals if p["id"] == args.dry_run.zfill(3)), None)
        if not target:
            print(f"[ERROR] Proposal {args.dry_run} not found.")
            sys.exit(1)
        preview_proposal(target)
        return

    if args.apply:
        target = next((p for p in proposals if p["id"] == args.apply.zfill(3)), None)
        if not target:
            print(f"[ERROR] Proposal {args.apply} not found.")
            sys.exit(1)
        apply_proposal(target, yes=args.yes)
        return

    if args.apply_all:
        approved = [p for p in proposals if "APPROVED" in p["status"]]
        if not approved:
            print("[INFO] No proposals with APPROVED status. Mark proposals as APPROVED in the file first.")
            return
        print(f"Applying {len(approved)} approved proposal(s)...")
        for p in approved:
            apply_proposal(p, yes=args.yes)
        return

    # Default: show usage
    parser.print_help()


if __name__ == "__main__":
    main()
