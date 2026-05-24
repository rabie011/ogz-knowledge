#!/usr/bin/env python3
"""
build_caption_length_hashtag_analysis.py
Caption length buckets + hashtag count + emoji × engagement.
Key signals: 10-30 words = 82%, 1-5 hashtags = 87%, 30-60 words collapses to 52%.
Output: logs/caption_length_hashtag_analysis.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

WC_BUCKETS  = [("<10",0,9),("10-30",10,29),("30-60",30,59),("60+",60,9999)]
HC_BUCKETS  = [("0",0,0),("1-5",1,5),("6-15",6,15),("16+",16,9999)]

def _wc_bucket(n):
    for label,lo,hi in WC_BUCKETS:
        if lo <= n <= hi: return label
    return "60+"

def _hc_bucket(n):
    for label,lo,hi in HC_BUCKETS:
        if lo <= n <= hi: return label
    return "16+"

def main():
    wc_eng   = defaultdict(list)
    hc_eng   = defaultdict(list)
    em_eng   = defaultdict(list)
    sent_eng = defaultdict(list)
    op_eng   = defaultdict(list)
    sec_wc   = defaultdict(lambda: defaultdict(list))
    sec_hc   = defaultdict(lambda: defaultdict(list))

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        e  = _eng(d)
        if e is None: continue
        vo  = d.get("voice_observations",{})
        sec = d.get("sector","")

        wc = vo.get("caption_word_count")
        if wc is not None:
            b = _wc_bucket(wc)
            wc_eng[b].append(e)
            if sec: sec_wc[sec][b].append(e)

        hc = vo.get("hashtag_count")
        if hc is not None:
            b = _hc_bucket(hc)
            hc_eng[b].append(e)
            if sec: sec_hc[sec][b].append(e)

        em = vo.get("has_emoji")
        if em is not None: em_eng[str(em)].append(e)

        sent = vo.get("caption_sentiment")
        if sent: sent_eng[sent].append(e)

        op = vo.get("opener_formula")
        if op: op_eng[op].append(e)

    global_avg = _avg([v for vals in wc_eng.values() for v in vals]) or 0

    def _build(eng_dict, order=None):
        items = sorted(eng_dict.items(), key=lambda x:-(_avg(x[1]) or 0))
        if order:
            items = [(k,eng_dict[k]) for k in order if k in eng_dict] + \
                    [(k,v) for k,v in items if k not in order]
        return {
            k: {"count":len(v),"avg_engagement":_avg(v),
                "lift_vs_avg":round((_avg(v) or 0)-global_avg,3)}
            for k,v in items
        }

    by_wc   = _build(wc_eng,  [b[0] for b in WC_BUCKETS])
    by_hc   = _build(hc_eng,  [b[0] for b in HC_BUCKETS])
    by_em   = _build(em_eng)
    by_sent = _build(sent_eng)
    by_op   = _build(op_eng)

    best_wc_by_sector = {
        sec: sorted([{"bucket":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in bkts.items() if len(v)>=2],
                    key=lambda x:-(x["avg_engagement"] or 0))
        for sec,bkts in sec_wc.items()
    }

    best_hc_by_sector = {
        sec: sorted([{"bucket":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in bkts.items() if len(v)>=2],
                    key=lambda x:-(x["avg_engagement"] or 0))
        for sec,bkts in sec_hc.items()
    }

    # Agency rules
    best_wc = max(by_wc.items(), key=lambda x:(x[1]["avg_engagement"] or 0))
    best_hc = max(by_hc.items(), key=lambda x:(x[1]["avg_engagement"] or 0))
    emoji_yes = (by_em.get("True",{}).get("avg_engagement") or 0)
    emoji_no  = (by_em.get("False",{}).get("avg_engagement") or 0)

    rules = [
        f"Optimal caption length: {best_wc[0]} words ({best_wc[1]['avg_engagement']:.0%}) — avoid 30-60 word range ({by_wc.get('30-60',{}).get('avg_engagement',0):.0%})",
        f"Optimal hashtag count: {best_hc[0]} ({best_hc[1]['avg_engagement']:.0%}) — 16+ tanks to {by_hc.get('16+',{}).get('avg_engagement',0):.0%}",
        f"Emoji: {'use' if emoji_yes >= emoji_no else 'avoid'} ({emoji_yes:.0%} with vs {emoji_no:.0%} without)",
    ]
    if by_op:
        best_op = max(by_op.items(), key=lambda x:(x[1]["avg_engagement"] or 0))
        rules.append(f"Best opener: {best_op[0]} ({best_op[1]['avg_engagement']:.0%})")

    out = {
        "obs_with_caption": sum(len(v) for v in wc_eng.values()),
        "global_avg":       round(global_avg,3),
        "by_word_count":    by_wc,
        "by_hashtag_count": by_hc,
        "by_emoji":         by_em,
        "by_sentiment":     by_sent,
        "by_opener_formula":by_op,
        "best_wc_by_sector":best_wc_by_sector,
        "best_hc_by_sector":best_hc_by_sector,
        "agency_rules":     rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"caption_length_hashtag_analysis.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Caption length + hashtag analysis — {out['obs_with_caption']} obs with captions\n")
    print("Word count buckets:")
    for k,d in by_wc.items():
        lift = f"+{d['lift_vs_avg']:.2f}" if d['lift_vs_avg']>=0 else f"{d['lift_vs_avg']:.2f}"
        print(f"  {k:<8}  {d['avg_engagement']:.0%}  lift {lift}  n={d['count']}")
    print("\nHashtag count buckets:")
    for k,d in by_hc.items():
        lift = f"+{d['lift_vs_avg']:.2f}" if d['lift_vs_avg']>=0 else f"{d['lift_vs_avg']:.2f}"
        print(f"  {k:<8}  {d['avg_engagement']:.0%}  lift {lift}  n={d['count']}")
    print("\nEmoji:")
    for k,d in by_em.items():
        print(f"  emoji={k:<6}  {d['avg_engagement']:.0%}  n={d['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/caption_length_hashtag_analysis.json")

if __name__ == "__main__":
    main()
