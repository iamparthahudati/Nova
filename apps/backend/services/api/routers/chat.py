from fastapi import APIRouter, Depends

from runtime.conversation import build_tool_handlers, process_message

from ..dependencies import RequestContext, get_request_context
from ..schemas import ChatRequest, ChatResponse, ToolCallRecord

router = APIRouter(prefix="/chat", tags=["chat"])

# Built once at import time — identical mapping to the voice/REPL entry point
# in nova.py, so a tool behaves the same over REST as it does over voice.
_TOOL_HANDLERS = build_tool_handlers()


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    _ctx: RequestContext = Depends(get_request_context),
) -> ChatResponse:
    result = process_message(
        body.message,
        _TOOL_HANDLERS,
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
