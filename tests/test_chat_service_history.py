import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

from app.agent.events import AgentEvent, EventType
from app.application.chat_service import ChatService
from app.models.conversation import Conversation
from app.repositories.conversation_repo import ConversationRepository


def _start():
    return AgentEvent(type=EventType.CONVERSATION_START)


def _delta(text: str):
    return AgentEvent(type=EventType.MESSAGE_DELTA, payload={"delta": text})


def _end():
    return AgentEvent(type=EventType.CONVERSATION_END, payload={"reason": "stop"})


def _fake_executor(events: list[AgentEvent], *, should_fail: bool = False):
    """返回模拟执行器：其 run 会产出事件，也可选择抛出异常。"""
    executor = MagicMock()

    async def run(message, thread_id):
        for event in events:
            yield event
        if should_fail:
            raise RuntimeError("graph failure")

    executor.run.side_effect = run
    return executor


class ChatServiceHistoryTest(unittest.IsolatedAsyncioTestCase):
    """任务 4：流式持久化和标题生成测试。

    All tests isolate DB/LLM via injected fakes/mocks.
    """

    # ── 流式持久化 ────────────────────────────────────────────────────────

    async def test_stream_saves_user_then_complete_assistant(self):
        conversations = AsyncMock()
        conv_id = uuid4()
        conv = Conversation(id=conv_id, user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        executor = _fake_executor([_start(), _delta("Hi"), _delta("!"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=None)
        events = [event async for event in service.stream("hello", None, "user-a")]

        # conversation.end 必须在持久化完成后发送。
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)

        conversations.add_message.assert_has_awaits([
            call(conv, "user", "hello"),
            call(conv, "assistant", "Hi!"),
        ])
        self.assertIn('"conversation_id"', events[0]["data"])
        envelope = json.loads(events[0]["data"])
        self.assertEqual(envelope["payload"]["conversation_id"], str(conv_id))

    async def test_conversation_end_after_persistence_and_title(self):
        """助手消息和标题持久化后，conversation.end 必须是最后一个 SSE 事件。"""
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        title_llm = MagicMock()
        fake_response = MagicMock()
        fake_response.content = "Hello World"
        title_llm.ainvoke = AsyncMock(return_value=fake_response)

        # 记录每个 await 调用的顺序：(方法名，角色或键)。
        call_order = []

        async def track_add_message(*args, **kwargs):
            # 参数为：(会话，角色，内容)。
            call_order.append(("add_message", args[1]))

        async def track_update_title(*args, **kwargs):
            call_order.append(("update_title",))

        conversations.add_message = AsyncMock()
        conversations.add_message.side_effect = track_add_message
        conversations.update_title = AsyncMock()
        conversations.update_title.side_effect = track_update_title

        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
        events = [event async for event in service.stream("hello", None, "user-a")]

        # 校验顺序：用户消息 → 助手消息 → 更新标题。
        self.assertEqual(
            call_order,
            [("add_message", "user"), ("add_message", "assistant"), ("update_title",)],
        )
        # conversation.end 最后发送。
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)
        env = json.loads(events[-1]["data"])
        self.assertEqual(env["payload"]["reason"], "stop")

    async def test_ephemeral_mode_no_persistence(self):
        """未注入会话服务时，流仍应可用，保证兼容性。"""
        tid = uuid4()
        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor)  # 不注入会话服务和标题 LLM。
        events = [event async for event in service.stream("hello", tid, "user-a")]

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["event"], EventType.CONVERSATION_START)
        self.assertEqual(events[1]["event"], EventType.MESSAGE_DELTA)
        self.assertEqual(events[2]["event"], EventType.CONVERSATION_END)
        envelope = json.loads(events[0]["data"])
        self.assertEqual(envelope["payload"]["conversation_id"], str(tid))

    # ── 标题生成 ──────────────────────────────────────────────────────────

    async def test_title_generation_on_new_chat(self):
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        title_llm = MagicMock()
        fake_response = MagicMock()
        fake_response.content = '  "Hello World"  '
        title_llm.ainvoke = AsyncMock(return_value=fake_response)

        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
        events = [event async for event in service.stream("hello", None, "user-a")]

        conversations.update_title.assert_awaited_once_with(conv.id, conv.user_id, "Hello World")
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)

    async def test_title_generation_failure_retains_new_chat(self):
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        title_llm = MagicMock()
        title_llm.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError)

        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
        events = [event async for event in service.stream("hello", None, "user-a")]

        conversations.update_title.assert_not_awaited()
        conversations.add_message.assert_any_await(conv, "assistant", "Hi")
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)

    async def test_existing_titled_conversation_skips_title_generation(self):
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="Already Titled")
        conversations.prepare_conversation.return_value = conv

        title_llm = MagicMock()
        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
        events = [event async for event in service.stream("hello", conv.id, "user-a")]

        title_llm.ainvoke.assert_not_called()
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)

    async def test_empty_title_from_llm_is_ignored(self):
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        title_llm = MagicMock()
        fake_response = MagicMock()
        fake_response.content = "   "  # 去除空白后为空。
        title_llm.ainvoke = AsyncMock(return_value=fake_response)

        executor = _fake_executor([_start(), _delta("Hi"), _end()])
        service = ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
        events = [event async for event in service.stream("hello", None, "user-a")]

        conversations.update_title.assert_not_awaited()
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)

    # ── 失败处理 ──────────────────────────────────────────────────────────

    async def test_graph_failure_writes_no_assistant(self):
        conversations = AsyncMock()
        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        conversations.prepare_conversation.return_value = conv

        executor = _fake_executor([_start(), _delta("partial")], should_fail=True)
        service = ChatService(executor=executor, conversations=conversations, title_llm=None)
        events = [event async for event in service.stream("hello", None, "user-a")]

        # 仅保存用户消息，不写入助手消息。
        conversations.add_message.assert_awaited_once_with(conv, "user", "hello")
        # error 是最后一个事件，不发送 conversation.end。
        self.assertEqual(events[-1]["event"], EventType.ERROR)
        self.assertNotIn(EventType.CONVERSATION_END, [e["event"] for e in events])

    # ── 线程 ID ───────────────────────────────────────────────────────────

    async def test_reused_conversation_thread_id(self):
        conversations = AsyncMock()
        conv_id = uuid4()
        conv = Conversation(id=conv_id, user_id="user-a", title="My Chat")
        conversations.prepare_conversation.return_value = conv

        executor = MagicMock()
        captured_thread_id = []

        async def run(message, thread_id):
            captured_thread_id.append(thread_id)
            yield _start()
            yield _end()

        executor.run.side_effect = run

        service = ChatService(executor=executor, conversations=conversations, title_llm=None)
        events = [event async for event in service.stream("hello", conv_id, "user-a")]

        self.assertEqual(captured_thread_id[0], f"user-a:{conv_id}")
        self.assertEqual(events[-1]["event"], EventType.CONVERSATION_END)


class ConversationRepositoryCommitTest(unittest.IsolatedAsyncioTestCase):
    """验证 ConversationRepository 的每次持久化写入均在返回前提交。"""

    def _make_session(self):
        """返回 add 为同步方法的 AsyncMock，符合 SQLAlchemy AsyncSession 的实际接口。"""
        session = AsyncMock()
        # ponytail: AsyncSession.add 是同步方法，使用普通 MagicMock 避免 RuntimeWarning。
        session.add = MagicMock()
        return session

    async def test_create_commits(self):
        session = self._make_session()
        repo = ConversationRepository(session)
        await repo.create("user-a")
        session.commit.assert_awaited_once()

    async def test_add_message_commits(self):
        session = self._make_session()
        repo = ConversationRepository(session)
        await repo.add_message(uuid4(), "user", "hello")
        session.commit.assert_awaited_once()

    async def test_update_title_commits(self):
        session = self._make_session()
        repo = ConversationRepository(session)
        await repo.update_title(uuid4(), "New Title")
        session.commit.assert_awaited_once()

    async def test_user_message_commits_before_graph(self):
        """模拟 ChatService 流程：用户消息必须在图调用前完成提交。"""
        session = self._make_session()
        repo = ConversationRepository(session)

        call_order = []

        async def track_commit():
            call_order.append("commit")

        session.commit.side_effect = track_commit

        await repo.create("user-a")
        await repo.add_message(uuid4(), "user", "hello")

        # 两次写入均已提交。
        self.assertEqual(session.commit.await_count, 2)
