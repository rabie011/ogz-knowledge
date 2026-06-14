#!/usr/bin/env python3
"""Parse the OpenClaw v3.7 Master Prompt Library (verbatim MD) into structured,
lossless per-chain JSON + indexes. The locked image-prompt canon — 15-block image
prompt + 5-block video prompt, placeholders {namespace.field}.

DETERMINISTIC by design (Rule #9 + repo convention "save your generators"):
no LLM touches the prompt text, so every word is preserved exactly. Mohamed's eye
is the semantic judge (AI-judge-can't-judge ruling) — this script only structures.

Handles BOTH metadata formats in the source:
  • foundational 18 (U01,T01-07,H01-04,G01-06): fenced ``` KEY VALUE ``` block,
    image/video prompts ALSO fenced.
  • rebuilt 76 (T08+, U02-U06): **Key:** v | **Key:** v bold-pipe lines,
    image/video prompts as raw text.

Source: data/openclaw_v37/source/OpenClaw_Master_Prompt_Library_v3_7_COMPLETE.md
Output: data/openclaw_v37/chains/<ID>.json · INDEX.json · placeholder_index.json
Usage:  python3 scripts/parse_openclaw_v37.py
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

B = Path(__file__).parent.parent
SRC = B / "data/openclaw_v37/source/OpenClaw_Master_Prompt_Library_v3_7_COMPLETE.md"
OUT = B / "data/openclaw_v37"
CHAINS = OUT / "chains"
TS = "2026-06-13"

# prefixes: U universal · T studio/treatment · H hand · G ground(Saudi) · F food
# · R retail · B beauty/booking · V native-video(t2v, no image) · S Saudi-UGC
CHAIN_HDR = re.compile(r"^##\s+(?:Chain\s+)?([UTHGFRBVS]\d{2})\b\s*·?\s*(.*)$")
STOP_HDR = re.compile(r"^(##\s+(?:Section|Library|Global|Open|FAMILY)|#\s+FAMILY|##\s+(?:Chain\s+)?[UTHGFRBVS]\d{2}\b)")
IMG_HDR = re.compile(r"^###\s+◆\s*Image prompt")
VID_HDR = re.compile(r"^###\s+[▶►]\s*(?:Video prompt|Native video)")
FENCE = re.compile(r"^```")
BLOCK = re.compile(r"^\[([^\]]+)\]")
PLACE = re.compile(r"\{([a-z][a-z0-9_.]+)\}")
META_PIPE = re.compile(r"\*\*([^:*]+):\*\*\s*([^|]+)")
META_FENCED = re.compile(r"^([A-Z][A-Z &/]+?)\s{2,}(.+)$")

KEYMAP = {
    "family": "family", "sectors": "sectors", "quality tier": "quality_tier",
    "tier": "quality_tier", "intent": "intent", "reference": "reference_image",
    "reference image": "reference_image", "frequency": "frequency",
    "image model": "image_model", "video model": "video_model",
    "ref accounts": "ref_accounts", "reference accounts": "ref_accounts",
    "cultural spec": "cultural_spec", "when to use": "when_to_use",
    "drama dial": "drama_dial", "color story": "color_story",
}


def _capture_block(lines, i):
    """From line i (the ### header), return (text, next_i). Handles fenced or raw."""
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines) and FENCE.match(lines[j]):          # fenced form
        start = j + 1
        k = start
        while k < len(lines) and not FENCE.match(lines[k]):
            k += 1
        return "\n".join(lines[start:k]).strip(), k + 1
    # raw form: until next ### / next chain-or-section header / --- / EOF
    start = j
    k = start
    while k < len(lines):
        ln = lines[k]
        if ln.startswith("### ") or STOP_HDR.match(ln) or ln.strip() == "---":
            break
        k += 1
    return "\n".join(lines[start:k]).strip(), k


def parse():
    lines = SRC.read_text().split("\n")
    # locate chain header line numbers
    starts = [i for i, ln in enumerate(lines) if CHAIN_HDR.match(ln)]
    starts.append(len(lines))
    chains = []
    for idx in range(len(starts) - 1):
        i, end = starts[idx], starts[idx + 1]
        m = CHAIN_HDR.match(lines[i])
        cid = m.group(1)
        title_raw = m.group(2).strip()
        locked = "LOCKED" in title_raw.upper()
        title = re.sub(r"\s*\*?\(.*?\)\*?\s*$", "", title_raw).strip()
        body = lines[i:end]

        meta, img, vid = {}, "", ""
        bi = 0
        # metadata: fenced KEY VALUE block OR bold-pipe lines (before ### ◆)
        while bi < len(body) and not IMG_HDR.match(body[bi]):
            ln = body[bi]
            if FENCE.match(ln):                              # fenced meta block
                bi += 1
                while bi < len(body) and not FENCE.match(body[bi]):
                    fm = META_FENCED.match(body[bi])
                    if fm:
                        key = KEYMAP.get(fm.group(1).strip().lower())
                        if key:
                            meta[key] = fm.group(2).strip()
                    bi += 1
            elif "**" in ln:                                  # bold-pipe meta
                for km, vm in META_PIPE.findall(ln):
                    key = KEYMAP.get(km.strip().lower())
                    if key:
                        meta[key] = vm.strip()
            bi += 1
        # image + video blocks
        for k in range(len(body)):
            if IMG_HDR.match(body[k]):
                img, _ = _capture_block(body, k)
            elif VID_HDR.match(body[k]):
                vid, _ = _capture_block(body, k)

        img_blocks = [BLOCK.match(l).group(1) for l in img.split("\n") if BLOCK.match(l)]
        vid_blocks = [BLOCK.match(l).group(1) for l in vid.split("\n") if BLOCK.match(l)]
        placeholders = sorted(set(PLACE.findall(img + " " + vid)))

        rec = {
            "chain_id": cid,
            "title": title,
            "locked": locked,
            "native_video": cid.startswith("V"),
            "family": meta.get("family", ""),
            "sectors": [s.strip() for s in re.split(r"[,/]", meta.get("sectors", "")) if s.strip()],
            "quality_tier": meta.get("quality_tier", ""),
            "intent": [s.strip() for s in meta.get("intent", "").split(",") if s.strip()],
            "reference_image": meta.get("reference_image", ""),
            "frequency": meta.get("frequency", ""),
            "image_model": meta.get("image_model", "fal-ai/flux-2-pro/edit"),
            "video_model": meta.get("video_model", "fal-ai/kling-video/v1.6/pro/i2v"),
            "ref_accounts": [s.strip() for s in meta.get("ref_accounts", "").split(",") if s.strip()],
            "cultural_spec": meta.get("cultural_spec", ""),
            "drama_dial": meta.get("drama_dial", ""),
            "color_story": meta.get("color_story", ""),
            "when_to_use": meta.get("when_to_use", ""),
            "image_prompt_template": img,
            "video_prompt_template": vid,
            "_stats": {
                "image_chars": len(img),
                "video_chars": len(vid),
                "image_blocks": img_blocks,
                "video_blocks": vid_blocks,
                "n_image_blocks": len(img_blocks),
                "placeholders": placeholders,
            },
            "provenance": {
                "source": "OpenClaw_Master_Prompt_Library_v3_7_COMPLETE.md",
                "date_added": TS, "confirmer": "alhareth+mohamed (canon)",
                "confidence": "confirmed", "scope": "global",
            },
        }
        chains.append(rec)
    return chains


def main():
    CHAINS.mkdir(parents=True, exist_ok=True)
    chains = parse()
    # write per-chain
    for c in chains:
        (CHAINS / f"{c['chain_id']}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2))
    # INDEX
    index = [{
        "chain_id": c["chain_id"], "title": c["title"], "family": c["family"],
        "sectors": c["sectors"], "quality_tier": c["quality_tier"],
        "locked": c["locked"], "drama_dial": c["drama_dial"],
        "image_chars": c["_stats"]["image_chars"],
        "video_chars": c["_stats"]["video_chars"],
        "n_image_blocks": c["_stats"]["n_image_blocks"],
    } for c in chains]
    (OUT / "INDEX.json").write_text(json.dumps(
        {"version": "3.7", "parsed": TS, "n_chains": len(chains), "chains": index},
        ensure_ascii=False, indent=2))
    # placeholder index: placeholder -> chains using it
    pidx = {}
    for c in chains:
        for p in c["_stats"]["placeholders"]:
            pidx.setdefault(p, []).append(c["chain_id"])
    (OUT / "placeholder_index.json").write_text(json.dumps(
        {"version": "3.7", "n_placeholders": len(pidx),
         "placeholders": {k: sorted(set(v)) for k, v in sorted(pidx.items())}},
        ensure_ascii=False, indent=2))

    # ---- VERIFY (Rule #9: assert, never feelings) ----
    over_img = [c["chain_id"] for c in chains if c["_stats"]["image_chars"] > 8000]
    over_vid = [c["chain_id"] for c in chains if c["_stats"]["video_chars"] > 2500]
    native = [c["chain_id"] for c in chains if c["native_video"]]
    # native-video (V0x) chains legitimately have NO image prompt
    empty = [c["chain_id"] for c in chains
             if not c["image_prompt_template"] and not c["native_video"]]
    native_no_vid = [c["chain_id"] for c in chains
                     if c["native_video"] and not c["video_prompt_template"]]
    thin = [c["chain_id"] for c in chains if 0 < c["_stats"]["n_image_blocks"] < 9]
    ids = [c["chain_id"] for c in chains]
    print(f"  parsed {len(chains)} chains")
    print(f"  with image prompt: {len(chains) - len(native)} · native-video (no image): {native}")
    print(f"  image-char ceiling (8000) breaches: {over_img or 'none'}")
    print(f"  video-char ceiling (2500) breaches: {over_vid or 'none'}")
    print(f"  empty image prompts (non-native): {empty or 'none'}")
    print(f"  <9 image blocks (suspect parse): {thin or 'none'}")
    print(f"  unique placeholders: {len(pidx)}")
    assert len(chains) >= 94, f"expected 94 chains, got {len(chains)}"
    assert not empty, f"empty image prompts: {empty}"
    assert not native_no_vid, f"native-video chains missing video prompt: {native_no_vid}"
    assert not over_img, f"image char breaches (canon cap 8000): {over_img}"
    assert not over_vid, f"video char breaches (canon cap 2500): {over_vid}"
    assert not thin, f"suspiciously thin parses: {thin}"
    assert "U01" in ids and "T08" in ids and "T02" in ids and "V01" in ids, "missing known chains"
    assert next(c for c in chains if c["chain_id"] == "T02")["locked"], "T02 must be locked"
    print("  ✓ all asserts passed")


if __name__ == "__main__":
    main()
