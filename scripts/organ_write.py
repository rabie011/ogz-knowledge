#!/usr/bin/env python3
"""ONE WRITE PATH — versioned organ writes (B115, June 12, Immune System).
Born from the phantom-commit scar: discipline isn't armor. Every curated-organ
write now goes through here — the old version is copied to .versions/ FIRST,
then the new content lands via tmp+atomic-rename (a crash mid-write can never
leave a half-file). Nothing is ever deleted; every historical version stays.

Usage:
    from organ_write import write_organ
    write_organ(path, obj)            # dict → versioned atomic JSON write
"""
import datetime, json, os, shutil
from pathlib import Path


def write_organ(path, obj) -> str | None:
    """Returns the version-backup path (None on first write)."""
    p = Path(path)
    backup = None
    if p.exists():
        vdir = p.parent / ".versions"
        vdir.mkdir(exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
        backup = vdir / f"{p.stem}.{ts}.json"
        shutil.copy2(p, backup)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    os.replace(tmp, p)                  # atomic on POSIX
    return str(backup) if backup else None
