#!/usr/bin/env python3
"""GENERATION FATIGUE + MOMENT ROTATION (ARMOR PORT steps 4-5, June 12).
The renderer's G9-lite catchphrase killer and date-hashed moment rotation,
extracted as a module so the 41-brand API and tests share ONE implementation.
"The pen develops catchphrases" at API scale = a template farm; this is the killer.
"""
import collections, datetime, hashlib, json, re
from pathlib import Path

GEN_LOG = Path(__file__).parent.parent / "logs/generation_log.jsonl"


def append_generation(brand: str, occasion: str, captions: list[str], gen: str = "v6",
                      log_path: Path = None):
    p = log_path or GEN_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps({"brand": brand, "occasion": occasion,
                             "captions": [c for c in captions if c], "gen": gen,
                             "ts": datetime.datetime.now().isoformat(timespec="seconds")},
                            ensure_ascii=False) + "\n")


def worn_grams(brand: str, log_path: Path = None) -> list[str]:
    """Worn 3-grams from this brand's recent 20 generations (same thresholds as the
    renderer's G9-lite: needs >=5 generations, gram in >=25% of them, min 3)."""
    p = log_path or GEN_LOG
    if not p.exists():
        return []
    recent = []
    for l in p.read_text().strip().split("\n")[-400:]:
        try:
            e = json.loads(l)
        except Exception:
            continue
        if e.get("brand") == brand:
            recent.append(e)
    recent = recent[-20:]
    grams = collections.Counter()
    for e in recent:
        seen_in_entry = set()
        for cap in e.get("captions", []):
            w = re.sub(r"[^؀-ۿ\s]", " ", cap).split()
            for j in range(len(w) - 2):
                seen_in_entry.add(" ".join(w[j:j + 3]))
        for g in seen_in_entry:
            grams[g] += 1
    return [g for g, c in grams.most_common(8)
            if len(recent) >= 5 and c >= max(3, len(recent) * 0.25)]


def rotate_moments(brand: str, moments: list[str], k: int = 3, day: str = None) -> list[str]:
    """Date-hashed rotation — same brand+day = same window (stable within a day,
    different across days). Static moments[:3] at API scale = every call, same scene."""
    if not moments:
        return []
    day = day or str(datetime.date.today())
    off = int(hashlib.md5(f"{brand}{day}".encode()).hexdigest(), 16) % len(moments)
    return [moments[(off + i) % len(moments)] for i in range(min(k, len(moments)))]
