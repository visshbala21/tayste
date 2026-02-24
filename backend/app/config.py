from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://tayste:tayste_dev@db:5432/tayste"
    database_url_sync: str = "postgresql://tayste:tayste_dev@db:5432/tayste"
    openai_api_key: str = ""
    youtube_api_key: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_market: str = "US"
    soundcloud_client_id: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # LLM settings
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 4096
    llm_timeout: int = 30
    llm_max_retries: int = 3

    # Ranking weights
    fit_weight: float = 1.0
    momentum_weight: float = 1.0
    risk_weight: float = 1.0

    # Embedding dimensions
    embedding_dim: int = 128

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
