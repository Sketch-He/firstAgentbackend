from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # 真实运行配置只从 .env 读取，.env.example 仅作为模板保留。
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "Agent Demo API"
    api_prefix: str = "/api"
    cors_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    # API Key 只从环境变量读取，不把真实密钥写进源码。
    openai_api_key: str = Field(default="", repr=False)
    # DeepSeek 的 OpenAI 兼容接口地址。
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_model: str = "deepseek-chat"
    assistant_system_prompt: str = "你是一个中文 AI 助手，请优先给出准确、直接、可执行的回答。"
    request_timeout_seconds: float = 60.0

    @field_validator("cors_origins_raw", mode="before")
    @classmethod
    def normalize_cors_origins_raw(cls, value: str | list[str]) -> str:
        # 允许 .env 里用逗号分隔的字符串来配置多个前端来源。
        if isinstance(value, str):
            return value

        return ",".join(item.strip() for item in value if item.strip())

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
