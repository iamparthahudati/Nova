from typing import Optional

from pydantic import BaseModel, Field

from .common import MutationMeta


class ReminderResponse(BaseModel):
    id: int
    text: str
    remind_date: str
    remind_time: Optional[str] = None
    created_at: str


class RemindersResponse(BaseModel):
    reminders: list[ReminderResponse]


class CreateReminderRequest(BaseModel):
    text: str = Field(..., min_length=1)
    remind_date: str = Field(..., description="ISO date YYYY-MM-DD")
    remind_time: Optional[str] = Field(None, description="24h HH:MM")


class ReminderMutationResponse(BaseModel):
    item: ReminderResponse
    meta: MutationMeta
