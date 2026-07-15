import unittest

from app.agent.prompt import build_messages, build_system_prompt, build_user_prompt


class PromptTest(unittest.TestCase):
    def test_builds_minimal_system_and_user_prompts(self):
        self.assertIn("pang-agent", build_system_prompt())
        self.assertEqual(build_user_prompt("hello"), "hello")
        self.assertEqual(
            build_messages("hello"),
            [("system", build_system_prompt()), ("human", "hello")],
        )
