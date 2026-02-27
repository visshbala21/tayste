from pydantic_settings import BaseSettings
from functools import lru_cache


def _normalize_async_db_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


def _normalize_sync_db_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://"):]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://tayste:tayste_dev@db:5432/tayste"
    database_url_sync: str = "postgresql://tayste:tayste_dev@db:5432/tayste"
    openai_api_key: str = ""
    youtube_api_key: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_market: str = "US"
    soundcharts_app_id: str = ""
    soundcharts_api_key: str = ""
    soundcharts_api_base: str = "https://customer.api.soundcharts.com"
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

    # Emerging artist defaults (quality gates)
    emerging_max_spotify_followers: int = 100000
    emerging_max_spotify_popularity: int = 35
    emerging_max_followers: int = 250000
    emerging_min_growth_7d: float = 0.03
    emerging_min_growth_30d: float = 0.10
    emerging_min_momentum: float = 0.25

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_url = _normalize_async_db_url(settings.database_url)
    if settings.database_url_sync:
        settings.database_url_sync = _normalize_sync_db_url(settings.database_url_sync)
    else:
        settings.database_url_sync = _normalize_sync_db_url(settings.database_url)
    return settings
