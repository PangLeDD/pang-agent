import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from app.container.infra import InfraContainer
from app.main import lifespan


class InfraContainerTest(unittest.IsolatedAsyncioTestCase):
    async def test_init_closes_connection_and_raises_when_setup_fails(self):
        """setup() 失败时应关闭连接、向上抛异常，且 checkpointer 保持 None。"""
        with patch("app.container.infra.AsyncPostgresSaver") as saver_class, \
             patch("app.container.infra.AsyncConnection.connect", new_callable=AsyncMock) as connect:
            conn = AsyncMock()
            saver = MagicMock()
            saver.setup = AsyncMock(side_effect=RuntimeError("setup failed"))
            connect.return_value = conn
            saver_class.return_value = saver

            container = InfraContainer()

            with self.assertRaisesRegex(RuntimeError, "setup failed"):
                await container.init_checkpointer()

            self.assertIsNone(container.checkpointer)
            conn.close.assert_awaited_once()

    async def test_init_success_exposes_saver(self):
        """成功的 setup() 后 checkpointer 属性应暴露 AsyncPostgresSaver 实例。"""
        with patch("app.container.infra.AsyncPostgresSaver") as saver_class, \
             patch("app.container.infra.AsyncConnection.connect", new_callable=AsyncMock) as connect:
            conn = AsyncMock()
            saver = MagicMock()
            saver.setup = AsyncMock()
            connect.return_value = conn
            saver_class.return_value = saver

            container = InfraContainer()
            await container.init_checkpointer()

            self.assertIsNotNone(container.checkpointer)
            self.assertEqual(container.checkpointer, saver)

    async def test_close_closes_connection(self):
        """close() 应关闭内部持有的连接。"""
        container = InfraContainer()
        container._conn = AsyncMock()
        container._checkpointer = MagicMock()

        await container.close()

        container._conn.close.assert_awaited_once()

    async def test_close_noop_when_no_connection(self):
        """未初始化连接时 close() 应安全无操作。"""
        container = InfraContainer()

        # 不应抛出异常。
        await container.close()

    async def test_lifespan_raises_when_init_checkpointer_fails(self):
        """lifespan 中 init_checkpointer 抛出异常时应阻止 yielding，向上传播异常。"""
        with patch("app.main.get_container") as get_container:
            get_container.return_value.infra.init_checkpointer = AsyncMock(
                side_effect=RuntimeError("checkpoint unavailable")
            )
            with self.assertRaisesRegex(RuntimeError, "checkpoint unavailable"):
                async with lifespan(FastAPI()):
                    self.fail("lifespan must not yield")
