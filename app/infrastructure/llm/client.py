from langchain_openai import ChatOpenAI

from app.agent.prompt import build_messages
from app.container import get_container


def get_llm() -> ChatOpenAI:
    return get_container().ai.llm


def invoke_llm(message: str) -> str:
    response = get_llm().invoke(build_messages(message))
    return response.content if isinstance(response.content, str) else str(response.content)
