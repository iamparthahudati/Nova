"""Category aggregate service."""

from __future__ import annotations

from typing import Optional

from ..aggregates import Category
from ..errors import CategoryNotFoundError, FinanceValidationError
from ..repository_adapters import SqliteCategoryRepository
from ..validation import validate_category_name


class CategoryService:
    def __init__(self, categories: Optional[SqliteCategoryRepository] = None) -> None:
        self._categories = categories or SqliteCategoryRepository()

    def create_category(self, name: str) -> Category:
        clean_name = validate_category_name(name)
        existing = self._categories.get_by_name(clean_name)
        if existing is not None:
            raise FinanceValidationError(f"Category already exists: {clean_name}")
        return self._categories.create(clean_name)

    def get_category(self, category_id: int) -> Category:
        category = self._categories.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        return category

    def list_categories(self) -> list[Category]:
        return self._categories.list_live()

    def update_category(self, category_id: int, name: str) -> Category:
        clean_name = validate_category_name(name)
        existing = self._categories.get_by_name(clean_name)
        if existing is not None and existing.id != category_id:
            raise FinanceValidationError(f"Category already exists: {clean_name}")
        updated = self._categories.update(category_id, clean_name)
        if updated is None:
            raise CategoryNotFoundError(category_id)
        return updated

    def delete_category(self, category_id: int) -> Category:
        category = self.get_category(category_id)
        if not self._categories.soft_delete(category_id):
            raise CategoryNotFoundError(category_id)
        return category
