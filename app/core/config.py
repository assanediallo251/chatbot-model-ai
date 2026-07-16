from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ISI Chatbot API"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot_isi"
    )

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 700

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimensions: int = 384

    chunk_size: int = Field(default=800, ge=200)
    chunk_overlap: int = Field(default=120, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    max_upload_mb: int = Field(default=20, ge=1, le=100)

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
