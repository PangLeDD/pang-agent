from app.agent.chat.builder import ChatGraphBuilder


class GraphFactory:
    """选择图构建器，并为一个执行器编译图。"""

    _builders = {"chat": ChatGraphBuilder}

    def create(self, graph_name: str, llm, checkpointer=None):
        try:
            builder = self._builders[graph_name]()
        except KeyError as exc:
            raise ValueError(f"Unknown graph: {graph_name}") from exc
        return builder.build(llm, checkpointer)
