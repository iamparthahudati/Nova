"""Finance persistence — SQL only, no business rules."""

from .accounts import (
    archive_account,
    create_account,
    get_account_by_id,
    list_accounts,
    update_account,
)
from .categories import (
    create_category,
    get_category_by_id,
    list_categories,
    soft_delete_category,
    update_category,
)
from .merchants import (
    create_merchant,
    get_merchant_by_id,
    list_merchants,
    soft_delete_merchant,
    update_merchant,
)
from .seed import ensure_default_cash_account
from .transactions import (
    create_transaction,
    get_transaction_by_id,
    list_transactions,
    soft_delete_transaction,
    soft_delete_transfer_group,
    update_transaction,
)

__all__ = [
    "ensure_default_cash_account",
    "create_account",
    "get_account_by_id",
    "list_accounts",
    "update_account",
    "archive_account",
    "create_category",
    "get_category_by_id",
    "list_categories",
    "update_category",
    "soft_delete_category",
    "create_merchant",
    "get_merchant_by_id",
    "list_merchants",
    "update_merchant",
    "soft_delete_merchant",
    "create_transaction",
    "get_transaction_by_id",
    "list_transactions",
    "update_transaction",
    "soft_delete_transaction",
    "soft_delete_transfer_group",
]
