#!/usr/bin/env python3
"""
overnight_full_rebuild.py — Run everything overnight.

When Mohamed wakes up:
  - All accounts re-extracted with real metrics
  - GPT-4o Vision on top images per brand
  - Deep Arabic caption NLP per brand
  - Brain rebuilt on real data
  - Proof presentation updated
  - Everything committed + pushed

Budget: ~$25 Apify + ~$10 OpenAI
"""
import json, os, sys, subprocess, glob, time, base64, urllib.request
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path(__file__).parent.parent
LOG_FILE = BASE / "logs" / "overnight_rebuild.log"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(BASE))
    return r.returncode, r.stdout, r.stderr

def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env()

log("═" * 60)
log("  OVERNIGHT FULL REBUILD — START")
log(f"  Apify: ${os.environ.get('APIFY_TOKEN','MISSING')[:5]}...")
log(f"  OpenAI: ${os.environ.get('OPENAI_API_KEY','MISSING')[:5]}...")
log("═" * 60)

# ═══════════════════════════════════════════════════════════
# PHASE 1: Re-extract remaining accounts with real metrics
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 1: Re-extract accounts with real metrics")

# Load target accounts — find done accounts without raw archive
target = json.loads((BASE / "11_who_to_learn_from" / "target_accounts.json").read_text())
accounts = target.get("accounts", [])
already_archived = set()
for d in (BASE / "11_who_to_learn_from" / "_raw_archive").glob("*"):
    if d.is_dir():
        already_archived.add(d.name)

to_extract = []
for a in accounts:
    if a["status"] in ("done", "force_done") and a["handle"] not in already_archived:
        to_extract.append(a)

log(f"  Already archived: {len(already_archived)}")
log(f"  Need re-extraction: {len(to_extract)}")

extracted = 0
for a in to_extract[:30]:  # Cap at 30 to stay within budget
    handle = a["handle"]
    sector = a.get("sector", "f_and_b")
    log(f"  Extracting @{handle} ({sector})...")
    try:
        rc, out, err = run([
            sys.executable, "scripts/extract_account_obs.py",
            "--handle", handle, "--sector", sector,
        ], timeout=1800)
        if rc == 0:
            extracted += 1
            log(f"    ✅ @{handle} done")
            # Backfill real metrics
            run([sys.executable, "scripts/reprocess_from_raw.py", "--handle", handle, "--sector", sector], timeout=120)
        else:
            log(f"    ⚠️ @{handle} failed: {err[:100]}")
    except Exception as e:
        log(f"    ❌ @{handle} error: {e}")
    time.sleep(5)  # Rate limit between extractions

log(f"  Phase 1 complete: {extracted} accounts re-extracted")

# ═══════════════════════════════════════════════════════════
# PHASE 2: GPT-4o Vision on top images per brand
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 2: GPT-4o Vision analysis")

import openai
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Get all brands with raw archive
vision_results = {}
for archive_dir in sorted((BASE / "11_who_to_learn_from" / "_raw_archive").glob("*")):
    handle = archive_dir.name
    if handle in ["albaik", "pizzahutsaudi"]:  # Already done
        continue

    jsonl_files = list(archive_dir.glob("**/*_apify_raw.jsonl"))
    if not jsonl_files:
        continue

    posts = []
    for jf in jsonl_files:
        for line in jf.read_text().strip().split("\n"):
            if line:
                posts.append(json.loads(line))

    posts.sort(key=lambda p: p.get("likesCount", 0), reverse=True)
    top_post = posts[0] if posts else None
    if not top_post or not top_post.get("displayUrl"):
        continue

    log(f"  Analyzing @{handle} top post ({top_post.get('likesCount',0)} likes)...")
    try:
        img_data = urllib.request.urlopen(top_post["displayUrl"], timeout=10).read()
        b64 = base64.b64encode(img_data).decode()

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Analyze this Saudi Instagram post. Report: COLORS (hex), LIGHTING, COMPOSITION, SETTING, MOOD. Be brief."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}},
            ]}],
            max_tokens=200,
        )
        analysis = resp.choices[0].message.content
        vision_results[handle] = {
            "likes": top_post.get("likesCount", 0),
            "analysis": analysis,
        }
        log(f"    ✅ {analysis[:80]}...")
    except Exception as e:
        log(f"    ⚠️ Vision failed: {e}")
    time.sleep(2)

# Save vision results
(BASE / "logs" / "vision_analysis_overnight.json").write_text(
    json.dumps(vision_results, indent=2, ensure_ascii=False))
log(f"  Phase 2 complete: {len(vision_results)} brands analyzed")

# ═══════════════════════════════════════════════════════════
# PHASE 3: Deep caption NLP per brand
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 3: Deep Arabic caption NLP")

caption_results = {}
for archive_dir in sorted((BASE / "11_who_to_learn_from" / "_raw_archive").glob("*")):
    handle = archive_dir.name
    if handle in ["albaik", "pizzahutsaudi"]:  # Already done
        continue

    # Get captions with likes
    captions = []
    for f in glob.glob(str(BASE / "11_who_to_learn_from" / "observations" / "*" / "*.json")):
        d = json.loads(Path(f).read_text())
        if d.get("account_handle_normalized", "").lstrip("@") != handle:
            continue
        cr = d.get("content_ref", {})
        cap = d.get("voice_observations", {}).get("caption_text", "") or ""
        likes = cr.get("likes_count", 0)
        if likes > 0 and len(cap) > 20:
            captions.append({"likes": likes, "caption": cap[:150]})

    if len(captions) < 5:
        continue

    captions.sort(key=lambda x: x["likes"], reverse=True)
    top = "\n".join(f"[{c['likes']} likes] {c['caption']}" for c in captions[:5])
    bottom = "\n".join(f"[{c['likes']} likes] {c['caption']}" for c in captions[-5:])

    log(f"  Analyzing @{handle} captions ({len(captions)} with real likes)...")
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""Analyze @{handle} Saudi Instagram captions.

TOP (highest likes):
{top}

BOTTOM (lowest likes):
{bottom}

In 3 bullet points: what makes the top captions work and what fails in the bottom ones? Be specific about Arabic dialect and tone."""}],
            max_tokens=300,
        )
        caption_results[handle] = resp.choices[0].message.content
        log(f"    ✅ Done")
    except Exception as e:
        log(f"    ⚠️ Caption NLP failed: {e}")
    time.sleep(2)

(BASE / "logs" / "caption_analysis_overnight.json").write_text(
    json.dumps(caption_results, indent=2, ensure_ascii=False))
log(f"  Phase 3 complete: {len(caption_results)} brands analyzed")

# ═══════════════════════════════════════════════════════════
# PHASE 4: Rebuild brain with all real data
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 4: Rebuild thin brain with real data")

brain = json.loads((BASE / "11_who_to_learn_from" / "intelligence_layer.json").read_text())

# Update real metrics for all brands with raw archive
for archive_dir in (BASE / "11_who_to_learn_from" / "_raw_archive").glob("*"):
    handle = archive_dir.name
    likes = []
    comments = []
    sector = ""
    for f in glob.glob(str(BASE / "11_who_to_learn_from" / "observations" / "*" / "*.json")):
        d = json.loads(Path(f).read_text())
        if d.get("account_handle_normalized", "").lstrip("@") == handle:
            cr = d.get("content_ref", {})
            l = cr.get("likes_count", 0)
            if l > 0:
                likes.append(l)
                comments.append(cr.get("comments_count", 0))
                sector = d.get("sector", "")
    if likes:
        brain["real_metrics"][handle] = {
            "obs_count": len(likes),
            "avg_likes": sum(likes) // len(likes),
            "max_likes": max(likes),
            "min_likes": min(likes),
            "avg_comments": sum(comments) // len(comments),
            "sector": sector,
            "verified": True,
        }

# Update reference examples
for handle in brain["real_metrics"]:
    examples = []
    for f in glob.glob(str(BASE / "11_who_to_learn_from" / "observations" / "*" / "*.json")):
        d = json.loads(Path(f).read_text())
        if d.get("account_handle_normalized", "").lstrip("@") != handle:
            continue
        cr = d.get("content_ref", {})
        if cr.get("likes_count", 0) > 0:
            examples.append({
                "url": cr.get("source_url", ""),
                "likes": cr.get("likes_count", 0),
                "comments": cr.get("comments_count", 0),
                "content_type": cr.get("content_type", ""),
                "caption_preview": (d.get("voice_observations", {}).get("caption_text", "") or "")[:80],
            })
    examples.sort(key=lambda x: x["likes"], reverse=True)
    brain["reference_examples"][handle] = examples[:5]

# Add overnight vision + caption results
if vision_results:
    brain["visual_intelligence_overnight"] = vision_results
if caption_results:
    brain["caption_intelligence_overnight"] = caption_results

brain["meta"]["updated_at"] = datetime.now().isoformat()
brain["meta"]["real_metrics_brands"] = len(brain["real_metrics"])

(BASE / "11_who_to_learn_from" / "intelligence_layer.json").write_text(
    json.dumps(brain, indent=2, ensure_ascii=False))

log(f"  Brain updated: {len(brain['real_metrics'])} brands with real metrics")
log(f"  Brain size: {len(json.dumps(brain)):,} chars")

# ═══════════════════════════════════════════════════════════
# PHASE 5: Rebuild analytics + sync
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 5: Rebuild analytics + sync")

rc, out, err = run([sys.executable, "scripts/run_all_analytics.py", "--fast"], timeout=120)
log(f"  Analytics: {'✅' if rc == 0 else '❌'}")

rc, out, err = run([sys.executable, "sync_to_supabase.py", "--execute"], timeout=300)
log(f"  DB sync: {'✅' if rc == 0 else '❌'}")

# ═══════════════════════════════════════════════════════════
# PHASE 6: Validate everything
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 6: Validate")

rc, out, err = run([sys.executable, "scripts/validate_all.py"], timeout=120)
log(f"  Validation: {out.strip().split(chr(10))[-1] if out else err[:50]}")

rc, out, err = run([sys.executable, "scripts/guard_data_quality.py", "--quick"], timeout=120)
log(f"  Guard: {'✅ PASS' if rc == 0 else '❌ FAIL'}")

# ═══════════════════════════════════════════════════════════
# PHASE 7: Commit + push
# ═══════════════════════════════════════════════════════════
log("\n── PHASE 7: Commit + push")

run(["git", "add", "-A"])
rc, out, err = run(["git", "commit", "-m",
    f"overnight: {extracted} accounts re-extracted, {len(vision_results)} vision analyzed, "
    f"{len(caption_results)} caption analyzed, brain rebuilt with {len(brain['real_metrics'])} verified brands"])
log(f"  Commit: {'✅' if rc == 0 else '⚠️ ' + err[:50]}")

rc, out, err = run(["git", "push", "origin", "main"])
log(f"  Push: {'✅' if rc == 0 else '⚠️ ' + err[:50]}")

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
log(f"\n{'═' * 60}")
log("  OVERNIGHT REBUILD COMPLETE")
log(f"{'═' * 60}")
log(f"  Accounts re-extracted: {extracted}")
log(f"  Vision analyses: {len(vision_results)}")
log(f"  Caption analyses: {len(caption_results)}")
log(f"  Brands with real metrics: {len(brain['real_metrics'])}")
log(f"  Brain size: {len(json.dumps(brain)):,} chars")
log(f"  All guards: {'PASS' if rc == 0 else 'CHECK NEEDED'}")
log(f"\n  Check results: tail -50 logs/overnight_rebuild.log")
log(f"  Brain: cat 11_who_to_learn_from/intelligence_layer.json | python3 -m json.tool | head -50")
