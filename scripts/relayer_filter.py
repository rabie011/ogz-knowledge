#!/usr/bin/env python3
"""DATA RE-LAYERING — LAYER 1 (June 12, Mohamed's go-build on the brainstorm plan).
The ranking law: Laws (hard) > Mohamed's taste > measured engagement (tie-breaker) >
extractor opinion (RETIRED). The corpus is raw material, never authority.

Builds ONE quality index over the 6,888 observations — the obs files are NEVER edited
(one fact, one place; DELETE APPROVED law: nothing deleted, everything tiered):

  tier 'clean'      — passes every law, not a duplicate → eligible to teach
  tier 'flagged'    — law hits (named) → never teaches; kept as negative examples
  tier 'duplicate'  — cross-brand near-copy → only the FIRST occurrence teaches
  short: True       — ≤12 words (the corpus's real treasure: the minority that
                      agrees with Mohamed's taste)
  eng_unverified    — ALWAYS true until the Apify join lands real numbers
                      (the eyeballed enum carries no signal — measured June 12)

Output: data/obs_quality_index.json + summary. Idempotent, deterministic, zero-LLM.
"""
import json
import glob
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso
from caption_filter import cultural_check, offer_check

SHORT_MAX = 12          # provisional — Mohamed's short_caption_number card may move it


def main():
    B = base()
    files = sorted(glob.glob(str(B / "11_who_to_learn_from/observations/*/*.json")))
    index, tiers, law_hits = {}, Counter(), Counter()
    caps_seen = {}
    for f in files:
        try:
            o = json.loads(Path(f).read_text())
        except Exception:
            continue
        ulid = o.get("observation_ulid") or Path(f).stem
        vo = o.get("voice_observations") or {}
        cap = vo.get("caption_text") or ""
        sector = o.get("sector", "?")
        brand = o.get("account_handle_normalized", "?")
        entry = {"sector": sector, "brand": brand, "eng_unverified": True}
        if not cap.strip():
            entry["tier"] = "captionless"
        else:
            occ = f"{o.get('occasion','')} {(o.get('cultural_notes') or {}).get('occasion_relevance','')}"
            _, hits = cultural_check(cap[:600], occ)
            _, h2 = offer_check(cap[:600])
            hits = hits + h2
            wc = vo.get("caption_word_count") or len(cap.split())
            entry["short"] = wc <= SHORT_MAX
            entry["words"] = wc
            k = cap[:60]
            if k in caps_seen and caps_seen[k][0] != brand:
                entry["tier"] = "duplicate"
                entry["duplicate_of"] = caps_seen[k][1]
            elif hits:
                entry["tier"] = "flagged"
                entry["law_hits"] = hits
                for h in hits:
                    law_hits[h] += 1
            else:
                entry["tier"] = "clean"
                caps_seen.setdefault(k, (brand, ulid))
        tiers[entry["tier"]] += 1
        index[ulid] = entry

    out = {"generated": now_iso(), "ranking_law": "laws > mohamed_taste > measured_engagement > extractor_opinion(retired)",
           "short_max": SHORT_MAX, "tiers": dict(tiers), "law_hits": dict(law_hits),
           "clean_short_count": sum(1 for e in index.values() if e.get("tier") == "clean" and e.get("short")),
           "index": index}
    (B / "data/obs_quality_index.json").write_text(json.dumps(out, ensure_ascii=False))
    # ASSERT by re-read (system layer)
    re = json.loads((B / "data/obs_quality_index.json").read_text())
    assert len(re["index"]) == len(index) and re["tiers"] == dict(tiers), "index write mismatch"
    print(f"obs indexed: {len(index)}")
    for t, n in tiers.most_common():
        print(f"  {t}: {n} ({100*n/len(index):.1f}%)")
    print(f"  law hits: {dict(law_hits)}")
    print(f"  ⭐ CLEAN + SHORT (the treasure): {out['clean_short_count']}")


if __name__ == "__main__":
    main()
