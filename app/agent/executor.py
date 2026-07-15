from collections.abc import AsyncIterator

from app.agent.events import AgentEvent, EventType
from app.agent.graph import build_agent_graph
from app.infrastructure.llm import get_llm


class AgentExecutor:
    """Agent 运行时：执行 LangGraph 图，产出 AgentEvent 流。

    这是 Agent 层的唯一对外接口——外部不直接碰图，
    只通过 AgentEvent 流感知 Agent 的内部状态变化。
    """

    def __init__(self, llm=None) -> None:
        self._graph = build_agent_graph(llm or get_llm())

    async def run(self, message: str) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(type=EventType.CONVERSATION_START)

        async for chunk_msg, _metadata in self._graph.astream(
            {"message": message, "reply": ""},
            stream_mode="messages",
        ):
            if chunk_msg.content:
                yield AgentEvent(type=EventType.MESSAGE_DELTA, payload={"delta": chunk_msg.content})

        yield AgentEvent(type=EventType.CONVERSATION_END, payload={"reason": "stop"})
