from typing import Optional

from pydantic import BaseModel


class ProfileObservationResponse(BaseModel):
    observation: str
    category: str
    confidence: float


class SettingsResponse(BaseModel):
    assistant_name: str
    voice_name: str
    briefing_time: str
    evening_wrapup_time: Optional[str] = None
    claude_model: str
    semantic_memory_enabled: bool
    entity_extraction_enabled: bool
    graph_context_enabled: bool
    observations: list[ProfileObservationResponse]
