"""Request/response models for the WorkOS API (WORKOS_PHASE1_SCHEMA §7)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .common import MutationMeta


class WorkMutationResponse(BaseModel):
    item: dict
    meta: MutationMeta


class CaptureNoteRequest(BaseModel):
    body: str
    capture_source: str = "manual"
    captured_on: Optional[str] = None
    idempotency_key: Optional[str] = None


class TriageTaskRequest(BaseModel):
    project_id: int
    title: str
    estimate_minutes: Optional[int] = None
    estimate_confidence: Optional[str] = None
    deadline_on: Optional[str] = None
    deadline_hardness: Optional[str] = None
    updated_at: str


class ConcurrencyRequest(BaseModel):
    """Body carrying only the optimistic-concurrency token."""

    updated_at: str


class CreateActionItemRequest(BaseModel):
    title: str
    note_id: Optional[int] = None


class PromoteActionItemRequest(BaseModel):
    project_id: int
    updated_at: str


class CreateProjectRequest(BaseModel):
    name: str
    objective: Optional[str] = None
    planned_start_on: Optional[str] = None
    planned_end_on: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    planned_start_on: Optional[str] = None
    planned_end_on: Optional[str] = None
    updated_at: str


class CreateTaskRequest(BaseModel):
    project_id: int
    title: str
    estimate_minutes: Optional[int] = None
    estimate_confidence: Optional[str] = None
    deadline_on: Optional[str] = None
    deadline_hardness: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    estimate_minutes: Optional[int] = None
    estimate_confidence: Optional[str] = None
    deadline_on: Optional[str] = None
    deadline_hardness: Optional[str] = None
    updated_at: str


class TransitionTaskRequest(BaseModel):
    to_status: str
    updated_at: str


class ReweightPolicyRequest(BaseModel):
    deadline_weight: int
    decay_weight: int
    updated_at: str
