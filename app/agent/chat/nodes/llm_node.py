from app.agent.chat.state import ChatState
from app.agent.prompt import build_messages


class LLMNode:
    """Invoke the configured LLM without knowing the graph topology."""

    def __init__(self, llm) -> None:
        self._llm = llm

    def __call__(self, state: ChatState) -> dict[str, str]:
        response = self._llm.invoke(build_messages(state["message"]))
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"reply": content}
