from langgraph.graph import END, START, StateGraph

from app.agent.state import AgentState


def echo_node(state: AgentState) -> dict[str, str]:
    # ponytail: deterministic stub; replace this node with real LLM/tool logic later.
    return {"reply": f"pang-agent received: {state['message']}"}


builder = StateGraph(AgentState)
builder.add_node("echo", echo_node)

builder.add_edge(START, "echo")
builder.add_edge("echo", END)

agent_graph = builder.compile()


def invoke_agent(message: str) -> str:
    result = agent_graph.invoke({"message": message, "reply": ""})
    return result["reply"]
