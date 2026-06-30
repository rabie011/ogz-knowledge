#!/usr/bin/env python3
"""LaunchAgent entry for brain_api — loads ~/.abraham_env, owns :4140."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("BRAIN_API_PORT", "4140"))
ENV_FILE = Path.home() / ".abraham_env"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))


def clear_port() -> None:
    try:
        out = subprocess.check_output(["lsof", "-ti", f":{PORT}"], text=True).strip()
        if out:
            for pid in out.splitlines():
                subprocess.run(["kill", pid], check=False)
            import time
            time.sleep(1)
    except subprocess.CalledProcessError:
        pass


def main() -> int:
    load_env()
    clear_port()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT / "scripts"))
    # Run in-process (KeepAlive expects this process to stay up)
    import brain_api  # noqa: WPS433

    brain_api.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
