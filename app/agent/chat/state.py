from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """Chat 业务 State，继承 MessagesState 的 messages 累积语义。

    后续按需追加业务字段（如 user_id、context、tools_result 等）。
    """
