#!/usr/bin/env python3
"""Verify Google Drive service account access. Run on Mac after SA key installed."""
from __future__ import annotations

import sys
from pathlib import Path

SA_PATHS = (
    Path.home() / ".config/ogz/google_sa.json",
    Path.home() / ".abraham_env",  # document only — parse GOOGLE_SA_PATH if set
)


def main() -> int:
    for p in SA_PATHS:
        if p.exists():
            print(f"found: {p}")
            print("TODO: implement Drive API list after copying credentials setup from PR 1")
            return 0
    print("No Google SA key found. Install to ~/.config/ogz/google_sa.json")
    print("See data/cursor_missions/artifacts/PROPOSAL_TRACK_PR_PLAN.md PR 1")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
