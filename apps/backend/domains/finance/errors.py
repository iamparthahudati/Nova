"""Finance domain errors."""

from __future__ import annotations


class FinanceValidationError(ValueError):
    """Input failed finance business validation."""


class AccountNotFoundError(LookupError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account {account_id} not found")
        self.account_id = account_id


class AccountArchivedError(LookupError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account {account_id} is archived")
        self.account_id = account_id


class CategoryNotFoundError(LookupError):
    def __init__(self, category_id: int) -> None:
        super().__init__(f"Category {category_id} not found")
        self.category_id = category_id


class MerchantNotFoundError(LookupError):
    def __init__(self, merchant_id: int) -> None:
        super().__init__(f"Merchant {merchant_id} not found")
        self.merchant_id = merchant_id


class TransactionNotFoundError(LookupError):
    def __init__(self, transaction_id: int) -> None:
        super().__init__(f"Transaction {transaction_id} not found")
        self.transaction_id = transaction_id


class TransferInvariantError(FinanceValidationError):
    """Transfer pair invariant violated."""


class CreditCardNotFoundError(LookupError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Credit card {account_id} not found")
        self.account_id = account_id


class StatementNotFoundError(LookupError):
    def __init__(self, statement_id: int) -> None:
        super().__init__(f"Statement {statement_id} not found")
        self.statement_id = statement_id


class StatementInvariantError(FinanceValidationError):
    """Statement period or linkage invariant violated."""


class PaymentConfirmationRequiredError(FinanceValidationError):
    """Overpayment requires explicit confirmation."""
