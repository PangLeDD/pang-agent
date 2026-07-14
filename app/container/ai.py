from langchain_openai import ChatOpenAI

from app.config import settings


class AIContainer:
    """AI 相关长生命周期资源：LLM 客户端、Embedding 等。"""

    def __init__(self) -> None:
        self._llm: ChatOpenAI | None = None

    @property
    def llm(self) -> ChatOpenAI:
        """LLM 客户端单例，首次访问时懒初始化。"""
        if self._llm is None:
            if not settings.llm_api_key:
                raise RuntimeError("LLM_API_KEY is not configured")
            self._llm = ChatOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
        return self._llm
