"""REST-side translators — domain rows to MutationEvent. No I/O, no side effects."""

from __future__ import annotations

from .mutation_event import MutationEvent


def _entity_metadata(row: dict) -> dict:
    entity_id = row.get("id")
    return {"entity_id": entity_id} if entity_id is not None else {}


def build_task_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="task.created",
        entity_type="task",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_task_completed(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="task.updated",
        entity_type="task",
        operation="complete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reminder_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="reminder.created",
        entity_type="reminder",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_spending_logged(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="spending.logged",
        entity_type="money",
        operation="log",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_account_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.account.created",
        entity_type="account",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_account_updated(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.account.updated",
        entity_type="account",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_account_archived(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.account.archived",
        entity_type="account",
        operation="archive",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_credit_card_created(row: dict) -> MutationEvent:
    metadata = {"entity_id": row.get("account_id")}
    return MutationEvent(
        event_type="finance.credit_card.created",
        entity_type="credit_card",
        operation="create",
        entity=row,
        metadata=metadata,
    )


def build_finance_credit_card_updated(row: dict) -> MutationEvent:
    metadata = {"entity_id": row.get("account_id")}
    return MutationEvent(
        event_type="finance.credit_card.updated",
        entity_type="credit_card",
        operation="update",
        entity=row,
        metadata=metadata,
    )


def build_finance_transaction_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.transaction.created",
        entity_type="transaction",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_transaction_updated(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.transaction.updated",
        entity_type="transaction",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_transaction_deleted(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.transaction.deleted",
        entity_type="transaction",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_transfer_created(entity: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.transfer.created",
        entity_type="transaction",
        operation="transfer",
        entity=entity,
        metadata={"transfer_group_id": entity.get("transfer_group_id")},
    )


def build_finance_card_payment_created(entity: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.card_payment.created",
        entity_type="transaction",
        operation="card_payment",
        entity=entity,
        metadata={"transfer_group_id": entity.get("transfer_group_id")},
    )


def build_finance_statement_paid(entity: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.statement.paid",
        entity_type="transaction",
        operation="pay_statement",
        entity=entity,
        metadata={
            "transfer_group_id": entity.get("transfer_group_id"),
            "statement_id": entity.get("statement_id"),
        },
    )


def build_finance_statement_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.statement.created",
        entity_type="statement",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_statement_updated(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.statement.updated",
        entity_type="statement",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_category_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.category.created",
        entity_type="category",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_category_updated(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.category.updated",
        entity_type="category",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_category_deleted(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.category.deleted",
        entity_type="category",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_merchant_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.merchant.created",
        entity_type="merchant",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_merchant_updated(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.merchant.updated",
        entity_type="merchant",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_merchant_deleted(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.merchant.deleted",
        entity_type="merchant",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_finance_cashback_earned(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="finance.cashback.earned",
        entity_type="reward_event",
        operation="earn",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_pomodoro_completed(minutes: int) -> MutationEvent:
    entity = {"minutes": minutes}
    return MutationEvent(
        event_type="pomodoro.completed",
        entity_type="automation",
        operation="complete",
        entity=entity,
        metadata={"minutes": minutes},
    )
