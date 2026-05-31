#!/usr/bin/env python3
"""
enrich_video_frames_ext.py
Extended version of enrich_video_frames.py that also processes jpg thumbnail
files (e.g. {shortcode}_thumb.jpg) for obs that are missing scene_type.

Fields filled (only if currently null — never overwrites):
  visual_observations.composition_style
  visual_observations.human_presence
  visual_observations.text_overlay_visible
  visual_observations.arabic_text_visible
  visual_observations.product_visible
  visual_observations.brand_logo_visible
  visual_observations.scene_type

Usage:
  python3 scripts/enrich_video_frames_ext.py --dry-run
  python3 scripts/enrich_video_frames_ext.py
  python3 scripts/enrich_video_frames_ext.py --limit 200
"""
from __future__ import annotations
import argparse, base64, json, os, re, sys, time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.exit("pip install openai")

REPO     = Path(__file__).parent.parent
OBS_ROOT = REPO / "11_who_to_learn_from" / "observations"
INBOX    = REPO / "11_who_to_learn_from" / "_inbox"
LOGS     = REPO / "logs"
STATE_F  = LOGS / "video_frames_ext_state.json"

FILL_FIELDS = [
    "composition_style", "human_presence", "text_overlay_visible",
    "arabic_text_visible", "product_visible", "brand_logo_visible", "scene_type",
]

VISION_PROMPT = """Analyse this Saudi social media post image/frame.
Return ONLY valid JSON (no markdown, no explanation):
{
  "composition_style": "product_hero"|"lifestyle_integrated"|"editorial"|"overhead_spread"|"face_forward"|"text_dominant"|"behind_the_scenes",
  "human_presence": true|false|null,
  "text_overlay_visible": true|false,
  "arabic_text_visible": true|false,
  "product_visible": true|false,
  "brand_logo_visible": true|false,
  "scene_type": "indoor"|"outdoor"|"studio"|"graphic"|"mixed"
}"""


def load_state() -> dict:
    if STATE_F.exists():
        return json.loads(STATE_F.read_text())
    return {"done_shortcodes": []}

def save_state(s: dict) -> None:
    STATE_F.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def sc_from_url(url: str) -> str | None:
    m = re.search(r"/p/([A-Za-z0-9_-]+)/?", url)
    return m.group(1) if m else None

def sc_from_stem(stem: str) -> str | None:
    stem = re.sub(r"_thumb$", "", stem).lstrip("-")
    if not stem: return None
    if len(stem) <= 13 and re.match(r"^[A-Za-z0-9_-]+$", stem):
        return stem
    return None

def needs_fill(obs_path: Path) -> bool:
    try:
        d = json.loads(obs_path.read_text())
        vis = d.get("visual_observations") or {}
        return any(vis.get(f) is None for f in FILL_FIELDS)
    except: return False

def build_obs_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            cr = d.get("content_ref") or {}
            ct = str(cr.get("content_type","")).lower()
            if ct not in ("video","reel","image","carousel_slide"):
                continue
            url = cr.get("source_url","")
            sc = sc_from_url(url)
            if sc and sc not in index:
                index[sc] = f
            fn = cr.get("filename","")
            if fn:
                fsc = sc_from_stem(Path(fn).stem)
                if fsc and fsc not in index:
                    index[fsc] = f
        except: pass
    return index

def iter_media_files():
    """Yield (path, shortcode) for all jpg/mp4 files under _inbox."""
    for f in sorted(INBOX.rglob("*")):
        if f.suffix in (".jpg",".jpeg",".png"):
            sc = sc_from_stem(f.stem)
            if sc: yield f, sc
        elif f.suffix == ".mp4":
            sc = sc_from_stem(f.stem)
            if sc: yield f, sc

def image_to_b64(path: Path) -> str | None:
    """Return base64-encoded JPEG. For mp4, extract middle frame via ffmpeg."""
    if path.suffix in (".jpg",".jpeg",".png"):
        try:
            return base64.b64encode(path.read_bytes()).decode()
        except: return None
    # mp4: extract middle frame
    import subprocess, tempfile
    try:
        result = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)],
            capture_output=True, text=True, timeout=15)
        info = json.loads(result.stdout)
        dur = None
        for s in info.get("streams",[]):
            try:
                dur = float(s["duration"]); break
            except: pass
        ts = (dur / 2) if dur else 1.0
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        subprocess.run(
            ["ffmpeg","-ss",str(ts),"-i",str(path),"-frames:v","1",
             "-q:v","3","-y",tmp_path],
            capture_output=True, timeout=30)
        data = Path(tmp_path).read_bytes()
        Path(tmp_path).unlink(missing_ok=True)
        return base64.b64encode(data).decode()
    except: return None

def build_batch_request(custom_id: str, b64: str, mime: str = "image/jpeg") -> dict:
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "max_tokens": 200,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "low"}},
                    {"type": "text", "text": VISION_PROMPT},
                ]
            }]
        }
    }

def submit_batch(requests_list: list[dict], tag: str) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    jsonl = "\n".join(json.dumps(r) for r in requests_list)
    f_obj = client.files.create(file=(f"{tag}.jsonl", jsonl.encode(), "application/jsonl"),
                                purpose="batch")
    batch = client.batches.create(input_file_id=f_obj.id,
                                  endpoint="/v1/chat/completions",
                                  completion_window="24h",
                                  metadata={"tag": tag})
    return batch.id

def poll_batch(batch_id: str) -> list[dict]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    while True:
        b = client.batches.retrieve(batch_id)
        done = b.request_counts.completed if b.request_counts else 0
        total = b.request_counts.total if b.request_counts else 0
        print(f"  [{tag_str}] status={b.status} completed={done}/{total}", flush=True)
        if b.status == "completed":
            raw = client.files.content(b.output_file_id).text
            return [json.loads(l) for l in raw.strip().splitlines() if l.strip()]
        if b.status in ("failed","expired","cancelled"):
            print(f"  Batch {batch_id} ended with status={b.status}")
            return []
        time.sleep(30)

tag_str = "vf_ext"

def apply_results(results: list[dict], obs_index: dict[str, Path], cid_map: dict) -> tuple[int,int]:
    written = errors = 0
    for r in results:
        cid = r.get("custom_id","")
        sc = cid_map.get(cid, cid.split("__",1)[-1] if "__" in cid else cid[3:])
        obs_path = obs_index.get(sc)
        if not obs_path:
            errors += 1; continue
        try:
            content = r.get("response",{}).get("body",{}).get("choices",[{}])[0].get("message",{}).get("content","")
            # strip markdown fences
            content = re.sub(r"^```[a-z]*\n?", "", content.strip())
            content = re.sub(r"\n?```$", "", content.strip())
            parsed = json.loads(content)
        except Exception as e:
            errors += 1; continue
        try:
            d = json.loads(obs_path.read_text())
            vis = d.setdefault("visual_observations", {})
            changed = False
            for field in FILL_FIELDS:
                if vis.get(field) is None and field in parsed:
                    vis[field] = parsed[field]
                    changed = True
            if changed:
                obs_path.write_text(json.dumps(d, indent=2, ensure_ascii=False))
                written += 1
        except Exception as e:
            errors += 1
    return written, errors

def main():
    global tag_str
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY","")
    if not api_key and not args.dry_run:
        # try loading from ~/.abraham_env
        env_file = Path.home() / ".abraham_env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY=") or line.startswith("OPENAI_KEY="):
                    api_key = line.split("=",1)[1].strip().strip('"').strip("'")
                    os.environ["OPENAI_API_KEY"] = api_key
                    break

    state = load_state()
    done_set = set(state.get("done_shortcodes",[]))

    if args.status:
        active = state.get("active_batch_id")
        print(f"done_shortcodes: {len(done_set)}")
        print(f"active_batch_id: {active}")
        return

    print("Building obs index...", end=" ", flush=True)
    obs_index = build_obs_index()
    print(f"{len(obs_index)} obs indexed")

    print("Scanning media files for work...")
    work: list[tuple[Path,str]] = []
    n_no_obs = n_filled = n_done = 0
    seen_sc: set[str] = set()
    for media_path, sc in iter_media_files():
        if sc in seen_sc: continue
        obs_path = obs_index.get(sc)
        if not obs_path:
            n_no_obs += 1; continue
        if not needs_fill(obs_path):
            n_filled += 1; continue
        if sc in done_set:
            n_done += 1; continue
        seen_sc.add(sc)
        work.append((media_path, sc))

    if args.limit:
        work = work[:args.limit]

    cost = len(work) * 0.001
    print(f"  Total media scanned     : {sum(1 for _ in iter_media_files())}")
    print(f"  No matching obs         : {n_no_obs}")
    print(f"  Already fully filled    : {n_filled}")
    print(f"  Already processed       : {n_done}")
    print(f"  To process now          : {len(work)}")
    print(f"  Estimated cost          : ${cost:.3f}")

    if args.dry_run or not work:
        if args.dry_run:
            print("[dry-run] No files read, no API calls.")
        return

    # Check for active batch
    active_id = state.get("active_batch_id")
    if active_id:
        print(f"\nResuming active batch: {active_id}")
        client = OpenAI(api_key=api_key)
        b = client.batches.retrieve(active_id)
        if b.status == "completed":
            raw = client.files.content(b.output_file_id).text
            results = [json.loads(l) for l in raw.strip().splitlines() if l.strip()]
            cid_map = state.get("cid_to_sc", {})
            n_w, n_e = apply_results(results, obs_index, cid_map)
            print(f"  Applied: {n_w} written, {n_e} errors")
            for r in results:
                cid = r.get("custom_id","")
                sc = cid_map.get(cid, cid.split("__",1)[-1] if "__" in cid else "")
                if sc: done_set.add(sc)
            state["done_shortcodes"] = list(done_set)
            state.pop("active_batch_id", None)
            save_state(state)
            return
        elif b.status in ("validating","in_progress","finalizing"):
            print(f"  Batch still {b.status} — run again later or wait.")
            return
        else:
            state.pop("active_batch_id", None)
            save_state(state)

    # Build batch requests
    print(f"\nEncoding {len(work)} images...")
    requests_list = []
    cid_to_sc = {}
    errors = 0
    for i, (media_path, sc) in enumerate(work):
        b64 = image_to_b64(media_path)
        if not b64:
            errors += 1; continue
        cid = f"vfe_{sc[:60]}__{i}"
        cid_to_sc[cid] = sc
        requests_list.append(build_batch_request(cid, b64))
    print(f"  Encoded: {len(requests_list)} | Errors: {errors}")

    if not requests_list:
        print("Nothing to submit."); return

    print("\nSubmitting to OpenAI Batch API...")
    batch_id = submit_batch(requests_list, "video_frames_ext")
    state["active_batch_id"] = batch_id
    state["cid_to_sc"] = cid_to_sc
    save_state(state)
    print(f"  Batch submitted: {batch_id}")

    print("\nPolling batch...")
    results = poll_batch(batch_id)
    if results:
        cid_map = state.get("cid_to_sc", {})
        n_w, n_e = apply_results(results, obs_index, cid_map)
        print(f"\nApplying results: {n_w} obs updated, {n_e} errors")
        for r in results:
            cid = r.get("custom_id","")
            sc = cid_map.get(cid, cid.split("__",1)[-1] if "__" in cid else "")
            if sc: done_set.add(sc)
        state["done_shortcodes"] = list(done_set)
        state.pop("active_batch_id", None)
        save_state(state)
        print(f"Done. Total processed: {len(done_set)}")

if __name__ == "__main__":
    main()
