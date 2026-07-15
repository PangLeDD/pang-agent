from langgraph.graph import END, START, StateGraph

from app.agent.prompt import build_messages
from app.agent.state import AgentState


def build_agent_graph(llm):
    def echo_node(state: AgentState) -> dict[str, str]:
        response = llm.invoke(build_messages(state["message"]))
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"reply": content}

    builder = StateGraph(AgentState)
    builder.add_node("echo", echo_node)

    builder.add_edge(START, "echo")
    builder.add_edge("echo", END)
    return builder.compile()
