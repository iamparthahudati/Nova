from fastapi import APIRouter, Depends, HTTPException, Query

import memory
from runtime.mutation_builders import build_reminder_created
from runtime.side_effects import finalize_mutations
from services.planner.api_commands import (
    ReminderDateInvalidError,
    ReminderTimeInvalidError,
    create_reminder,
)

from ..dependencies import RequestContext, get_request_context
from ..schemas import (
    CreateReminderRequest,
    MutationMeta,
    ReminderMutationResponse,
    ReminderResponse,
    RemindersResponse,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=RemindersResponse)
def list_reminders(
    limit: int = Query(20, ge=1, le=200),
    _ctx: RequestContext = Depends(get_request_context),
) -> RemindersResponse:
    rows = memory.get_upcoming_reminders(limit)
    return RemindersResponse(reminders=[ReminderResponse(**row) for row in rows])


@router.post("", response_model=ReminderMutationResponse, status_code=201)
def post_reminder(
    body: CreateReminderRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> ReminderMutationResponse:
    try:
        row, message = create_reminder(body.text, body.remind_date, body.remind_time)
    except ReminderDateInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except ReminderTimeInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    finalize_mutations([build_reminder_created(row)])
    return ReminderMutationResponse(
        item=ReminderResponse(**row),
        meta=MutationMeta(message=message),
    )
