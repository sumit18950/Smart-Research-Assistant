"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: Literal["openai", "anthropic"] = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Vector Store
    vector_store_type: Literal["faiss", "pinecone"] = "faiss"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "research-assistant"
    pinecone_environment: str = "us-east-1"

    # FAISS
    faiss_index_path: str = "./data/vectorstore/faiss_index"

    # Web Search
    serpapi_key: str = ""

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    users_db_path: str = "./data/users.json"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    confidence_threshold: float = 0.6
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def faiss_path(self) -> Path:
        path = Path(self.faiss_index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    return Settings()
