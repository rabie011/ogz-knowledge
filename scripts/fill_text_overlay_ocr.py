#!/usr/bin/env python3
"""
fill_text_overlay_ocr.py
Run Tesseract OCR on local images to extract actual text from overlays.

For obs with local images:
  - Run Tesseract (Arabic + English)
  - If text found: update/add text_overlays with real content_summary
  - Detect if text is Arabic, English, or bilingual

Skips obs that already have text_overlays with non-empty content_summary.
Output: logs/fill_text_overlay_ocr_report.json
"""
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
INBOX       = BASE / "11_who_to_learn_from" / "_inbox"
LOGS        = BASE / "logs"
TESSERACT   = "/opt/homebrew/bin/tesseract"
IMAGE_EXTS  = {".jpg", ".jpeg", ".png"}

AR_RE = re.compile(r'[؀-ۿݐ-ݿ]+')
EN_RE = re.compile(r'[a-zA-Z]{3,}')


def _run_ocr(img_path: Path) -> str:
    """Run Tesseract on image, return extracted text."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_base = Path(tmpdir) / "out"
            subprocess.run(
                [TESSERACT, str(img_path), str(out_base),
                 "-l", "ara+eng",
                 "--psm", "3",
                 "txt"],
                capture_output=True, timeout=30,
            )
            out_file = out_base.with_suffix(".txt")
            if out_file.exists():
                text = out_file.read_text(encoding="utf-8", errors="ignore")
                # Clean whitespace noise
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                return " ".join(lines)
    except Exception:
        pass
    return ""


def _detect_language(text: str) -> str:
    has_ar = bool(AR_RE.search(text))
    has_en = bool(EN_RE.search(text))
    if has_ar and has_en: return "bilingual"
    if has_ar:            return "arabic"
    if has_en:            return "english"
    return "none"


def _build_file_index() -> dict:
    """shortcode → best local image (non-thumb, prefer _1 for carousels)."""
    index = {}
    for p in INBOX.rglob("*"):
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        if "_thumb" in p.stem:
            continue
        stem = p.stem
        m = re.match(r'^(.+)_(\d+)$', stem)
        if m:
            sc = m.group(1)
            if int(m.group(2)) != 1:
                continue
            stem = sc
        if "_" in stem:
            last = stem.split("_")[-1]
            if len(last) >= 8 and re.match(r"^[A-Za-z0-9_\-]+$", last):
                stem = last
        if stem not in index:
            index[stem] = p
    return index


def _build_obs_index() -> dict:
    idx = {}
    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        url = (d.get("content_ref") or {}).get("source_url", "")
        m   = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        if m:
            idx[m.group(1)] = f
    return idx


def main():
    print("Building indexes…", flush=True)
    file_index = _build_file_index()
    obs_index  = _build_obs_index()
    print(f"Images indexed   : {len(file_index)}")
    print(f"Obs with shortcode: {len(obs_index)}")
    print()

    updated    = 0
    skipped    = 0
    no_text    = 0
    no_file    = 0
    errors     = 0
    lang_dist  = Counter()
    results    = []

    for i, (sc, obs_file) in enumerate(sorted(obs_index.items()), 1):
        d  = json.loads(obs_file.read_text())
        vo = d.get("visual_observations") or {}

        # Skip if overlays already have content_summary filled
        overlays = vo.get("text_overlays") or []
        if overlays and any(o.get("content_summary") for o in overlays
                            if isinstance(o, dict)):
            skipped += 1
            continue

        img = file_index.get(sc)
        if not img:
            no_file += 1
            continue

        if i % 20 == 0:
            print(f"  …{i}/{len(obs_index)} ({updated} updated)", flush=True)

        try:
            text = _run_ocr(img)
            # Require at least 5 chars of real content
            if len(text.strip()) < 5:
                no_text += 1
                continue

            lang = _detect_language(text)
            lang_dist[lang] += 1

            # Write back — replace text_overlays entirely with OCR result
            new_overlay = {
                "language": lang,
                "content_summary": text[:400],  # cap at 400 chars
            }

            if overlays:
                # Update first overlay if it has no content_summary
                first = overlays[0] if isinstance(overlays[0], dict) else {}
                if not first.get("content_summary"):
                    overlays[0] = {**first, **new_overlay}
                else:
                    overlays = [new_overlay] + overlays
            else:
                overlays = [new_overlay]

            vo["text_overlays"] = overlays
            d["visual_observations"] = vo
            obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            updated += 1
            results.append({
                "shortcode": sc,
                "language": lang,
                "text_preview": text[:80],
            })

        except Exception as e:
            errors += 1

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_text_overlay_ocr_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_text_found": no_text, "no_file": no_file,
                    "errors": errors,
                    "language_distribution": dict(lang_dist.most_common()),
                    "sample": results[:20]},
                   ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("TEXT OVERLAY OCR COMPLETE")
    print(f"  Updated      : {updated}")
    print(f"  Already set  : {skipped}")
    print(f"  No text found: {no_text}")
    print(f"  No file      : {no_file}")
    print(f"  Errors       : {errors}")
    print()
    print("  Language distribution:")
    for lang, c in lang_dist.most_common():
        print(f"    {lang:<12} {c}")
    print()
    print("  Output → logs/fill_text_overlay_ocr_report.json")


if __name__ == "__main__":
    main()
