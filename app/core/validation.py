from loguru import logger

from app.config import settings


def validate_settings() -> None:
    """启动时配置校验。新增校验项直接在此函数内追加。"""
    if not settings.llm_api_key:
        logger.warning("LLM_API_KEY is not configured — streaming will fail at runtime without LLM key")
