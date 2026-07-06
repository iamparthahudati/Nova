from fastapi import APIRouter, Depends, HTTPException, Query

from runtime.mutation_builders import build_task_completed, build_task_created
from runtime.side_effects import finalize_mutations
from services.planner.api_commands import TaskNotFoundError, TaskNotOpenError, complete_task_by_id, create_task

from ..dependencies import RequestContext, get_request_context
from ..schemas import CreateTaskRequest, MutationMeta, TaskMutationResponse, TaskResponse, TasksResponse
import memory

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TasksResponse)
def list_tasks(
    limit: int | None = Query(None, ge=1, le=200),
    _ctx: RequestContext = Depends(get_request_context),
) -> TasksResponse:
    rows = memory.get_all_tasks(limit=limit)
    return TasksResponse(tasks=[TaskResponse(**row) for row in rows])


@router.post("", response_model=TaskMutationResponse, status_code=201)
def post_task(
    body: CreateTaskRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> TaskMutationResponse:
    row = create_task(body.text, body.due)
    message = "Task logged." + (f" Due {row['due']}." if row.get("due") else "")
    finalize_mutations([build_task_created(row)])
    return TaskMutationResponse(
        item=TaskResponse(**row),
        meta=MutationMeta(message=message),
    )


@router.post("/{task_id}/complete", response_model=TaskMutationResponse)
def post_complete_task(
    task_id: int,
    _ctx: RequestContext = Depends(get_request_context),
) -> TaskMutationResponse:
    try:
        row = complete_task_by_id(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found") from None
    except TaskNotOpenError:
        raise HTTPException(status_code=409, detail=f"Task {task_id} is not open") from None

    finalize_mutations([build_task_completed(row)])
    return TaskMutationResponse(
        item=TaskResponse(**row),
        meta=MutationMeta(message="Task marked done."),
    )
