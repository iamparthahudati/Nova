import identity
import memory
from fastapi import APIRouter, Depends
from services.brain import config as brain_config
from services import planner
from ..dependencies import RequestContext, get_request_context
from ..schemas import ProfileObservationResponse, SettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    _ctx: RequestContext = Depends(get_request_context),
) -> SettingsResponse:
    observations = [
        ProfileObservationResponse(
            observation=o["observation"],
            category=o["category"],
            confidence=o["confidence"],
        )
        for o in memory.get_profile_observations()
    ]
    return SettingsResponse(
        assistant_name=identity.ASSISTANT_NAME,
        voice_name=identity.VOICE_NAME,
        briefing_time=planner.BRIEFING_TIME,
        evening_wrapup_time=planner.EVENING_WRAPUP_TIME,
        claude_model=brain_config.CLAUDE_MODEL,
        semantic_memory_enabled=brain_config.SEMANTIC_MEMORY_ENABLED,
        entity_extraction_enabled=brain_config.ENTITY_EXTRACTION_ENABLED,
        graph_context_enabled=brain_config.GRAPH_CONTEXT_ENABLED,
        observations=observations,
    )
