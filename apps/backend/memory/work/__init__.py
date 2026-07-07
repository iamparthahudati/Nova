"""WorkOS persistence — SQL only, no business rules."""

from .migrations import (
    FORBIDDEN_DERIVED_COLUMNS,
    migrate_work_phase1,
    migrate_work_schema,
    verify_work_table_governance,
)

# Bumped per additive schema gate; desktop/backend negotiate before write.
WORK_SCHEMA_VERSION = 1

__all__ = [
    "FORBIDDEN_DERIVED_COLUMNS",
    "WORK_SCHEMA_VERSION",
    "migrate_work_phase1",
    "migrate_work_schema",
    "verify_work_table_governance",
]
