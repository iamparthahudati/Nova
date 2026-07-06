from fastapi import APIRouter, Depends

from ..dependencies import RequestContext, get_request_context
from ..projections.home import build_home_response
from ..schemas import HomeResponse

router = APIRouter(prefix="/home", tags=["home"])


@router.get("", response_model=HomeResponse)
def get_home(
    _ctx: RequestContext = Depends(get_request_context),
) -> HomeResponse:
    return build_home_response()
