#!/usr/bin/env python3
"""
deduplicate_obs.py
Detect and remove duplicate observations (same Instagram shortcode extracted twice).

Two-phase:
  Phase 1 (default): REPORT only — show what would be removed, no changes
  Phase 2 (--execute): DELETE approved duplicates (requires DELETE APPROVED from Mohamed)

Strategy:
  For each duplicate pair, keep the obs with more filled fields.
  Tie-break: keep the one with color_palette filled.
  Tie-break 2: keep the newer ULID (more recent extraction).
  Optionally merge unique fields from the loser into the winner before deletion.

Usage:
  python3 scripts/deduplicate_obs.py            # report only
  python3 scripts/deduplicate_obs.py --merge    # report with merge preview
  python3 scripts/deduplicate_obs.py --execute  # DELETE (requires DELETE APPROVED)
"""
import json, re, argparse
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

MERGE_FIELDS = [
    # (path_as_tuple, merge_strategy)
    # "take_if_winner_null" = fill winner's null with loser's value
    (("content_ref", "aspect_ratio"),         "take_if_winner_null"),
    (("content_ref", "video_duration_seconds"),"take_if_winner_null"),
    (("content_ref", "editing_pace"),          "take_if_winner_null"),
    (("content_ref", "carousel_slide_count"),  "take_if_winner_null"),
    (("visual_observations", "color_palette"), "take_if_winner_null"),
    (("visual_observations", "human_presence"),"take_if_winner_null"),
    (("visual_observations", "props"),         "take_if_winner_null"),
    (("voice_observations", "caption_text"),   "take_if_winner_null"),
    (("voice_observations", "caption_sentiment"),"take_if_winner_null"),
    (("voice_observations", "opener_formula"), "take_if_winner_null"),
    (("voice_observations", "has_emoji"),      "take_if_winner_null"),
    (("voice_observations", "notable_phrases"),"append_unique"),
    (("audio_strategy", "has_voiceover"),      "take_if_winner_null"),
    (("audio_strategy", "music_type"),         "take_if_winner_null"),
    (("audio_strategy", "has_subtitles"),      "take_if_winner_null"),
]


def _get_nested(d, path):
    cur = d
    for key in path:
        if not isinstance(cur, dict): return None
        cur = cur.get(key)
    return cur


def _set_nested(d, path, value):
    cur = d
    for key in path[:-1]:
        cur = cur.setdefault(key, {})
    cur[path[-1]] = value


def count_filled(d: dict) -> int:
    checks = [
        d.get("sector"),
        d.get("occasion"),
        (d.get("content_ref") or {}).get("content_type"),
        (d.get("content_ref") or {}).get("aspect_ratio"),
        (d.get("content_ref") or {}).get("caption_text"),
        (d.get("visual_observations") or {}).get("setting"),
        (d.get("visual_observations") or {}).get("color_palette"),
        (d.get("visual_observations") or {}).get("human_presence"),
        (d.get("voice_observations") or {}).get("caption_text"),
        (d.get("voice_observations") or {}).get("notable_phrases"),
        (d.get("audio_strategy") or {}).get("music_type"),
        (d.get("audio_strategy") or {}).get("has_voiceover"),
    ]
    return sum(1 for c in checks if c is not None and c != [] and c != "")


def pick_winner(f1: Path, d1: dict, f2: Path, d2: dict):
    """Return (winner_path, winner_data, loser_path, loser_data)."""
    c1, c2 = count_filled(d1), count_filled(d2)

    if c1 != c2:
        return (f1, d1, f2, d2) if c1 > c2 else (f2, d2, f1, d1)

    # Tie: prefer the one with color_palette
    cp1 = bool((d1.get("visual_observations") or {}).get("color_palette"))
    cp2 = bool((d2.get("visual_observations") or {}).get("color_palette"))
    if cp1 and not cp2: return (f1, d1, f2, d2)
    if cp2 and not cp1: return (f2, d2, f1, d1)

    # Tie: newer ULID = winner (lexicographically larger = more recent)
    return (f1, d1, f2, d2) if f1.stem > f2.stem else (f2, d2, f1, d1)


def merge_into_winner(winner: dict, loser: dict) -> tuple[dict, list]:
    """Merge missing fields from loser into winner. Returns (merged_dict, merge_log)."""
    merged = json.loads(json.dumps(winner))  # deep copy
    log = []
    for path, strategy in MERGE_FIELDS:
        w_val = _get_nested(winner, path)
        l_val = _get_nested(loser,  path)
        if l_val is None or l_val == "" or l_val == []:
            continue
        if strategy == "take_if_winner_null":
            if not w_val:
                _set_nested(merged, path, l_val)
                log.append(f"  + merged {'.'.join(path)} from loser")
        elif strategy == "append_unique":
            w_list = w_val or []
            l_list = l_val or []
            new_items = [x for x in l_list if x not in w_list]
            if new_items:
                _set_nested(merged, path, w_list + new_items)
                log.append(f"  + appended {len(new_items)} item(s) to {'.'.join(path)}")
    return merged, log


def build_obs_index():
    """shortcode → list of (file, data)"""
    idx = defaultdict(list)
    for f in OBS_ROOT.rglob("*.json"):
        d = json.loads(f.read_text())
        url = (d.get("content_ref") or {}).get("source_url", "")
        m = re.search(r"/p/([A-Za-z0-9_\-]+)/?", url)
        if m:
            idx[m.group(1)].append((f, d))
    return idx


def main():
    parser = argparse.ArgumentParser(description="OGZ Observation Deduplicator")
    parser.add_argument("--execute", action="store_true",
                        help="DELETE duplicates (only run after DELETE APPROVED from Mohamed)")
    parser.add_argument("--merge",   action="store_true",
                        help="Merge fields from loser before deleting (in report: show preview)")
    args = parser.parse_args()

    if args.execute:
        print("\n⚠️  EXECUTE MODE — Will permanently delete files.")
        print("  This requires DELETE APPROVED from Mohamed.\n")

    idx = build_obs_index()
    dupes = {sc: files for sc, files in idx.items() if len(files) > 1}

    if not dupes:
        print("✓ No duplicates found.")
        return

    W = 70
    print(f"\n{'═'*W}")
    print(f"  DUPLICATE OBSERVATION REPORT")
    print(f"  {len(dupes)} shortcodes with 2+ obs files")
    print(f"{'═'*W}\n")

    from collections import Counter
    acc_counts = Counter()
    to_delete = []
    to_merge  = []
    total_merges = 0
    same_data = 0
    richer    = 0

    for sc, files in sorted(dupes.items()):
        if len(files) != 2:
            print(f"  ⚠ {sc} has {len(files)} obs — skipping (manual review needed)")
            continue

        (fw, dw), (fl, dl) = files[0], files[1]
        fw, dw, fl, dl = *pick_winner(fw, dw, fl, dl),  # type: ignore
        fw, dw, fl, dl = fw, dw, fl, dl  # noqa

        # pick_winner returns 4 values
        winner_f, winner_d, loser_f, loser_d = pick_winner(files[0][0], files[0][1], files[1][0], files[1][1])

        acc = winner_d.get("account_handle_normalized", "")
        acc_counts[acc] += 1

        cw, cl = count_filled(winner_d), count_filled(loser_d)
        if abs(cw - cl) <= 1:
            same_data += 1
        else:
            richer += 1

        merged_d, merge_log = merge_into_winner(winner_d, loser_d)
        has_merge = len(merge_log) > 0
        if has_merge:
            total_merges += 1

        to_delete.append((loser_f, sc))
        to_merge.append((winner_f, merged_d, merge_log, has_merge))

    # Summary by account
    print(f"  BY ACCOUNT:")
    for acc, n in sorted(acc_counts.items(), key=lambda x: -x[1]):
        print(f"    {acc:<45}  {n} dupes")

    print(f"\n  SUMMARY:")
    print(f"    Total duplicate pairs:  {len(to_delete)}")
    print(f"    Both have same data:    {same_data}")
    print(f"    One has richer data:    {richer}")
    print(f"    Merges available:       {total_merges} (fields to rescue from losers)")
    print(f"    Files to delete:        {len(to_delete)}")
    print(f"    Corpus after dedup:     {648 - len(to_delete)} obs")

    if args.merge:
        print(f"\n  MERGE PREVIEW (fields rescued from losers):")
        merge_shown = 0
        for winner_f, merged_d, merge_log, has_merge in to_merge:
            if has_merge and merge_shown < 5:
                print(f"\n    Winner: {winner_f.name}")
                for line in merge_log:
                    print(f"   {line}")
                merge_shown += 1

    print(f"\n{'─'*W}")
    if not args.execute:
        print(f"  ℹ️  DRY RUN — no files changed.")
        print(f"  To execute: python3 scripts/deduplicate_obs.py --execute [--merge]")
        print(f"  (Requires DELETE APPROVED from Mohamed)\n")
        return

    # ── EXECUTE: merge + delete ───────────────────────────────────────────
    deleted = 0
    merged_count = 0

    for i, (loser_f, sc) in enumerate(to_delete):
        winner_f, merged_d, merge_log, has_merge = to_merge[i]
        if args.merge and has_merge:
            winner_f.write_text(json.dumps(merged_d, ensure_ascii=False, indent=2))
            merged_count += 1
        loser_f.unlink()
        deleted += 1

    print(f"\n  ✓ Deleted {deleted} duplicate files")
    if args.merge:
        print(f"  ✓ Merged data into {merged_count} winner files")
    print(f"  Corpus is now {sum(1 for _ in OBS_ROOT.rglob('*.json'))} obs\n")

    # Save report
    report = {
        "deleted": deleted,
        "merged": merged_count,
        "corpus_after": sum(1 for _ in OBS_ROOT.rglob("*.json")),
    }
    (LOGS / "dedup_report.json").write_text(json.dumps(report, indent=2))
    print(f"  Report saved: logs/dedup_report.json\n")


if __name__ == "__main__":
    main()
