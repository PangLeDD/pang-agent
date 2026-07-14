from langgraph.graph import END, START, StateGraph

from app.agent.state import AgentState
from app.infrastructure.llm import invoke_llm


def echo_node(state: AgentState) -> dict[str, str]:
    return {"reply": invoke_llm(state["message"])}


builder = StateGraph(AgentState)
builder.add_node("echo", echo_node)

builder.add_edge(START, "echo")
builder.add_edge("echo", END)

agent_graph = builder.compile()
