def build_system_prompt() -> str:
    # 统一 Prompt 入口；记忆和工具上下文实际出现后再在此补充。
    return "你是 pang-agent，一个通过自然语言帮助用户操作系统的 AI Agent。回答要简洁、准确。"


def build_user_prompt(message: str) -> str:
    return message


def build_messages(message: str) -> list[tuple[str, str]]:
    return [("system", build_system_prompt()), ("human", build_user_prompt(message))]
