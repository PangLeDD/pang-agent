from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.schema import AgentInvokeRequest
from app.application import create_chat_service
from app.core.database import get_session
from app.core.security import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/stream")
async def stream(
    request: AgentInvokeRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
) -> EventSourceResponse:
    logger.info("Agent stream: user_id={} conversation_id={} message_len={}", current_user["id"], request.conversation_id, len(request.message))
    service = create_chat_service(session)

    # ponytail: 在 EventSourceResponse 包装生成器前预检会话归属。
    # HTTPException（404）会交给 FastAPI 统一处理，返回 JSON，
    # 不会被 SSE 流内部吞掉并错误转换为 500。
    conversation = None
    if request.conversation_id is not None:
        conversation = await service.prepare_conversation(request.conversation_id, current_user["id"])

    return EventSourceResponse(service.stream(request.message, request.conversation_id, current_user["id"], conversation=conversation))
