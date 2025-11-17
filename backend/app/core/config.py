"""Application configuration powered by pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_DB_PATH = _BASE_DIR / "data" / "maa_remote.db"


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    app_name: str = "MAA Remote Control Server"
    debug: bool = False
    database_url: str = Field(
        default=f"sqlite:///{_DEFAULT_DB_PATH}",
        description="Database connection string.",
    )
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"], description="CORS origins for REST API."
    )
    api_prefix: str = "/api"
    maa_get_task_endpoint: str = "/maa/getTask"
    maa_report_status_endpoint: str = "/maa/reportStatus"

    model_config = SettingsConfigDict(
        env_prefix="MAA_",
        env_file=(_BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


settings = get_settings()

__all__ = ["Settings", "settings", "get_settings"]

