#!/usr/bin/env python3
"""
backfill_schema_v2_fields.py
Add new P0 fields (null) to all existing observations.
NEVER overwrites existing non-null values.

New fields added:
  voice_observations.caption_text         → null
  voice_observations.caption_word_count   → null
  voice_observations.hashtag_count        → null
  voice_observations.has_emoji            → null
  voice_observations.audio_strategy       → null (video obs get empty obj, image gets null)
  content_ref.video_duration_seconds      → null
  content_ref.aspect_ratio                → null

Run once. Safe to re-run (idempotent — skips already-set fields).
"""
import json
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"

VIDEO_TYPES = {"video", "reel"}


def main():
    stats = defaultdict(int)

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except:
            stats["parse_error"] += 1
            continue

        stats["total"] += 1
        changed = False

        # Ensure sub-dicts exist
        if not isinstance(data.get("voice_observations"), dict):
            data["voice_observations"] = {}
        if not isinstance(data.get("content_ref"), dict):
            data["content_ref"] = {}

        vo = data["voice_observations"]
        cr = data["content_ref"]
        ct = str(cr.get("content_type","") or "").lower()
        is_video = ct in VIDEO_TYPES

        # voice_observations — add only if key missing entirely
        for field in ["caption_text", "caption_word_count", "hashtag_count", "has_emoji"]:
            if field not in vo:
                vo[field] = None
                changed = True
                stats[f"added_{field}"] += 1

        # audio_strategy — null for images/carousels, empty obj for video
        if "audio_strategy" not in vo:
            if is_video:
                vo["audio_strategy"] = {
                    "has_voiceover": None,
                    "voiceover_language": None,
                    "music_type": None,
                    "has_subtitles": None,
                }
            else:
                vo["audio_strategy"] = None
            changed = True
            stats["added_audio_strategy"] += 1

        # content_ref
        for field in ["video_duration_seconds", "aspect_ratio"]:
            if field not in cr:
                cr[field] = None
                changed = True
                stats[f"added_{field}"] += 1

        if changed:
            stats["files_modified"] += 1
            obs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    print(f"Backfill complete")
    print(f"  Total obs processed  : {stats['total']}")
    print(f"  Files modified       : {stats['files_modified']}")
    print(f"\n  Fields added:")
    for field in ["caption_text","caption_word_count","hashtag_count","has_emoji",
                  "audio_strategy","video_duration_seconds","aspect_ratio"]:
        print(f"    {field:<30} +{stats[f'added_{field}']}")


if __name__ == "__main__":
    main()
