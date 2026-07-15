from collections.abc import AsyncIterator
from uuid import uuid4

from loguru import logger

from app.agent import AgentExecutor, EventType
from app.presentation import sse_event


class ChatService:
    """编排一次对话请求的完整流程。

    API 层只做 HTTP 收口，业务编排全部下沉到这里。
    executor 可注入，方便测试和后续多 Agent 扩展。
    """

    def __init__(self, executor: AgentExecutor | None = None) -> None:
        # 默认使用通用的 AgentExecutor
        self._executor = executor or AgentExecutor()

    async def stream(self, message: str, conversation_id: str | None = None) -> AsyncIterator[dict[str, str]]:
        cid = conversation_id or str(uuid4())

        try:
            async for event in self._executor.run(message, thread_id=cid):
                if event.type == EventType.CONVERSATION_START:
                    event.payload["conversation_id"] = cid
                yield sse_event(event.type, event.payload)
        except Exception:
            logger.exception("Agent stream failed: conversation_id={}", cid)
            yield sse_event(EventType.ERROR, {"code": 500, "message": "Internal Server Error"})



