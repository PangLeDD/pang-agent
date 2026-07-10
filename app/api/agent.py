from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from app.agent import invoke_agent
from app.agent.schema import AgentInvokeRequest, AgentInvokeResponse
from app.application import ChatService, get_chat_service
from app.core.response import success
from app.infrastructure.llm import invoke_llm

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/invoke")
async def invoke(request: AgentInvokeRequest) -> dict[str, object]:
    conversation_id = request.conversation_id or str(uuid4())
    logger.info("Agent invoke: conversation_id={} message_len={}", conversation_id, len(request.message))
    response = AgentInvokeResponse(reply=invoke_agent(request.message), conversation_id=conversation_id)
    return success(response.model_dump())


@router.post("/llm-test")
async def llm_test(request: AgentInvokeRequest) -> dict[str, object]:
    conversation_id = request.conversation_id or str(uuid4())
    logger.info("LLM test: conversation_id={} message_len={}", conversation_id, len(request.message))
    try:
        response = AgentInvokeResponse(reply=invoke_llm(request.message), conversation_id=conversation_id)
        return success(response.model_dump())
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/stream")
async def stream(
    request: AgentInvokeRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> EventSourceResponse:
    logger.info("Agent stream: conversation_id={} message_len={}", request.conversation_id, len(request.message))
    return EventSourceResponse(service.stream(request.message, request.conversation_id))
