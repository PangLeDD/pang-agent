import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 读取配置。字段名大小写不敏感，自动匹配 .env 中的变量。"""

    # ===== DeepSeek =====
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ===== LangSmith =====
    langsmith_tracing: bool = True
    langsmith_api_key: str
    langsmith_project: str = "pang-agent-home"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def apply_langsmith_env(self) -> None:
        """LangSmith SDK 只认 os.environ，这里把配置回写到进程环境变量。"""
        os.environ["LANGSMITH_TRACING"] = str(self.langsmith_tracing).lower()
        os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = self.langsmith_endpoint


settings = Settings()
