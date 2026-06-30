#!/usr/bin/env python3
"""LEARNER — move raw knowledge to staged, then index into domains/."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/knowledge/raw"
STAGED = ROOT / "data/knowledge/staged"
INDEXED = ROOT / "data/knowledge/indexed"
DOMAINS = ROOT / "data/knowledge/domains"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def _keywords(text: str, n: int = 12) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    stop = {"that", "this", "with", "from", "have", "been", "were", "their", "which", "also", "used"}
    freq: dict[str, int] = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:n]]


def stage_domain(domain: str) -> int:
    raw_dir = RAW / domain
    if not raw_dir.exists():
        return 0
    staged_dir = STAGED / domain
    staged_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for src in raw_dir.glob("*.json"):
        doc = json.loads(src.read_text(encoding="utf-8"))
        if doc.get("status") == "staged":
            continue
        excerpt = doc.get("excerpt", "")
        if excerpt.startswith("(fetch failed"):
            continue
        staged = {
            **doc,
            "status": "staged",
            "staged_at": _now(),
            "keywords": _keywords(excerpt),
            "summary": excerpt[:400] + ("…" if len(excerpt) > 400 else ""),
        }
        out = staged_dir / src.name
        out.write_text(json.dumps(staged, indent=2, ensure_ascii=False), encoding="utf-8")
        doc["status"] = "staged"
        src.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        count += 1
    return count


def index_domain(domain: str) -> int:
    staged_dir = STAGED / domain
    if not staged_dir.exists():
        return 0
    idx_dir = INDEXED / domain
    dom_dir = DOMAINS / domain
    idx_dir.mkdir(parents=True, exist_ok=True)
    dom_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    count = 0
    for src in staged_dir.glob("*.json"):
        doc = json.loads(src.read_text(encoding="utf-8"))
        card = {
            "id": _slug(doc.get("title", src.stem)),
            "domain": domain,
            "title": doc.get("title"),
            "url": doc.get("url"),
            "keywords": doc.get("keywords", []),
            "summary": doc.get("summary", ""),
            "indexed_at": _now(),
        }
        out = idx_dir / f"{card['id']}.json"
        out.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
        cards.append(card)
        count += 1
    manifest = {"domain": domain, "updated": _now(), "count": len(cards), "cards": cards}
    (dom_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--stage-only", action="store_true")
    ap.add_argument("--index-only", action="store_true")
    args = ap.parse_args()
    staged = 0 if args.index_only else stage_domain(args.domain)
    indexed = 0 if args.stage_only else index_domain(args.domain)
    print(json.dumps({"domain": args.domain, "staged": staged, "indexed": indexed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
