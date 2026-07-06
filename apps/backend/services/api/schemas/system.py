from typing import Literal, Optional

from pydantic import BaseModel, Field


SubsystemStatus = Literal["ok", "degraded", "unavailable"]


class SubsystemDiagnostic(BaseModel):
    name: str
    status: SubsystemStatus
    message: Optional[str] = None


class SystemStatusResponse(BaseModel):
    status: SubsystemStatus
    version: str
    subsystems: list[SubsystemDiagnostic] = Field(default_factory=list)
