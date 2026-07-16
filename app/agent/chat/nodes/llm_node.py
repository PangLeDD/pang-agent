from langchain_core.messages import AIMessage, SystemMessage

from app.agent.chat.state import ChatState
from app.agent.prompt import build_system_prompt


class LLMNode:
    """调用已配置的 LLM，不感知图拓扑。"""

    def __init__(self, llm) -> None:
        self._llm = llm

    def __call__(self, state: ChatState) -> dict:
        messages = [SystemMessage(content=build_system_prompt())]
        messages.extend(state["messages"])
        response = self._llm.invoke(messages)
        return {"messages": [response]}
