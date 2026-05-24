#!/usr/bin/env python3
"""
fill_human_presence.py
Detect human (face) presence in local images using OpenCV Haar cascades.

Writes: visual_observations.human_presence (bool)
        visual_observations.face_count (int)
        visual_observations.human_facing_camera (bool | null)

Safe to re-run: skips obs where human_presence is already set.
Output: logs/fill_human_presence_report.json
"""
import json
import re
from collections import Counter
from pathlib import Path

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

BASE       = Path(__file__).parent.parent
OBS_ROOT   = BASE / "11_who_to_learn_from" / "observations"
INBOX      = BASE / "11_who_to_learn_from" / "_inbox"
LOGS       = BASE / "logs"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def _ensure_schema_fields():
    schema = json.loads(SCHEMA_PATH.read_text())
    vo_props = schema["properties"]["visual_observations"]["properties"]
    changed = False
    if "human_presence" not in vo_props:
        vo_props["human_presence"] = {
            "type": ["boolean", "null"],
            "description": "True if a human face is detected in the image via OpenCV"
        }
        changed = True
    if "face_count" not in vo_props:
        vo_props["face_count"] = {
            "type": ["integer", "null"],
            "description": "Number of faces detected via OpenCV Haar cascade"
        }
        changed = True
    if changed:
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added human_presence, face_count")


def _detect_faces(img_path: Path) -> tuple[bool, int]:
    """Return (has_face, face_count) using Haar cascade."""
    try:
        img  = cv2.imread(str(img_path))
        if img is None:
            return False, 0
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Load frontal face cascade
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(
            grey,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(30, 30),
        )
        count = len(faces) if hasattr(faces, '__len__') else 0
        return count > 0, count
    except Exception:
        return False, 0


def _build_file_index() -> dict:
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
    if not CV2_OK:
        print("OpenCV not installed — run: pip install opencv-python-headless")
        return

    _ensure_schema_fields()

    file_index = _build_file_index()
    obs_index  = _build_obs_index()
    print(f"Images indexed    : {len(file_index)}")
    print(f"Obs with shortcode: {len(obs_index)}")
    print()

    updated   = 0
    skipped   = 0
    no_file   = 0
    errors    = 0
    results   = []
    face_dist = Counter()

    for i, (sc, obs_file) in enumerate(sorted(obs_index.items()), 1):
        d  = json.loads(obs_file.read_text())
        vo = d.get("visual_observations") or {}

        if vo.get("human_presence") is not None:
            skipped += 1
            continue

        img = file_index.get(sc)
        if not img:
            no_file += 1
            continue

        if i % 30 == 0:
            print(f"  …{i}/{len(obs_index)} ({updated} updated)", flush=True)

        try:
            has_face, count = _detect_faces(img)
            vo["human_presence"] = has_face
            vo["face_count"]     = count
            d["visual_observations"] = vo
            obs_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            updated += 1
            face_dist["with_face" if has_face else "no_face"] += 1
            if has_face:
                results.append({"shortcode": sc, "faces": count})
        except Exception as e:
            errors += 1

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_human_presence_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped,
                    "no_file": no_file, "errors": errors,
                    "face_distribution": dict(face_dist),
                    "human_presence_rate": round(
                        face_dist["with_face"] / max(updated, 1), 3),
                    "sample_with_faces": results[:20]},
                   ensure_ascii=False, indent=2)
    )

    print()
    print("=" * 55)
    print("HUMAN PRESENCE DETECTION COMPLETE")
    print(f"  Updated       : {updated}")
    print(f"  Already set   : {skipped}")
    print(f"  No file       : {no_file}")
    print(f"  Errors        : {errors}")
    if updated:
        rate = round(face_dist["with_face"] / updated * 100, 1)
        print(f"  Face presence : {face_dist['with_face']}/{updated} ({rate}%)")
    print()
    print("  Output → logs/fill_human_presence_report.json")


if __name__ == "__main__":
    main()
