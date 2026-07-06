"""Reward program aggregate service — CRUD."""

from __future__ import annotations

from typing import Optional

from ...errors import AccountNotFoundError, FinanceValidationError
from ...repository_adapters import SqliteAccountRepository
from ...value_objects import AccountType
from ..aggregates import RewardProgram
from ..errors import RewardInvariantError, RewardProgramNotFoundError
from ..repository_adapters import SqliteRewardProgramRepository
from ..validation import validate_program_name, validate_reward_unit


class RewardProgramService:
    def __init__(
        self,
        programs: Optional[SqliteRewardProgramRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
    ) -> None:
        self._programs = programs or SqliteRewardProgramRepository()
        self._accounts = accounts or SqliteAccountRepository()

    def _require_card_account(self, account_id: int) -> None:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        if account.type != AccountType.CREDIT_CARD.value:
            raise FinanceValidationError(
                "Reward programs can only be attached to credit card accounts",
            )
        if account.archived_at is not None:
            raise FinanceValidationError("Cannot attach a reward program to an archived card")

    def create_program(
        self,
        account_id: int,
        name: str,
        unit: str,
        earn_rate_note: Optional[str] = None,
        expiry_note: Optional[str] = None,
    ) -> RewardProgram:
        self._require_card_account(account_id)
        fields = {
            "account_id": account_id,
            "name": validate_program_name(name),
            "unit": validate_reward_unit(unit),
            "earn_rate_note": earn_rate_note,
            "expiry_note": expiry_note,
        }
        return self._programs.create(fields)

    def get_program(self, program_id: int) -> RewardProgram:
        program = self._programs.get_by_id(program_id)
        if program is None:
            raise RewardProgramNotFoundError(program_id)
        return program

    def list_programs(self, account_id: Optional[int] = None) -> list[RewardProgram]:
        if account_id is not None:
            self._require_card_account(account_id)
        return self._programs.list_live(account_id)

    def update_program(
        self,
        program_id: int,
        name: Optional[str] = None,
        earn_rate_note: Optional[str] = None,
        expiry_note: Optional[str] = None,
    ) -> RewardProgram:
        self.get_program(program_id)
        fields: dict = {}
        if name is not None:
            fields["name"] = validate_program_name(name)
        if earn_rate_note is not None:
            fields["earn_rate_note"] = earn_rate_note
        if expiry_note is not None:
            fields["expiry_note"] = expiry_note
        updated = self._programs.update(program_id, fields)
        if updated is None:
            raise RewardProgramNotFoundError(program_id)
        return updated

    def delete_program(self, program_id: int) -> RewardProgram:
        program = self.get_program(program_id)
        if self._programs.count_live_events(program_id) > 0:
            raise RewardInvariantError(
                "Cannot delete a reward program with live events",
            )
        if not self._programs.soft_delete(program_id):
            raise RewardProgramNotFoundError(program_id)
        return program
