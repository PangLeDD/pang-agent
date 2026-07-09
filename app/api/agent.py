from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.agent.graph import invoke_agent
from app.agent.llm import invoke_llm
from app.agent.schema import AgentInvokeRequest, AgentInvokeResponse
from app.core.response import success

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/invoke")
async def invoke(request: AgentInvokeRequest) -> dict[str, object]:
    # 只记录长度和会话标识，避免把用户原文直接打进日志。
    logger.info(
        "Agent invoke: conversation_id={} message_len={}",
        request.conversation_id,
        len(request.message),
    )
    response = AgentInvokeResponse(
        reply=invoke_agent(request.message),
        conversation_id=request.conversation_id,
    )
    return success(response.model_dump())


@router.post("/llm-test")
async def llm_test(request: AgentInvokeRequest) -> dict[str, object]:
    try:
        logger.info("LLM test: conversation_id={} message_len={}", request.conversation_id, len(request.message))
        response = AgentInvokeResponse(
            reply=invoke_llm(request.message),
            conversation_id=request.conversation_id,
        )
        return success(response.model_dump())
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
