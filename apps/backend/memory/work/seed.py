"""Idempotent WorkOS bootstrap rows — populated from WOS-1 onward."""

from __future__ import annotations

from . import priority_policies


def ensure_default_priority_policy(con, owner_id: int = 1) -> None:
    """Seed the single active PriorityPolicy for an owner if none exists.

    Runs inside the migration's open connection so the write lands in the same
    transaction as the schema DDL (WORKOS_PHASE1_SCHEMA §12 step 7).
    """
    priority_policies.ensure_default_policy_in(con, owner_id)
