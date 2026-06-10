#!/usr/bin/env python3
"""Pattern → engagement evidence join (L3.9, June 11).
Makes the pattern library PREDICTIVE: for every pattern slug observed in the 6,888
observations, compute per-sector engagement evidence (n, engagement score, high-share,
CTA and emoji correlation). Side-file output (schema-safe, no pattern-file mutation):
logs/pattern_engagement_evidence.json
"""
import json, glob
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent.parent
ENG = {"high": 3, "medium": 2, "low": 1}


def main():
    agg = defaultdict(lambda: defaultdict(lambda: {"n": 0, "eng_sum": 0, "eng_n": 0,
                                                     "high": 0, "cta": 0, "emoji": 0}))
    total_obs = 0
    for f in glob.glob(str(BASE / "11_who_to_learn_from/observations/*/*.json")):
        try:
            d = json.loads(open(f).read())
        except Exception:
            continue
        total_obs += 1
        sector = d.get("sector", "?")
        qa = d.get("quality_assessment") or {}
        eng = ENG.get(str(qa.get("engagement_potential", "")).lower())
        vo = d.get("voice_observations") or {}
        cta = bool(vo.get("call_to_action_present"))
        emoji = bool(vo.get("has_emoji"))
        for pm in d.get("pattern_matches") or []:
            slug = pm.get("pattern_slug")
            if not slug or pm.get("confidence") == "weak":
                continue
            a = agg[slug][sector]
            a["n"] += 1
            if eng:
                a["eng_sum"] += eng
                a["eng_n"] += 1
                if eng == 3:
                    a["high"] += 1
            a["cta"] += cta
            a["emoji"] += emoji

    out = {}
    for slug, sectors in agg.items():
        total = sum(s["n"] for s in sectors.values())
        ssum = sum(s["eng_sum"] for s in sectors.values())
        sn = sum(s["eng_n"] for s in sectors.values())
        out[slug] = {
            "total_observations": total,
            "eng_score_overall": round(ssum / sn, 2) if sn else None,
            "by_sector": {
                sec: {"n": s["n"],
                       "eng_score": round(s["eng_sum"] / s["eng_n"], 2) if s["eng_n"] else None,
                       "high_share_pct": round(100 * s["high"] / s["eng_n"]) if s["eng_n"] else None,
                       "cta_rate_pct": round(100 * s["cta"] / s["n"]) if s["n"] else 0,
                       "emoji_rate_pct": round(100 * s["emoji"] / s["n"]) if s["n"] else 0}
                for sec, s in sorted(sectors.items(), key=lambda kv: -kv[1]["n"])
            },
        }
    out = dict(sorted(out.items(), key=lambda kv: -kv[1]["total_observations"]))
    meta = {"_meta": {"built": "2026-06-11", "obs_scanned": total_obs,
                       "patterns_with_evidence": len(out),
                       "note": "weak-confidence matches excluded; eng: high=3 med=2 low=1"}}
    (BASE / "logs" / "pattern_engagement_evidence.json").write_text(
        json.dumps({**meta, **out}, ensure_ascii=False, indent=1))
    top = [(k, v["eng_score_overall"], v["total_observations"]) for k, v in out.items()
           if v["total_observations"] >= 30 and v["eng_score_overall"]]
    top.sort(key=lambda x: -x[1])
    print(f"✓ evidence for {len(out)} patterns from {total_obs} obs")
    print("strongest (n≥30):", [(s, e) for s, e, _ in top[:5]])
    print("weakest  (n≥30):", [(s, e) for s, e, _ in top[-5:]])


if __name__ == "__main__":
    main()
