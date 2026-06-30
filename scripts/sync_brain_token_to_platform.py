#!/usr/bin/env python3
"""Sync BRAIN_API_TOKEN from ~/.abraham_env to ~/ogz-platform/.env.local"""
from __future__ import annotations

import re
from pathlib import Path

ENV = Path.home() / ".abraham_env"
PLATFORM = Path.home() / "ogz-platform" / ".env.local"


def main() -> int:
    token = ""
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            if line.startswith("BRAIN_API_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"')
                break
    if not token:
        print("missing BRAIN_API_TOKEN in ~/.abraham_env")
        return 1
    if not PLATFORM.exists():
        print(f"missing {PLATFORM}")
        return 1
    text = PLATFORM.read_text()
    if re.search(r"^BRAIN_API_TOKEN=", text, flags=re.M):
        text = re.sub(r"^BRAIN_API_TOKEN=.*$", f"BRAIN_API_TOKEN={token}", text, flags=re.M)
    else:
        text = text.rstrip() + f"\nBRAIN_API_TOKEN={token}\n"
    PLATFORM.write_text(text)
    print("synced BRAIN_API_TOKEN to ogz-platform/.env.local")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
