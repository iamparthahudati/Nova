"""Pure MutationEvent builders for finance operations."""

from __future__ import annotations

from runtime.mutation_event import MutationEvent


def _entity_metadata(row: dict) -> dict:
    entity_id = row.get("id")
    return {"entity_id": entity_id} if entity_id is not None else {}


def _row_dict(entity) -> dict:
    if hasattr(entity, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(entity)
    return dict(entity)


def build_account_created(account) -> MutationEvent:
    row = _row_dict(account)
    return MutationEvent(
        event_type="finance.account.created",
        entity_type="account",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_account_updated(account) -> MutationEvent:
    row = _row_dict(account)
    return MutationEvent(
        event_type="finance.account.updated",
        entity_type="account",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_account_archived(account) -> MutationEvent:
    row = _row_dict(account)
    return MutationEvent(
        event_type="finance.account.archived",
        entity_type="account",
        operation="archive",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_transaction_created(transaction) -> MutationEvent:
    row = _row_dict(transaction)
    return MutationEvent(
        event_type="finance.transaction.created",
        entity_type="transaction",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_transaction_updated(transaction) -> MutationEvent:
    row = _row_dict(transaction)
    return MutationEvent(
        event_type="finance.transaction.updated",
        entity_type="transaction",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_transaction_deleted(transaction) -> MutationEvent:
    row = _row_dict(transaction)
    return MutationEvent(
        event_type="finance.transaction.deleted",
        entity_type="transaction",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_transfer_created(legs: list, transfer_group_id: str) -> MutationEvent:
    entity = {"legs": [_row_dict(leg) for leg in legs], "transfer_group_id": transfer_group_id}
    return MutationEvent(
        event_type="finance.transfer.created",
        entity_type="transaction",
        operation="transfer",
        entity=entity,
        metadata={"transfer_group_id": transfer_group_id},
    )


def build_card_payment_created(legs: list, transfer_group_id: str) -> MutationEvent:
    entity = {"legs": [_row_dict(leg) for leg in legs], "transfer_group_id": transfer_group_id}
    return MutationEvent(
        event_type="finance.card_payment.created",
        entity_type="transaction",
        operation="card_payment",
        entity=entity,
        metadata={"transfer_group_id": transfer_group_id},
    )


def build_statement_paid(
    legs: list,
    transfer_group_id: str,
    statement_id: int,
) -> MutationEvent:
    entity = {
        "legs": [_row_dict(leg) for leg in legs],
        "transfer_group_id": transfer_group_id,
        "statement_id": statement_id,
    }
    return MutationEvent(
        event_type="finance.statement.paid",
        entity_type="transaction",
        operation="pay_statement",
        entity=entity,
        metadata={"transfer_group_id": transfer_group_id, "statement_id": statement_id},
    )


def build_category_created(category) -> MutationEvent:
    row = _row_dict(category)
    return MutationEvent(
        event_type="finance.category.created",
        entity_type="category",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_category_updated(category) -> MutationEvent:
    row = _row_dict(category)
    return MutationEvent(
        event_type="finance.category.updated",
        entity_type="category",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_category_deleted(category) -> MutationEvent:
    row = _row_dict(category)
    return MutationEvent(
        event_type="finance.category.deleted",
        entity_type="category",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_merchant_created(merchant) -> MutationEvent:
    row = _row_dict(merchant)
    return MutationEvent(
        event_type="finance.merchant.created",
        entity_type="merchant",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_merchant_updated(merchant) -> MutationEvent:
    row = _row_dict(merchant)
    return MutationEvent(
        event_type="finance.merchant.updated",
        entity_type="merchant",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_merchant_deleted(merchant) -> MutationEvent:
    row = _row_dict(merchant)
    return MutationEvent(
        event_type="finance.merchant.deleted",
        entity_type="merchant",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_credit_card_created(card) -> MutationEvent:
    row = {
        "account": _row_dict(card.account),
        "profile": _row_dict(card.profile),
    }
    return MutationEvent(
        event_type="finance.credit_card.created",
        entity_type="account",
        operation="create",
        entity=row,
        metadata={"entity_id": card.id},
    )


def build_credit_card_updated(card) -> MutationEvent:
    row = {
        "account": _row_dict(card.account),
        "profile": _row_dict(card.profile),
    }
    return MutationEvent(
        event_type="finance.credit_card.updated",
        entity_type="account",
        operation="update",
        entity=row,
        metadata={"entity_id": card.id},
    )


def build_credit_card_archived(card) -> MutationEvent:
    row = {
        "account": _row_dict(card.account),
        "profile": _row_dict(card.profile),
    }
    return MutationEvent(
        event_type="finance.credit_card.archived",
        entity_type="account",
        operation="archive",
        entity=row,
        metadata={"entity_id": card.id},
    )


def build_statement_created(statement) -> MutationEvent:
    row = _row_dict(statement)
    return MutationEvent(
        event_type="finance.statement.created",
        entity_type="statement",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_statement_updated(statement) -> MutationEvent:
    row = _row_dict(statement)
    return MutationEvent(
        event_type="finance.statement.updated",
        entity_type="statement",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_statement_deleted(statement) -> MutationEvent:
    row = _row_dict(statement)
    return MutationEvent(
        event_type="finance.statement.deleted",
        entity_type="statement",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_spending_logged_from_transaction(transaction) -> MutationEvent:
    """Legacy spending.logged envelope for existing desktop invalidation."""
    row = _row_dict(transaction)
    legacy = {
        "id": row["id"],
        "type": "earned" if row["kind"] == "income" else "spent",
        "amount": row["amount_minor"] / 100.0,
        "note": row.get("note") or "",
        "created_at": row["created_at"],
    }
    return MutationEvent(
        event_type="spending.logged",
        entity_type="money",
        operation="log",
        entity=legacy,
        metadata=_entity_metadata(legacy),
    )
