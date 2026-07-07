"""Finance API schemas — canonical HTTP contracts."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .common import MutationMeta


class FinanceDashboardResponse(BaseModel):
    total_balance_minor: int
    total_balance: float
    total_assets_minor: int
    total_assets: float
    total_liabilities_minor: int
    total_liabilities: float
    cash_available_minor: int
    cash_available: float
    credit_utilization_ratio: float
    credit_utilization_percent: float
    total_outstanding_minor: int
    total_outstanding: float
    total_available_credit_minor: int
    total_available_credit: float
    cards_near_due_count: int
    income_month: float
    spent_month: float
    savings_month: float
    reward_balance: int
    rewards_earned_month: int
    cashback_earned_month_minor: int
    cashback_earned_month: float
    account_count: int
    credit_card_count: int
    upcoming_due_dates: list[dict[str, Any]]
    recent_transactions: list[dict[str, Any]]
    latest_rewards: list[dict[str, Any]]


class AccountResponse(BaseModel):
    id: int
    name: str
    type: str
    classification: str
    currency: str
    opening_balance_minor: int
    opening_balance_on: str
    archived_at: Optional[str] = None
    created_at: str
    updated_at: str
    balance_minor: Optional[int] = None
    balance: Optional[float] = None


class AccountsResponse(BaseModel):
    accounts: list[AccountResponse]


class CreateAccountRequest(BaseModel):
    name: str = Field(..., min_length=1)
    account_type: str
    opening_balance: float = 0.0
    opening_balance_on: Optional[str] = None


class UpdateAccountRequest(BaseModel):
    name: Optional[str] = None
    opening_balance: Optional[float] = None
    opening_balance_on: Optional[str] = None


class AccountMutationResponse(BaseModel):
    item: AccountResponse
    meta: MutationMeta


class CreditCardResponse(BaseModel):
    account_id: int
    name: str
    type: str
    network: Optional[str] = None
    last4: Optional[str] = None
    credit_limit_minor: int
    credit_limit: float
    statement_day: int
    due_day_offset: int
    autopay: bool
    opening_balance_minor: int
    opening_balance_on: str
    archived_at: Optional[str] = None
    created_at: str
    updated_at: str
    balance_minor: Optional[int] = None
    balance: Optional[float] = None
    outstanding_minor: Optional[int] = None
    outstanding: Optional[float] = None
    utilization_ratio: Optional[float] = None
    utilization_percent: Optional[float] = None
    available_limit_minor: Optional[int] = None
    available_limit: Optional[float] = None
    current_statement: Optional[dict[str, Any]] = None
    previous_statement: Optional[dict[str, Any]] = None


class CreditCardsResponse(BaseModel):
    cards: list[CreditCardResponse]


class CreateCreditCardRequest(BaseModel):
    name: str = Field(..., min_length=1)
    credit_limit: float = Field(..., gt=0)
    statement_day: int = Field(..., ge=1, le=28)
    due_day_offset: int = Field(..., ge=1, le=45)
    opening_balance: float = 0.0
    opening_balance_on: Optional[str] = None
    network: Optional[str] = None
    last4: Optional[str] = None
    autopay: bool = False


class UpdateCreditCardRequest(BaseModel):
    name: Optional[str] = None
    credit_limit: Optional[float] = Field(None, gt=0)
    statement_day: Optional[int] = Field(None, ge=1, le=28)
    due_day_offset: Optional[int] = Field(None, ge=1, le=45)
    network: Optional[str] = None
    last4: Optional[str] = None
    autopay: Optional[bool] = None


class CreditCardMutationResponse(BaseModel):
    item: CreditCardResponse
    meta: MutationMeta


class StatementResponse(BaseModel):
    id: int
    account_id: int
    period_start: str
    period_end: str
    statement_date: str
    due_date: str
    total_due_minor: Optional[int] = None
    min_due_minor: Optional[int] = None
    created_at: str
    updated_at: str
    spend_minor: Optional[int] = None
    spend: Optional[float] = None
    paid_minor: Optional[int] = None
    paid: Optional[float] = None
    remaining_due_minor: Optional[int] = None
    remaining_due: Optional[float] = None
    status: Optional[str] = None
    transactions: Optional[list[dict[str, Any]]] = None


class StatementsResponse(BaseModel):
    statements: list[StatementResponse]


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    direction: str
    kind: str
    amount_minor: int
    amount: float
    category_id: Optional[int] = None
    merchant_id: Optional[int] = None
    note: Optional[str] = None
    occurred_on: str
    transfer_group_id: Optional[str] = None
    statement_id: Optional[int] = None
    source: str
    created_at: str
    updated_at: str
    account_name: Optional[str] = None
    category_name: Optional[str] = None
    merchant_name: Optional[str] = None


class TransactionsResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int


class CreateTransactionRequest(BaseModel):
    account_id: int
    kind: str
    amount: float = Field(..., gt=0)
    occurred_on: str
    category_id: Optional[int] = None
    merchant_id: Optional[int] = None
    note: Optional[str] = None
    direction: Optional[str] = None


class UpdateTransactionRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    merchant_id: Optional[int] = None
    note: Optional[str] = None
    occurred_on: Optional[str] = None


class TransactionMutationResponse(BaseModel):
    item: TransactionResponse
    meta: MutationMeta


class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str


class CategoriesResponse(BaseModel):
    categories: list[CategoryResponse]


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1)


class UpdateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1)


class CategoryMutationResponse(BaseModel):
    item: CategoryResponse
    meta: MutationMeta


class MerchantResponse(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str


class MerchantsResponse(BaseModel):
    merchants: list[MerchantResponse]


class CreateMerchantRequest(BaseModel):
    name: str = Field(..., min_length=1)


class UpdateMerchantRequest(BaseModel):
    name: str = Field(..., min_length=1)


class MerchantMutationResponse(BaseModel):
    item: MerchantResponse
    meta: MutationMeta


class TransferLegResponse(BaseModel):
    id: int
    account_id: int
    direction: str
    kind: str
    amount_minor: int
    amount: float
    note: Optional[str] = None
    occurred_on: str
    transfer_group_id: Optional[str] = None
    statement_id: Optional[int] = None
    source: str
    created_at: str
    updated_at: str


class TransferGroupResponse(BaseModel):
    legs: list[TransferLegResponse]
    transfer_group_id: str
    statement_id: Optional[int] = None


class TransferMutationResponse(BaseModel):
    item: TransferGroupResponse
    meta: MutationMeta


class CreateTransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0)
    occurred_on: str
    note: Optional[str] = None


class CreateCardPaymentRequest(BaseModel):
    from_account_id: int
    card_account_id: int
    amount: float = Field(..., gt=0)
    occurred_on: str
    statement_id: Optional[int] = None
    note: Optional[str] = None
    confirm_overpayment: bool = False


class PayStatementRequest(BaseModel):
    from_account_id: int
    payment_mode: str = "partial"
    amount: Optional[float] = Field(None, gt=0)
    note: Optional[str] = None
    confirm_overpayment: bool = False


class UpdateStatementRequest(BaseModel):
    total_due: Optional[float] = Field(None, ge=0)
    min_due: Optional[float] = Field(None, ge=0)


class StatementMutationResponse(BaseModel):
    item: StatementResponse
    meta: MutationMeta


class RewardProgramResponse(BaseModel):
    id: int
    account_id: int
    name: str
    unit: str
    earn_rate_note: Optional[str] = None
    expiry_note: Optional[str] = None
    created_at: str
    updated_at: str
    balance: Optional[dict[str, Any]] = None
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    status: Optional[str] = None


class RewardProgramsResponse(BaseModel):
    programs: list[RewardProgramResponse]


class RewardsOverviewResponse(BaseModel):
    total_balance: int
    total_balance_cashback_minor: int
    total_balance_cashback: float
    earned_month: int
    earned_year: int
    earned_lifetime: int
    earned_month_cashback_minor: int
    earned_year_cashback_minor: int
    earned_lifetime_cashback_minor: int
    earned_month_cashback: float
    earned_year_cashback: float
    earned_lifetime_cashback: float


class RewardLedgerResponse(BaseModel):
    program: RewardProgramResponse
    balance: dict[str, Any]
    events: list[dict[str, Any]]
    yearly_earned: int
    monthly_earned: int
    lifetime_earned: int


class RewardProgramDetailResponse(BaseModel):
    program: RewardProgramResponse
    balance: dict[str, Any]
    status: str
    account_name: str
    bank_name: str
    earned_month: int
    earned_year: int
    earned_lifetime: int
    monthly_history: list[dict[str, Any]]
    recent_events: list[dict[str, Any]]
    related_transactions: list[dict[str, Any]]


class CashbackRuleResponse(BaseModel):
    id: int
    program_id: int
    account_id: Optional[int] = None
    name: str
    flat_rate_bps: int
    flat_rate_percent: float
    category_multipliers: dict[int, int]
    merchant_multipliers: dict[int, int]
    excluded_category_ids: tuple[int, ...]
    excluded_merchant_ids: tuple[int, ...]
    excluded_mcc_codes: tuple[str, ...]
    excluded_transaction_kinds: tuple[str, ...]
    monthly_cap_minor: Optional[int] = None
    monthly_cap: Optional[float] = None
    minimum_spend_minor: int
    minimum_spend: float
    created_at: str
    updated_at: str
    program_name: Optional[str] = None
    account_name: Optional[str] = None
    card_name: Optional[str] = None
    earned_month_minor: Optional[int] = None
    earned_month: Optional[float] = None
    remaining_cap_minor: Optional[int] = None
    remaining_cap: Optional[float] = None
    status: Optional[str] = None
    excluded_category_names: list[str] = Field(default_factory=list)
    excluded_merchant_names: list[str] = Field(default_factory=list)


class CashbackSummaryResponse(BaseModel):
    total_balance_minor: int
    total_balance: float
    monthly_earned_minor: int
    monthly_earned: float
    earned_year_minor: int
    earned_year: float
    earned_lifetime_minor: int
    earned_lifetime: float
    remaining_monthly_cap_minor: Optional[int] = None
    remaining_monthly_cap: Optional[float] = None
    active_rules_count: int
    rules: list[CashbackRuleResponse]


class CashbackActivityEventResponse(BaseModel):
    id: int
    program_id: int
    program_name: str
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    transaction_id: Optional[int] = None
    transaction_note: Optional[str] = None
    amount_minor: int
    amount: float
    occurred_on: str
    note: Optional[str] = None


class CashbackActivityResponse(BaseModel):
    events: list[CashbackActivityEventResponse]


class CashbackRuleDetailResponse(BaseModel):
    rule: CashbackRuleResponse
    program_name: str
    account_name: str
    card_name: str
    earned_month: int
    earned_year: int
    earned_lifetime: int
    monthly_history: list[dict[str, Any]]
    recent_events: list[dict[str, Any]]
    related_transactions: list[dict[str, Any]]
    remaining_cap_minor: Optional[int] = None
    remaining_cap: Optional[float] = None
