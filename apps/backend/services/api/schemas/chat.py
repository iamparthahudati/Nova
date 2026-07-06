from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to route through Brain")
    conversation_id: Optional[str] = Field(None, description="Stable id across turns in one session")


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: str = ""


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tools_called: list[ToolCallRecord] = Field(default_factory=list)
    error: Optional[str] = None
