from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from app.agent.schema import AgentInvokeRequest
from app.application import ChatService, get_chat_service

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/stream")
async def stream(
    request: AgentInvokeRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> EventSourceResponse:
    logger.info("Agent stream: conversation_id={} message_len={}", request.conversation_id, len(request.message))
    return EventSourceResponse(service.stream(request.message, request.conversation_id))
