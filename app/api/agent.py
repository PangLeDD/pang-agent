from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from app.agent.schema import AgentInvokeRequest
from app.application import ChatService, create_chat_service
from app.core.security import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/stream")
async def stream(
    request: AgentInvokeRequest,
    service: Annotated[ChatService, Depends(create_chat_service)],
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
) -> EventSourceResponse:
    logger.info("Agent stream: user_id={} conversation_id={} message_len={}", current_user["id"], request.conversation_id, len(request.message))
    return EventSourceResponse(service.stream(request.message, request.conversation_id, current_user["id"]))
