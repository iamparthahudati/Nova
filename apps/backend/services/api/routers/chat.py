from fastapi import APIRouter, Depends

from ..dependencies import RequestContext, get_request_context
from ..schemas import ChatRequest, ChatResponse, ToolCallRecord
from runtime.conversation import process_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> ChatResponse:
    result = process_message(
        body.message,
        body.conversation_id,
        speak_output=False,
        emit_events=True,
    )
    return ChatResponse(
        reply=result.reply,
        conversation_id=result.conversation_id,
        tools_called=[ToolCallRecord(**t) for t in result.tools_called],
        error=result.error,
    )
