"""Cashback rule service — CRUD for earn rules."""

from __future__ import annotations

import json
from typing import Optional

from ...errors import FinanceValidationError
from ...rewards.services.program_service import RewardProgramService
from ..aggregates import CashbackRule
from ..errors import CashbackRuleNotFoundError
from ..repository_adapters import SqliteCashbackRuleRepository
from ..validation import (
    validate_flat_rate_bps,
    validate_minimum_spend_minor,
    validate_monthly_cap_minor,
    validate_multiplier_map,
    validate_rule_name,
)


class CashbackRuleService:
    def __init__(
        self,
        rules: Optional[SqliteCashbackRuleRepository] = None,
        programs: Optional[RewardProgramService] = None,
    ) -> None:
        self._rules = rules or SqliteCashbackRuleRepository()
        self._programs = programs or RewardProgramService()

    def create_rule(
        self,
        program_id: int,
        name: str,
        flat_rate_bps: int,
        account_id: Optional[int] = None,
        category_multipliers: Optional[dict[int, int]] = None,
        merchant_multipliers: Optional[dict[int, int]] = None,
        excluded_category_ids: Optional[list[int]] = None,
        excluded_merchant_ids: Optional[list[int]] = None,
        excluded_mcc_codes: Optional[list[str]] = None,
        excluded_transaction_kinds: Optional[list[str]] = None,
        monthly_cap_minor: Optional[int] = None,
        minimum_spend_minor: int = 0,
    ) -> CashbackRule:
        program = self._programs.get_program(program_id)
        if account_id is not None and account_id != program.account_id:
            raise FinanceValidationError("Card-specific rule must target the program card")
        fields = {
            "program_id": program_id,
            "account_id": account_id,
            "name": validate_rule_name(name),
            "flat_rate_bps": validate_flat_rate_bps(flat_rate_bps),
            "category_multipliers": json.dumps(validate_multiplier_map(category_multipliers or {})),
            "merchant_multipliers": json.dumps(validate_multiplier_map(merchant_multipliers or {})),
            "excluded_category_ids": json.dumps(excluded_category_ids or []),
            "excluded_merchant_ids": json.dumps(excluded_merchant_ids or []),
            "excluded_mcc_codes": json.dumps(excluded_mcc_codes or []),
            "excluded_transaction_kinds": json.dumps(excluded_transaction_kinds or []),
            "monthly_cap_minor": validate_monthly_cap_minor(monthly_cap_minor),
            "minimum_spend_minor": validate_minimum_spend_minor(minimum_spend_minor),
        }
        return self._rules.create(fields)

    def get_rule(self, rule_id: int) -> CashbackRule:
        rule = self._rules.get_by_id(rule_id)
        if rule is None:
            raise CashbackRuleNotFoundError(rule_id)
        return rule

    def list_rules_for_program(self, program_id: int) -> list[CashbackRule]:
        self._programs.get_program(program_id)
        return self._rules.list_for_program(program_id)
