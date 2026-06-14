#!/usr/bin/env python3
"""Un-poison the organs where h_passport stored Mohamed's DIRECTIVE as the brand's VALUE
(zoom-out 2026-06-14: "Go check and search the client" became albaik's identity/red_line/
truth; "no answer for this brand" became alnasser's goal). His COMMAND is not the brand's
truth. This strips the directive-values, KEEPS real answers (albaik goal بناء براند وبيع),
and records the extraction MODE his directive meant.

His directives → modes:
  albaik         → auto_research      (established brand: research all platforms+Google, don't ask)
  alnasserjewelry→ no_answer_figure_out (no client answer: system figures out + default role)

Idempotent, asserts no directive text survives in the cleaned organs.
Usage: python3 scripts/apply_directive_cleanup.py
"""
import json, re
from pathlib import Path

B = Path(__file__).parent.parent
TS = "2026-06-14"
DIRECTIVE = re.compile(
    r"go\s*(check|search)|search (for )?the client|extract every|no answer for this brand|"
    r"figure (it )?out|let the system|consider.*(role|is the role)|could be for (a )?new brand|"
    r"very established brand|same answer|same no answer", re.I)

MODES = {
    "albaik": ("auto_research",
               "ESTABLISHED brand — research the client across all platforms + Google; do NOT ask the passport questions (Mohamed 2026-06-14)"),
    "alnasserjewelry": ("no_answer_figure_out",
                        "NO client answer — the system figures the brand out from extraction + a sensible default role (Mohamed 2026-06-14)"),
}


def is_dir(v):
    return isinstance(v, str) and bool(DIRECTIVE.search(v))


def clean_brand(h, mode, note):
    p = B / "clients" / h / "profile"
    cleaned = []
    # red_lines — drop directive lines
    rlf = p / "red_lines.json"
    if rlf.exists():
        rl = json.loads(rlf.read_text())
        before = len(rl.get("lines", []))
        rl["lines"] = [l for l in rl.get("lines", [])
                       if not is_dir(l.get("line", "") if isinstance(l, dict) else l)]
        if len(rl["lines"]) < before:
            cleaned.append(f"red_lines -{before - len(rl['lines'])} directive line(s)")
        rlf.write_text(json.dumps(rl, ensure_ascii=False, indent=1))
    # goals — null directive-valued fields, KEEP real (albaik primary بناء براند وبيع), recount
    gf = p / "goals.json"
    if gf.exists():
        g = json.loads(gf.read_text())
        for k in ("primary", "capacity", "goal_ratio", "usp_his_words", "capacity_ceiling"):
            if is_dir(g.get(k)):
                g[k] = None
                cleaned.append(f"goals.{k} nulled")
        g["answered"] = sum(1 for k in ("goal_ratio", "capacity_ceiling", "usp_his_words", "primary") if g.get(k))
        gf.write_text(json.dumps(g, ensure_ascii=False, indent=1))
    # fingerprint l1_strategy — null directive fields
    fpf = p / "fingerprint.json"
    if fpf.exists():
        fp = json.loads(fpf.read_text())
        for layer in ("l1_strategy", "l2_voice"):
            d = fp.get(layer) or {}
            for k in list(d):
                if is_dir(d.get(k)):
                    d[k] = None
                    cleaned.append(f"{layer}.{k} nulled")
        fpf.write_text(json.dumps(fp, ensure_ascii=False, indent=1))
    # truth_pack — null directive top-level string fields (keep product_candidates: mined)
    tpf = p / "truth_pack.json"
    if tpf.exists():
        tp = json.loads(tpf.read_text())
        for k in list(tp):
            if is_dir(tp.get(k)):
                tp[k] = None
                cleaned.append(f"truth_pack.{k} nulled")
        # his directive got stored as confirmed product/truth NAMES — drop them
        for lk in ("confirmed", "product_candidates", "channels"):
            if isinstance(tp.get(lk), list):
                before = len(tp[lk])
                tp[lk] = [x for x in tp[lk]
                          if not is_dir(x.get("name", "") if isinstance(x, dict) else x)]
                if len(tp[lk]) < before:
                    cleaned.append(f"truth_pack.{lk} -{before - len(tp[lk])} directive entr(y/ies)")
        tpf.write_text(json.dumps(tp, ensure_ascii=False, indent=1))
    # record the mode his directive meant
    (p / "extraction_mode.json").write_text(json.dumps({
        "mode": mode, "note": note, "set": TS, "by": "mohamed_directive",
        "source": "directive-as-data cleanup (zoom-out wfh3fs64c)"}, ensure_ascii=False, indent=1))

    # ASSERT no directive text survives in the cleaned organs
    for f in ("red_lines.json", "goals.json", "fingerprint.json", "truth_pack.json"):
        fp2 = p / f
        if fp2.exists():
            assert not DIRECTIVE.search(fp2.read_text()), f"{h}/{f} STILL has directive text"
    return cleaned


def main():
    for h, (mode, note) in MODES.items():
        cl = clean_brand(h, mode, note)
        print(f"  ✓ {h}: mode={mode} · cleaned {cl or '(already clean)'}")
    # prove albaik's REAL goal survived
    g = json.loads((B / "clients/albaik/profile/goals.json").read_text())
    assert g.get("primary") == "بناء براند الاول وبيع", "albaik real goal must survive!"
    print("  ✅ albaik real goal بناء براند وبيع preserved · no directive text remains")


if __name__ == "__main__":
    main()
