import unittest
from unittest.mock import Mock, patch

from app.infrastructure.llm import invoke_llm
from app.agent.prompt import build_messages, build_system_prompt, build_user_prompt


class PromptTest(unittest.TestCase):
    def test_builds_minimal_system_and_user_prompts(self):
        self.assertIn("pang-agent", build_system_prompt())
        self.assertEqual(build_user_prompt("hello"), "hello")
        self.assertEqual(
            build_messages("hello"),
            [("system", build_system_prompt()), ("human", "hello")],
        )

    def test_invoke_llm_sends_chat_messages(self):
        fake_llm = Mock()
        fake_llm.invoke.return_value = Mock(content="model reply")

        with patch("app.infrastructure.llm.client.get_llm", return_value=fake_llm):
            self.assertEqual(invoke_llm("hello"), "model reply")

        fake_llm.invoke.assert_called_once_with(build_messages("hello"))
