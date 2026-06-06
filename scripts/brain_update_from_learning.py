#!/usr/bin/env python3
"""
brain_update_from_learning.py — Learning Loop Closer for OGZ Knowledge Base

Reads logs/learning_store.jsonl → groups failures by category →
proposes specific brain rule updates → writes proposals to
logs/system/BRAIN_UPDATE_PROPOSALS.md for Mohamed to review.

IMPORTANT: This script NEVER touches intelligence_layer.json directly.
It only writes proposals. Mohamed approves, then apply_brain_proposals.py executes.

Usage:
    python3 scripts/brain_update_from_learning.py            # analyze + write proposals
    python3 scripts/brain_update_from_learning.py --apply 001  # delegate to apply script
    python3 scripts/brain_update_from_learning.py --dry-run    # print proposals, don't write file
    python3 scripts/brain_update_from_learning.py --min-freq 2 # lower threshold (default 3)
"""

import json
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, Counter
from typing import Any


# ─── Paths ────────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent.parent
LEARNING_STORE   = BASE / "logs" / "learning_store.jsonl"
BRAIN_FILE       = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
PROPOSALS_DIR    = BASE / "logs" / "system"
PROPOSALS_FILE   = PROPOSALS_DIR / "BRAIN_UPDATE_PROPOSALS.md"
APPLY_SCRIPT     = BASE / "scripts" / "apply_brain_proposals.py"

MIN_FREQ_DEFAULT = 3   # propose only when category appears ≥ this many times


# ─── Category Detection ───────────────────────────────────────────────────────

# Each entry is (category_key, display_label, list_of_regex_patterns_on_mistake_text)
CATEGORY_RULES: list[tuple[str, str, list[str]]] = [
    (
        "timeout_error",
        "Pipeline Timeout",
        [r"TimeoutError", r"timed out"],
    ),
    (
        "no_saudi_markers",
        "No Saudi dialect markers",
        [
            r"no saudi markers?", r"generic gulf arabic", r"gulf dialect detected",
            r"not saudi", r"lacks? saudi", r"missing saudi", r"saudi dialect",
            r"زين\b", r"شنو\b", r"جذي\b",          # kuwaiti/emirati markers
        ],
    ),
    (
        "wrong_product_name",
        "Wrong or missing product name",
        [
            r"wrong product", r"missing product", r"product name",
            r"incorrect.*product", r"product.*incorrect",
        ],
    ),
    (
        "missing_occasion_word",
        "Missing required occasion keyword",
        [
            r"missing occasion", r"occasion keyword", r"no occasion",
            r"lacks? occasion", r"occasion.*missing", r"occasion word",
        ],
    ),
    (
        "gulf_dialect_detected",
        "Gulf/non-Saudi dialect used",
        [
            r"gulf dialect", r"kuwaiti", r"emirati", r"bahraini",
            r"egyptian.*dialect", r"non.saudi", r"مو سعودي",
        ],
    ),
    (
        "caption_too_long",
        "Caption exceeds optimal length",
        [
            r"too long", r"caption.*length", r"long caption",
            r"exceed.*length", r"overly? long",
        ],
    ),
    (
        "caption_truncated",
        "Caption cuts off / incomplete ending",
        [
            r"cuts? off", r"abruptly", r"truncat", r"incomplete.*end",
            r"incomplete.*caption", r"hangs?",
        ],
    ),
    (
        "low_cultural_depth",
        "Low cultural depth / generic content",
        [
            r"cultural depth", r"generic.*content", r"generic.*post",
            r"lacks? cultural", r"missing.*cultural", r"cultural.*miss",
            r"no cultural",
        ],
    ),
    (
        "missing_hashtag",
        "Missing brand or occasion hashtag",
        [
            r"missing.*hashtag", r"hashtag.*missing", r"no hashtag",
            r"lacks? hashtag",
        ],
    ),
    (
        "msa_formal_language",
        "Formal MSA language instead of Saudi spoken",
        [
            r"formal.*arabic", r"msa", r"formal msa", r"too formal",
            r"literary arabic", r"فصحى",
        ],
    ),
    (
        "lack_of_usp",
        "Lack of Unique Selling Proposition",
        [
            r"unique selling", r"usp", r"selling proposition",
            r"generic.*brand", r"doesn.t.*differentiat", r"not.distinctive",
        ],
    ),
    (
        "weak_engagement_hook",
        "Weak or missing engagement hook / CTA",
        [
            r"engagement hook", r"call.to.action", r"cta",
            r"lacks? cta", r"missing.*cta", r"weak.*hook",
        ],
    ),
]


def detect_categories(mistake_text: str) -> list[str]:
    """Return list of category keys that match the mistake text."""
    text_lower = mistake_text.lower()
    matched = []
    for cat_key, _label, patterns in CATEGORY_RULES:
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                matched.append(cat_key)
                break
    return matched if matched else ["uncategorized"]


# ─── Brain Proposal Builder ───────────────────────────────────────────────────

def load_brain() -> dict:
    """Load intelligence_layer.json — read-only."""
    with open(BRAIN_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_entries() -> list[dict]:
    """Load all entries from learning_store.jsonl."""
    if not LEARNING_STORE.exists():
        return []
    entries = []
    for line in LEARNING_STORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def group_failures(entries: list[dict]) -> dict[str, list[dict]]:
    """
    Group ONLY failing entries by category.

    Failures = score < 70 (the quality_gate minimum_score) OR score == 0.
    Exception entries (score=0, 'exception:' prefix) are kept as a
    separate sub-group within their category.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        score = entry.get("score", 100)
        mistake = entry.get("mistake", "")
        if score >= 70 and not mistake.startswith("exception:"):
            continue   # pass — not a failure
        cats = detect_categories(mistake)
        for cat in cats:
            grouped[cat].append(entry)
    return dict(grouped)


def extract_evidence(entries: list[dict], category: str) -> dict:
    """
    Extract structured evidence for a proposal:
    - handles affected
    - sample mistake texts (up to 5)
    - whether exception-type or quality-type
    """
    handles = Counter(e.get("handle", "unknown") for e in entries)
    is_exception = all(
        e.get("mistake", "").startswith("exception:")
        for e in entries
    )
    samples = []
    for e in entries[:5]:
        m = e.get("mistake", "")
        # truncate long mistake strings for readability
        samples.append(m[:120].rstrip() + ("…" if len(m) > 120 else ""))

    return {
        "handles": dict(handles.most_common()),
        "is_exception_type": is_exception,
        "samples": samples,
    }


# ─── Proposal Templates ───────────────────────────────────────────────────────

def build_proposal(
    index: int,
    category: str,
    label: str,
    entries: list[dict],
    brain: dict,
    evidence: dict,
) -> dict:
    """
    Return a proposal dict with:
        id, category, label, frequency, path_in_brain,
        proposed_action, rationale, evidence, status
    """
    freq = len(entries)
    handles_str = ", ".join(
        f"{h} ({n})" for h, n in evidence["handles"].items()
    )

    # ── Specialised logic per category ──────────────────────────────────────

    if category == "timeout_error":
        path    = "quality_gate → auto_fixes → timeout_retry"
        action  = (
            "Add timeout_retry policy: max 2 retries with 5 s back-off before "
            "logging to learning_store. Currently there is NO retry — every "
            "timeout burns a learning entry."
        )
        rationale = (
            f"{freq} timeout errors recorded across {len(evidence['handles'])} account(s). "
            "All scored 0 and pollute failure stats without representing quality issues."
        )

    elif category == "no_saudi_markers":
        current_markers = (
            brain.get("arabic_quality_rules", {})
                 .get("saudi_markers", {})
                 .get("use", [])
        )
        path   = "arabic_quality_rules → saudi_markers → use"
        action = (
            "Add 'وياكم' and 'يا حلا' to the saudi_markers use-list. "
            "Current list has حيّاكم but misses common Najdi/Hejazi warm variants. "
            "Also add a hard-fail rule: output without any saudi_marker token → auto-reject, "
            "not just soft-warn."
        )
        rationale = (
            f"{freq} captions failed for missing Saudi dialect markers. "
            f"Affected accounts: {handles_str}."
        )

    elif category == "wrong_product_name":
        path   = "brand_product_names → [affected handles]"
        affected = list(evidence["handles"].keys())
        action = (
            f"Verify product name entries for: {', '.join(affected)}. "
            "Add a pre-generation product-name assertion: if brand is known and "
            "product_name slot is empty, hard-block generation before calling LLM."
        )
        rationale = (
            f"{freq} failures due to wrong or missing product names across "
            f"{len(evidence['handles'])} brands."
        )

    elif category == "missing_occasion_word":
        path   = "occasion_required_words → [occasion_key]"
        action = (
            "Add occasion_required_words enforcement to quality_gate: "
            "if occasion is known and caption contains none of the required words, "
            "auto-inject the first required word OR reject (hard-block). "
            "Currently this is only a soft_warning."
        )
        rationale = (
            f"{freq} captions missing required occasion keywords. "
            "quality_gate lists these as soft_warnings but they never get auto-fixed."
        )

    elif category == "gulf_dialect_detected":
        avoid_list = (
            brain.get("arabic_quality_rules", {})
                 .get("saudi_markers", {})
                 .get("avoid", [])
        )
        path   = "arabic_quality_rules → saudi_markers → avoid"
        action = (
            "Promote Gulf-dialect detection from soft_warning to hard_block. "
            "Currently 'gulf_dialect_detected' tokens (زين, شنو, جذي) are listed "
            "in the avoid list but only in docs — they are not checked at runtime. "
            "Add a runtime check in quality_gate."
        )
        rationale = (
            f"{freq} captions used Gulf/non-Saudi dialect. "
            f"Affected: {handles_str}."
        )

    elif category == "caption_too_long":
        path   = "arabic_quality_rules → caption_structure → length"
        action = (
            "Add hard length cap: if len(caption) > 150 chars and sector != long_form, "
            "auto-trim to 100 chars at natural sentence boundary. "
            "Current guidance is '30-80 chars optimal' but no enforcement exists."
        )
        rationale = (
            f"{freq} captions cited for being too long. "
            "The length guidance exists in the brain but is advisory only."
        )

    elif category == "caption_truncated":
        path   = "quality_gate → hard_blocks"
        action = (
            "Add truncation detector to hard_blocks: if caption ends mid-word "
            "or ends with a comma/conjunction, flag as 'incomplete_caption' and reject. "
            "Pattern: ends with [,،وفلب] or capital Arabic letter followed by end of string."
        )
        rationale = (
            f"{freq} captions were flagged as truncated/cut-off. "
            f"Affected: {handles_str}."
        )

    elif category == "low_cultural_depth":
        path   = "arabic_quality_rules → caption_structure + cultural_guardrails"
        action = (
            "Add cultural_depth scoring rule: caption must reference at least ONE of "
            "[saudi_cultural_references.food, occasions, pride, places] to clear cultural_depth check. "
            "Generic product captions with no cultural anchor → soft-fail, add cultural hook."
        )
        rationale = (
            f"{freq} captions cited for low cultural depth / generic content. "
            f"Affected: {handles_str}."
        )

    elif category == "missing_hashtag":
        path   = "arabic_quality_rules → proven_caption_patterns + quality_gate"
        action = (
            "Add hashtag presence check: every caption must include at least ONE "
            "brand hashtag (from brand_product_names → hashtag key). "
            "Add auto_fix rule: if no hashtag present, append brand hashtag from brand profile."
        )
        rationale = (
            f"{freq} captions missing brand/occasion hashtag. "
            f"Affected: {handles_str}."
        )

    elif category == "msa_formal_language":
        path   = "quality_gate → auto_fixes → msa_replace"
        action = (
            "Expand msa_replace dictionary with additional high-frequency formal words: "
            "تفضلوا→تعالوا already exists. Add: "
            "لاحظنا→شفنا, نقدم→نقدملكم, يسعدنا→يفرحنا, جميع→كل, الحصول→تاخذ."
        )
        rationale = (
            f"{freq} captions cited for formal MSA language. "
            "The existing msa_replace list is short; expanding it closes this gap."
        )

    elif category == "lack_of_usp":
        path   = "arabic_quality_rules → proven_caption_patterns + brand_profiles"
        action = (
            "Add USP injection rule: if brand has a usp_hook in brand_profiles and "
            "caption does not contain any usp_token, auto-prepend the short USP phrase. "
            "This requires adding a usp_hook field to brand_profiles entries."
        )
        rationale = (
            f"{freq} captions lacked a Unique Selling Proposition. "
            f"Affected brands: {handles_str}."
        )

    elif category == "weak_engagement_hook":
        path   = "arabic_quality_rules → caption_structure → ending"
        action = (
            "Strengthen the ending rule: caption must end with EITHER "
            "a brand hashtag OR a direct question (شرايكم؟, وش رأيكم؟) OR an imperative CTA "
            "(اطلب الحين, جربه). Generic captions ending with '.' → auto-add appropriate CTA "
            "based on sector template."
        )
        rationale = (
            f"{freq} captions cited for weak/missing engagement hooks or CTAs. "
            f"Affected: {handles_str}."
        )

    else:  # uncategorized
        path   = "arabic_quality_rules (review needed)"
        action = (
            f"Review {freq} uncategorized failures manually. "
            "Consider adding a new category rule to brain_update_from_learning.py "
            "if a clear pattern emerges."
        )
        rationale = (
            f"{freq} failures could not be mapped to a known category. "
            f"Affected: {handles_str}. "
            "Sample: " + (evidence["samples"][0] if evidence["samples"] else "—")
        )

    return {
        "id": f"{index:03d}",
        "category": category,
        "label": label,
        "frequency": freq,
        "path_in_brain": path,
        "proposed_action": action,
        "rationale": rationale,
        "handles": evidence["handles"],
        "samples": evidence["samples"],
        "is_exception_type": evidence["is_exception_type"],
        "status": "PENDING",
    }


# ─── Markdown Renderer ────────────────────────────────────────────────────────

def render_proposals_md(proposals: list[dict], total_entries: int, total_failures: int) -> str:
    """Render proposals as Markdown."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# BRAIN UPDATE PROPOSALS",
        "",
        f"Generated: {now}  ",
        f"Source: `logs/learning_store.jsonl`  ",
        f"Total entries analyzed: {total_entries}  ",
        f"Total failures: {total_failures}  ",
        f"Proposals generated: {len(proposals)}  ",
        "",
        "> **Workflow:** Mohamed reads this file, marks `[APPROVED]` or `[REJECTED]` on each proposal,",
        "> then runs `python3 scripts/apply_brain_proposals.py --apply <ID>` to execute approved ones.",
        "> The apply script prints what it will do before writing anything.",
        "",
        "---",
        "",
    ]

    if not proposals:
        lines += [
            "## No proposals at this time.",
            "",
            f"No failure category reached the minimum frequency threshold.",
            "Run with `--min-freq 1` to see all single-occurrence patterns.",
            "",
        ]
        return "\n".join(lines)

    for p in proposals:
        tag = "[EXCEPTION-TYPE — runtime fix, not content fix]" if p["is_exception_type"] else ""
        lines += [
            f"## PROPOSAL {p['id']} — {p['label']} {tag}",
            "",
            f"**Category:** `{p['category']}`  ",
            f"**Frequency:** {p['frequency']} failure(s)  ",
            f"**Brain path:** `{p['path_in_brain']}`  ",
            "",
            "**Proposed change:**",
            f"> {p['proposed_action']}",
            "",
            "**Rationale:**",
            f"> {p['rationale']}",
            "",
        ]

        if p["handles"]:
            handle_list = ", ".join(
                f"`{h}` ({n})" for h, n in list(p["handles"].items())[:8]
            )
            lines.append(f"**Affected handles:** {handle_list}  ")
            lines.append("")

        if p["samples"]:
            lines.append("**Evidence (up to 5 samples):**")
            for i, s in enumerate(p["samples"], 1):
                lines.append(f"{i}. `{s}`")
            lines.append("")

        lines += [
            f"**Status:** `[PENDING Mohamed approval]`",
            "",
            "---",
            "",
        ]

    lines += [
        "## How to Apply",
        "",
        "```bash",
        "# Dry-run a specific proposal (shows what would change, no write):",
        "python3 scripts/apply_brain_proposals.py --dry-run 001",
        "",
        "# Apply a proposal:",
        "python3 scripts/apply_brain_proposals.py --apply 001",
        "",
        "# Apply all APPROVED proposals:",
        "python3 scripts/apply_brain_proposals.py --apply-all",
        "```",
        "",
    ]

    return "\n".join(lines)


# ─── Terminal Summary ─────────────────────────────────────────────────────────

def print_summary(
    proposals: list[dict],
    total_entries: int,
    total_failures: int,
    min_freq: int,
    output_path: Path | None,
):
    SEP = "=" * 62
    print(SEP)
    print("  OGZ BRAIN UPDATE ANALYZER")
    print(SEP)
    print(f"  Source       : {LEARNING_STORE.relative_to(BASE)}")
    print(f"  Entries read : {total_entries}")
    print(f"  Failures     : {total_failures}")
    print(f"  Min threshold: {min_freq} occurrences")
    print(f"  Proposals    : {len(proposals)}")
    if output_path:
        print(f"  Output       : {output_path.relative_to(BASE)}")
    print(SEP)

    if not proposals:
        print("  No recurring patterns reached the threshold.")
        print(f"  Try --min-freq 1 to see all patterns.")
    else:
        print()
        print(f"  {'ID':>4}  {'Freq':>4}  Category")
        print(f"  {'-'*4}  {'-'*4}  {'-'*40}")
        for p in proposals:
            exc_tag = " [TIMEOUT/EXCEPTION]" if p["is_exception_type"] else ""
            print(f"  {p['id']:>4}  {p['frequency']:>4}  {p['category']}{exc_tag}")
        print()
        print("  Next step: review proposals file, then:")
        print("  python3 scripts/apply_brain_proposals.py --apply <ID>")
    print(SEP)


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(min_freq: int = MIN_FREQ_DEFAULT, dry_run: bool = False) -> list[dict]:
    """Core analysis. Returns list of proposals."""
    entries = load_entries()
    if not entries:
        print(f"[WARNING] {LEARNING_STORE} is empty or missing. No proposals generated.")
        return []

    brain = load_brain()
    grouped = group_failures(entries)

    total_failures = sum(len(v) for v in grouped.values())

    # Sort categories by frequency descending
    sorted_cats = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

    proposals = []
    idx = 1
    for cat_key, cat_entries in sorted_cats:
        if len(cat_entries) < min_freq:
            continue
        # Find display label
        label = next(
            (lbl for k, lbl, _ in CATEGORY_RULES if k == cat_key),
            cat_key.replace("_", " ").title()
        )
        evidence = extract_evidence(cat_entries, cat_key)
        proposal = build_proposal(idx, cat_key, label, cat_entries, brain, evidence)
        proposals.append(proposal)
        idx += 1

    md = render_proposals_md(proposals, len(entries), total_failures)

    output_path = None
    if not dry_run:
        PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
        PROPOSALS_FILE.write_text(md, encoding="utf-8")
        output_path = PROPOSALS_FILE

    print_summary(proposals, len(entries), total_failures, min_freq, output_path)

    if dry_run:
        print("\n--- DRY-RUN: Proposals (not written) ---\n")
        print(md)

    return proposals


def delegate_to_apply(proposal_id: str):
    """Hand off to apply_brain_proposals.py for the actual write."""
    if not APPLY_SCRIPT.exists():
        print(f"[ERROR] apply_brain_proposals.py not found at {APPLY_SCRIPT}")
        print("Run brain_update_from_learning.py first to generate proposals,")
        print("then the apply script can read them.")
        sys.exit(1)
    import subprocess
    result = subprocess.run(
        [sys.executable, str(APPLY_SCRIPT), "--apply", proposal_id],
        cwd=BASE
    )
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze learning failures and propose brain rule updates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--apply",
        metavar="ID",
        help="Delegate application of a specific proposal to apply_brain_proposals.py",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposals to terminal without writing the file",
    )
    parser.add_argument(
        "--min-freq",
        type=int,
        default=MIN_FREQ_DEFAULT,
        help=f"Minimum occurrences to generate a proposal (default: {MIN_FREQ_DEFAULT})",
    )
    args = parser.parse_args()

    if args.apply:
        delegate_to_apply(args.apply)
        return  # unreachable — delegate exits

    run(min_freq=args.min_freq, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
