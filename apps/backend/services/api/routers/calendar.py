from datetime import datetime

from fastapi import APIRouter, Depends, Query

from services import calendar

from ..dependencies import RequestContext, get_request_context
from ..schemas import CalendarEventResponse, CalendarResponse

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=CalendarResponse)
def get_calendar(
    day: str | None = Query(None, description="Natural-language day, e.g. 'today' or 'friday'"),
    _ctx: RequestContext = Depends(get_request_context),
) -> CalendarResponse:
    date_obj = calendar.parse_date(day) if day else datetime.now()
    if date_obj is None:
        date_obj = datetime.now()
    try:
        events = calendar.get_events(date_obj)
        unavailable = False
    except Exception:
        events = []
        unavailable = True
    return CalendarResponse(
        date=date_obj.strftime("%Y-%m-%d"),
        events=[CalendarEventResponse(**e) for e in events],
        unavailable=unavailable,
    )
