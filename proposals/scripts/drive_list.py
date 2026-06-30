#!/usr/bin/env python3
"""List Drive folders — Amira templates + quotations. Stub until PR 1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "drive_manifest.json"


def main() -> int:
    print("TODO: implement after Google SA configured")
    print(f"Output will be: {OUT}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
