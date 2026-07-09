from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm() -> ChatOpenAI:
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured")
    # OpenAI-compatible endpoint, so DeepSeek/Qwen/local gateways can swap by config.
    return ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


def invoke_llm(message: str) -> str:
    response = get_llm().invoke(message)
    return response.content if isinstance(response.content, str) else str(response.content)
