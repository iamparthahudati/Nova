"""Finance REST routes — thin facade over planner finance queries/commands."""

from __future__ import annotations

from fastapi import APIRouter

from ._accounts import router as accounts_router
from ._cashback import router as cashback_router
from ._rewards import router as rewards_router
from ._taxonomy import router as taxonomy_router
from ._transactions import router as transactions_router

router = APIRouter(prefix="/finance", tags=["finance"])
router.include_router(accounts_router)
router.include_router(transactions_router)
router.include_router(taxonomy_router)
router.include_router(rewards_router)
router.include_router(cashback_router)
