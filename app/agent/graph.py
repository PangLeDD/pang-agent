from langgraph.graph import END, START, StateGraph

from app.agent.state import AgentState
from app.config import settings
from app.infrastructure.llm import invoke_llm


def echo_node(state: AgentState) -> dict[str, str]:
    # ponytail: no key keeps local tests deterministic; real key switches to LLM.
    if settings.llm_api_key:
        return {"reply": invoke_llm(state["message"])}
    return {"reply": f"pang-agent received: {state['message']}"}


builder = StateGraph(AgentState)
builder.add_node("echo", echo_node)

builder.add_edge(START, "echo")
builder.add_edge("echo", END)

agent_graph = builder.compile()


def invoke_agent(message: str) -> str:
    """同步调用入口，供 /agent/invoke 使用。"""
    result = agent_graph.invoke({"message": message, "reply": ""})
    return result["reply"]
