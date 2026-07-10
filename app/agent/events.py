from dataclasses import dataclass, field
from typing import Any


class EventType:
    """Agent 事件类型常量，全部集中管理，避免分散在各处的字符串字面量。"""

    CONVERSATION_START = "conversation.start"
    MESSAGE_DELTA = "message.delta"
    CONVERSATION_END = "conversation.end"
    ERROR = "error"


@dataclass
class AgentEvent:
    """Agent 领域事件模型，连接「LLM 世界」和「业务系统世界」的防腐层。

    所有 Agent 输出都先收敛为 AgentEvent，
    再由 presentation 层转换为具体传输格式（SSE / WebSocket / 语音 等）。
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
