"""WorkOS read models — inbox, projects, items, priority queue, briefing.

Every projection is recomputed on read from ledger rows + injected clock; nothing
derived is persisted (ADR 0023).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domains.work.insights import build_briefing_shell
from domains.work.planning import PriorityPolicyService, build_priority_queue
from domains.work.project_service import ProjectService
from domains.work.repository_adapters import SqliteWorkItemRepository
from domains.work.work_item_service import WorkItemService
from domains.work.workspace import CaptureService, PromotionService

from . import work_serializers as ser

_capture = CaptureService()
_promotion = PromotionService()
_projects = ProjectService()
_items = WorkItemService()
_policy = PriorityPolicyService()
_open_commitments = SqliteWorkItemRepository()

BRIEFING_TOP_N = 5


def _now(now: Optional[datetime]) -> datetime:
    return now or datetime.now(timezone.utc)


def list_capture_inbox(owner_id: int = 1, limit: int = 50) -> list[dict]:
    return [ser.serialize_note(note) for note in _capture.list_inbox(owner_id, limit)]


def list_open_action_items(owner_id: int = 1, limit: int = 50) -> list[dict]:
    return [ser.serialize_action_item(item) for item in _promotion.list_open(owner_id, limit)]


def list_projects(owner_id: int = 1) -> list[dict]:
    return [ser.serialize_project(project) for project in _projects.list_projects(owner_id)]


def list_project_items(project_id: int, owner_id: int = 1) -> list[dict]:
    return [ser.serialize_work_item(item) for item in _items.list_for_project(project_id, owner_id)]


def get_priority_policy(owner_id: int = 1) -> dict:
    return ser.serialize_priority_policy(_policy.get_active_policy(owner_id))


def get_priority_queue(limit: int = 0, owner_id: int = 1, now: Optional[datetime] = None) -> dict:
    queue = _build_queue(owner_id, now)
    return ser.serialize_priority_queue(queue, limit)


def get_briefing(owner_id: int = 1, now: Optional[datetime] = None) -> dict:
    moment = _now(now)
    queue = _build_queue(owner_id, moment)
    inbox_count = len(_capture.list_inbox(owner_id, limit=1000))
    briefing = build_briefing_shell(queue, inbox_count, moment, BRIEFING_TOP_N)
    return ser.serialize_briefing(briefing)


def _build_queue(owner_id: int, now: Optional[datetime]):
    items = _open_commitments.list_open_commitments(owner_id)
    policy = _policy.get_active_policy(owner_id)
    return build_priority_queue(items, policy, _now(now))
