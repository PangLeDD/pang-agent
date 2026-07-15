from langgraph.graph import END, START, StateGraph

from app.agent.chat.nodes.llm_node import LLMNode
from app.agent.chat.state import ChatState


class ChatGraphBuilder:
    """Assemble and compile the chat graph."""

    def build(self, llm, checkpointer=None):
        builder = StateGraph(ChatState)
        builder.add_node("llm", LLMNode(llm))
        builder.add_edge(START, "llm")
        builder.add_edge("llm", END)
        return builder.compile()
