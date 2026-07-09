from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.agent.graph import invoke_agent
from app.agent.llm import invoke_llm

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentInvokeRequest(BaseModel):
    message: str


@router.post("/invoke")
async def invoke(request: AgentInvokeRequest) -> dict[str, str]:
    return {"reply": invoke_agent(request.message)}


@router.post("/llm-test")
async def llm_test(request: AgentInvokeRequest) -> dict[str, str]:
    try:
        return {"reply": invoke_llm(request.message)}
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
