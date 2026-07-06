"""Merchant aggregate service."""

from __future__ import annotations

from typing import Optional

from ..aggregates import Merchant
from ..errors import FinanceValidationError, MerchantNotFoundError
from ..repository_adapters import SqliteMerchantRepository
from ..validation import validate_merchant_name


class MerchantService:
    def __init__(self, merchants: Optional[SqliteMerchantRepository] = None) -> None:
        self._merchants = merchants or SqliteMerchantRepository()

    def create_merchant(self, name: str) -> Merchant:
        clean_name = validate_merchant_name(name)
        existing = self._merchants.get_by_name(clean_name)
        if existing is not None:
            raise FinanceValidationError(f"Merchant already exists: {clean_name}")
        return self._merchants.create(clean_name)

    def get_merchant(self, merchant_id: int) -> Merchant:
        merchant = self._merchants.get_by_id(merchant_id)
        if merchant is None:
            raise MerchantNotFoundError(merchant_id)
        return merchant

    def list_merchants(self) -> list[Merchant]:
        return self._merchants.list_live()

    def update_merchant(self, merchant_id: int, name: str) -> Merchant:
        clean_name = validate_merchant_name(name)
        existing = self._merchants.get_by_name(clean_name)
        if existing is not None and existing.id != merchant_id:
            raise FinanceValidationError(f"Merchant already exists: {clean_name}")
        updated = self._merchants.update(merchant_id, clean_name)
        if updated is None:
            raise MerchantNotFoundError(merchant_id)
        return updated

    def delete_merchant(self, merchant_id: int) -> Merchant:
        merchant = self.get_merchant(merchant_id)
        if not self._merchants.soft_delete(merchant_id):
            raise MerchantNotFoundError(merchant_id)
        return merchant
