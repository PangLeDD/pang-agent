from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage
from loguru import logger

from app.agent import AgentExecutor, EventType
from app.presentation import sse_event

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class ChatService:
    """编排一次对话请求的完整流程。

    API 层只做 HTTP 收口，业务编排全部下沉到这里。
    executor / conversations / title_llm 均可注入，方便测试和后续扩展。
    """

    def __init__(self, executor: AgentExecutor | None = None, conversations=None, title_llm=None) -> None:
        self._executor = executor or AgentExecutor()
        self._conversations = conversations
        self._title_llm = title_llm

    async def prepare_conversation(self, conversation_id: UUID, user_id: str) -> Conversation:
        """预检会话归属，返回会话或抛出 HTTP 404。"""
        if self._conversations is None:
            raise RuntimeError("Conversation persistence not configured")
        return await self._conversations.prepare_conversation(conversation_id, user_id)

    async def stream(
        self, message: str, conversation_id: UUID | None, user_id: str,
        conversation: Conversation | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        conv = await self._prepare(message, conversation_id, user_id, conversation)

        full_response = ""
        held_end = None
        try:
            async for event in self._executor.run(message, thread_id=f"{user_id}:{conv.id}"):
                if event.type == EventType.CONVERSATION_START:
                    # ponytail: 复制载荷，避免跨层修改 AgentEvent。
                    yield sse_event(event.type, {**event.payload, "conversation_id": str(conv.id)})
                elif event.type == EventType.CONVERSATION_END:
                    held_end = event  # 暂存结束事件，在持久化完成后再发送。
                elif event.type == EventType.MESSAGE_DELTA:
                    full_response += event.payload.get("delta", "")
                    yield sse_event(event.type, event.payload)
                else:
                    yield sse_event(event.type, event.payload)
        except Exception:
            logger.exception("Agent stream failed: conversation_id={}", conv.id)
            yield sse_event(EventType.ERROR, {"code": 500, "message": "Internal Server Error"})
        else:
            if full_response and self._conversations is not None:
                await self._conversations.add_message(conv, "assistant", full_response)
                if conv.title == "New Chat" and self._title_llm:
                    await self._generate_title(conv, message, full_response[:200])

        if held_end is not None:
            yield sse_event(held_end.type, held_end.payload)

    async def _prepare(
        self, message: str, conversation_id: UUID | None, user_id: str,
        conversation: Conversation | None = None,
    ):
        """解析或创建会话并持久化用户消息，返回会话对象。"""
        if self._conversations is None:
            # ponytail: 未注入持久化层时仅生成 SSE 所需的临时 ID。
            class _Ephemeral:
                pass
            conv = _Ephemeral()
            conv.id = str(conversation_id) if conversation_id else str(uuid4())
            return conv

        if conversation is not None:
            # ponytail: API 预检已解析会话，避免重复查询。
            conv = conversation
        else:
            conv = await self._conversations.prepare_conversation(conversation_id, user_id)
        await self._conversations.add_message(conv, "user", message)
        return conv

    async def _generate_title(self, conv, user_msg: str, assistant_snippet: str) -> None:
        """尽力生成标题，不抛出异常，也不发送 SSE 事件。"""
        try:
            prompt = (
                "Generate a short, concise title (max 6 words) for a conversation.\n\n"
                f"User: {user_msg}\n"
                f"Assistant: {assistant_snippet}\n\n"
                "Title:"
            )
            response = await asyncio.wait_for(
                self._title_llm.ainvoke([HumanMessage(content=prompt)]),
                timeout=5.0,
            )
            title = response.content.strip().strip('"').strip("'")
            if title:
                await self._conversations.update_title(conv.id, conv.user_id, title)
        except Exception:
            pass  # ponytail: 标题生成失败时保留 "New Chat"，不影响聊天结果。



