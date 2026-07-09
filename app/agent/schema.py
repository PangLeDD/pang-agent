from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    # 用户本轮输入，先保持单条消息，后续再扩展多轮消息结构。
    message: str = Field(..., min_length=1, strict=True)
    conversation_id: str | None = None


class AgentInvokeResponse(BaseModel):
    reply: str
    conversation_id: str | None = None
