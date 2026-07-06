from fastapi import APIRouter, Depends

from ..dependencies import RequestContext, get_request_context
from ..diagnostics import build_system_status
from ..schemas import SystemStatusResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
def system_status(
    _ctx: RequestContext = Depends(get_request_context),
) -> SystemStatusResponse:
    return build_system_status()
