#!/usr/bin/env python3
"""SEARCH agent v1 — collect domain facts from curated sources into knowledge/raw/."""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/knowledge/raw"

# Curated seed sources per domain (no random web crawl)
DOMAIN_SOURCES: dict[str, list[dict]] = {
    "cinematography": [
        {"title": "Three-point lighting", "url": "https://en.wikipedia.org/wiki/Three-point_lighting"},
        {"title": "Cinematography basics", "url": "https://en.wikipedia.org/wiki/Cinematography"},
        {"title": "Color grading", "url": "https://en.wikipedia.org/wiki/Color_grading"},
        {"title": "Depth of field", "url": "https://en.wikipedia.org/wiki/Depth_of_field"},
        {"title": "Rule of thirds", "url": "https://en.wikipedia.org/wiki/Rule_of_thirds"},
        {"title": "Aspect ratio film", "url": "https://en.wikipedia.org/wiki/Aspect_ratio_(image)"},
        {"title": "Camera angle", "url": "https://en.wikipedia.org/wiki/Camera_angle"},
        {"title": "Golden hour photography", "url": "https://en.wikipedia.org/wiki/Golden_hour_(photography)"},
        {"title": "High-key lighting", "url": "https://en.wikipedia.org/wiki/High-key_lighting"},
        {"title": "Low-key lighting", "url": "https://en.wikipedia.org/wiki/Low-key_lighting"},
    ],
    "filmmaking": [
        {"title": "Film editing", "url": "https://en.wikipedia.org/wiki/Film_editing"},
        {"title": "Storyboard", "url": "https://en.wikipedia.org/wiki/Storyboard"},
        {"title": "Shot reverse shot", "url": "https://en.wikipedia.org/wiki/Shot_reverse_shot"},
        {"title": "Montage", "url": "https://en.wikipedia.org/wiki/Montage_(filmmaking)"},
        {"title": "B-roll", "url": "https://en.wikipedia.org/wiki/B-roll"},
    ],
    "saudi_ad_culture": [
        {"title": "Advertising in Saudi Arabia", "url": "https://en.wikipedia.org/wiki/Advertising"},
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def _fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "OGZ-SearchAgent/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        html = r.read().decode("utf-8", errors="replace")
    # crude extract first paragraphs from wiki
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
    chunks = []
    for p in paras[:8]:
        t = unescape(re.sub(r"<[^>]+>", " ", p))
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 80:
            chunks.append(t)
    return "\n\n".join(chunks)[:4000]


def collect(domain: str, limit: int = 10) -> list[Path]:
    sources = DOMAIN_SOURCES.get(domain, [])
    if not sources:
        raise SystemExit(f"unknown domain: {domain}. Known: {', '.join(DOMAIN_SOURCES)}")
    out_dir = RAW / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for src in sources[:limit]:
        slug = _slug(src["title"])
        path = out_dir / f"{slug}.json"
        if path.exists():
            written.append(path)
            continue
        try:
            body = _fetch_text(src["url"])
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            body = f"(fetch failed: {e})"
        doc = {
            "domain": domain,
            "title": src["title"],
            "url": src["url"],
            "fetched_at": _now(),
            "agent": "SEARCH",
            "status": "raw",
            "excerpt": body,
        }
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    paths = collect(args.domain, args.limit)
    print(json.dumps({"domain": args.domain, "collected": len(paths), "files": [str(p) for p in paths]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
