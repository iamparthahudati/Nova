"""WorkOS domain errors."""

from __future__ import annotations


class WorkValidationError(ValueError):
    """Input failed WorkOS business validation."""


class WorkNotFoundError(LookupError):
    """A referenced WorkOS aggregate does not exist or is not owned."""


class WorkConflictError(RuntimeError):
    """Optimistic-concurrency clash or illegal lifecycle transition.

    Raised when a write matches no live row for the supplied `updated_at`
    token, or a state precondition (e.g. project archived) is violated.
    Maps to HTTP 409 (WORKOS_PHASE1_SCHEMA §1.6).
    """
