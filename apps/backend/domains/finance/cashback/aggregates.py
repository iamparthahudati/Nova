"""Cashback bounded context — immutable domain shapes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from ..rewards.aggregates import RewardEvent


def _parse_json_map(raw: Any) -> dict[int, int]:
    if raw in (None, "", "{}"):
        return {}
    data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    return {int(key): int(value) for key, value in data.items()}


def _parse_json_list(raw: Any) -> tuple[int, ...]:
    if raw in (None, "", "[]"):
        return ()
    data = json.loads(raw) if isinstance(raw, str) else list(raw)
    return tuple(int(item) for item in data)


def _parse_kind_list(raw: Any) -> tuple[str, ...]:
    if raw in (None, "", "[]"):
        return ()
    data = json.loads(raw) if isinstance(raw, str) else list(raw)
    return tuple(str(item) for item in data)


def _parse_mcc_list(raw: Any) -> tuple[str, ...]:
    return _parse_kind_list(raw)


@dataclass(frozen=True)
class CashbackRule:
    """Deterministic earn rule — no balance storage."""

    id: int
    program_id: int
    account_id: Optional[int]
    name: str
    flat_rate_bps: int
    category_multipliers: dict[int, int]
    merchant_multipliers: dict[int, int]
    excluded_category_ids: tuple[int, ...]
    excluded_merchant_ids: tuple[int, ...]
    excluded_mcc_codes: tuple[str, ...]
    excluded_transaction_kinds: tuple[str, ...]
    monthly_cap_minor: Optional[int]
    minimum_spend_minor: int
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict) -> CashbackRule:
        return cls(
            id=int(row["id"]),
            program_id=int(row["program_id"]),
            account_id=int(row["account_id"]) if row.get("account_id") is not None else None,
            name=str(row["name"]),
            flat_rate_bps=int(row["flat_rate_bps"]),
            category_multipliers=_parse_json_map(row.get("category_multipliers")),
            merchant_multipliers=_parse_json_map(row.get("merchant_multipliers")),
            excluded_category_ids=_parse_json_list(row.get("excluded_category_ids")),
            excluded_merchant_ids=_parse_json_list(row.get("excluded_merchant_ids")),
            excluded_mcc_codes=_parse_mcc_list(row.get("excluded_mcc_codes")),
            excluded_transaction_kinds=_parse_kind_list(row.get("excluded_transaction_kinds")),
            monthly_cap_minor=(
                int(row["monthly_cap_minor"]) if row.get("monthly_cap_minor") is not None else None
            ),
            minimum_spend_minor=int(row.get("minimum_spend_minor") or 0),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )


@dataclass(frozen=True)
class CashbackCalculation:
    """Pure calculation result — emitted before persistence."""

    program_id: int
    rule_id: int
    transaction_id: int
    spend_minor: int
    effective_bps: int
    gross_reward_minor: int
    capped_reward_minor: int
    monthly_earned_before: int
    monthly_cap_minor: Optional[int]
    qualified: bool
    exclusion_reason: Optional[str]


@dataclass(frozen=True)
class CashbackEarnResult:
    """Engine output — calculation plus optional earned reward event."""

    calculation: CashbackCalculation
    reward_event: Optional[RewardEvent]
