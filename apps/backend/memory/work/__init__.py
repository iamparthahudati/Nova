"""WorkOS persistence — SQL only, no business rules."""

from .migrations import (
    FORBIDDEN_DERIVED_COLUMNS,
    migrate_work_schema,
    verify_work_table_governance,
)

__all__ = [
    "FORBIDDEN_DERIVED_COLUMNS",
    "migrate_work_schema",
    "verify_work_table_governance",
]
