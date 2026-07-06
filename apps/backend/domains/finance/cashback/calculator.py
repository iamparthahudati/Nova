"""Pure cashback reward calculation — deterministic, no I/O."""

from __future__ import annotations

from typing import Optional

from ..aggregates import CreditCard, Transaction
from ..rewards.aggregates import RewardProgram
from .aggregates import CashbackCalculation, CashbackRule
from .policy import CashbackPolicy
from .projections import apply_monthly_cap
from .value_objects import MultiplierScale


class CashbackCalculator:
    """Evaluate earn rules and compute reward amounts in cashback_minor."""

    @classmethod
    def compute_effective_bps(cls, rule: CashbackRule, transaction: Transaction) -> int:
        effective = rule.flat_rate_bps
        if transaction.category_id is not None:
            category_scale = rule.category_multipliers.get(transaction.category_id)
            if category_scale is not None:
                effective = effective * category_scale // MultiplierScale.SCALE
        if transaction.merchant_id is not None:
            merchant_scale = rule.merchant_multipliers.get(transaction.merchant_id)
            if merchant_scale is not None:
                effective = effective * merchant_scale // MultiplierScale.SCALE
        return effective

    @classmethod
    def compute_gross_reward(cls, spend_minor: int, effective_bps: int) -> int:
        if spend_minor <= 0 or effective_bps <= 0:
            return 0
        return spend_minor * effective_bps // 10_000

    @classmethod
    def calculate(
        cls,
        transaction: Transaction,
        card: CreditCard,
        program: RewardProgram,
        rule: CashbackRule,
        monthly_earned_before: int = 0,
        transaction_mcc: Optional[str] = None,
    ) -> CashbackCalculation:
        qualified, exclusion_reason = CashbackPolicy.qualifies(
            transaction,
            card,
            program,
            rule,
            transaction_mcc=transaction_mcc,
        )
        if not qualified:
            return CashbackCalculation(
                program_id=program.id,
                rule_id=rule.id,
                transaction_id=transaction.id,
                spend_minor=transaction.amount_minor,
                effective_bps=0,
                gross_reward_minor=0,
                capped_reward_minor=0,
                monthly_earned_before=monthly_earned_before,
                monthly_cap_minor=rule.monthly_cap_minor,
                qualified=False,
                exclusion_reason=exclusion_reason,
            )

        effective_bps = cls.compute_effective_bps(rule, transaction)
        gross_reward = cls.compute_gross_reward(transaction.amount_minor, effective_bps)
        capped_reward = apply_monthly_cap(
            gross_reward,
            monthly_earned_before,
            rule.monthly_cap_minor,
        )
        return CashbackCalculation(
            program_id=program.id,
            rule_id=rule.id,
            transaction_id=transaction.id,
            spend_minor=transaction.amount_minor,
            effective_bps=effective_bps,
            gross_reward_minor=gross_reward,
            capped_reward_minor=capped_reward,
            monthly_earned_before=monthly_earned_before,
            monthly_cap_minor=rule.monthly_cap_minor,
            qualified=True,
            exclusion_reason=None,
        )
