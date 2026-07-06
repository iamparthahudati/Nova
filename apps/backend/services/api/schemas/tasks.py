from typing import Optional

from pydantic import BaseModel, Field

from .common import MutationMeta


class TaskResponse(BaseModel):
    id: int
    text: str
    status: str
    created_at: str
    due: Optional[str] = None


class TasksResponse(BaseModel):
    tasks: list[TaskResponse]


class CreateTaskRequest(BaseModel):
    text: str = Field(..., min_length=1)
    due: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class TaskMutationResponse(BaseModel):
    item: TaskResponse
    meta: MutationMeta
