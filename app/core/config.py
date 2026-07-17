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
    groq_retry_attempts: int = Field(default=4, ge=1, le=8)
    groq_retry_min_seconds: float = Field(default=1.0, ge=0.1, le=30.0)
    groq_retry_max_seconds: float = Field(default=20.0, ge=1.0, le=120.0)

    embedding_provider: Literal["hashing", "sentence_transformers"] = "hashing"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimensions: int = 384
    embedding_batch_size: int = 32
    embedding_preload_on_startup: bool = False

    chunk_size: int = Field(default=800, ge=200)
    chunk_overlap: int = Field(default=120, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    isi_official_url: str = "https://www.groupeisi.com/"
    isi_corpus_filter_enabled: bool = True
    isi_corpus_keywords: str = (
        "Institut Superieur d'Informatique,"
        "Institut Supérieur d'Informatique,"
        "Groupe ISI,"
        "groupeisi,"
        "groupeisi.com,"
        "www.groupeisi.com"
    )
    isi_acronym_regex: str = r"\misi\M"
    external_search_enabled: bool = True
    external_search_timeout_seconds: float = Field(default=4.0, ge=1.0, le=30.0)
    external_search_total_timeout_seconds: float = Field(default=12.0, ge=2.0, le=60.0)
    external_search_max_pages: int = Field(default=5, ge=1, le=30)
    external_search_max_sources: int = Field(default=4, ge=1, le=10)
    external_search_min_score: float = Field(default=0.35, ge=0.0, le=1.0)
    external_search_trigger_keywords: str = (
        "tarif,"
        "tarifs,"
        "tarification,"
        "prix,"
        "cout,"
        "coût,"
        "frais,"
        "scolarite,"
        "scolarité,"
        "mensualite,"
        "mensualité,"
        "paiement,"
        "inscription,"
        "admission,"
        "directeur,"
        "direction,"
        "president,"
        "président,"
        "pdg,"
        "diplome,"
        "diplôme,"
        "diplomes,"
        "diplômes,"
        "reconnu,"
        "reconnus,"
        "reconnaissance,"
        "accreditation,"
        "accréditation,"
        "cames,"
        "anaq,"
        "anaq-sup,"
        "anaqsup,"
        "histoire,"
        "historique,"
        "presentation,"
        "présentation,"
        "creation,"
        "création,"
        "fondateur,"
        "fondation,"
        "contact,"
        "campus,"
        "formation,"
        "formations,"
        "horaire,"
        "horaires"
    )
    external_search_seed_urls: str = (
        "https://www.groupeisi.com/,"
        "https://siege.groupeisi.com/paiement/,"
        "https://siege.groupeisi.com/administration/,"
        "https://siege.groupeisi.com/mot-du-pdg/,"
        "https://www.groupeisi.com/?page_id=47335,"
        "https://www.groupeisi.com/?page_id=25185,"
        "https://www.groupeisi.com/?page_id=50350"
    )
    external_search_allowed_domains: str = (
        "groupeisi.com,"
        "siege.groupeisi.com,"
        "elearning-groupeisi.com,"
        "test.groupeisi.com,"
        "isikeurmassar.com,"
        "isisuptech.com,"
        "ziguinchor.groupeisi.com,"
        "diourbel.groupeisi.com,"
        "cfegroupeisi.com"
    )

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def isi_corpus_keyword_list(self) -> list[str]:
        return [
            keyword.strip()
            for keyword in self.isi_corpus_keywords.split(",")
            if keyword.strip()
        ]

    @computed_field
    @property
    def external_search_trigger_keyword_list(self) -> list[str]:
        return [
            keyword.strip()
            for keyword in self.external_search_trigger_keywords.split(",")
            if keyword.strip()
        ]

    @computed_field
    @property
    def external_search_seed_url_list(self) -> list[str]:
        return [
            url.strip()
            for url in self.external_search_seed_urls.split(",")
            if url.strip()
        ]

    @computed_field
    @property
    def external_search_allowed_domain_list(self) -> list[str]:
        return [
            domain.strip().casefold()
            for domain in self.external_search_allowed_domains.split(",")
            if domain.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
