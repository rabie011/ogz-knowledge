#!/usr/bin/env python3
"""Memory search for agents — scars, history master, knowledge domains."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tokenize(q: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z\u0600-\u06FF]{3,}", q)}


def _score(text: str, tokens: set[str]) -> float:
    if not tokens:
        return 0.0
    low = text.lower()
    return sum(1 for t in tokens if t in low) / len(tokens)


def search_knowledge(query: str, top: int = 5) -> list[dict]:
    tokens = _tokenize(query)
    hits: list[tuple[float, dict]] = []
    base = ROOT / "data/knowledge/indexed"
    if not base.exists():
        return []
    for path in base.glob("**/*.json"):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        blob = json.dumps(doc, ensure_ascii=False)
        s = _score(blob, tokens)
        if s > 0:
            hits.append((s, {"source": "knowledge", "path": str(path.relative_to(ROOT)), **doc}))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:top]]


def search_scars(query: str, top: int = 5) -> list[dict]:
    tokens = _tokenize(query)
    reg = ROOT / "data/mistake_registry.jsonl"
    if not reg.exists():
        return []
    hits = []
    for line in reg.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except Exception:
            continue
        s = _score(json.dumps(doc), tokens)
        if s > 0 or not tokens:
            hits.append((s, {"source": "mistake_registry", **doc}))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:top]]


def search_history(query: str, top: int = 3) -> list[dict]:
    master = ROOT / "data/cursor_missions/done/claude-code-history-master.json"
    if not master.exists():
        return []
    try:
        doc = json.loads(master.read_text(encoding="utf-8"))
    except Exception:
        return []
    blob = json.dumps(doc, ensure_ascii=False)
    if _score(blob, _tokenize(query)) > 0 or not query:
        return [{"source": "claude_history", "keys": list(doc.keys()), "commits": doc.get("commits_by_month")}]
    return []


def search(query: str, top: int = 8) -> dict:
    return {
        "query": query,
        "knowledge": search_knowledge(query, top),
        "scars": search_scars(query, min(5, top)),
        "history": search_history(query, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = search(args.query, args.top)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Query: {args.query}\n")
        for section in ("knowledge", "scars", "history"):
            items = result.get(section, [])
            print(f"## {section} ({len(items)})")
            for item in items:
                title = item.get("title") or item.get("scar_class") or item.get("source")
                print(f"  - {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
