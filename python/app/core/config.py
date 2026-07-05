from functools import lru_cache
from pathlib import Path

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
    cors_origins_raw: str = "http://localhost:5174,http://127.0.0.1:5174"
    sqlite_path: str = "agent_demo.db"
    # API Key 只从环境变量读取，不把真实密钥写进源码。
    openai_api_key: str = Field(default="", repr=False)
    # DeepSeek 的 OpenAI 兼容接口地址。
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_model: str = "deepseek-chat"
    assistant_system_prompt: str = "你是一个中文 AI 助手，请优先给出准确、直接、可执行的回答。"
    request_timeout_seconds: float = 60.0

    # RAG 知识库配置
    embedding_api_key: str = Field(default="", repr=False)
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "./chroma_db"
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 3
    max_upload_size_mb: int = 10

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

    @property
    def resolved_sqlite_path(self) -> Path:
        sqlite_path = Path(self.sqlite_path).expanduser()
        if sqlite_path.is_absolute():
            return sqlite_path

        return Path(__file__).resolve().parents[2] / sqlite_path

    @property
    def resolved_chroma_dir(self) -> Path:
        chroma_path = Path(self.chroma_persist_dir).expanduser()
        if chroma_path.is_absolute():
            return chroma_path

        return Path(__file__).resolve().parents[2] / chroma_path

    @property
    def effective_embedding_api_key(self) -> str:
        """Embedding API Key 未单独配置时，回退到 openai_api_key。"""
        return self.embedding_api_key or self.openai_api_key

    @property
    def effective_embedding_base_url(self) -> str:
        """Embedding Base URL 未单独配置时，回退到 openai_base_url。"""
        return self.embedding_base_url or self.openai_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
