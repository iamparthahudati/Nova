"""Shared money value object tests."""

from __future__ import annotations

import pytest

from money import MoneyAmount, MoneyValidationError


def test_money_amount_from_rupees():
    amount = MoneyAmount.from_rupees(10.50)
    assert amount.minor == 1050
    assert amount.to_rupees() == 10.50


def test_money_amount_rejects_non_positive():
    with pytest.raises(MoneyValidationError):
        MoneyAmount.from_rupees(0)
