#!/usr/bin/env python3
"""GENERATION IDENTITY LAYER (B095v step 1, L4 Bedrock) — the missing producer of stable IDs.

THE BEDROCK GAP (root-hunted 2026-06-22): the publish ledger (outcome_ledger.record_published,
B095w) and both its readers (outcome_receipt B094, outcome_question B095) are keyed on a
`subject_generation_ulid` + `brand_ulid` — but NO producer ever minted them. produce_batch
wrote post entries identified only by (handle, date, file); a produced piece therefore had no
stable identity to carry INTO the ledger when it went live. Both outcome readers ran honest-empty
not only for lack of live events but for lack of an identity to reference. This module is that
identity producer: the ONE place produce-time generation IDs are minted (Rule #6 — one source,
no parallel id schemes drifting apart; Rule #3 — same deterministic algorithm the readers use).

WHY DETERMINISTIC (CLAUDE.md "ULIDs, deterministic where possible"): a produced piece's identity
is content-addressed to its stable natural key, so re-running produce_batch does NOT re-mint a new
id for the same piece, and the publish-confirm card (step 2, staged) can reference a piece by an
id that never moves. Same 26-char Crockford-base32 shape as the ledger ecosystem
(generate_chains / outcome_receipt / outcome_question), so the join key is uniform end-to-end.

  subject_generation_ulid(handle, date, file) — identity of ONE produced post (the join key
      Hesham's metrics feed and the publish ledger both reference).
  brand_ulid(handle)                          — canonical identity of a brand/pilot. The handle
      is the stable natural key for the 3 pilots; this is the FIRST canonical brand id in the
      system (none existed before — visual_dna's `vdna_<handle>` is a per-organ id, not the brand).
"""
import hashlib

# Crockford base32 — identical to generate_chains.py / outcome_receipt.py / outcome_question.py.
ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def deterministic_ulid(seed: str) -> str:
    """Deterministic 26-char Crockford-base32 ULID from a seed (mirrors the ledger readers)."""
    val = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32], 16)
    out = []
    for _ in range(26):
        out.append(ULID_ALPHABET[val % 32])
        val //= 32
    return "".join(reversed(out))


def brand_ulid(handle: str) -> str:
    """Canonical, stable brand identity for a pilot, content-addressed to its handle.

    Raises ValueError on an empty handle (Rule #8: refuse, never mint an empty identity)."""
    h = (handle or "").strip()
    if not h:
        raise ValueError("brand_ulid: handle is required and non-empty")
    return deterministic_ulid("brand:" + h)


def subject_generation_ulid(handle: str, date: str, file: str) -> str:
    """Stable identity of ONE produced post — the join key into the publish ledger + metrics feed.

    Keyed on (handle, date, file): the natural key produce_batch already uses to name a post card.
    Re-running produce over the same piece yields the SAME id (idempotent identity).
    Raises ValueError if any component is empty (Rule #8)."""
    h, d, f = (handle or "").strip(), (date or "").strip(), (file or "").strip()
    if not (h and d and f):
        raise ValueError(
            f"subject_generation_ulid: handle/date/file all required and non-empty "
            f"(got handle={h!r}, date={d!r}, file={f!r})")
    return deterministic_ulid(f"gen:{h}:{d}:{f}")
