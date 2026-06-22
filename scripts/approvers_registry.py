#!/usr/bin/env python3
"""APPROVERS REGISTRY (B156, June 12). WHO may confirm WHAT — and the ledger
gate refuses trust-moving events with machine confirmers at WRITE time (the
trust replay already filters reads; now the door itself checks)."""

# humans — the only confirmers that move trust
HUMANS = {"mohamed", "alhareth", "client"}
# system writers — legitimate for proposals/reports, NEVER for trust-moving events
SYSTEM = {"staleness_report", "drift_watch", "menu_sync", "process_rejection", "trust_ladder",
           "pending", "pending_client", "test"}
TRUST_MOVING_TYPES = {"client_approved", "pick_selected", "client_rejected"}


def check_confirmer(event: dict):
    """Raises on a trust-moving event with a non-human confirmer."""
    c = (event.get("confirmer") or "").lower()
    if event.get("type") in TRUST_MOVING_TYPES and c not in HUMANS and c != "pending":
        raise ValueError(f"trust-moving event '{event.get('type')}' needs a HUMAN confirmer, got '{c}' "
                          f"(registry: {sorted(HUMANS)})")
    return True
