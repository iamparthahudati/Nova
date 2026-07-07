"""WorkOS REST routes — thin facade over planner work queries/commands."""

from __future__ import annotations

from fastapi import APIRouter

from ._captures import router as captures_router
from ._items import router as items_router
from ._priority import router as priority_router
from ._projects import router as projects_router

router = APIRouter(prefix="/work", tags=["work"])
router.include_router(captures_router)
router.include_router(projects_router)
router.include_router(items_router)
router.include_router(priority_router)
